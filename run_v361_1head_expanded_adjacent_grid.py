#!/usr/bin/env python3
from __future__ import annotations
"""v361: expanded 313R adjacent-pair grid using v360 prepared rows.

No exhibition/model rebuild. Candidate selection uses Feb-Jun DEV only.
Jul-Aug SUPPORT is never used for selection.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import argparse, json, math, pickle, urllib.request
import numpy as np
import pandas as pd

import backtest
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v351_1head_third_close_margin_audit as pay

OUT=Path('/tmp/v361-expanded-adjacent-grid');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
PAIRS={'5>6':(5,6),'4>5':(4,5)}
BASES=('SCORE','ST','COMBO')
ATTACK_MIN=(.40,.50,.60,.70,.80)
RISK_MIN=(0.,.10,.20,.30,.40,.50)
MASS_MIN=(0.,.35,.375,.40,.425,.45)
G2=(0.,.25,.50,1.0)
G3=(.25,.50,.75,1.0,1.5,2.0)

def norm(q):
    s=sum(max(float(v),0.0) for v in q.values())
    return {k:max(float(v),0.0)/s for k,v in q.items()} if s>0 else {k:1/len(q) for k in q}

def tickets(p2,pc):
    pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
    return ';'.join(f'1-{s}-{t}' for s,t in top)

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

def payout_values(rows):
    cache={};vals={}
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901':raise RuntimeError(f'September entered {code}')
        _,p=pay._payout(code,str(r['actual_combo']),cache)
        vals[code]=int(p)
    return vals

def base_metrics(rows,payouts):
    n=len(rows);hits=sum(int(r['base_hit']) for r in rows)
    ret=sum(payouts[str(r['race_code']).zfill(12)] for r in rows if int(r['base_hit']))
    stake=n*300
    return {'R':n,'hits':hits,'return_yen':ret,'stake_yen':stake,'roi':ret/stake if stake else 0.0}

def risk_for(r,inner,outer,basis):
    sg=float(r[f'score{outer}'])-float(r[f'score{inner}'])
    st=float(r[f'st{outer}'])-float(r[f'st{inner}'])
    if basis=='SCORE':return sg
    if basis=='ST':return st
    return .65*st+.35*sg

def eval_cfg(rows,payouts,pair,basis,attack_min,risk_min,mass_min,g2,g3,need_detail=False):
    inner,outer=PAIRS[pair]
    hits=0;ret=0;changed=gain=loss=triggered=0;detail=[]
    for r in rows:
        code=str(r['race_code']).zfill(12);base_hit=int(r['base_hit']);ts=str(r['base_tickets']);risk=0.0
        active=(float(r['opp_mass'])>=mass_min and bool(r.get('ex_ready',False)) and float(r[f'score{outer}'])>=attack_min)
        if active:
            rv=risk_for(r,inner,outer,basis)
            if rv>=risk_min and rv>0:
                risk=float(rv);triggered+=1
                p2,pc=apply_pair(r['_p2'],r['_pc'],inner,outer,risk,g2,g3)
                ts=tickets(p2,pc)
        hit=int(str(r['actual_combo']) in ts.split(';'))
        hits+=hit
        if hit:ret+=payouts[code]
        ch=int(ts!=str(r['base_tickets']));changed+=ch
        d=hit-base_hit;gain+=int(d==1);loss+=int(d==-1)
        if need_detail and (ch or d):
            detail.append({'race_code':code,'month':str(r['month']),'actual_combo':str(r['actual_combo']),
                           'opp_mass':float(r['opp_mass']),'risk':risk,'base_tickets':str(r['base_tickets']),
                           'tickets':ts,'base_hit':base_hit,'hit':hit,'delta':d})
    stake=len(rows)*300
    return {'R':len(rows),'hits':hits,'return_yen':ret,'stake_yen':stake,'roi':ret/stake if stake else 0.0,
            'changed_R':changed,'gain_R':gain,'loss_R':loss,'triggered_R':triggered},detail

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));allrows=x['rows']
    rows313=allrows['H0775_M350']
    if len(rows313)!=313:raise RuntimeError(f'prepared 313 drift {len(rows313)}')
    union_by_code={}
    for rr in allrows.values():
        for r in rr: union_by_code[str(r['race_code']).zfill(12)]=r
    unionrows=list(union_by_code.values())
    prefetch=install_payout_cache(unionrows);payouts=payout_values(unionrows)
    dev=[r for r in rows313 if str(r['month']) in DEV];sup=[r for r in rows313 if str(r['month']) in SUP]
    bdev=base_metrics(dev,payouts);bsup=base_metrics(sup,payouts);ball=base_metrics(rows313,payouts)

    rec=[]
    for pair in PAIRS:
      for basis in BASES:
       for amin in ATTACK_MIN:
        for rmin in RISK_MIN:
         for mmin in MASS_MIN:
          for g2 in G2:
           for g3 in G3:
            m,_=eval_cfg(dev,payouts,pair,basis,amin,rmin,mmin,g2,g3)
            rec.append({'pair':pair,'basis':basis,'attack_min':amin,'risk_min':rmin,'mass_min':mmin,'g2':g2,'g3':g3,
                        **{f'dev_{k}':v for k,v in m.items()},
                        'dev_delta_hits':m['hits']-bdev['hits'],'dev_delta_roi_pp':100*(m['roi']-bdev['roi'])})
    grid=pd.DataFrame(rec)
    # DEV-only selection. Prefer gain with zero loss; then hit count, ROI, fewer changes, weaker params.
    elig=grid[(grid.dev_delta_hits>=1)&(grid.dev_loss_R==0)].copy()
    if len(elig)==0:
        elig=grid.sort_values(['dev_delta_hits','dev_delta_roi_pp'],ascending=False).head(50).copy()
    elig['complexity']=elig.g2+elig.g3+elig.risk_min+elig.attack_min
    best=elig.sort_values(['dev_hits','dev_delta_roi_pp','dev_changed_R','complexity'],
                          ascending=[False,False,True,True]).iloc[0]

    # Top plateau for robustness, selected without support.
    top=elig.sort_values(['dev_hits','dev_delta_roi_pp','dev_changed_R','complexity'],
                         ascending=[False,False,True,True]).head(30).copy()
    support_rows=[];all_rows=[]
    for _,cfg in top.iterrows():
        kw=dict(pair=cfg.pair,basis=cfg.basis,attack_min=float(cfg.attack_min),risk_min=float(cfg.risk_min),
                mass_min=float(cfg.mass_min),g2=float(cfg.g2),g3=float(cfg.g3))
        sm,_=eval_cfg(sup,payouts,**kw)
        am,_=eval_cfg(rows313,payouts,**kw)
        support_rows.append({**kw,**{f'support_{k}':v for k,v in sm.items()},
                             'support_delta_hits':sm['hits']-bsup['hits'],'support_delta_roi_pp':100*(sm['roi']-bsup['roi'])})
        all_rows.append({**kw,**{f'all_{k}':v for k,v in am.items()},
                         'all_delta_hits':am['hits']-ball['hits'],'all_delta_roi_pp':100*(am['roi']-ball['roi'])})
    top=top.merge(pd.DataFrame(support_rows),on=['pair','basis','attack_min','risk_min','mass_min','g2','g3'])
    top=top.merge(pd.DataFrame(all_rows),on=['pair','basis','attack_min','risk_min','mass_min','g2','g3'])

    kw=dict(pair=best.pair,basis=best.basis,attack_min=float(best.attack_min),risk_min=float(best.risk_min),
            mass_min=float(best.mass_min),g2=float(best.g2),g3=float(best.g3))
    # Evaluate same DEV-selected config on every universe + disjoint bands.
    universes=[];details=[]
    for name,rr in allrows.items():
        m,dd=eval_cfg(rr,payouts,need_detail=True,**kw);b=base_metrics(rr,payouts)
        universes.append({'universe':name,**b,**{f'cfg_{k}':v for k,v in m.items()},
                          'delta_hits':m['hits']-b['hits'],'delta_roi_pp':100*(m['roi']-b['roi'])})
        for d in dd:d['universe']=name
        details.extend(dd)

    # Disjoint nested bands from the expanded env=.05 chain.
    chain=['LIVE165','H078_M375','H0775_M375','H0775_M350']
    bands=[]
    prev=set()
    for name in chain:
        ids={str(r['race_code']).zfill(12) for r in allrows[name]}
        bandids=ids-prev;rr=[r for r in allrows[name] if str(r['race_code']).zfill(12) in bandids]
        m,_=eval_cfg(rr,payouts,**kw);b=base_metrics(rr,payouts)
        bands.append({'band':name if not prev else f'ADDED_TO_{name}',**b,**{f'cfg_{k}':v for k,v in m.items()},
                      'delta_hits':m['hits']-b['hits'],'delta_roi_pp':100*(m['roi']-b['roi'])})
        prev=ids

    # DEV-month LOMO: select config on other 4 DEV months from top DEV plateau only, evaluate held month.
    lomo=[]
    topkeys=top[['pair','basis','attack_min','risk_min','mass_min','g2','g3']].drop_duplicates()
    for hold in DEV:
        train=[r for r in dev if str(r['month'])!=hold];test=[r for r in dev if str(r['month'])==hold]
        bt=base_metrics(train,payouts);cands=[]
        for _,cfg in topkeys.iterrows():
            k=dict(pair=cfg.pair,basis=cfg.basis,attack_min=float(cfg.attack_min),risk_min=float(cfg.risk_min),
                   mass_min=float(cfg.mass_min),g2=float(cfg.g2),g3=float(cfg.g3))
            mm,_=eval_cfg(train,payouts,**k)
            cands.append((mm['hits']-bt['hits'],mm['roi']-bt['roi'],-mm['loss_R'],-mm['changed_R'],k))
        sel=max(cands,key=lambda z:(z[0],z[1],z[2],z[3]))[-1]
        hm,_=eval_cfg(test,payouts,**sel);hb=base_metrics(test,payouts)
        lomo.append({'holdout_month':hold,**sel,'base_hits':hb['hits'],'cfg_hits':hm['hits'],
                     'delta_hits':hm['hits']-hb['hits'],'base_roi':hb['roi'],'cfg_roi':hm['roi'],
                     'delta_roi_pp':100*(hm['roi']-hb['roi']),'gain_R':hm['gain_R'],'loss_R':hm['loss_R']})

    grid.to_csv(OUT/'dev_grid.csv',index=False);top.to_csv(OUT/'top30_support.csv',index=False)
    pd.DataFrame(universes).to_csv(OUT/'universes.csv',index=False);pd.DataFrame(bands).to_csv(OUT/'bands.csv',index=False)
    pd.DataFrame(details).to_csv(OUT/'best_changed_races.csv',index=False);pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False)
    result={'prepared_source':'v360 Artifact 10539401122','payout_prefetch':prefetch,
            'base313':ball,'base_dev':bdev,'base_support':bsup,'dev_selected_best':kw,
            'best_dev':best.to_dict(),
            'best_support':top.iloc[0].to_dict() if len(top) else None,
            'universes':universes,'bands':bands,
            'lomo_delta_hits_total':int(sum(x['delta_hits'] for x in lomo)),
            'lomo_nonnegative_months':int(sum(x['delta_hits']>=0 for x in lomo)),
            'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)
    print('\nTOP30',flush=True);print(top.head(30).to_string(index=False),flush=True)
    print('\nLOMO',flush=True);print(pd.DataFrame(lomo).to_string(index=False),flush=True)

if __name__=='__main__':main()
