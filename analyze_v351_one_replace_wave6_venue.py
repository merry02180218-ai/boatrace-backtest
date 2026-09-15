#!/usr/bin/env python3
"""Wave6 diagnostic: frozen-June venue/JCD effect on Wave4 one-replacement.
Historical only. September 2026 outcomes are never read. Production unchanged.
"""
import numpy as np
import pandas as pd

TH=-0.05

def main():
 q=pd.read_csv('analysis_v351_one_replace_wave4_june.csv',dtype={'race_code':str})
 q['race_code']=q.race_code.astype(str).str.zfill(12)
 if not (q.race_code.str[:8]<'20260901').all(): raise RuntimeError('September outcome guard')
 q['jcd']=q.race_code.str[8:10]
 q['override']=q.margin.ge(TH)
 q['final_hit']=np.where(q.override,q.proposal_hit,q.baseline_hit)
 q['damage']=q.override & q.kind.eq('KEEP') & q.proposal_hit.eq(0)
 q['rescue']=q.override & q.kind.eq('REPLACE_ONE') & q.proposal_hit.eq(1)
 q['delta']=q.final_hit-q.baseline_hit

 def summarize(x):
  return pd.Series({
   'R':len(x),'baseline_hits':int(x.baseline_hit.sum()),'baseline_rate':100*x.baseline_hit.mean(),
   'union_hits':int(x.union_hit.sum()),'overrides':int(x.override.sum()),
   'rescue':int(x.rescue.sum()),'damage':int(x.damage.sum()),
   'final_hits':int(x.final_hit.sum()),'final_rate':100*x.final_hit.mean(),'delta_hits':int(x.delta.sum())})
 s=q.groupby('jcd',sort=True).apply(summarize,include_groups=False).reset_index()
 s.to_csv('analysis_v351_one_replace_wave6_venue_summary.csv',index=False,encoding='utf-8-sig')
 lts=q[q.schema.eq('lap+turn+straight')].copy()
 sl=lts.groupby('jcd',sort=True).apply(summarize,include_groups=False).reset_index()
 sl.to_csv('analysis_v351_one_replace_wave6_lts_venue_summary.csv',index=False,encoding='utf-8-sig')
 focus=q[q.rescue|q.damage].copy()
 focus['outcome']=np.where(focus.rescue,'RESCUE','DAMAGE')
 focus.to_csv('analysis_v351_one_replace_wave6_focus.csv',index=False,encoding='utf-8-sig')
 print('THRESHOLD',TH,'R',len(q),'VENUES',q.jcd.nunique())
 print('BY_VENUE');print(s.to_string(index=False))
 print('LTS_BY_VENUE');print(sl.to_string(index=False))
 print('FOCUS_BY_VENUE');print(focus.groupby(['jcd','outcome']).size().rename('R').reset_index().to_string(index=False))
 print('FOCUS_CASES');print(focus[['race_code','jcd','schema','outcome','margin','current_pair','keep_boat','drop_boat','replacement','actual_pair']].sort_values(['jcd','outcome']).to_string(index=False))
 print('SEPTEMBER_OUTCOMES_USED',False);print('PRODUCTION_CHANGED',False)
if __name__=='__main__':main()
