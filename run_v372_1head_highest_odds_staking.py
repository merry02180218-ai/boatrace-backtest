#!/usr/bin/env python3
from __future__ import annotations
"""v372: simple highest-closing-odds staking and conditional extra-stake audit.

Frozen input: v370 race_inputs.csv. Tickets are never changed. Every race buys
all 3 formal tickets for 100 yen each. Optional extra stake is placed only on
the highest-odds ticket among the three.
"""
from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd

OUT=Path('/tmp/v372-highest-odds-staking');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
EXTRA=(1,2,3,4,5,6,9)
ODDS_MAX=(8.,10.,12.,15.,20.,999.)
RATIO_MAX=(1.4,1.6,2.0,99.)
COMBINED_MAX=(1.8,2.0,2.2,2.5,99.)

def prep(z):
    odds=z[['odds1','odds2','odds3']].to_numpy(float)
    order=np.argsort(-odds,axis=1)
    n=np.arange(len(z));t=order[:,0];s=order[:,1]
    z=z.copy()
    z['target_rank']=t+1
    z['target_odds']=odds[n,t]
    z['second_odds']=odds[n,s]
    z['odds_ratio']=z.target_odds/z.second_odds
    z['combined_odds']=1.0/(1.0/odds).sum(axis=1)
    z['target_hit']=((z.hit_rank.to_numpy(int)==z.target_rank.to_numpy(int))&(z.hit_rank.to_numpy(int)>0)).astype(int)
    z['base_return']=np.where(z.hit_rank.to_numpy(int)>0,z.payout100.to_numpy(int),0)
    return z

def evaluate(z,extra_units,gate=None,detail=False):
    if gate is None:
        active=np.ones(len(z),dtype=bool)
    else:
        active=(
          z.target_odds.le(gate['odds_max']+1e-12)&
          z.odds_ratio.le(gate['ratio_max']+1e-12)&
          z.combined_odds.le(gate['combined_max']+1e-12)
        ).to_numpy()
    base=z.base_return.to_numpy(int)
    bonus=(z.payout100.to_numpy(int)*z.target_hit.to_numpy(int)*extra_units)*active.astype(int)
    ret_vec=base+bonus
    stake_vec=np.full(len(z),300,dtype=int)+active.astype(int)*extra_units*100
    profit=ret_vec-stake_vec
    cum=np.cumsum(profit)
    peak=np.maximum.accumulate(np.r_[0,cum])[1:] if len(cum) else np.array([])
    dd=peak-cum if len(cum) else np.array([0])
    zero=(ret_vec==0)
    streak=mx=0
    for v in zero:
        if v:streak+=1;mx=max(mx,streak)
        else:streak=0
    out={
      'R':len(z),'hits':int((z.hit_rank>0).sum()),'active_R':int(active.sum()),
      'target_hits_active':int((z.target_hit.to_numpy(int)*active.astype(int)).sum()),
      'stake_yen':int(stake_vec.sum()),'return_yen':int(ret_vec.sum()),
      'profit_yen':int(profit.sum()),'roi':float(ret_vec.sum()/stake_vec.sum()) if stake_vec.sum() else 0.0,
      'max_drawdown_yen':int(dd.max()) if len(dd) else 0,
      'profit_per_maxdd':float(profit.sum()/dd.max()) if len(dd) and dd.max()>0 else None,
      'max_zero_return_streak':mx,'profit_std_yen':float(np.std(profit)) if len(profit) else 0.0,
    }
    if detail:
        d=z[['race_code','month','hit_rank','target_rank','target_odds','odds_ratio','combined_odds','payout100','target_hit']].copy()
        d['active']=active.astype(int);d['stake_yen']=stake_vec;d['return_yen']=ret_vec;d['profit_yen']=profit
        out['detail']=d
    return out

def baseline(z):
    return evaluate(z,0,gate=None)

