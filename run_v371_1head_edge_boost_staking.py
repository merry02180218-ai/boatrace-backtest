#!/usr/bin/env python3
from __future__ import annotations
"""v371: base 300 yen + positive-edge ticket boosts on current formal top3.

All 165 races and all 3 formal tickets remain bought at >=100 yen each.
Only extra 100-yen units are added to tickets whose pre-race model/market edge
passes a fixed threshold. DEV Feb-Jun selects robust parameters; Jul-Aug is holdout.
"""
from pathlib import Path
import argparse,json,pickle
import numpy as np
import pandas as pd

OUT=Path('/tmp/v371-edge-boost');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
THRESH=(.5,.6,.7,.8,.9,1.0,1.1,1.2,1.3,1.4,1.5,1.75,2.0)
MAX_EXTRA=(1,2,3)

def enrich(v370,prepared):
    z=pd.read_csv(v370,dtype={'race_code':str})
    x=pickle.load(open(prepared,'rb'))
    p=pd.DataFrame([{'race_code':str(r['race_code']).zfill(12),'p_head':float(r['p_head'])}
                    for r in x['rows']['LIVE165']])
    z.race_code=z.race_code.astype(str).str.zfill(12)
    z=z.merge(p,on='race_code',validate='one_to_one')
    if len(z)!=165 or int((z.hit_rank>0).sum())!=87:raise RuntimeError('formal row identity drift')
    return z

def edge_values(r,mode):
    vals=[float(r.p1)*float(r.odds1),float(r.p2)*float(r.odds2),float(r.p3)*float(r.odds3)]
    if mode=='UNCOND':vals=[float(r.p_head)*v for v in vals]
    return vals

def policy_units(r,mode,threshold,max_extra):
    e=edge_values(r,mode);u=[1,1,1];added=0
    for i in sorted(range(3),key=lambda i:(-e[i],i)):
        if added>=max_extra:break
        if e[i]>=threshold:
            u[i]+=1;added+=1
    return u,e

def evaluate(z,mode,threshold,max_extra,detail=False):
    stake=ret=extras=0;alloc=[0,0,0];rows=[]
    for r in z.itertuples():
        u,e=policy_units(r,mode,threshold,max_extra)
        s=sum(u)*100;stake+=s;extras+=sum(u)-3
        for i in range(3):alloc[i]+=u[i]
        rank=int(r.hit_rank);rr=0
        if rank>0:
            rr=int(r.payout100)*u[rank-1];ret+=rr
        if detail:
            rows.append({'race_code':r.race_code,'month':r.month,'u1':u[0],'u2':u[1],'u3':u[2],
                         'e1':e[0],'e2':e[1],'e3':e[2],'hit_rank':rank,'return_yen':rr})
    return {
      'R':len(z),'extra_units':extras,'stake_yen':stake,'return_yen':ret,
      'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
      'avg_u1':alloc[0]/len(z),'avg_u2':alloc[1]/len(z),'avg_u3':alloc[2]/len(z),
      'details':rows
    }

