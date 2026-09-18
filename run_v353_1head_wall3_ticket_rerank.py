#!/usr/bin/env python3
from __future__ import annotations
"""v353: wall3-aware opponent rerank for fixed 1-head BASIC/WATCH gates.

Research only. Same 3 tickets. Existing opponent attackCore adjustment is applied
first; then a soft 3-vs-4 wall overlay changes SECOND/THIRD probabilities.
September outcomes stay unread.
"""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v347_1head_opponent_attackcore as v347
import run_v351_1head_production_regression as base
import run_v351_1head_joint_roi_grid as grid
import run_v352_1head_wall3_risk_audit as v352

OUT=Path('/tmp/v353-wall3-ticket'); OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
G=(0.0,.5,1.0,1.5,2.0,3.0)
A4=(.50,.60,.70)
RISK=('ST','SCORE','COMBO')


def norm(q):
    s=sum(max(float(v),0.0) for v in q.values())
    return {k:max(float(v),0.0)/s for k,v in q.items()} if s>0 else {k:1/len(q) for k in q}


def risk_value(r,kind,a4):
    if not bool(r.wall_exhibition_ready): return 0.0
    if float(r.attack4_score)<a4: return 0.0
    st=max(0.0,-float(r.st_wall_gap))
    sc=max(0.0,-float(r.ex_wall_score))
    if kind=='ST': return st
    if kind=='SCORE': return sc
    return .65*st+.35*sc


def tilt(p2,pc,risk,g2,g3):
    q2={int(b):float(p2[b]) for b in BOATS}
    if risk>0 and g2>0:
        q2[4]*=math.exp(g2*risk); q2[3]*=math.exp(-g2*risk)
    q2=norm(q2)
    q3={}
    for s in BOATS:
        q={t:float(pc[(s,t)]) for t in BOATS if t!=s}
        if risk>0 and g3>0:
            if 4 in q:q[4]*=math.exp(g3*risk)
            if 3 in q:q[3]*=math.exp(-g3*risk)
        q=norm(q)
        for t,v in q.items():q3[(s,t)]=v
    return q2,q3


def tickets(p2,pc):
    pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
    return ';'.join(f'1-{s}-{t}' for s,t in top)


def build_rows(sel,wall,maps,cores):
    p2d,pcd,p2j,pcj=maps
    z=sel.merge(wall,on='race_code',how='left',validate='one_to_one').copy()
    rec=[]
    for _,r in z.iterrows():
        tm=str(r.month); code=str(r.race_code).zfill(12)
        p2,pc=v347.get_dist(tm,code,p2d,pcd,p2j,pcj)
        core=cores.get(code)
        if core is not None:
            p2=base._second_adjust(p2,core); pc=base._third_adjust(pc,core)
        else:
            p2={int(k):float(v) for k,v in p2.items()}; pc={(int(s),int(t)):float(v) for (s,t),v in pc.items()}
        bt=tickets(p2,pc)
        rec.append({**r.to_dict(),'base_tickets':bt,'_p2':p2,'_pc':pc})
    return rec


def metrics(df,cache):
    return grid.met(df,cache)


