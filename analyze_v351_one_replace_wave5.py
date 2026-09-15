#!/usr/bin/env python3
"""Wave5 diagnostic: explain Wave4 frozen-June rescue vs false damage.
Historical only; September 2026 outcomes are never read. Production unchanged.
"""
import numpy as np
import pandas as pd

TH=-0.05

def main():
 q=pd.read_csv('analysis_v351_one_replace_wave4_june.csv',dtype={'race_code':str})
 q['race_code']=q.race_code.astype(str).str.zfill(12)
 if not (q.race_code.str[:8]<'20260901').all(): raise RuntimeError('September outcome guard')
 q['override']=q.margin.ge(TH)
 q['outcome']='NO_OVERRIDE'
 q.loc[q.override,'outcome']='OVERRIDE_OTHER'
 q.loc[q.override & q.kind.eq('REPLACE_ONE') & q.proposal_hit.eq(1),'outcome']='RESCUE'
 q.loc[q.override & q.kind.eq('KEEP') & q.proposal_hit.eq(0),'outcome']='DAMAGE'
 q.to_csv('analysis_v351_one_replace_wave5_cases.csv',index=False,encoding='utf-8-sig')
 focus=q[q.outcome.isin(['RESCUE','DAMAGE'])].copy()
 print('THRESHOLD',TH,'R',len(q),'OVERRIDES',int(q.override.sum()))
 print('FOCUS_COUNTS');print(focus.outcome.value_counts().to_string())
 print('FOCUS_CASES')
 cols=['race_code','schema','outcome','margin','current_pair','keep_boat','drop_boat','replacement','actual_pair']
 print(focus[cols].sort_values(['outcome','margin'],ascending=[True,False]).to_string(index=False))
 print('BY_SCHEMA')
 print(q.groupby(['schema','outcome']).size().rename('R').reset_index().to_string(index=False))
 # Guard candidates are diagnostic only. They use causal schema/margin, not June labels at runtime.
 guards={
  'ALL_TH_-005': q.margin.ge(-.05),
  'TH_000': q.margin.ge(0),
  'TH_005': q.margin.ge(.05),
  'LTS_TH_-005': q.margin.ge(-.05)&q.schema.eq('lap+turn+straight'),
  'LTS_TH_000': q.margin.ge(0)&q.schema.eq('lap+turn+straight'),
 }
 rows=[]
 for name,ov in guards.items():
  hit=np.where(ov,q.proposal_hit,q.baseline_hit)
  rows.append({'guard':name,'R':len(q),'overrides':int(ov.sum()),'hits':int(hit.sum()),'hit_rate':100*hit.mean(),'delta_hits':int(hit.sum()-q.baseline_hit.sum()),'damage':int((ov&q.kind.eq('KEEP')&q.proposal_hit.eq(0)).sum()),'rescue':int((ov&q.kind.eq('REPLACE_ONE')&q.proposal_hit.eq(1)).sum())})
 s=pd.DataFrame(rows);s.to_csv('analysis_v351_one_replace_wave5_guard_summary.csv',index=False,encoding='utf-8-sig')
 print('GUARDS');print(s.to_string(index=False))
 print('SEPTEMBER_OUTCOMES_USED',False);print('PRODUCTION_CHANGED',False)
if __name__=='__main__':main()
