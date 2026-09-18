#!/usr/bin/env python3
from __future__ import annotations
"""v380: bankroll / drawdown audit for fixed WALL3 rank3 overweight allocation.

No parameter search. Total stake is identical race-by-race to the current EITHER2x
shadow. Only internal units on WALL3 races change from 2/2/2 to 1/1/4.
"""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd

OUT=Path('/tmp/v380-wall3-rank3-risk');OUT.mkdir(parents=True,exist_ok=True)
UNIVERSES=('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276')

def hit_rank(r):
    if not int(r.hit):return 0
    ts=str(r.tickets).split(';');a=str(r.actual_combo)
    if a not in ts:raise RuntimeError(f'hit mismatch {r.race_code}')
    return ts.index(a)+1

def enrich(z):
    z=z.copy();z['hit_rank']=[hit_rank(r) for r in z.itertuples()]
    return z

def units(r,candidate):
    if int(r.wall3):
        return (1,1,4) if candidate else (2,2,2)
    if int(r.either):return (2,2,2)
    return (1,1,1)

def longest(xs):
    best=cur=0
    for x in xs:
        if bool(x):cur+=1;best=max(best,cur)
        else:cur=0
    return best

def curve(z,candidate):
    rows=[]
    for r in z.sort_values('race_code').itertuples():
        u=units(r,candidate);s=sum(u)*100;rank=int(r.hit_rank)
        ret=int(r.payout100)*u[rank-1] if rank>0 else 0
        rows.append({'race_code':str(r.race_code),'month':str(r.month),'wall3':int(r.wall3),
                     'five6':int(r.five6),'hit_rank':rank,'u1':u[0],'u2':u[1],'u3':u[2],
                     'stake':s,'return':ret,'profit':ret-s})
    a=pd.DataFrame(rows)
    a['cum_stake']=a.stake.cumsum();a['cum_return']=a['return'].cumsum();a['equity']=a.profit.cumsum()
    eq=a.equity.to_numpy(float)
    peaks=np.maximum.accumulate(np.r_[0,eq])[1:] if len(eq) else np.array([])
    dd=peaks-eq if len(eq) else np.array([])
    maxdd=float(dd.max()) if len(dd) else 0.0
    trough=int(dd.argmax()) if len(dd) else -1
    peak_val=float(peaks[trough]) if trough>=0 else 0.0
    prior=eq[:trough+1] if trough>=0 else np.array([])
    matches=np.where(np.isclose(prior,peak_val))[0]
    peak_idx=int(matches[-1]) if len(matches) else -1
    span=trough-peak_idx if trough>=0 else 0
    roll10=float(a.profit.rolling(10).sum().min()) if len(a)>=10 else float(a.profit.sum())
    roll20=float(a.profit.rolling(20).sum().min()) if len(a)>=20 else float(a.profit.sum())
    m=a.groupby('month',sort=True).agg(stake=('stake','sum'),returns=('return','sum'),profit=('profit','sum'))
    m['roi']=m.returns/m.stake
    stake=int(a.stake.sum());ret=int(a['return'].sum());profit=ret-stake
    metric={
      'R':len(a),'stake':stake,'return':ret,'profit':profit,'roi':ret/stake if stake else 0.0,
      'max_drawdown_yen':maxdd,'drawdown_race_span':int(span),
      'longest_losing_streak':int(longest(a.profit.lt(0).tolist())),
      'worst_10R_profit':roll10,'worst_20R_profit':roll20,
      'monthly_profit_std':float(m.profit.std(ddof=0)) if len(m) else 0.0,
      'monthly_worst_profit':int(m.profit.min()) if len(m) else 0,
      'monthly_best_profit':int(m.profit.max()) if len(m) else 0,
      'profit_per_10k_stake':10000*profit/stake if stake else 0.0,
      'profit_per_maxdd':profit/maxdd if maxdd>0 else None,
    }
    return metric,a,m.reset_index()

def compare(z):
    b,bc,bm=curve(z,False);c,cc,cm=curve(z,True)
    if b['stake']!=c['stake']:raise RuntimeError('total stake mismatch')
    return b,c,bc,cc,bm,cm

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--v374-dir',required=True,type=Path);a=ap.parse_args()
    rows={}
    for u in UNIVERSES:
        p=a.v374_dir/f'rows_{u}.csv'
        z=pd.read_csv(p,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12)
        rows[u]=enrich(z)
    live=rows['LIVE165']
    if (len(live),int(live.hit.sum()),int(live.loc[live.hit.eq(1),'payout100'].sum()),int(live.either.sum()))!=(165,87,63700,36):
        raise RuntimeError('LIVE165 sentinel drift')

    univ=[];live_detail=None;monthly=[]
    for u,z in rows.items():
        b,c,bc,cc,bm,cm=compare(z)
        univ.append({'universe':u,**{f'base_{k}':v for k,v in b.items()},**{f'cand_{k}':v for k,v in c.items()},
                     'delta_profit':c['profit']-b['profit'],'delta_roi_pp':100*(c['roi']-b['roi']),
                     'delta_maxdd_yen':c['max_drawdown_yen']-b['max_drawdown_yen']})
        if u=='LIVE165':
            d=bc.merge(cc,on=['race_code','month','wall3','five6','hit_rank'],suffixes=('_base','_cand'),validate='one_to_one')
            d['delta_return']=d.return_cand-d.return_base;d['delta_profit']=d.profit_cand-d.profit_base
            live_detail=d
            mm=bm.merge(cm,on='month',suffixes=('_base','_cand'),validate='one_to_one')
            mm['delta_profit']=mm.profit_cand-mm.profit_base;mm['delta_roi_pp']=100*(mm.roi_cand-mm.roi_base)
            monthly=mm.to_dict('records')

    # WALL3-only incremental cashflow in LIVE.
    w=live_detail[live_detail.wall3.eq(1)].copy()
    incr={
      'wall3_R':len(w),'rank1_hits':int((w.hit_rank==1).sum()),'rank2_hits':int((w.hit_rank==2).sum()),
      'rank3_hits':int((w.hit_rank==3).sum()),'miss_R':int((w.hit_rank==0).sum()),
      'delta_return_total':int(w.delta_return.sum()),'delta_profit_total':int(w.delta_profit.sum()),
      'delta_return_positive_R':int((w.delta_return>0).sum()),
      'delta_return_negative_R':int((w.delta_return<0).sum()),
      'delta_return_zero_R':int((w.delta_return==0).sum()),
      'worst_single_delta':int(w.delta_return.min()),'best_single_delta':int(w.delta_return.max()),
    }

    u=pd.DataFrame(univ);u.to_csv(OUT/'universes.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly_live165.csv',index=False)
    live_detail.to_csv(OUT/'live165_curve_compare.csv',index=False)
    w.to_csv(OUT/'live165_wall3_incremental.csv',index=False)

    liveu=u[u.universe.eq('LIVE165')].iloc[0].to_dict()
    result={
      'rule':'WALL3 100/100/400; five6-only 200/200/200; none 100/100/100',
      'baseline':'EITHER overlay all 200/200/200; none 100/100/100',
      'live165':liveu,'wall3_incremental':incr,'universes':univ,'monthly_live165':monthly,
      'NO_PARAMETER_SEARCH':True,'TOTAL_STAKE_IDENTICAL':True,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
