#!/usr/bin/env python3
from __future__ import annotations
"""v371: pre-specified odds-aware staking formulas on current formal 3 tickets.

Uses v370 race_level with 165/165 official closing odds coverage.
No ticket/race selection changes. Strategies are fixed before SUPPORT evaluation.
"""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd

OUT=Path('/tmp/v371-confidence-value-staking');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
BUDGETS=(6,9,12,15,18,21,24,30)

STRATEGIES={
 'EQUAL': lambda p,o: np.ones(3,float),
 'DUTCH': lambda p,o: np.power(o,-1.0),
 'MODEL_P': lambda p,o: p,
 'EV_PxO': lambda p,o: p*o,
 'CONF_EV_P2xO': lambda p,o: p*p*o,
 'SOFT_EV_PxSQRT_O': lambda p,o: p*np.sqrt(o),
}

def alloc(scores,total_units):
    scores=np.asarray(scores,float)
    scores=np.where(np.isfinite(scores)&(scores>0),scores,0.0)
    u=np.ones(3,dtype=int);rem=int(total_units-3)
    if rem<0:raise ValueError('budget too small')
    if rem==0:return u
    if scores.sum()<=0:scores=np.ones(3,float)
    target=rem*scores/scores.sum()
    fl=np.floor(target).astype(int);u+=fl
    left=total_units-int(u.sum())
    frac=target-fl
    order=sorted(range(3),key=lambda i:(-frac[i],-scores[i],i))
    for i in order[:left]:u[i]+=1
    if int(u.sum())!=total_units:raise RuntimeError('allocation drift')
    return u

def evaluate(z,name,budget,need_rows=False):
    f=STRATEGIES[name];rows=[]
    ret=0
    for _,r in z.iterrows():
        p=np.array([r.p1,r.p2,r.p3],float);o=np.array([r.o1,r.o2,r.o3],float)
        u=alloc(f(p,o),budget)
        rank=int(r.hit_rank);rr=int(r.payout100)*int(u[rank-1]) if rank>0 else 0
        ret+=rr
        if need_rows:
            rows.append({'race_code':str(r.race_code).zfill(12),'month':r.month,
                         'u1':int(u[0]),'u2':int(u[1]),'u3':int(u[2]),
                         'hit_rank':rank,'payout100':int(r.payout100),'return_yen':rr})
    stake=len(z)*budget*100
    m={'R':len(z),'budget_units':budget,'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,
       'roi':ret/stake if stake else 0.0}
    if need_rows:
        q=pd.DataFrame(rows)
        m.update({'avg_u1':float(q.u1.mean()),'avg_u2':float(q.u2.mean()),'avg_u3':float(q.u3.mean()),
                  'min_u1':int(q.u1.min()),'max_u1':int(q.u1.max()),
                  'min_u2':int(q.u2.min()),'max_u2':int(q.u2.max()),
                  'min_u3':int(q.u3.min()),'max_u3':int(q.u3.max())})
        return m,q
    return m,None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--race-level',required=True,type=Path);args=ap.parse_args()
    z=pd.read_csv(args.race_level,dtype={'race_code':str})
    z.race_code=z.race_code.str.zfill(12)
    if len(z)!=165:raise RuntimeError(f'v370 coverage drift {len(z)}')
    if any(z.race_code.str.startswith('202609')):raise RuntimeError('September entered')
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    baseline_return=int(z.loc[z.hit_rank.gt(0),'payout100'].sum())
    if (int(z.hit_rank.gt(0).sum()),baseline_return)!=(87,63700):
        raise RuntimeError('formal baseline drift')

    rec=[];monthly=[]
    for name in STRATEGIES:
      for budget in BUDGETS:
        dm,_=evaluate(dev,name,budget);sm,_=evaluate(sup,name,budget);am,rows=evaluate(z,name,budget,True)
        rec.append({'strategy':name,'budget_units':budget,
                    **{f'dev_{k}':v for k,v in dm.items()},
                    **{f'support_{k}':v for k,v in sm.items()},
                    **{f'all_{k}':v for k,v in am.items()}})
        for mon,g in z.groupby('month'):
            mm,_=evaluate(g,name,budget)
            em,_=evaluate(g,'EQUAL',budget)
            monthly.append({'strategy':name,'budget_units':budget,'month':mon,**mm,
                            'equal_roi':em['roi'],'delta_roi_pp_vs_equal':100*(mm['roi']-em['roi'])})
        if name=='CONF_EV_P2xO':
            rows['budget_units']=budget
            rows.to_csv(OUT/f'conf_ev_rows_budget_{budget}.csv',index=False)

    res=pd.DataFrame(rec);mo=pd.DataFrame(monthly)
    res.to_csv(OUT/'strategy_budget_summary.csv',index=False);mo.to_csv(OUT/'monthly.csv',index=False)

    # Pre-specified CONF_EV diagnostics only; support is not used to define formula.
    conf=res[res.strategy.eq('CONF_EV_P2xO')].copy()
    eq=res[res.strategy.eq('EQUAL')][['budget_units','dev_roi','support_roi','all_roi']].rename(
        columns={'dev_roi':'eq_dev_roi','support_roi':'eq_support_roi','all_roi':'eq_all_roi'})
    conf=conf.merge(eq,on='budget_units',validate='one_to_one')
    conf['dev_delta_pp']=100*(conf.dev_roi-conf.eq_dev_roi)
    conf['support_delta_pp']=100*(conf.support_roi-conf.eq_support_roi)
    conf['all_delta_pp']=100*(conf.all_roi-conf.eq_all_roi)
    conf.to_csv(OUT/'conf_ev_budget_sensitivity.csv',index=False)

    robust=conf[(conf.dev_delta_pp.gt(0))&(conf.support_delta_pp.gt(0))]
    # A representative budget is chosen by stability, not max SUPPORT:
    # smallest budget in the contiguous >=900-yen robust region.
    representative=None
    if len(robust):
        representative=robust.sort_values('budget_units').iloc[0].to_dict()

    # 1200 yen is pre-declared practical checkpoint for rounding granularity.
    checkpoint=conf[conf.budget_units.eq(12)].iloc[0].to_dict()
    cm=mo[(mo.strategy.eq('CONF_EV_P2xO'))&(mo.budget_units.eq(12))].copy()

    result={
      'source':'v370 current formal3 / official closing odds 165R',
      'formal_hits':87,
      'strategies_pre_specified':list(STRATEGIES),
      'budgets_yen':[x*100 for x in BUDGETS],
      'conf_ev_robust_budgets_yen':[int(x*100) for x in robust.budget_units.tolist()],
      'conf_ev_representative_smallest_robust':representative,
      'conf_ev_1200_checkpoint':checkpoint,
      'conf_ev_1200_monthly_nonnegative_vs_equal':int((cm.delta_roi_pp_vs_equal>=-1e-12).sum()),
      'conf_ev_1200_monthly_total':len(cm),
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