def gate(om,rm,cm):
    return {'odds_max':float(om),'ratio_max':float(rm),'combined_max':float(cm)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--race-inputs',required=True,type=Path);args=ap.parse_args()
    z=pd.read_csv(args.race_inputs,dtype={'race_code':str});z.race_code=z.race_code.str.zfill(12)
    z=prep(z)
    if len(z)!=165 or int((z.hit_rank>0).sum())!=87 or int(z.base_return.sum())!=63700:
        raise RuntimeError('frozen input sentinel drift')
    if any(z.race_code.str.startswith('202609')):raise RuntimeError('September entered')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    base_all=baseline(z);base_dev=baseline(dev);base_sup=baseline(sup)

    # No-gate simple line.
    simple=[]
    for e in EXTRA:
        dm=evaluate(dev,e);sm=evaluate(sup,e);am=evaluate(z,e)
        monthly=[]
        for mon,g in z.groupby('month'):
            mm=evaluate(g,e);bb=baseline(g)
            monthly.append({'month':mon,'roi':mm['roi'],'base_roi':bb['roi'],'delta_roi_pp':100*(mm['roi']-bb['roi'])})
        simple.append({'extra_units':e,
                       **{f'dev_{k}':v for k,v in dm.items()},
                       **{f'support_{k}':v for k,v in sm.items()},
                       **{f'all_{k}':v for k,v in am.items()},
                       'months_nonnegative_vs_base':sum(x['delta_roi_pp']>=0 for x in monthly),
                       'monthly':monthly})

    # Conditional gates selected on DEV only.
    rows=[]
    for e in EXTRA:
      for om in ODDS_MAX:
       for rm in RATIO_MAX:
        for cm in COMBINED_MAX:
         c=gate(om,rm,cm);dm=evaluate(dev,e,c)
         if dm['active_R']<20:continue
         deltas=[];nonneg=0
         for mon in DEV:
            q=dev[dev.month.eq(mon)];mm=evaluate(q,e,c);bb=baseline(q);d=100*(mm['roi']-bb['roi'])
            deltas.append(d);nonneg+=int(d>=0)
         rows.append({'extra_units':e,**c,**{f'dev_{k}':v for k,v in dm.items()},
                      'dev_delta_roi_pp':100*(dm['roi']-base_dev['roi']),
                      'dev_month_nonnegative_R':nonneg,'dev_month_worst_delta_pp':min(deltas)})
    grid=pd.DataFrame(rows)
    raw=grid.sort_values(['dev_roi','dev_active_R'],ascending=[False,False]).iloc[0]
    robust_pool=grid[grid.dev_month_nonnegative_R.ge(3)].copy()
    robust=robust_pool.sort_values(['dev_roi','dev_month_worst_delta_pp','dev_max_drawdown_yen'],
                                   ascending=[False,False,True]).iloc[0] if len(robust_pool) else raw

    def rowcfg(r):
        return int(r.extra_units),gate(r.odds_max,r.ratio_max,r.combined_max)

    selected=[]
    for label,r in [('RAW_DEV',raw),('ROBUST_DEV',robust)]:
        e,c=rowcfg(r);sm=evaluate(sup,e,c);am=evaluate(z,e,c,detail=True)
        selected.append({'selector':label,'extra_units':e,**c,
                         **{f'support_{k}':v for k,v in sm.items()},
                         **{f'all_{k}':v for k,v in am.items() if k!='detail'},
                         'support_delta_roi_pp':100*(sm['roi']-base_sup['roi']),
                         'all_delta_roi_pp':100*(am['roi']-base_all['roi'])})
        am['detail'].to_csv(OUT/f'detail_{label}.csv',index=False)

    # True LOMO re-selection on gated grid.
    lomo=[]
    configs=[(int(r.extra_units),gate(r.odds_max,r.ratio_max,r.combined_max)) for _,r in grid.iterrows()]
    for hold in DEV:
        train=dev[~dev.month.eq(hold)].copy();test=dev[dev.month.eq(hold)].copy()
        cand=[]
        for e,c in configs:
            m=evaluate(train,e,c)
            if m['active_R']<15:continue
            cand.append((m['roi'],-m['max_drawdown_yen'],e,c))
        _,_,e,c=max(cand,key=lambda x:(x[0],x[1]))
        hm=evaluate(test,e,c);hb=baseline(test)
        lomo.append({'holdout_month':hold,'extra_units':e,**c,
                     'roi':hm['roi'],'base_roi':hb['roi'],'delta_roi_pp':100*(hm['roi']-hb['roi']),
                     'active_R':hm['active_R'],'profit_yen':hm['profit_yen'],'base_profit_yen':hb['profit_yen']})

    # Save simple monthly rows separately.
    simple_rows=[]
    for s in simple:
        for m in s.pop('monthly'):
            simple_rows.append({'extra_units':s['extra_units'],**m})
    simple_df=pd.DataFrame(simple)
    grid.to_csv(OUT/'dev_gate_grid.csv',index=False);simple_df.to_csv(OUT/'simple_no_gate.csv',index=False)
    pd.DataFrame(simple_rows).to_csv(OUT/'simple_monthly.csv',index=False)
    pd.DataFrame(selected).to_csv(OUT/'selected_gates.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo_reselected.csv',index=False)
    z.to_csv(OUT/'frozen_features.csv',index=False)

    result={
      'formal_equal300':base_all,'formal_dev':base_dev,'formal_support':base_sup,
      'simple_no_gate':simple_df.to_dict('records'),
      'gate_grid_R':len(grid),'raw_dev_gate':raw.to_dict(),'robust_dev_gate':robust.to_dict(),
      'selected_gate_support_all':selected,'lomo':lomo,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
