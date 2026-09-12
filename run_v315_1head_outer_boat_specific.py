#!/usr/bin/env python3
"""v315: boat-specific outer SECOND probabilities on frozen 345R.

Runs after v314. Keeps the v308 head cohort fixed and THIRD frozen. For boats 4/5/6,
fit separate monthly walk-forward binary models P(actual SECOND == boat b) from the
candidate row for that boat, then blend those boat-specific probabilities with v314's
outer specialist distribution. This targets the persistent boat5/6 blind spot.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v314_1head_opponent_role_split as v314

ROOT=Path(__file__).resolve().parent
SEL=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
P=ROOT/'analysis_v315_1head_outer_boat_specific'
S=ROOT/'summary_v315_1head_outer_boat_specific.md'
TM=list(v298.TEST_MONTHS)


def boat_specific(sl,tm,boat,C=.3):
    tr=sl[(sl.month<tm)&(sl.boat.astype(int)==int(boat))].copy()
    te=sl[(sl.month==tm)&(sl.boat.astype(int)==int(boat))].copy()
    tr['yb']=(pd.to_numeric(tr.actual2,errors='coerce')==int(boat)).astype(int)
    fs=v311.audited_features(tr)
    fs=[c for c in fs if v311.family(c)!='START']
    if tr.yb.nunique()<2: raise RuntimeError(f'v315 one class tm={tm} boat={boat}')
    m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=C,max_iter=1000,class_weight='balanced'))
    m.fit(tr[fs],tr.yb)
    p=m.predict_proba(te[fs])[:,1]
    return dict(zip(te.race_code.astype(str).str.zfill(12),p)),len(fs)


def blend_outer(role_outer, specific, alpha):
    q={b:float(role_outer.get(b,0.0)) for b in (4,5,6)}
    s=sum(q.values()); q={b:(q[b]/s if s>0 else 1/3) for b in q}
    sp={b:max(0.0,float(specific.get(b,0.0))) for b in (4,5,6)}
    ss=sum(sp.values()); sp={b:(sp[b]/ss if ss>0 else 1/3) for b in sp}
    a=float(alpha); z={b:(1-a)*q[b]+a*sp[b] for b in q}; sz=sum(z.values())
    return {b:z[b]/sz for b in z}


def main():
    frozen=pd.read_csv(SEL,dtype={'race_code':str}); frozen['race_code']=frozen.race_code.astype(str).str.zfill(12)
    if len(frozen)!=345: raise RuntimeError('v315 frozen cohort changed')
    ids=set(frozen.race_code)
    d,p3,p4=v312.load_cache(); d['race_code']=d.race_code.astype(str).str.zfill(12)
    q=d[d.race_code.isin(ids)]
    if len(q)!=345 or int(q.head_hit.sum())!=290: raise RuntimeError('v315 cache frozen mismatch')
    v300.setup_v298(); sufs=v298.suffixes(d)
    if any('meet_' in str(x) for x in sufs): raise RuntimeError('v315 forbidden meet leakage')
    sl=v310.add_headrisk(v300.augment_second(v298.second_long(d,sufs)),p3,p4)
    cl=v300.augment_third(v298.conditional_long(d,sufs))
    pc={tm:v300.pc_predict(cl,tm,.1,True)[0] for tm in TM}
    base={tm:v311.p2_predict_explicit(sl,tm,3.0,None,{'START'})[0] for tm in TM}
    gt=v312.gate_table(sl); gate={tm:v312.gate_predict(gt,tm,.3)[0] for tm in TM}
    inner={}; role_outer={}; spec={}; frows=[]
    for tm in TM:
        inner[tm],ni=v314.specialist_predict(sl,tm,(2,3),3.0)
        role_outer[tm],no=v314.specialist_predict(sl,tm,(4,5,6),3.0)
        spec[tm]={}; counts={}
        for b in (4,5,6): spec[tm][b],counts[b]=boat_specific(sl,tm,b,.3)
        frows.append({'month':tm,'inner_features':ni,'outer_features':no,**{f'boat{b}_features':counts[b] for b in (4,5,6)}})

    configs=[('DROP_START_BASE',0.0,0.0,1.0,.03)]
    for alpha in (.25,.50,.75,1.00):
        for mix in (.65,.80,1.00):
            for gp in (.85,1.00,1.20):
                configs.append((f'SPEC_a{alpha:.2f}_m{mix:.2f}_g{gp:.2f}',alpha,mix,gp,.08))
    sums=[]; outs=[]
    for name,alpha,mix,gp,floor in configs:
        p2={}
        for tm in TM:
            p2[tm]={}
            for code,bp in base[tm].items():
                if name=='DROP_START_BASE': p2[tm][code]=bp; continue
                sp={b:spec[tm][b].get(code,0.0) for b in (4,5,6)}
                out=blend_outer(role_outer[tm][code],sp,alpha)
                p2[tm][code]=v314.combine(inner[tm][code],out,gate[tm].get(code,.5),bp,gp,mix,floor)
        z,m=v314.evaluate(p2,pc,d,ids); z['config']=name; outs.append(z)
        m.update({'config':name,'outer_specific_alpha':alpha,'specialist_mix':mix,'gate_power':gp,'gate_floor':floor}); sums.append(m)
        print('v315',name,m,flush=True)
    sm=pd.DataFrame(sums); baseM=sm[sm.config=='DROP_START_BASE'].iloc[0]
    for c,src in [('delta_top2_pp','second_top2'),('delta_outer_pp','outer456_top2'),('delta_exact3_pp','exact3_rate')]: sm[c]=100*(sm[src]-baseM[src])
    cand=sm[sm.config!='DROP_START_BASE'].copy(); best=cand.sort_values(['second_top2','worst_month_second_top2','outer456_top2','exact3_rate'],ascending=False).iloc[0]
    allz=pd.concat(outs,ignore_index=True); bz=allz[allz.config==best.config].copy(); bh=bz[bz.head_hit==1]
    by=bh.groupby('actual2').agg(R=('race_code','size'),top2=('second_top2','mean'),top3=('second_top3','mean'),exact3=('exact3','mean')).reset_index()
    mon=bz.groupby('month').agg(R=('race_code','size'),head=('head_hit','sum'),exact3=('exact3','mean')).reset_index(); mon=mon.merge(bh.groupby('month').second_top2.mean().rename('second_top2').reset_index(),on='month')
    sm.to_csv(str(P)+'_configs.csv',index=False); pd.DataFrame(frows).to_csv(str(P)+'_feature_counts.csv',index=False); by.to_csv(str(P)+'_best_by_second.csv',index=False); mon.to_csv(str(P)+'_best_monthly.csv',index=False); bz.to_csv(str(P)+'_best_race.csv',index=False)
    L=['# v315 outer boat-specific SECOND research','', '- Frozen 345R / 290 boat-1 wins; THIRD frozen v300 L2=.1.', '- v313 cache only; monthly walk-forward; no meet_*; no future backfill.', '- Separate P(SECOND=4), P(SECOND=5), P(SECOND=6) blended with v314 outer specialist.','', '## Result', f'- Base TOP2 {100*baseM.second_top2:.2f}%, outer {100*baseM.outer456_top2:.2f}%, exact3 {int(baseM.exact3_hits)}/345={100*baseM.exact3_rate:.2f}%.', f'- Best **{best.config}** TOP2 **{100*best.second_top2:.2f}%**, outer **{100*best.outer456_top2:.2f}%**, exact3 **{int(best.exact3_hits)}/345={100*best.exact3_rate:.2f}%**, worst month **{100*best.worst_month_second_top2:.2f}%**.','', '## Best by actual SECOND','|boat|R|TOP2|TOP3|exact3|','|---:|---:|---:|---:|---:|']
    for _,r in by.iterrows(): L.append(f'|{int(r.actual2)}|{int(r.R)}|{100*r.top2:.2f}%|{100*r.top3:.2f}%|{100*r.exact3:.2f}%|')
    L+=['','## Monthly','|month|R|head|TOP2|exact3|','|---|---:|---:|---:|---:|']
    for _,r in mon.iterrows(): L.append(f'|{r.month}|{int(r.R)}|{int(r["head"])}|{100*r.second_top2:.2f}%|{100*r.exact3:.2f}%|')
    S.write_text('\n'.join(L)+'\n',encoding='utf-8'); print(S.read_text(),flush=True)

if __name__=='__main__': main()
