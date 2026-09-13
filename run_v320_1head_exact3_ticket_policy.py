#!/usr/bin/env python3
"""v320: exact-3-ticket policy optimization after v319 ordered-pair underperformed.

Frozen v308 cohort: 345 races / 290 boat-1 wins. Uses the stronger factorized
v317 SECOND + v318 DROPSTART_T0.1 THIRD probability reference. The ranking models
are frozen; this experiment changes ticket ordering only. Exactly three tickets are
issued for every race in the fixed cohort. Feb-Jun development only; Jul/Aug remain
NON-PRISTINE and September outcomes remain unread. v313 cache only; no meet_* or
future backfill. Month M models train only on months before M.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v317_1head_opponent_error_features as v317
import run_v318_1head_opponent_third_rebuild as v318
import run_v299_1head_trifecta3_policy_search as v299

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P=ROOT/'analysis_v320_1head_exact3_ticket_policy'
S=ROOT/'summary_v320_1head_exact3_ticket_policy.md'
TM=list(v298.TEST_MONTHS)
ALPHAS=(.20,.30,.40,.50,.60,.70,.80)


def assert_dev_months():
    bad=[m for m in TM if str(m).startswith(('2026-07','2026-08','2026-09'))]
    if bad: raise RuntimeError(f'v320 forbidden evaluation months {bad}')


def build_factorized(d,p3,p4):
    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v320 forbidden meet suffix')
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(d,sufs)),p3,p4)
    sx,_=v317.add_engineered(sl,'OUTER')
    p2={tm:v311.p2_predict_explicit(sx,tm,1.0,None,{'START'})[0] for tm in TM}
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    pc={tm:v318.pc_predict(cl,tm,.1,'DROP_START')[0] for tm in TM}
    return p2,pc


def evaluate_policy(name,alpha,p2,pc,d,ids):
    rows=[]
    fn=v299.STRATEGIES[name]
    for tm in TM:
        q=d[(d.month==tm)&(d.race_code.isin(ids))]
        for _,r in q.iterrows():
            code=str(r.race_code).zfill(12)
            probs=v299.pair_prob(p2[tm][code],pc[tm][code],alpha)
            order=fn(p2[tm][code],pc[tm][code],probs)
            top3=order[:3]
            if len(top3)!=3 or len(set(top3))!=3: raise RuntimeError(f'v320 invalid 3-ticket set {code}')
            tickets=';'.join(f'1-{s}-{t}' for s,t in top3)
            parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts)
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual_combo':str(r.actual_combo),
                         'tickets':tickets,'hit':int(str(r.actual_combo) in tickets),
                         'strategy':name,'alpha':alpha})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290: raise RuntimeError(f'v320 frozen mismatch {len(z)}/{int(z.head_hit.sum())}')
    gm=z.groupby('month').hit.agg(['size','sum','mean']).reset_index()
    return z,{'strategy':name,'alpha':alpha,'R':345,'head_hits':290,'hits':int(z.hit.sum()),
              'hit_rate':float(z.hit.mean()),'worst_month':float(gm['mean'].min())},gm


def main():
    assert_dev_months()
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen.race_code=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError('v320 cohort changed')
    ids=set(frozen.race_code)
    d,p3,p4=v312.load_cache(); d.race_code=d.race_code.astype(str).str.zfill(12)
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise RuntimeError('v320 cache frozen mismatch')
    p2,pc=build_factorized(d,p3,p4)

    sums=[]; outs=[]; monthly=[]
    for a in ALPHAS:
        for name in v299.STRATEGIES:
            z,m,gm=evaluate_policy(name,a,p2,pc,d,ids)
            outs.append(z); sums.append(m)
            gm=gm.rename(columns={'size':'R','sum':'hits','mean':'hit_rate'})
            gm['strategy']=name; gm['alpha']=a; monthly.append(gm)
            print('v320',name,a,m,flush=True)
    sm=pd.DataFrame(sums)
    allz=pd.concat(outs,ignore_index=True); mon=pd.concat(monthly,ignore_index=True)
    base=sm[(sm.strategy=='TOP2XTOP2')&(np.isclose(sm.alpha,.60))].iloc[0]
    if int(base.hits)!=137: raise RuntimeError(f'v320 baseline drift {int(base.hits)} != 137')
    sm['delta_vs_factorized_pp']=100*(sm.hit_rate-float(base.hit_rate))
    best=sm.sort_values(['hit_rate','worst_month','hits'],ascending=False).iloc[0]
    bz=allz[(allz.strategy==best.strategy)&(np.isclose(allz.alpha,float(best.alpha)))].copy()
    bm=mon[(mon.strategy==best.strategy)&(np.isclose(mon.alpha,float(best.alpha)))].copy()
    sm.to_csv(str(P)+'_policies.csv',index=False)
    bz.to_csv(str(P)+'_best_race.csv',index=False)
    bm.to_csv(str(P)+'_best_monthly.csv',index=False)
    L=['# v320 exact-3-ticket policy optimization','',
       '- Fixed v308 cohort: **345 races / 290 boat-1 wins**; boat-1 losses remain misses.',
       '- Ranking reference frozen to factorized v317 SECOND + v318 DROPSTART_T0.1 THIRD because v319 direct pair was weaker.',
       '- Exactly 3 tickets on every race; no race filtering or denominator shrinkage.',
       '- v313 cache only; no `meet_*`; no future backfill; month M trains only before M.',
       '- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.','',
       '## Baseline',f'- TOP2XTOP2 alpha=.60: **{int(base.hits)}/345={100*base.hit_rate:.2f}%**, worst month **{100*base.worst_month:.2f}%**.','',
       '## Best',f'- **{best.strategy} alpha={best.alpha:.2f}**: **{int(best.hits)}/345={100*best.hit_rate:.2f}%**, delta **{best.delta_vs_factorized_pp:+.2f}pt**, worst month **{100*best.worst_month:.2f}%**.','',
       '## Monthly best','|month|R|hits|hit rate|','|---|---:|---:|---:|']
    for _,r in bm.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.hit_rate:.2f}%|')
    L += ['','## Automatic next decision','- If a policy materially improves exact3 with acceptable monthly stability, freeze it as the development winner; reused Feb-Jun evidence is not prospective validation.','- If no material stable gain, retain the factorized TOP2XTOP2 alpha=.60 baseline and stop micro-tuning ticket order.','- Any suspiciously large gain requires immediate leakage/causal audit.']
    S.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print(S.read_text(),flush=True)

if __name__=='__main__': main()
