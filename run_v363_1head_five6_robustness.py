#!/usr/bin/env python3
from __future__ import annotations
"""v363: robustness audit for 5->6 ST rerank before any formal promotion.

Uses v360 prepared rows only.  Selection is Feb-Jun DEV only; Jul-Aug SUPPORT
is evaluated only after the DEV candidate/plateau is frozen.
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

OUT=Path('/tmp/v363-five6-robustness');OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

SCORE6=(.50,.55,.60,.65,.70)
STMIN=(.30,.35,.40,.45,.50,.55)
G2=(0.0,.25)
G3=(.50,.625,.75,.875,1.00)
MASS=(.35,.375,.40,.425)

def norm(q):
    s=sum(max(float(v),0.0) for v in q.values())
    if not math.isfinite(s) or s<=0: raise RuntimeError('invalid probability mass')
    return {k:max(float(v),0.0)/s for k,v in q.items()}

def tickets(p2,pc):
    pr=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pr)[:3]
    out=';'.join(f'1-{s}-{t}' for s,t in top)
    if len(out.split(';'))!=3 or len(set(out.split(';')))!=3:raise RuntimeError('invalid tickets')
    return out

def apply_pair(p2,pc,risk,g2,g3):
    q2={b:float(p2[b]) for b in BOATS}
    if g2>0:
        q2[6]*=math.exp(g2*risk);q2[5]*=math.exp(-g2*risk);q2=norm(q2)
    q3={}
    for s in BOATS:
        q={t:float(pc[(s,t)]) for t in BOATS if t!=s}
        if 6 in q:q[6]*=math.exp(g3*risk)
        if 5 in q:q[5]*=math.exp(-g3*risk)
        q=norm(q)
        for t,v in q.items():q3[(s,t)]=v
    return q2,q3

def wall3(p2,pc,r):
    watch=float(r['opp_mass'])>=prod.WATCH_OPPONENT_MASS_MIN
    if not watch or not bool(r.get('ex_ready',False)):
        return p2,pc,False,0.0
    wall=float(r['score3'])-float(r['score4'])
    risk=max(0.0,-wall) if float(r['score4'])>=prod.WALL3_SHADOW_ATTACK4_MIN else 0.0
    if risk<=0:return p2,pc,False,risk
    q2={b:float(p2[b]) for b in BOATS}
    q2[4]*=math.exp(prod.WALL3_SHADOW_SECOND_G2*risk);q2[3]*=math.exp(-prod.WALL3_SHADOW_SECOND_G2*risk);q2=norm(q2)
    q3={}
    for s in BOATS:
        q={t:float(pc[(s,t)]) for t in BOATS if t!=s}
        if 4 in q:q[4]*=math.exp(prod.WALL3_SHADOW_THIRD_G3*risk)
        if 3 in q:q[3]*=math.exp(-prod.WALL3_SHADOW_THIRD_G3*risk)
        q=norm(q)
        for t,v in q.items():q3[(s,t)]=v
    return q2,q3,True,risk

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
    cache={};vals={}
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901':raise RuntimeError(f'September entered {code}')
        _,p=pay._payout(code,str(r['actual_combo']),cache);vals[code]=int(p)
    return vals

def base_ticket(r):
    return str(r['base_tickets'])

def wall_ticket(r):
    p2={int(k):float(v) for k,v in r['_p2'].items()}
    pc={(int(s),int(t)):float(v) for (s,t),v in r['_pc'].items()}
    p2,pc,_,_=wall3(p2,pc,r)
    return tickets(p2,pc),p2,pc

def candidate_ticket(r,cfg,post_wall3=False):
    if post_wall3:
        base_t,p2,pc=wall_ticket(r)
    else:
        base_t=base_ticket(r)
        p2={int(k):float(v) for k,v in r['_p2'].items()}
        pc={(int(s),int(t)):float(v) for (s,t),v in r['_pc'].items()}
    applied=False;gap=float(r['st6'])-float(r['st5'])
    if (bool(r.get('ex_ready',False)) and float(r['score6'])>=cfg['score6_min']
        and gap>=cfg['st_min'] and float(r['opp_mass'])>=cfg['mass_min']):
        p2,pc=apply_pair(p2,pc,gap,cfg['g2'],cfg['g3']);applied=True
    return base_t,tickets(p2,pc),applied,gap

def evaluate(rows,cfg,payouts,post_wall3=False,need_rows=False):
    monthly={}
    total={'R':0,'base_hits':0,'hits':0,'base_return':0,'return':0,'changed':0,'gain':0,'loss':0,'applied':0}
    det=[]
    for r in rows:
        code=str(r['race_code']).zfill(12);mon=str(r['month']);actual=str(r['actual_combo'])
        bt,ct,applied,gap=candidate_ticket(r,cfg,post_wall3)
        bh=int(actual in bt.split(';'));h=int(actual in ct.split(';'));p=payouts[code]
        d=h-bh
        m=monthly.setdefault(mon,{'R':0,'base_hits':0,'hits':0,'base_return':0,'return':0,'changed':0,'gain':0,'loss':0,'applied':0})
        for q in (total,m):
            q['R']+=1;q['base_hits']+=bh;q['hits']+=h;q['base_return']+=p*bh;q['return']+=p*h
            q['changed']+=int(bt!=ct);q['gain']+=int(d==1);q['loss']+=int(d==-1);q['applied']+=int(applied)
        if need_rows and (bt!=ct or d!=0):
            det.append({'race_code':code,'month':mon,'actual_combo':actual,'opp_mass':float(r['opp_mass']),
                        'score6':float(r['score6']),'st_gap':gap,'base_tickets':bt,'tickets':ct,
                        'base_hit':bh,'hit':h,'delta':d,'applied':int(applied)})
    def fin(q):
        stake=q['R']*300
        return {**q,'stake':stake,'base_roi':q['base_return']/stake if stake else 0.0,
                'roi':q['return']/stake if stake else 0.0,'delta_hits':q['hits']-q['base_hits'],
                'delta_roi_pp':100*((q['return']-q['base_return'])/stake) if stake else 0.0}
    return fin(total),{k:fin(v) for k,v in monthly.items()},det

def cfg_dict(score6,stmin,g2,g3,mass):
    return {'score6_min':float(score6),'st_min':float(stmin),'g2':float(g2),'g3':float(g3),'mass_min':float(mass)}

def cfg_key(c):
    return f"s6={c['score6_min']:.3f}|st={c['st_min']:.3f}|g2={c['g2']:.3f}|g3={c['g3']:.3f}|m={c['mass_min']:.3f}"

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));allrows=x['rows']
    rows313=allrows['H0775_M350']; rows165=allrows['LIVE165']
    if len(rows313)!=313 or len(rows165)!=165:raise RuntimeError('prepared universe drift')
    union_by_code={}
    for name in ('LIVE165','H078_M375','H0775_M375','H0775_M350'):
        for r in allrows[name]: union_by_code[str(r['race_code']).zfill(12)]=r
    unionrows=list(union_by_code.values())
    prefetch=install_payout_cache(unionrows);payouts=payouts_for(unionrows)
    dev=[r for r in rows313 if str(r['month']) in DEV];sup=[r for r in rows313 if str(r['month']) in SUP]

    grid=[];monthly_cache={}
    configs=[]
    for s6 in SCORE6:
      for stm in STMIN:
       for g2 in G2:
        for g3 in G3:
         for mass in MASS:
          c=cfg_dict(s6,stm,g2,g3,mass);configs.append(c)
          dm,dmon,_=evaluate(dev,c,payouts,False)
          grid.append({**c,'key':cfg_key(c),**{f'dev_{k}':v for k,v in dm.items()}})
          monthly_cache[cfg_key(c)]=dmon
    g=pd.DataFrame(grid)
    zero=g[g.dev_loss.eq(0)].copy()
    maxdh=int(zero.dev_delta_hits.max())
    z=zero[zero.dev_delta_hits.eq(maxdh)].copy()
    best_roi=float(z.dev_roi.max())
    plateau=z[z.dev_roi.ge(best_roi-.01)].copy()  # within 1 ROI point of DEV best
    if len(plateau)==0:raise RuntimeError('empty plateau')

    # DEV-only raw best; tie-break toward fewer changes, then parameter-center/simple g2.
    raw=z.sort_values(['dev_roi','dev_changed','g2','st_min','score6_min'],
                      ascending=[False,True,True,True,True]).iloc[0]
    med={k:float(plateau[k].median()) for k in ['score6_min','st_min','g2','g3','mass_min']}
    plateau['medoid_dist']=sum((plateau[k]-med[k]).abs()/(max(1e-9,float(plateau[k].max()-plateau[k].min()))) for k in med)
    center=plateau.sort_values(['medoid_dist','dev_changed','g2'],ascending=[True,True,True]).iloc[0]

    def rowcfg(row):return {k:float(row[k]) for k in ['score6_min','st_min','g2','g3','mass_min']}
    chosen=rowcfg(center)

    # Frozen chosen candidate: SUPPORT / ALL313 / current wall3+LIVE165.
    supm,supmon,_=evaluate(sup,chosen,payouts,False)
    allm,allmon,detail313=evaluate(rows313,chosen,payouts,False,True)
    livem,livemon,detail165=evaluate(rows165,chosen,payouts,True,True)

    # Formal wall3 baseline sentinel on LIVE165.
    dummy={'score6_min':2.0,'st_min':2.0,'g2':0.0,'g3':0.0,'mass_min':1.0}
    wallbase,_,_=evaluate(rows165,dummy,payouts,True)
    if (wallbase['R'],wallbase['base_hits'],wallbase['base_return'])!=(165,83,58650):
        raise RuntimeError(f'wall3 sentinel drift {wallbase}')

    # Disjoint expanded bands using frozen chosen config.
    chain=['LIVE165','H078_M375','H0775_M375','H0775_M350']
    bands=[];prev=set()
    for name in chain:
        rr=allrows[name];ids={str(r['race_code']).zfill(12) for r in rr};bid=ids-prev
        br=[r for r in rr if str(r['race_code']).zfill(12) in bid]
        mm,_,_=evaluate(br,chosen,payouts,False)
        bands.append({'band':name if not prev else f'ADDED_TO_{name}',**mm});prev=ids

    # LOMO re-selection entirely within DEV: subtract held month from cached DEV summary.
    lomo=[]
    dev_by_month={m:[r for r in dev if str(r['month'])==m] for m in DEV}
    for hold in DEV:
        train=[r for r in dev if str(r['month'])!=hold]
        rec=[]
        for c in configs:
            mm,_,_=evaluate(train,c,payouts,False)
            if mm['loss']==0:
                rec.append(({**c},mm))
        md=max(m['delta_hits'] for _,m in rec)
        rr=[(c,m) for c,m in rec if m['delta_hits']==md]
        broi=max(m['roi'] for _,m in rr)
        rr=[(c,m) for c,m in rr if m['roi']>=broi-.01]
        # medoid-like deterministic choice using fixed grid center preference.
        target={'score6_min':.60,'st_min':.40,'g2':0.0,'g3':.75,'mass_min':.375}
        sel=min(rr,key=lambda cm:sum(abs(cm[0][k]-target[k]) for k in target))[0]
        hm,_,_=evaluate(dev_by_month[hold],sel,payouts,False)
        lomo.append({'holdout_month':hold,**sel,**{f'hold_{k}':v for k,v in hm.items()}})

    # Neighborhood stats around chosen using one grid step in every dimension.
    neigh=g[
      (g.score6_min.sub(chosen['score6_min']).abs()<=.05+1e-12)&
      (g.st_min.sub(chosen['st_min']).abs()<=.05+1e-12)&
      (g.g2.sub(chosen['g2']).abs()<=.25+1e-12)&
      (g.g3.sub(chosen['g3']).abs()<=.125+1e-12)&
      (g.mass_min.sub(chosen['mass_min']).abs()<=.025+1e-12)
    ].copy()

    promotion={
      'dev_loss_zero':bool(center.dev_loss==0),
      'support_loss_zero':bool(supm['loss']==0),
      'support_nonnegative_hits':bool(supm['delta_hits']>=0),
      'live165_loss_zero':bool(livem['loss']==0),
      'live165_improves_hits':bool(livem['delta_hits']>0),
      'lomo_all_nonnegative':bool(all(x['hold_delta_hits']>=0 for x in lomo)),
      'plateau_size_ge_10':bool(len(plateau)>=10),
      'neighborhood_nonnegative_share':float((neigh.dev_delta_hits>=0).mean()) if len(neigh) else 0.0,
      'outer_bands_have_gain':bool(sum(max(0,int(x['delta_hits'])) for x in bands[1:])>0),
    }
    promotion['all_conditions_pass']=all(v for k,v in promotion.items() if k!='neighborhood_nonnegative_share') and promotion['neighborhood_nonnegative_share']>=.80

    g.to_csv(OUT/'dev_grid.csv',index=False);plateau.to_csv(OUT/'dev_plateau.csv',index=False)
    neigh.to_csv(OUT/'neighborhood.csv',index=False)
    pd.DataFrame(bands).to_csv(OUT/'bands.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False)
    pd.DataFrame(detail313).to_csv(OUT/'chosen_changed_313.csv',index=False)
    pd.DataFrame(detail165).to_csv(OUT/'chosen_changed_live165.csv',index=False)
    pd.DataFrame([{'month':m,**v} for m,v in allmon.items()]).to_csv(OUT/'chosen_monthly_313.csv',index=False)
    pd.DataFrame([{'month':m,**v} for m,v in livemon.items()]).to_csv(OUT/'chosen_monthly_live165.csv',index=False)

    result={
      'prepared_source':'v360 Artifact 10539401122','payout_prefetch':prefetch,
      'grid_cells':len(g),'max_dev_delta_hits_zero_loss':maxdh,'dev_plateau_size':len(plateau),
      'dev_plateau_ranges':{k:[float(plateau[k].min()),float(plateau[k].max())] for k in ['score6_min','st_min','g2','g3','mass_min']},
      'raw_dev_best':raw.to_dict(),'plateau_center_selected':chosen,
      'selected_dev':{k:v for k,v in center.to_dict().items() if k.startswith('dev_')},
      'selected_support':supm,'selected_all313':allm,
      'wall3_live165_baseline':wallbase,'selected_combined_live165':livem,
      'bands':bands,'lomo':lomo,'promotion_checks':promotion,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
