#!/usr/bin/env python3
"""v304: combine the best v303 head-model feature families on the same frozen 204 races.

Development-only. Jul/Aug remain NON-PRISTINE; September outcomes unread.
Every config preserves the v303 BASE selected count in each test month, so gains cannot
come from shrinking the denominator. Selection eligibility stays frozen to v298/v299 BASE.
"""
from pathlib import Path
import itertools
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v304_1head_headmodel_combo_research'
SUMMARY=ROOT/'summary_v304_1head_headmodel_combo_research.md'
TM=list(v298.TEST_MONTHS)

# v303 showed TURN_FORM strongest, WALL_INNER and STMOTOR next, ST_EDGE mildly positive.
CAND=('TURN_FORM','WALL_INNER','STMOTOR','ST_EDGE')

def main():
    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre();d=v298.v294.add_prior_history(d);d=v298.v294.add_rel(d);d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d)
    d,tf=v303.add_transfer_features(d)
    print('v304 PRE frozen; settlement now',flush=True)
    d,_=v298.v297.settle_full_after_freeze(d);d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    masses=v303.opponent_mass(d)
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat))
    guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]

    combos=[('BASE',set()),('TURN_FORM',{'TURN_FORM'})]
    for k in (2,3,4):
        for xs in itertools.combinations(CAND,k):
            if 'TURN_FORM' in xs:
                combos.append(('PLUS_'+'_'.join(xs),set(xs)))

    pred=[]
    for tm in TM:
        tr=d[d.month<tm].copy();te=d[d.month==tm].copy()
        z=te[['date','month','race_code','venue','race','head_hit']].copy();z['test_month']=tm
        z['opp_mass']=[masses[str(x).zfill(12)] for x in z.race_code]
        z['eligible']=(z.opp_mass>=v300.BASE_CONF).astype(int)
        base_core=v298.v293.available(tr,core0,.55);base_guard=v298.v293.available(tr,guard0,.55)
        ph,_,hc,_,_,_=v298.head_fold(tr,te,base_core,base_guard)
        z['p_BASE']=ph
        base_sel=(ph>=hc[.95])&(z.eligible.to_numpy()==1)
        n=int(base_sel.sum());z['sel_BASE']=base_sel.astype(int)
        for name,allowed in combos[1:]:
            extra=[]
            for f in allowed:extra+=v303.available(tr,tf[f])
            phx,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(base_core+extra)),base_guard)
            z[f'p_{name}']=phx
            idx=z[z.eligible==1].sort_values(f'p_{name}',ascending=False).head(n).index
            z[f'sel_{name}']=0;z.loc[idx,f'sel_{name}']=1
        pred.append(z);print('v304 fold',tm,'n',n,flush=True)

    p=pd.concat(pred,ignore_index=True)
    base=p[p.sel_BASE==1]
    if len(base)!=204 or int(base.head_hit.sum())!=166:
        raise RuntimeError(f'baseline drift R={len(base)} hits={int(base.head_hit.sum())}')

    rows=[];monthly=[]
    for name,allowed in combos:
        s=p[p[f'sel_{name}']==1];gm=s.groupby('test_month').head_hit.agg(['size','sum','mean'])
        rows.append({'config':name,'families':'+'.join(sorted(allowed)) if allowed else 'none','R':len(s),'head_hits':int(s.head_hit.sum()),'head_rate':float(s.head_hit.mean()),'worst_month':float(gm['mean'].min())})
        for mo,r in gm.iterrows():monthly.append({'config':name,'month':mo,'R':int(r['size']),'hits':int(r['sum']),'head_rate':float(r['mean'])})
    score=pd.DataFrame(rows);mon=pd.DataFrame(monthly)
    base_rate=float(score.loc[score.config=='BASE','head_rate'].iloc[0]);score['delta']=score.head_rate-base_rate
    # Primary objective head rate, tie-break by worst month.
    best=score.sort_values(['head_rate','worst_month','head_hits'],ascending=False).iloc[0]

    p.to_csv(str(PREFIX)+'_pred.csv',index=False);score.to_csv(str(PREFIX)+'_configs.csv',index=False);mon.to_csv(str(PREFIX)+'_monthly.csv',index=False)
    L=['# v304 1HEAD head-model combination research','',
       '- Development only; production unchanged.','- Jul/Aug NON-PRISTINE; September outcomes unread.',
       '- Same v303 frozen opponent eligibility and exact monthly selection counts.','- Baseline audit: 204 races / 166 head hits = 81.37%.','',
       '## Results','|config|families|R|head hits|head rate|delta|worst month|','|---|---|---:|---:|---:|---:|---:|']
    for _,r in score.sort_values(['head_rate','worst_month'],ascending=False).iterrows():
        L.append(f"|{r.config}|{r.families}|{int(r.R)}|{int(r.head_hits)}|{100*r.head_rate:.2f}%|{100*r.delta:+.2f}pt|{100*r.worst_month:.2f}%|")
    L+=['','## Best monthly audit','|month|R|hits|head rate|','|---|---:|---:|---:|']
    for _,r in mon[mon.config==best.config].iterrows():L.append(f"|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.head_rate:.2f}%|")
    L+=['','## Decision',f"- Best: **{best.config}: {int(best.head_hits)}/{int(best.R)} = {100*best.head_rate:.2f}%**, delta {100*best.delta:+.2f}pt vs BASE; worst month {100*best.worst_month:.2f}%.",
        '- Prefer a config that improves overall head rate without materially worsening the weakest month; this remains reused Feb-Jun development evidence.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
