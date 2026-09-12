#!/usr/bin/env python3
"""v310: rebuild SECOND ranking with causal 3-head/4-head attack probabilities.

The 1-head selection is frozen to the v308 345-race operating set. This is a focused
SECOND-model experiment motivated by v309: outer boats 4/5/6 were badly under-ranked.
We add result-blind, monthly walk-forward head-risk signals for boat 3 and boat 4 as
race/candidate context. THIRD remains the current v300 conditional model so any gain can
be attributed mainly to SECOND ranking.

Development only. Jul/Aug are NON-PRISTINE and are not part of scoring/selection here;
September outcomes remain unread.
"""
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v242_3head_target_comp3_min5_max10 as v242
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v309_1head_opponent_zero_base_audit as v309

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P4=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
P=ROOT/'analysis_v310_1head_opponent_headrisk_second'
S=ROOT/'summary_v310_1head_opponent_headrisk_second.md'
TM=list(v298.TEST_MONTHS)
L2S=(1.0,3.0,10.0,30.0)


def causal_p3_map():
    """Reproduce monthly walk-forward v243-family p3 for every test race."""
    cov=v242.v234.reconstruct()
    if (cov.source=='missing').any(): raise RuntimeError('missing restored Waku10 for p3')
    d,dc,vc,basefs=v242.v234.build_restored()
    fs=[x for x in v242.v234.full_features(d,basefs) if x in d.columns]
    out={}
    for mon in TM:
        first=pd.Timestamp(mon+'-01'); nxt=first+pd.offsets.MonthBegin(1)
        te,_=v242.v234.v223.fit_head(d,fs,vc,first,nxt)
        for _,r in te.iterrows():
            out[str(r.race_code).zfill(12)]=float(r._p)
        print('v310 p3',mon,len(te),flush=True)
    return out


def causal_p4_map():
    """Use v250 PRE probabilities, which are already monthly walk-forward and PRE-only."""
    if not P4.exists(): raise RuntimeError('missing v250 p4 walk-forward output')
    q=pd.read_csv(P4,dtype={'race_code':str})
    q=q[(q.variant=='PRE') & q.month.astype(str).isin(TM)].copy()
    q['race_code']=q.race_code.astype(str).str.zfill(12)
    if q.race_code.duplicated().any(): raise RuntimeError('duplicate PRE p4 race codes')
    return dict(zip(q.race_code,q.p4head.astype(float)))


def add_headrisk(sl,p3,p4):
    q=sl.copy()
    q['race_code']=q.race_code.astype(str).str.zfill(12)
    q['v310_p3head']=q.race_code.map(p3)
    q['v310_p4head']=q.race_code.map(p4)
    if q[['v310_p3head','v310_p4head']].isna().any().any():
        miss=q[q[['v310_p3head','v310_p4head']].isna().any(axis=1)].race_code.unique()[:10]
        raise RuntimeError(f'missing causal head-risk probabilities: {miss}')
    b=q.boat.astype(int)
    p3s=q.v310_p3head.astype(float); p4s=q.v310_p4head.astype(float)
    q['v310_attack34_max']=np.maximum(p3s,p4s)
    q['v310_attack34_sum']=p3s+p4s
    q['v310_attack34_gap']=p3s-p4s
    q['v310_candidate_headrisk']=np.where(b.eq(3),p3s,np.where(b.eq(4),p4s,0.0))
    # Role interactions let the listwise ranker learn how 3/4 attack pressure changes
    # the chance that each possible opponent becomes SECOND, including boats 5/6.
    for boat in v298.BOATS:
        role=b.eq(int(boat)).astype(float)
        q[f'v310_p3_x_b{boat}']=p3s*role
        q[f'v310_p4_x_b{boat}']=p4s*role
        q[f'v310_a34max_x_b{boat}']=q.v310_attack34_max*role
    return q


def evaluate(p2,pc,d,ids):
    rows=[]
    for tm in TM:
        q=d[d.month==tm].copy(); q['race_code']=q.race_code.astype(str).str.zfill(12); q=q[q.race_code.isin(ids)]
        for _,r in q.iterrows():
            code=r.race_code; parts=str(r.actual_combo).split('-')
            if len(parts)!=3: continue
            a1,a2,a3=map(int,parts); p2m=p2[tm][code]; pcm=pc[tm][code]
            sr=v309.rank_of(p2m,a2) if a1==1 else np.nan
            tickets=v300.ticket3(p2m,pcm).split(';')
            rows.append({'month':tm,'race_code':code,'head_hit':int(a1==1),'actual2':a2,
                         'second_rank':sr,'second_top1':int(a1==1 and sr<=1) if pd.notna(sr) else 0,
                         'second_top2':int(a1==1 and sr<=2) if pd.notna(sr) else 0,
                         'second_top3':int(a1==1 and sr<=3) if pd.notna(sr) else 0,
                         'exact3':int(str(r.actual_combo) in tickets)})
    z=pd.DataFrame(rows)
    if len(z)!=345 or int(z.head_hit.sum())!=290: raise RuntimeError(f'frozen mismatch {len(z)} {int(z.head_hit.sum())}')
    h=z[z.head_hit==1]
    return z,{'R':len(z),'exact3_hits':int(z.exact3.sum()),'exact3_rate':float(z.exact3.mean()),
              'second_top1':float(h.second_top1.mean()),'second_top2':float(h.second_top2.mean()),
              'second_top3':float(h.second_top3.mean())}


