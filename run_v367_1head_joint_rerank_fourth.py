#!/usr/bin/env python3
from __future__ import annotations
"""v367: joint 2->3 post-exhibition rerank + sparse conditional 4th ticket.

Research only. DEV Feb-Jun selects both stages. Jul-Aug is untouched holdout.
September outcomes/payouts are forbidden.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, json, math, pickle, urllib.request
import numpy as np
import pandas as pd

import backtest
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v351_1head_third_close_margin_audit as pay
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v367-joint-hit-push');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

C23_BASES=('SCORE','ST','COMBO')
C23_SCORE_MIN=(.40,.50,.60,.70)
C23_RISK_MIN=(0.,.10,.20,.30)
C23_MASS_MIN=(.375,.400,.425)
C23_G2=(0.,.25,.50)
C23_G3=(.25,.50,.75)

FOURTH_GAP=(.005,.01,.015,.02,.03,.05,.075,.10)
FOURTH_PAIR_MIN=(0.,.075,.09)
FOURTH_P2_MIN=(0.,.35,.40)

def norm(q):
    s=sum(max(float(v),0.0) for v in q.values())
    if not math.isfinite(s) or s<=0: raise RuntimeError('invalid mass')
    return {k:max(float(v),0.0)/s for k,v in q.items()}

def tickets(p2,pc):
    pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
    if len(top)!=3 or len(set(top))!=3: raise RuntimeError('invalid top3')
    return top

def apply_pair(p2,pc,inner,outer,risk,g2,g3):
    q2={b:float(p2[b]) for b in BOATS}
    if g2>0:
        q2[outer]*=math.exp(g2*risk);q2[inner]*=math.exp(-g2*risk);q2=norm(q2)
    q3={}
    for s in BOATS:
        q={t:float(pc[(s,t)]) for t in BOATS if t!=s}
        if g3>0:
            if outer in q:q[outer]*=math.exp(g3*risk)
            if inner in q:q[inner]*=math.exp(-g3*risk)
        q=norm(q)
        for t,v in q.items():q3[(s,t)]=v
    return q2,q3

def risk23(r,basis):
    sg=float(r['score3'])-float(r['score2'])
    st=float(r['st3'])-float(r['st2'])
    if basis=='SCORE':return sg
    if basis=='ST':return st
    return .65*st+.35*sg

def c23_active(r,c):
    rv=risk23(r,c['basis'])
    return (bool(r.get('ex_ready',False)) and float(r['score3'])>=c['score_min']
            and rv>=c['risk_min'] and rv>0 and float(r['opp_mass'])>=c['mass_min']),rv

def install_payout_cache(rows):
    days=sorted({str(r['race_code'])[:8] for r in rows})
    paths=[f"data/results/payouts/{d[:4]}/{d[4:6]}/{d[6:8]}.csv" for d in days]
    original=backtest.fetch
    def one(path):
        try:
            with urllib.request.urlopen(backtest.BASE+path,timeout=30) as resp:
                return path,resp.read().decode('utf-8-sig')
        except Exception:
            return path,''
    cache={}
    with ThreadPoolExecutor(max_workers=24) as ex:
        for path,txt in ex.map(one,paths):cache[path]=txt
    def cached(path):
        if path in cache:return cache[path]
        return original(path)
    backtest.fetch=cached
    return {'days':len(days),'nonempty':sum(bool(v) for v in cache.values())}

def payouts_for(rows):
    cache={};out={}
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901':raise RuntimeError(f'September entered {code}')
        _,p=pay._payout(code,str(r['actual_combo']),cache);out[code]=int(p)
    return out

def formal_dist(r):
    return v365.formal_post_five6(r)

def fourth_features(p2,pc):
    pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pair)[:3]
    s=top[0][0]
    thirds=sorted([t for t in BOATS if t!=s],key=lambda t:(-float(pc[(s,t)]),t))
    if top[0]!=(s,thirds[0]) or top[1]!=(s,thirds[1]):
        raise RuntimeError(f'HYBRID semantics drift top={top} thirds={thirds}')
    extra=(s,thirds[2])
    if extra in top:raise RuntimeError(f'extra duplicate {extra}')
    gap=float(pc[(s,thirds[1])])-float(pc[(s,thirds[2])])
    return top,extra,gap,float(pair[extra]),float(p2[s])

def row_after_c23(r,c):
    p2,pc=formal_dist(r)
    active,rv=c23_active(r,c)
    if active:p2,pc=apply_pair(p2,pc,2,3,rv,c['g2'],c['g3'])
    top,extra,gap,ep,p2dom=fourth_features(p2,pc)
    base=['1-%d-%d'%x for x in top]; extra_ticket='1-%d-%d'%extra
    actual=str(r['actual_combo'])
    return {
      'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),
      'actual_combo':actual,'base_tickets':';'.join(base),
      'base_hit':int(actual in base),'extra_ticket':extra_ticket,'extra_hit':int(actual==extra_ticket),
      'gap23':gap,'extra_pair_prob':ep,'p2_dom':p2dom,'c23_applied':int(active),
    }

def metrics_frame(df,payouts,mask=None):
    if mask is None:mask=np.zeros(len(df),dtype=bool)
    mask=np.asarray(mask,dtype=bool)
    hit=df.base_hit.astype(bool).to_numpy()|(mask&df.extra_hit.astype(bool).to_numpy())
    expanded=int(mask.sum());stake=len(df)*300+expanded*100
    ret=int(sum(payouts[str(code)] for code,h in zip(df.race_code,hit) if h))
    return {
      'R':len(df),'expanded_R':expanded,'hits':int(hit.sum()),'hit_rate':float(hit.mean()),
      'gain_hits':int(hit.sum()-df.base_hit.sum()),'stake_yen':stake,'return_yen':ret,
      'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
    }

def fourth_mask(df,c):
    return (
      df.gap23.le(c['gap_max']+1e-12)&
      df.extra_pair_prob.ge(c['pair_min']-1e-12)&
      df.p2_dom.ge(c['p2_min']-1e-12)
    ).to_numpy()

def c23_cfg(basis,smin,rmin,mmin,g2,g3):
    return {'basis':basis,'score_min':float(smin),'risk_min':float(rmin),
            'mass_min':float(mmin),'g2':float(g2),'g3':float(g3)}

def f4_cfg(gap,pair,p2):
    return {'gap_max':float(gap),'pair_min':float(pair),'p2_min':float(p2)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));rows=x['rows']['LIVE165']
    if len(rows)!=165:raise RuntimeError(f'LIVE165 drift {len(rows)}')
    prefetch=install_payout_cache(rows);payouts=payouts_for(rows)
    devrows=[r for r in rows if str(r['month']) in DEV]
    suprows=[r for r in rows if str(r['month']) in SUP]

    # Formal baseline sentinel.
    formal=[]
    for r in rows:
        p2,pc=formal_dist(r);top=tickets(p2,pc);ts=['1-%d-%d'%x for x in top]
        actual=str(r['actual_combo'])
        formal.append({'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),
                       'base_hit':int(actual in ts),'extra_hit':0})
    fdf=pd.DataFrame(formal);formal_all=metrics_frame(fdf,payouts)
    if (formal_all['R'],formal_all['hits'],formal_all['return_yen'])!=(165,87,63700):
        raise RuntimeError(f'formal sentinel drift {formal_all}')

    # Stage 1: DEV-only 2>3 shortlist.
    c23_grid=[]
    c23_frames={}
    for basis in C23_BASES:
      for smin in C23_SCORE_MIN:
       for rmin in C23_RISK_MIN:
        for mmin in C23_MASS_MIN:
         for g2 in C23_G2:
          for g3 in C23_G3:
           c=c23_cfg(basis,smin,rmin,mmin,g2,g3)
           key=json.dumps(c,sort_keys=True)
           d=pd.DataFrame([row_after_c23(r,c) for r in devrows])
           m=metrics_frame(d,payouts)
           changed=int((d.base_tickets != pd.DataFrame([row_after_c23(r,c23_cfg('SCORE',2,2,1,0,0)) for r in devrows]).base_tickets).sum()) if False else int(d.c23_applied.sum())
           c23_grid.append({**c,**{f'dev3_{k}':v for k,v in m.items()},'dev3_applied_R':int(d.c23_applied.sum())})
           c23_frames[key]=d
    cg=pd.DataFrame(c23_grid)
    max3=int(cg.dev3_hits.max())
    # Keep broad DEV-only shortlist: max hit and near-max, zero concern about SUPPORT.
    shortlist=cg[cg.dev3_hits.ge(max3-1)].copy()
    shortlist=shortlist.sort_values(['dev3_hits','dev3_roi','dev3_applied_R'],
                                    ascending=[False,False,True]).head(60)

    # Stage 2: joint fourth-ticket search on shortlist, DEV only.
    joint=[];cache={}
    for _,cr in shortlist.iterrows():
        c={k:(str(cr[k]) if k=='basis' else float(cr[k])) for k in ['basis','score_min','risk_min','mass_min','g2','g3']}
        key=json.dumps(c,sort_keys=True)
        d=c23_frames[key]
        for gap in FOURTH_GAP:
          for pm in FOURTH_PAIR_MIN:
           for p2m in FOURTH_P2_MIN:
            f=f4_cfg(gap,pm,p2m);m=metrics_frame(d,payouts,fourth_mask(d,f))
            joint.append({**{f'c23_{k}':v for k,v in c.items()},**{f'f4_{k}':v for k,v in f.items()},
                          **{f'dev_{k}':v for k,v in m.items()}})
    j=pd.DataFrame(joint)

    # exact3 first; require DEV ROI>=120%. Prefer ROI, then fewer expansions/applied.
    elig=j[j.dev_roi.ge(1.20)].copy()
    if len(elig)==0:raise RuntimeError('no joint candidate >=120% DEV ROI')
    mh=int(elig.dev_hits.max());cand=elig[elig.dev_hits.eq(mh)].copy()
    best=cand.sort_values(['dev_roi','dev_expanded_R'],ascending=[False,True]).iloc[0]
    csel={k.replace('c23_',''):(str(best[k]) if k=='c23_basis' else float(best[k]))
          for k in ['c23_basis','c23_score_min','c23_risk_min','c23_mass_min','c23_g2','c23_g3']}
    fsel={k.replace('f4_',''):float(best[k]) for k in ['f4_gap_max','f4_pair_min','f4_p2_min']}

    # Evaluate frozen selection on DEV/SUPPORT/ALL.
    def frame_for(rr):
        return pd.DataFrame([row_after_c23(r,csel) for r in rr])
    dd=frame_for(devrows);sd=frame_for(suprows);ad=frame_for(rows)
    dm=metrics_frame(dd,payouts,fourth_mask(dd,fsel))
    sm=metrics_frame(sd,payouts,fourth_mask(sd,fsel))
    am=metrics_frame(ad,payouts,fourth_mask(ad,fsel))

    # Also report the sparse fixed gap-only .015 after selected c23.
    sparse=f4_cfg(.015,0,0)
    sparse_all=metrics_frame(ad,payouts,fourth_mask(ad,sparse))
    sparse_dev=metrics_frame(dd,payouts,fourth_mask(dd,sparse))
    sparse_sup=metrics_frame(sd,payouts,fourth_mask(sd,sparse))

    # Monthly frozen candidate.
    monthly=[]
    for mon in sorted(ad.month.unique()):
        md=ad[ad.month.eq(mon)].copy()
        mm=metrics_frame(md,payouts,fourth_mask(md,fsel))
        monthly.append({'month':mon,**mm})

    # Row details.
    mask=fourth_mask(ad,fsel)
    out=ad.copy();out['expanded']=mask.astype(int)
    out['final_hit']=(out.base_hit.astype(bool)|(mask&out.extra_hit.astype(bool))).astype(int)
    out['delta_hit']=out.final_hit-out.base_hit
    out.to_csv(OUT/'rows_selected.csv',index=False)
    cg.to_csv(OUT/'c23_dev_grid.csv',index=False);shortlist.to_csv(OUT/'c23_shortlist.csv',index=False)
    j.to_csv(OUT/'joint_dev_grid.csv',index=False);pd.DataFrame(monthly).to_csv(OUT/'monthly.csv',index=False)

    result={
      'formal_live165':formal_all,'c23_max_dev_hits':max3,'c23_shortlist_R':len(shortlist),
      'joint_grid_R':len(j),'dev_selected_c23':csel,'dev_selected_fourth':fsel,
      'selected_dev':dm,'selected_support':sm,'selected_all165':am,
      'target_55pct_reached':bool(am['hit_rate']>=.55),
      'sparse_gap015_after_selected_c23':{'dev':sparse_dev,'support':sparse_sup,'all':sparse_all},
      'payout_prefetch':prefetch,'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
