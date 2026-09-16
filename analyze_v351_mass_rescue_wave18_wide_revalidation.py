#!/usr/bin/env python3
"""Wave18: wide revalidation of frozen BOAT3_STRONGER -> boat5 THIRD rescue.

Uses Wave17 definitions unchanged. Feb-Apr is discovery only. Every available
historical month after Apr and before Sep 2026 is holdout. September outcomes
and payouts are hard forbidden. Production is unchanged.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import analyze_v351_mass_rescue_wave17_boat5_third_rescue as w17


def smry(scope,key,q):
    R=len(q)
    return {'scope':scope,'key':str(key),'R':R,
            'baseline_hits':int(q.baseline_hit.sum()),
            'baseline_rate':100*q.baseline_hit.mean() if R else np.nan,
            'candidate_hits':int(q.candidate_hit.sum()),
            'candidate_rate':100*q.candidate_hit.mean() if R else np.nan,
            'overrides':int(q.fixed3_override.sum()),
            'fixed3_hits':int(q.fixed3_hit.sum()),
            'fixed3_rate':100*q.fixed3_hit.mean() if R else np.nan,
            'rescues':int(q.fixed3_rescue.sum()),
            'damages':int(q.fixed3_damage.sum()),
            'net':int(q.fixed3_rescue.sum()-q.fixed3_damage.sum())}


def main():
    base=pd.read_csv(w17.SRC,dtype={'race_code':str})
    base.race_code=base.race_code.astype(str).str.zfill(12)
    if (base.race_code.str[:8]>='20260901').any():
        raise RuntimeError('September outcome row detected')
    base=base[(base.opp_mass>=w17.LO)&(base.opp_mass<w17.HI)&base.schema.isin(w17.SCHEMAS)].copy()
    feat=w17.build_pre_result_strength(base)
    allr=w17.make_rows(base,feat)
    if (allr.race_code.str[:8]>='20260901').any():
        raise RuntimeError('September row after feature build')
    elig=allr[allr.eligible.eq(1)].copy()
    train=elig[elig.month.isin(['202602','202603','202604'])].copy()
    if train.empty: raise RuntimeError('empty Feb-Apr discovery set')

    # Reproduce Wave17 freeze exactly from discovery months; no holdout outcome selects policy.
    grid=[]
    for sb in w17.SECOND_CHOICES:
        for slot in range(3):
            q=w17.eval_policy(train,sb,slot); s=w17.summary('TRAIN',q)
            grid.append({'second_boat':sb,'replace_slot':slot+1,**s})
    gd=pd.DataFrame(grid)
    best=gd.sort_values(['fixed3_net','fixed3_rescues','fixed3_damages','second_boat','replace_slot'],
                        ascending=[False,False,True,True,False]).iloc[0]
    chosen_second=int(best.second_boat); chosen_slot=int(best.replace_slot)-1
    if chosen_second != 3:
        raise RuntimeError(f'Wave17 freeze drift: expected SECOND=3, got {chosen_second}')

    evaluated=[]
    for m,g in elig.groupby('month'):
        q=w17.eval_policy(g,chosen_second,chosen_slot)
        q['period']='DISCOVERY' if m in ['202602','202603','202604'] else ('HOLDOUT' if m>'202604' else 'PRE_DISCOVERY')
        evaluated.append(q)
    d=pd.concat(evaluated,ignore_index=True)
    d=d[d.month<'202609'].copy()
    if (d.race_code.str[:8]>='20260901').any(): raise RuntimeError('September evaluated row detected')
    d['strength_bucket']=pd.cut(d.strength2_minus3,[-np.inf,.75,1.0,1.5,np.inf],right=False).astype(str)
    d.to_csv('analysis_v351_mass_rescue_wave18_rows.csv',index=False,encoding='utf-8-sig')

    out=[]
    for m,g in d.groupby('month'): out.append(smry('month',m,g))
    hold=d[d.period.eq('HOLDOUT')].copy()
    out.append(smry('holdout_all','ALL',hold))
    for j,g in hold.groupby('jcd'): out.append(smry('holdout_jcd',j,g))
    for s,g in hold.groupby('schema'): out.append(smry('holdout_schema',s,g))
    for b,g in hold.groupby('strength_bucket',observed=True): out.append(smry('holdout_strength_bucket',b,g))
    summary=pd.DataFrame(out)
    summary.to_csv('analysis_v351_mass_rescue_wave18_summary.csv',index=False,encoding='utf-8-sig')

    print('SEPTEMBER_OUTCOMES_USED False')
    print('PRODUCTION_CHANGED False')
    print('HEAD_EXHIBITION_DIRECT_FEATURE False')
    print('POLICY_FROZEN_FROM Feb-Apr only')
    print('CHOSEN_SECOND',chosen_second,'CHOSEN_REPLACE_SLOT',chosen_slot+1,'CANDIDATE',f'1-{chosen_second}-5')
    print('AVAILABLE_MONTHS',','.join(sorted(d.month.unique())))
    print('HOLDOUT_MONTHS',','.join(sorted(hold.month.unique())))
    print('\nMONTHLY')
    print(summary[summary.scope.eq('month')].to_string(index=False))
    print('\nHOLDOUT_ALL')
    print(summary[summary.scope.eq('holdout_all')].to_string(index=False))
    print('\nHOLDOUT_BY_SCHEMA')
    print(summary[summary.scope.eq('holdout_schema')].to_string(index=False))
    print('\nHOLDOUT_BY_STRENGTH_BUCKET')
    print(summary[summary.scope.eq('holdout_strength_bucket')].to_string(index=False))
    print('\nHOLDOUT_BY_VENUE')
    print(summary[summary.scope.eq('holdout_jcd')].sort_values(['R','net'],ascending=[False,False]).to_string(index=False))

if __name__=='__main__': main()