def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError(f'expected 345 frozen races, got {len(frozen)}')
    ids=set(frozen.race_code)
    p3=causal_p3_map(); p4=causal_p4_map()

    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre(); d=v298.v294.add_prior_history(d); d=v298.v294.add_rel(d); d,_=v298.add_threat(d)
    d,_=v298.v297.settle_full_after_freeze(d); d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    sufs=v298.suffixes(d)
    sl0=v300.augment_second(v298.second_long(d,sufs)); sl1=add_headrisk(sl0,p3,p4)
    cl=v300.augment_third(v298.conditional_long(d,sufs))

    # THIRD is frozen at v300 best (.1). Build it once per fold.
    pc={tm:v300.pc_predict(cl,tm,.1,True)[0] for tm in TM}
    configs=[('BASE',3.0,sl0)]+[(f'HEADRISK_L2_{l2:g}',l2,sl1) for l2 in L2S]
    summaries=[]; allrows=[]
    for name,l2,sl in configs:
        p2={tm:v300.p2_predict(sl,tm,l2,True)[0] for tm in TM}
        z,m=evaluate(p2,pc,d,ids); m.update({'config':name,'second_l2':l2}); summaries.append(m)
        z['config']=name; allrows.append(z)
        print(name,m,flush=True)
    sm=pd.DataFrame(summaries)
    base=sm[sm.config=='BASE'].iloc[0]
    sm['delta_second_top2_pp']=100*(sm.second_top2-base.second_top2)
    sm['delta_exact3_pp']=100*(sm.exact3_rate-base.exact3_rate)
    cand=sm[sm.config!='BASE'].sort_values(['second_top2','exact3_rate','second_top1'],ascending=False)
    best=cand.iloc[0]
    zall=pd.concat(allrows,ignore_index=True)
    bestz=zall[zall.config==best.config].copy(); bh=bestz[bestz.head_hit==1]
    bys=bh.groupby('actual2').agg(R=('race_code','size'),top1=('second_top1','mean'),top2=('second_top2','mean'),top3=('second_top3','mean'),exact3=('exact3','mean')).reset_index()
    mon=bestz.groupby('month').agg(R=('race_code','size'),head=('head_hit','sum'),exact3=('exact3','mean')).reset_index()
    mh=bh.groupby('month').agg(second_top1=('second_top1','mean'),second_top2=('second_top2','mean'),second_top3=('second_top3','mean')).reset_index(); mon=mon.merge(mh,on='month',how='left')

    sm.to_csv(str(P)+'_configs.csv',index=False); bys.to_csv(str(P)+'_best_by_second.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False); bestz.to_csv(str(P)+'_best_race.csv',index=False)
    L=['# v310 opponent SECOND with causal 3/4-head risk','',
       '- Frozen race set: v308 345 races; head model is unchanged.',
       '- p3: monthly walk-forward v243-family head probability using only earlier data for each month.',
       '- p4: v250 PRE monthly walk-forward probability; current-race exhibition is not used.',
       '- THIRD remains v300 conditional THIRD L2=.1.', '',
       '## Config comparison','|config|L2|second TOP1|TOP2|TOP3|exact3|dTOP2 pp|dExact3 pp|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in sm.sort_values(['second_top2','exact3_rate'],ascending=False).iterrows():
        L.append(f"|{r.config}|{r.second_l2:g}|{100*r.second_top1:.2f}%|{100*r.second_top2:.2f}%|{100*r.second_top3:.2f}%|{100*r.exact3_rate:.2f}%|{r.delta_second_top2_pp:+.2f}|{r.delta_exact3_pp:+.2f}|")
    L += ['',f'## Best: {best.config}',f'- SECOND TOP2: **{100*best.second_top2:.2f}%** (baseline {100*base.second_top2:.2f}%)',f'- exact 3-ticket: **{int(best.exact3_hits)}/345 = {100*best.exact3_rate:.2f}%** (baseline {100*base.exact3_rate:.2f}%)','',
          '## Best by actual SECOND','|boat|R|TOP1|TOP2|TOP3|exact3|','|---:|---:|---:|---:|---:|---:|']
    for _,r in bys.iterrows(): L.append(f"|{int(r.actual2)}|{int(r.R)}|{100*r.top1:.2f}%|{100*r.top2:.2f}%|{100*r.top3:.2f}%|{100*r.exact3:.2f}%|")
    L += ['', '## Monthly','|month|R|head wins|SECOND TOP2|exact3|','|---|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f"|{r.month}|{int(r.R)}|{int(r['head'])}|{100*r.second_top2:.2f}%|{100*r.exact3:.2f}%|")
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__': main()