def equal(z):
    stake=len(z)*300
    ret=int(sum(int(r.payout100) for r in z.itertuples() if int(r.hit_rank)>0))
    return {'R':len(z),'extra_units':0,'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def monthly_deltas(z,mode,t,m):
    out=[]
    for mon in DEV:
        g=z[z.month.eq(mon)]
        b=equal(g);q=evaluate(g,mode,t,m)
        out.append({'month':mon,'delta_roi_pp':100*(q['roi']-b['roi']),
                    'equal_roi':b['roi'],'policy_roi':q['roi'],
                    'delta_profit_yen':q['profit_yen']-b['profit_yen'],
                    'extra_units':q['extra_units']})
    return out

def robust_select(z,months,min_delta=0.05,worst_floor=-3.0,nonneg_need=None):
    if nonneg_need is None:nonneg_need=max(1,len(months)-1)
    rec=[]
    base=equal(z)
    for mode in ('COND','UNCOND'):
      for t in THRESH:
       for mx in MAX_EXTRA:
        q=evaluate(z,mode,t,mx)
        deltas=[]
        for mon in months:
            g=z[z.month.eq(mon)]
            b=equal(g);qm=evaluate(g,mode,t,mx)
            deltas.append(100*(qm['roi']-b['roi']))
        row={'mode':mode,'threshold':t,'max_extra':mx,
             'roi':q['roi'],'profit_yen':q['profit_yen'],'extra_units':q['extra_units'],
             'delta_roi_pp':100*(q['roi']-base['roi']),
             'nonnegative_months':sum(x>=0 for x in deltas),
             'worst_month_delta_pp':min(deltas),'median_month_delta_pp':float(np.median(deltas)),
             'monthly_deltas':deltas}
        rec.append(row)
    df=pd.DataFrame([{k:v for k,v in r.items() if k!='monthly_deltas'} for r in rec])
    eligible=[r for r in rec if r['delta_roi_pp']>=100*min_delta and
              r['nonnegative_months']>=nonneg_need and r['worst_month_delta_pp']>=worst_floor]
    if not eligible:
        eligible=[r for r in rec if r['delta_roi_pp']>0 and r['nonnegative_months']>=nonneg_need]
    if not eligible:
        eligible=rec
    chosen=max(eligible,key=lambda r:(r['worst_month_delta_pp'],r['roi'],-r['extra_units'],-r['threshold']))
    return chosen,df

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--v370-csv',required=True,type=Path)
    ap.add_argument('--prepared',required=True,type=Path)
    args=ap.parse_args()
    z=enrich(args.v370_csv,args.prepared)
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    base=equal(z);bdev=equal(dev);bsup=equal(sup)
    if (base['return_yen'],base['stake_yen'])!=(63700,49500):raise RuntimeError(f'baseline drift {base}')

    chosen,grid=robust_select(dev,DEV,min_delta=.05,worst_floor=-3.0,nonneg_need=4)
    mode=chosen['mode'];t=float(chosen['threshold']);mx=int(chosen['max_extra'])
    dm=evaluate(dev,mode,t,mx,True);sm=evaluate(sup,mode,t,mx,True);am=evaluate(z,mode,t,mx,True)

    # monthly frozen policy
    monthly=[]
    for mon,g in z.groupby('month'):
        b=equal(g);q=evaluate(g,mode,t,mx)
        monthly.append({'month':mon,'equal_roi':b['roi'],'policy_roi':q['roi'],
                        'delta_roi_pp':100*(q['roi']-b['roi']),
                        'equal_profit_yen':b['profit_yen'],'policy_profit_yen':q['profit_yen'],
                        'delta_profit_yen':q['profit_yen']-b['profit_yen'],
                        'extra_units':q['extra_units']})

    # LOMO re-selection within DEV only.
    lomo=[]
    for hold in DEV:
        train_months=[m for m in DEV if m!=hold]
        train=z[z.month.isin(train_months)]
        test=z[z.month.eq(hold)]
        sel,_=robust_select(train,train_months,min_delta=.03,worst_floor=-4.0,nonneg_need=3)
        b=equal(test);q=evaluate(test,sel['mode'],float(sel['threshold']),int(sel['max_extra']))
        lomo.append({'holdout_month':hold,'mode':sel['mode'],'threshold':sel['threshold'],'max_extra':sel['max_extra'],
                     'equal_roi':b['roi'],'test_roi':q['roi'],'delta_roi_pp':100*(q['roi']-b['roi']),
                     'equal_profit_yen':b['profit_yen'],'test_profit_yen':q['profit_yen'],
                     'delta_profit_yen':q['profit_yen']-b['profit_yen'],'extra_units':q['extra_units']})

    # Threshold neighborhood for chosen mode/max_extra.
    near=grid[(grid['mode']==mode)&(grid['max_extra']==mx)&
              (grid['threshold'].between(max(min(THRESH),t-.2),min(max(THRESH),t+.2)))].copy()

    # Edge distribution diagnostics and allocation detail.
    detail=pd.DataFrame(am['details'])
    zz=z.merge(detail,on=['race_code','month'],validate='one_to_one')
    zz['max_cond_edge']=zz[['ev1','ev2','ev3']].max(axis=1)
    zz['max_uncond_edge']=zz['p_head']*zz['max_cond_edge']

    grid.to_csv(OUT/'dev_grid.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo.csv',index=False)
    near.to_csv(OUT/'neighborhood.csv',index=False)
    zz.to_csv(OUT/'chosen_allocations.csv',index=False)

    result={
      'formal_equal':base,'equal_dev':bdev,'equal_support':bsup,
      'dev_selection_rule':{'min_dev_delta_roi_pp':5.0,'nonnegative_dev_months_min':4,'worst_month_delta_pp_min':-3.0,
                            'tie_break':'max worst-month delta, then DEV ROI, then fewer extras'},
      'dev_selected':{k:v for k,v in chosen.items() if k!='monthly_deltas'},
      'selected_dev':{k:v for k,v in dm.items() if k!='details'},
      'selected_support':{k:v for k,v in sm.items() if k!='details'},
      'selected_all':{k:v for k,v in am.items() if k!='details'},
      'delta_roi_pp_all':100*(am['roi']-base['roi']),
      'delta_profit_yen_all':am['profit_yen']-base['profit_yen'],
      'delta_roi_pp_support':100*(sm['roi']-bsup['roi']),
      'delta_profit_yen_support':sm['profit_yen']-bsup['profit_yen'],
      'lomo':lomo,
      'lomo_nonnegative_months':int(sum(x['delta_roi_pp']>=0 for x in lomo)),
      'lomo_total_delta_profit_yen':int(sum(x['delta_profit_yen'] for x in lomo)),
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
