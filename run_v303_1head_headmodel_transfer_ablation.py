#!/usr/bin/env python3
"""v303: improve 1-head gate with feature structures proven in 3-head/4-head models.

Development-only. Jul/Aug remain NON-PRISTINE; September outcomes unread.
Fair comparison rule: freeze opponent-confidence eligibility and preserve the exact
baseline selected count in every test month. Candidate head models only re-rank
eligible races, so the total denominator cannot shrink to inflate head accuracy.
"""
from __future__ import annotations
from pathlib import Path
import itertools
import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v303_1head_headmodel_transfer_ablation'
SUMMARY=ROOT/'summary_v303_1head_headmodel_transfer_ablation.md'
TM=list(v298.TEST_MONTHS)
FAMILIES=('ST_EDGE','WALL_INNER','MOTOR','TURN_FORM','STMOTOR')

START=('nst','st_','start','waku_st','hist_st')
MOTOR=('motor',)
TURNFORM=('turn','foot','mawari','exh','tenji','wr','local','grade','racer','past','win','pl_')

def match(s,toks):
    x=s.lower(); return any(t in x for t in toks)

def add_transfer_features(d):
    q=d.copy(); fam={k:[] for k in FAMILIES}
    # Discover symmetric wide b1..b6 suffixes actually available in PRE data.
    suffix=[]
    for c in q.columns:
        if c.startswith('b1_') and all(f'b{b}_{c[3:]}' in q.columns for b in range(2,7)):
            k=c[3:]
            if match(k,START+MOTOR+TURNFORM): suffix.append(k)
    suffix=sorted(set(suffix))
    for k in suffix:
        vals={b:pd.to_numeric(q[f'b{b}_{k}'],errors='coerce') for b in range(1,7)}
        if match(k,START): family='ST_EDGE'
        elif match(k,MOTOR): family='MOTOR'
        else: family='TURN_FORM'
        # Head resilience: b1 edge against each attacker and strongest inner attack.
        for b in range(2,7):
            c=f'v303_{family.lower()}_b1_minus_b{b}_{k}'; q[c]=vals[1]-vals[b]; fam[family].append(c)
        c=f'v303_{family.lower()}_b1_minus_maxopp_{k}'
        q[c]=vals[1]-pd.concat([vals[b] for b in range(2,7)],axis=1).max(axis=1); fam[family].append(c)
        # Structures that matter for 3/4-head attacks: wall/inner resistance around 2-4.
        for a,b in ((2,3),(3,4),(2,4)):
            c=f'v303_wall_inner_b{a}_minus_b{b}_{k}';q[c]=vals[a]-vals[b];fam['WALL_INNER'].append(c)
    # Compact start x motor consensus for b1 vs main attackers 2-4.
    sk=[k for k in suffix if match(k,START)][:4]; mk=[k for k in suffix if match(k,MOTOR)][:3]
    for s in sk:
        for m in mk:
            for b in (2,3,4):
                se=pd.to_numeric(q[f'b1_{s}'],errors='coerce')-pd.to_numeric(q[f'b{b}_{s}'],errors='coerce')
                me=pd.to_numeric(q[f'b1_{m}'],errors='coerce')-pd.to_numeric(q[f'b{b}_{m}'],errors='coerce')
                c=f'v303_stmotor_b1v{b}_{s}_{m}';q[c]=se*me;fam['STMOTOR'].append(c)
    return q,{k:list(dict.fromkeys(v)) for k,v in fam.items()}

def available(tr,fs):
    out=[]
    for c in fs:
        if c not in tr: continue
        x=pd.to_numeric(tr[c],errors='coerce')
        if x.notna().mean()>=.55 and x.nunique(dropna=True)>=2: out.append(c)
    return out

def opponent_mass(d):
    """Reproduce frozen v298/v299 BASE opponent confidence, not v300 winner."""
    sufs=v298.suffixes(d)
    sl=v300.augment_second(v298.second_long(d,sufs));cl=v300.augment_third(v298.conditional_long(d,sufs))
    out={}
    for tm in TM:
        p2,_=v300.p2_predict(sl,tm,10.0,False);pc,_=v300.pc_predict(cl,tm,.3,False)
        for code in d.loc[d.month==tm,'race_code']:
            z=str(code).zfill(12);out[z]=v300.base5(p2[z],pc[z])[1]
    return out

