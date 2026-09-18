#!/usr/bin/env python3
from __future__ import annotations
"""v373: LOMO robustness for v372 same-budget odds-spread reallocation."""
from pathlib import Path
import argparse,json
import pandas as pd
import run_v372_1head_soft_dutch_300 as v372

OUT=Path('/tmp/v373-soft-dutch-lomo');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

def select_threshold(train):
    rec=[]
    for t in v372.THRESHOLDS:
        m,_=v372.evaluate(train,t)
        if m['lost_hits']==0:
            rec.append(m)
    if not rec:raise RuntimeError('no zero-loss train threshold')
    d=pd.DataFrame(rec)
    return float(d.sort_values(['roi','changed_R','threshold'],ascending=[False,True,False]).iloc[0].threshold),d

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--race-level',required=True,type=Path);args=ap.parse_args()
    z=pd.read_csv(args.race_level,dtype={'race_code':str});z.race_code=z.race_code.str.zfill(12)
    if len(z)!=165 or any(z.race_code.str.startswith('202609')):raise RuntimeError('race-level drift')
    base=v372.baseline(z)
    if (base['hits'],base['return_yen'])!=(87,63700):raise RuntimeError('baseline drift')

    lomo=[]
    for hold in DEV:
        train=z[z.month.isin([m for m in DEV if m!=hold])].copy()
        test=z[z.month.eq(hold)].copy()
        th,_=select_threshold(train)
        tm,_=v372.evaluate(test,th);tb=v372.baseline(test)
        lomo.append({'holdout_month':hold,'selected_threshold':th,
                     'base_hits':tb['hits'],'policy_hits':tm['hits'],'delta_hits':tm['hits']-tb['hits'],
                     'lost_hits':tm['lost_hits'],'base_roi':tb['roi'],'policy_roi':tm['roi'],
                     'delta_roi_pp':100*(tm['roi']-tb['roi']),'changed_R':tm['changed_R'],
                     'doubled_win_R':tm['doubled_win_R']})
    ld=pd.DataFrame(lomo)

    fixed=[]
    for mon,g in z.groupby('month'):
        m,_=v372.evaluate(g,3.5);b=v372.baseline(g)
        fixed.append({'month':mon,'base_hits':b['hits'],'policy_hits':m['hits'],'delta_hits':m['hits']-b['hits'],
                      'lost_hits':m['lost_hits'],'base_roi':b['roi'],'policy_roi':m['roi'],
                      'delta_roi_pp':100*(m['roi']-b['roi']),'changed_R':m['changed_R']})
    fd=pd.DataFrame(fixed)

    # Aggregate LOMO realized stake/return across the held-out months.
    # Each DEV month appears exactly once.
    total_base_stake=sum(v372.baseline(z[z.month.eq(m)])['stake_yen'] for m in DEV)
    total_base_ret=sum(v372.baseline(z[z.month.eq(m)])['return_yen'] for m in DEV)
    total_pol_stake=0;total_pol_ret=0
    for x in lomo:
        g=z[z.month.eq(x['holdout_month'])]
        mm,_=v372.evaluate(g,float(x['selected_threshold']))
        total_pol_stake+=mm['stake_yen'];total_pol_ret+=mm['return_yen']
    agg={'R':len(z[z.month.isin(DEV)]),'base_stake_yen':total_base_stake,'base_return_yen':total_base_ret,
         'base_roi':total_base_ret/total_base_stake,'policy_stake_yen':total_pol_stake,
         'policy_return_yen':total_pol_ret,'policy_roi':total_pol_ret/total_pol_stake,
         'delta_roi_pp':100*(total_pol_ret/total_pol_stake-total_base_ret/total_base_stake)}

    support=z[z.month.isin(SUP)].copy()
    sm,_=v372.evaluate(support,3.5);sb=v372.baseline(support)

    ld.to_csv(OUT/'lomo.csv',index=False);fd.to_csv(OUT/'fixed35_monthly.csv',index=False)
    result={
      'lomo':lomo,'lomo_aggregate':agg,
      'lomo_all_zero_lost_hits':bool((ld.lost_hits==0).all()),
      'lomo_all_nonnegative_roi':bool((ld.delta_roi_pp>=-1e-12).all()),
      'fixed35_all_months_zero_lost_hits':bool((fd.lost_hits==0).all()),
      'fixed35_all_months_nonnegative_roi':bool((fd.delta_roi_pp>=-1e-12).all()),
      'support_fixed35':{'base':sb,'policy':sm,'delta_roi_pp':100*(sm['roi']-sb['roi'])},
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