def eval_cfg(rows,kind,a4,g2,g3,cache,label):
    rec=[]
    for r in rows:
        rv=risk_value(pd.Series(r),kind,a4)
        p2,pc=tilt(r['_p2'],r['_pc'],rv,g2,g3)
        ts=tickets(p2,pc); actual=str(r['actual_combo'])
        rec.append({'month':str(r['month']),'race_code':str(r['race_code']).zfill(12),'head_hit':int(r['head_hit']),
                    'actual_combo':actual,'tickets':ts,'hit':int(actual in ts.split(';')),
                    'base_tickets':r['base_tickets'],'changed':int(ts!=r['base_tickets']),'risk':rv})
    z=pd.DataFrame(rec)
    dev=z[z.month.isin(v352.DEV)]; sup=z[z.month.isin(v352.SUP)]
    a=metrics(z,cache);d=metrics(dev,cache);s=metrics(sup,cache)
    return z,{'universe':label,'risk_kind':kind,'attack4_min':a4,'g2':g2,'g3':g3,
              **{f'all_{k}':v for k,v in a.items()},**{f'dev_{k}':v for k,v in d.items()},**{f'support_{k}':v for k,v in s.items()},
              'changed_R':int(z.changed.sum())}


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise RuntimeError('September guard disabled')
    y=grid.universe(); maps=v347.opponent_maps(); cores=v347.build_opponent_attackcore(set(y.race_code)); cache={}
    basic=v352.selected(y,**v352.BASIC,maps=maps,cores=cores)
    watch=v352.selected(y,**v352.WATCH,maps=maps,cores=cores)
    ids=set(basic.race_code)|set(watch.race_code)
    wall=v352.exhibition_wall(ids)
    out=[]; races=[]
    for label,sel in [('BASIC',basic),('WATCH',watch)]:
        rows=build_rows(sel,wall,maps,cores)
        # Baseline must reproduce v352 exact3 counts before any wall overlay.
        bz,bm=eval_cfg(rows,'ST',.50,0,0,cache,label)
        exp=80 if label=='BASIC' else 44
        if bm['all_exact3']!=exp: raise RuntimeError(f'{label} baseline drift {bm}')
        bm['risk_kind']='BASE'; out.append(bm); races.append(bz.assign(universe=label,risk_kind='BASE',attack4_min=np.nan,g2=0,g3=0))
        for kind in RISK:
            for a4 in A4:
                for g2 in G:
                    for g3 in G:
                        if g2==0 and g3==0: continue
                        z,m=eval_cfg(rows,kind,a4,g2,g3,cache,label);out.append(m)
                        races.append(z.assign(universe=label,risk_kind=kind,attack4_min=a4,g2=g2,g3=g3))
    sm=pd.DataFrame(out)
    sm['all_roi']=sm.all_return_yen/sm.all_stake_yen
    sm['dev_roi']=sm.dev_return_yen/sm.dev_stake_yen
    sm['support_roi']=sm.support_return_yen/sm.support_stake_yen
    for label in ('BASIC','WATCH'):
        b=sm[(sm.universe==label)&(sm.risk_kind=='BASE')].iloc[0]
        ix=sm.universe.eq(label)
        sm.loc[ix,'delta_hits']=sm.loc[ix,'all_exact3']-int(b.all_exact3)
        sm.loc[ix,'delta_roi_pp']=100*(sm.loc[ix,'all_roi']-float(b.all_roi))
        sm.loc[ix,'delta_dev_hits']=sm.loc[ix,'dev_exact3']-int(b.dev_exact3)
        sm.loc[ix,'delta_support_hits']=sm.loc[ix,'support_exact3']-int(b.support_exact3)
    sm.to_csv(OUT/'grid.csv',index=False)
    rr=pd.concat(races,ignore_index=True);rr.to_csv(OUT/'race_predictions.csv',index=False)
    picks={}
    for label in ('BASIC','WATCH'):
        q=sm[(sm.universe==label)&(sm.risk_kind!='BASE')].copy()
        robust=q[(q.dev_roi>=1.0)&(q.support_roi>=1.0)]
        if len(robust):
            best=robust.sort_values(['all_exact3','all_roi','support_roi','changed_R'],ascending=[False,False,False,True]).iloc[0]
        else:
            best=q.sort_values(['all_exact3','all_roi'],ascending=False).iloc[0]
        picks[label]=best.to_dict()
    result={'basic_base':sm[(sm.universe=='BASIC')&(sm.risk_kind=='BASE')].iloc[0].to_dict(),
            'watch_base':sm[(sm.universe=='WATCH')&(sm.risk_kind=='BASE')].iloc[0].to_dict(),
            'best':picks,'grid_R':len(sm),'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