def main():
    v300.setup_v298()
    d,_=v298.v294.freeze_true_pre();d=v298.v294.add_prior_history(d);d=v298.v294.add_rel(d);d,threat=v298.add_threat(d)
    fams=v298.v296.clean_manifest(d)
    d,tf=add_transfer_features(d)
    print('v303 PRE frozen; settlement now',flush=True)
    d,_=v298.v297.settle_full_after_freeze(d);d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    masses=opponent_mass(d)
    core0=list(dict.fromkeys(fams['CLEAN_STATIC6_PLAYER']+threat))
    guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    configs=[('BASE',set())]+[(f'ONLY_{f}',{f}) for f in FAMILIES]
    pred=[]
    # First pass singles; preserve baseline monthly counts exactly.
    for tm in TM:
        tr=d[d.month<tm].copy();te=d[d.month==tm].copy();z=te[['date','month','race_code','venue','race','head_hit']].copy();z['test_month']=tm
        z['opp_mass']=[masses[str(x).zfill(12)] for x in z.race_code];z['eligible']=(z.opp_mass>=v300.BASE_CONF).astype(int)
        base_core=v298.v293.available(tr,core0,.55);base_guard=v298.v293.available(tr,guard0,.55)
        ph,_,hc,_,_,_=v298.head_fold(tr,te,base_core,base_guard);z['p_BASE']=ph
        base_sel=(ph>=hc[.95])&(z.eligible.to_numpy()==1);n=int(base_sel.sum());z['sel_BASE']=base_sel.astype(int)
        for name,allowed in configs[1:]:
            extra=[]
            for f in allowed: extra+=available(tr,tf[f])
            phx,_,_,_,_,_=v298.head_fold(tr,te,list(dict.fromkeys(base_core+extra)),base_guard)
            z[f'p_{name}']=phx
            idx=z[z.eligible==1].sort_values(f'p_{name}',ascending=False).head(n).index
            z[f'sel_{name}']=0;z.loc[idx,f'sel_{name}']=1
        pred.append(z);print('v303 fold',tm,'baseline n',n,flush=True)
    p=pd.concat(pred,ignore_index=True)
    # Audit baseline must be the known frozen 204 / 81.37% selector.
    base=p[p.sel_BASE==1]
    if len(base)!=204: raise RuntimeError(f'baseline denominator drift: expected 204 got {len(base)}')
    if int(base.head_hit.sum())!=166: raise RuntimeError(f'baseline head hits drift: expected 166 got {int(base.head_hit.sum())}')
    rows=[];monthly=[]
    for name,_ in configs:
        s=p[p[f'sel_{name}']==1];gm=s.groupby('test_month').head_hit.agg(['size','sum','mean'])
        rows.append({'config':name,'R':len(s),'head_hits':int(s.head_hit.sum()),'head_rate':float(s.head_hit.mean()),'worst_month':float(gm['mean'].min())})
        for mo,r in gm.iterrows():monthly.append({'config':name,'month':mo,'R':int(r['size']),'hits':int(r['sum']),'head_rate':float(r['mean'])})
    score=pd.DataFrame(rows);mon=pd.DataFrame(monthly);base_rate=float(score.loc[score.config=='BASE','head_rate'].iloc[0]);score['delta']=score.head_rate-base_rate
    keep=[f for f in FAMILIES if float(score.loc[score.config==f'ONLY_{f}','head_rate'].iloc[0])>=base_rate]
    best=score.sort_values(['head_rate','worst_month'],ascending=False).iloc[0]
    p.to_csv(str(PREFIX)+'_pred.csv',index=False);score.to_csv(str(PREFIX)+'_configs.csv',index=False);mon.to_csv(str(PREFIX)+'_monthly.csv',index=False)
    L=['# v303 1HEAD head-model transferred-feature ablation','', '- Development only; production unchanged.','- Jul/Aug NON-PRISTINE; September outcomes unread.','- Opponent-confidence eligibility is frozen to v298/v299 BASE.','- Every candidate preserves the exact baseline selected count in each month; denominator cannot shrink.','- Baseline audit asserted: 204 races / 166 head hits = 81.37%.','', '## Results','|config|R|head hits|head rate|delta|worst month|','|---|---:|---:|---:|---:|---:|']
    for _,r in score.sort_values(['head_rate','worst_month'],ascending=False).iterrows():L.append(f"|{r.config}|{int(r.R)}|{int(r.head_hits)}|{100*r.head_rate:.2f}%|{100*r.delta:+.2f}pt|{100*r.worst_month:.2f}%|")
    L+=['','## Non-harmful single families','- '+(', '.join(keep) if keep else 'none'),'','## Best monthly audit','|month|R|hits|head rate|','|---|---:|---:|---:|']
    for _,r in mon[mon.config==best.config].iterrows():L.append(f"|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.head_rate:.2f}%|")
    L+=['','## Decision',f"- Best single-family head model: **{best.config}: {int(best.head_hits)}/{int(best.R)} = {100*best.head_rate:.2f}%**, delta {100*best.delta:+.2f}pt vs frozen baseline.",'- If a family improves, next step is combination/interaction research at the same monthly counts; do not promote from reused Feb-Jun development evidence.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
