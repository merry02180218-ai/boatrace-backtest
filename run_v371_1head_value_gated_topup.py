#!/usr/bin/env python3
from __future__ import annotations
"""v371: robust value-gated top-up staking on current formal 3 tickets.

Uses v370 formal_with_closing_odds.csv only. All 165 races remain bought, and
formal ticket composition is frozen. Each race starts at 1 unit per ticket.
Additional units are allowed only when both combined-odds and conditional-value
gates fire. Selection is DEV-only; SUPPORT is untouched until core freeze.
"""
from pathlib import Path
import argparse,json,math
import numpy as np
import pandas as pd

OUT=Path('/tmp/v371-value-gated-topup');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
COMBINED=[2.0,2.25,2.5,2.75,3.0,3.25,3.5,3.75,4.0]
VALUE=[.7,.8,.9,1.0,1.1,1.2,1.3,1.4,1.5]
EXTRA=(1,2,3)

def alloc_value(r,extra):
    vals=np.array([float(r.p1*r.odds1),float(r.p2*r.odds2),float(r.p3*r.odds3)],dtype=float)
    units=np.ones(3,dtype=int)
    rem=int(extra)
    if rem<=0:return units.tolist()
    if not np.isfinite(vals).all() or vals.sum()<=0:vals=np.ones(3)
    target=rem*vals/vals.sum()
    floor=np.floor(target).astype(int);units+=floor
    left=rem-int(floor.sum())
    frac=target-floor
    for i in np.argsort(-frac)[:left]:units[int(i)]+=1
    return units.tolist()

def gate(r,c,e):
    return float(r.combined_odds)>=c and max(float(r.p1*r.odds1),float(r.p2*r.odds2),float(r.p3*r.odds3))>=e

def evaluate(z,c,e,extra):
    stake=ret=0;rows=[];trig=0
    for _,r in z.iterrows():
        active=gate(r,c,e)
        u=alloc_value(r,extra) if active else [1,1,1]
        trig+=int(active);s=sum(u)*100;stake+=s
        rr=0;hr=int(r.hit_rank)
        if hr>0:rr=int(r.payout100)*u[hr-1]
        ret+=rr
        rows.append({'race_code':r.race_code,'month':r.month,'active':int(active),
                     'u1':u[0],'u2':u[1],'u3':u[2],'return_yen':rr,'hit_rank':hr})
    return {'R':len(z),'trigger_R':trig,'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0},pd.DataFrame(rows)

def baseline(z):
    stake=len(z)*300
    ret=int(sum(int(r.payout100) for _,r in z.iterrows() if int(r.hit_rank)>0))
    return {'R':len(z),'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--features',required=True,type=Path);args=ap.parse_args()
    z=pd.read_csv(args.features,dtype={'race_code':str});z.race_code=z.race_code.str.zfill(12)
    if len(z)!=165:raise RuntimeError(f'R drift {len(z)}')
    if any(z.race_code.str[:8].ge('20260901')):raise RuntimeError('September entered')
    base=baseline(z)
    if (base['return_yen'],base['stake_yen'])!=(63700,49500):raise RuntimeError(f'baseline drift {base}')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    bdev=baseline(dev);bsup=baseline(sup)

    grid=[]
    for c in COMBINED:
      for e in VALUE:
       for x in EXTRA:
        m,_=evaluate(dev,c,e,x)
        row={'combined_min':c,'value_min':e,'extra_units':x,
             **{f'dev_{k}':v for k,v in m.items()},
             'dev_delta_roi_pp':100*(m['roi']-bdev['roi'])}
        deltas=[]
        for mon in DEV:
            mm,_=evaluate(dev[dev.month.eq(mon)],c,e,x)
            bb=baseline(dev[dev.month.eq(mon)])
            deltas.append(100*(mm['roi']-bb['roi']))
        row['dev_nonnegative_months']=sum(d>=-1e-12 for d in deltas)
        row['dev_worst_month_delta_pp']=min(deltas)
        row['dev_mean_month_delta_pp']=float(np.mean(deltas))
        grid.append(row)
    g=pd.DataFrame(grid)
    raw=g.sort_values(['dev_roi','dev_profit_yen'],ascending=False).iloc[0]
    best_roi=float(raw.dev_roi)
    plateau=g[g.dev_roi.ge(best_roi-.025)].copy()
    med={'combined_min':float(plateau.combined_min.median()),
         'value_min':float(plateau.value_min.median()),
         'extra_units':float(plateau.extra_units.median())}
    ranges={k:max(float(plateau[k].max()-plateau[k].min()),1e-9) for k in med}
    plateau['medoid_dist']=sum((plateau[k]-med[k]).abs()/ranges[k] for k in med)
    core=plateau.sort_values(['medoid_dist','dev_roi','dev_profit_yen'],ascending=[True,False,False]).iloc[0]
    c=float(core.combined_min);e=float(core.value_min);x=int(core.extra_units)

    dm,drows=evaluate(dev,c,e,x);sm,srows=evaluate(sup,c,e,x);am,arows=evaluate(z,c,e,x)

    monthly=[]
    for mon in sorted(z.month.unique()):
        q=z[z.month.eq(mon)]
        mm,_=evaluate(q,c,e,x);bb=baseline(q)
        monthly.append({'month':mon,'baseline_roi':bb['roi'],'core_roi':mm['roi'],
                        'delta_roi_pp':100*(mm['roi']-bb['roi']),
                        'baseline_profit':bb['profit_yen'],'core_profit':mm['profit_yen'],
                        'trigger_R':mm['trigger_R']})

    # Neighborhood around frozen core.
    neigh=g[(g.combined_min.sub(c).abs()<=.25+1e-12)&
            (g.value_min.sub(e).abs()<=.10+1e-12)&
            (g.extra_units.sub(x).abs()<=1)].copy()

    g.to_csv(OUT/'dev_grid.csv',index=False);plateau.to_csv(OUT/'dev_plateau.csv',index=False)
    neigh.to_csv(OUT/'neighborhood.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly.csv',index=False)
    arows.to_csv(OUT/'core_allocations.csv',index=False)

    result={
      'baseline_all':base,'baseline_dev':bdev,'baseline_support':bsup,
      'raw_dev_best':raw.to_dict(),'dev_plateau_size':len(plateau),
      'plateau_ranges':{k:[float(plateau[k].min()),float(plateau[k].max())] for k in ['combined_min','value_min','extra_units']},
      'dev_plateau_medoid':{'combined_min':c,'value_min':e,'extra_units':x},
      'core_dev':dm,'core_support':sm,'core_all':am,
      'delta_roi_pp_all':100*(am['roi']-base['roi']),
      'delta_roi_pp_support':100*(sm['roi']-bsup['roi']),
      'neighborhood_cells':len(neigh),
      'neighborhood_nonnegative_dev_share':float((neigh.dev_delta_roi_pp>=0).mean()) if len(neigh) else 0.0,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
