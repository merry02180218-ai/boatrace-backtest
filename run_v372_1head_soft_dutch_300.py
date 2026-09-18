#!/usr/bin/env python3
from __future__ import annotations
"""v372: same-300-yen odds-spread reallocation on current formal3.

When selected-ticket closing odds are sufficiently dispersed, move one 100-yen
unit from the longest-odds ticket to the shortest-odds ticket. Total stake stays
300 yen/race. Threshold is selected on Feb-Jun DEV only.
"""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd

OUT=Path('/tmp/v372-soft-dutch-300');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
THRESHOLDS=tuple(round(x,2) for x in np.arange(2.5,6.01,.1))

def evaluate(z,threshold,need_rows=False):
    rec=[];ret=0;hits=0;changed=0;lost=0;doubled_win=0
    source_rank={1:0,2:0,3:0};target_rank={1:0,2:0,3:0}
    for _,r in z.iterrows():
        odds=np.array([r.o1,r.o2,r.o3],float);u=np.ones(3,dtype=int)
        ratio=float(odds.max()/odds.min())
        src=tgt=0
        if ratio>=threshold:
            src=int(np.argmax(odds));tgt=int(np.argmin(odds))
            if src==tgt:raise RuntimeError('same source/target')
            u[src]-=1;u[tgt]+=1;changed+=1
            source_rank[src+1]+=1;target_rank[tgt+1]+=1
        rank=int(r.hit_rank);h=False;rr=0
        if rank>0 and u[rank-1]>0:
            h=True;hits+=1;rr=int(r.payout100)*int(u[rank-1]);ret+=rr
            if u[rank-1]>1:doubled_win+=1
        elif rank>0:
            lost+=1
        if need_rows:
            rec.append({'race_code':str(r.race_code).zfill(12),'month':r.month,'hit_rank':rank,
                        'payout100':int(r.payout100),'o1':float(r.o1),'o2':float(r.o2),'o3':float(r.o3),
                        'odds_ratio':ratio,'u1':int(u[0]),'u2':int(u[1]),'u3':int(u[2]),
                        'changed':int(src!=tgt and ratio>=threshold),'source_rank':src+1 if ratio>=threshold else 0,
                        'target_rank':tgt+1 if ratio>=threshold else 0,'hit':int(h),'return_yen':rr})
    stake=len(z)*300
    m={'R':len(z),'threshold':threshold,'hits':hits,'hit_rate':hits/len(z) if len(z) else 0.0,
       'lost_hits':lost,'changed_R':changed,'doubled_win_R':doubled_win,
       'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
       'source_rank1_R':source_rank[1],'source_rank2_R':source_rank[2],'source_rank3_R':source_rank[3],
       'target_rank1_R':target_rank[1],'target_rank2_R':target_rank[2],'target_rank3_R':target_rank[3]}
    return (m,pd.DataFrame(rec)) if need_rows else (m,None)

def baseline(z):
    ret=int(z.loc[z.hit_rank.gt(0),'payout100'].sum());stake=len(z)*300
    return {'R':len(z),'hits':int(z.hit_rank.gt(0).sum()),'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--race-level',required=True,type=Path);args=ap.parse_args()
    z=pd.read_csv(args.race_level,dtype={'race_code':str});z.race_code=z.race_code.str.zfill(12)
    if len(z)!=165 or any(z.race_code.str.startswith('202609')):raise RuntimeError('race-level drift')
    base=baseline(z)
    if (base['hits'],base['return_yen'],base['stake_yen'])!=(87,63700,49500):
        raise RuntimeError(f'formal baseline drift {base}')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    bdev=baseline(dev);bsup=baseline(sup)

    grid=[]
    for t in THRESHOLDS:
        dm,_=evaluate(dev,t);grid.append({**dm,'delta_roi_pp':100*(dm['roi']-bdev['roi']),
                                         'delta_hits':dm['hits']-bdev['hits']})
    g=pd.DataFrame(grid)
    elig=g[g.lost_hits.eq(0)].copy()
    if len(elig)==0:raise RuntimeError('no zero-loss DEV threshold')
    best=elig.sort_values(['roi','changed_R','threshold'],ascending=[False,True,False]).iloc[0]
    chosen=float(best.threshold)

    sm,_=evaluate(sup,chosen);am,rows=evaluate(z,chosen,True)
    # Full threshold support diagnostics after DEV freeze.
    full=[]
    for t in THRESHOLDS:
        dm,_=evaluate(dev,t);ss,_=evaluate(sup,t);aa,_=evaluate(z,t)
        full.append({'threshold':t,
                     'dev_hits':dm['hits'],'dev_lost_hits':dm['lost_hits'],'dev_roi':dm['roi'],
                     'support_hits':ss['hits'],'support_lost_hits':ss['lost_hits'],'support_roi':ss['roi'],
                     'all_hits':aa['hits'],'all_lost_hits':aa['lost_hits'],'all_roi':aa['roi'],
                     'changed_R':aa['changed_R']})
    f=pd.DataFrame(full)
    plateau=f[(f.dev_lost_hits.eq(0))&(f.support_lost_hits.eq(0))].copy()

    monthly=[]
    for mon,q in z.groupby('month'):
        mm,_=evaluate(q,chosen);bb=baseline(q)
        monthly.append({'month':mon,**{f'base_{k}':v for k,v in bb.items()},
                        **{f'policy_{k}':v for k,v in mm.items()},
                        'delta_roi_pp':100*(mm['roi']-bb['roi']),
                        'delta_hits':mm['hits']-bb['hits']})

    rows.to_csv(OUT/'chosen_race_level.csv',index=False)
    g.to_csv(OUT/'dev_threshold_grid.csv',index=False);f.to_csv(OUT/'full_threshold_diagnostics.csv',index=False)
    plateau.to_csv(OUT/'zero_loss_plateau.csv',index=False);pd.DataFrame(monthly).to_csv(OUT/'monthly.csv',index=False)

    result={
      'formal_equal100':base,'formal_dev':bdev,'formal_support':bsup,
      'dev_selected_threshold':chosen,'selected_dev':best.to_dict(),
      'selected_support':sm,'selected_all':am,
      'all_delta_roi_pp':100*(am['roi']-base['roi']),
      'zero_loss_dev_support_threshold_min':float(plateau.threshold.min()) if len(plateau) else None,
      'zero_loss_dev_support_threshold_max':float(plateau.threshold.max()) if len(plateau) else None,
      'zero_loss_plateau_cells':len(plateau),
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
