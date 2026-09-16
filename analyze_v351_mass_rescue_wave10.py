#!/usr/bin/env python3
"""Wave10: audit whether the [0.350,0.375) opponent-mass band is rescueable.
Post-ranking / ticket-rescue diagnostic only; production is unchanged.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
SRC='analysis_v351_opponent_mass_threshold_rows.csv'; LO,HI=.350,.375
# JCD03 (Edogawa) has no rows in the schema-rebuild source population, so no
# additional original-exhibition schema can be established there. Treat it
# explicitly as BASE rather than silently guessing an unavailable schema.
EXPLICIT_BASE_FALLBACK={3:'base'}

def rate(s): return 100*float(s.mean()) if len(s) else np.nan

def main():
 z=pd.read_csv(SRC,dtype={'race_code':str}); z['race_code']=z.race_code.astype(str).str.zfill(12)
 if (z.race_code.str[:8]>='20260901').any(): raise RuntimeError('September outcome row detected')
 q=z[(z.opp_mass>=LO)&(z.opp_mass<HI)].copy()
 if q.empty: raise RuntimeError('low-mass rescue band empty')
 q['month']=q.race_code.str[:4]+'-'+q.race_code.str[4:6]; q['jcd']=q.race_code.str[8:10].astype(int); q['race_no']=q.race_code.str[10:12].astype(int)
 # Correct classification: schema is venue-level, so join the explicit jcd->schema map.
 sm=pd.read_csv('analysis_v351_schema_map.csv')
 sm['jcd']=pd.to_numeric(sm.jcd,errors='raise').astype(int)
 if sm.jcd.duplicated().any(): raise RuntimeError('duplicate jcd in schema map')
 mp=sm.set_index('jcd').schema.astype(str).to_dict()
 overlap=set(mp).intersection(EXPLICIT_BASE_FALLBACK)
 if overlap: raise RuntimeError(f'explicit fallback now present in schema map jcd={sorted(overlap)}; remove fallback and audit schema')
 mp.update(EXPLICIT_BASE_FALLBACK)
 q['schema']=q.jcd.map(mp)
 if q.schema.isna().any():
  missing=sorted(q.loc[q.schema.isna(),'jcd'].unique().tolist()); raise RuntimeError(f'unmapped schema jcd={missing}')
 # Known domain invariant: half is Kiryu-only.
 bad=q[q.schema.str.contains('half',na=False)&q.jcd.ne(1)]
 if len(bad): raise RuntimeError('half schema outside Kiryu')
 q['rescue_opportunity']=((q.head_hit==1)&(q.exact3==0)).astype(int); q['already_exact3']=q.exact3.astype(int); q['head_miss']=(q.head_hit==0).astype(int)
 q.to_csv('analysis_v351_mass_rescue_wave10_rows.csv',index=False,encoding='utf-8-sig')
 out=[]
 def add(scope,key,g): out.append({'scope':scope,'key':str(key),'R':len(g),'HEAD':int(g.head_hit.sum()),'HEAD_rate':rate(g.head_hit),'EXACT3':int(g.exact3.sum()),'EXACT3_rate':rate(g.exact3),'RESCUE_OPP':int(g.rescue_opportunity.sum()),'RESCUE_OPP_rate':rate(g.rescue_opportunity),'mass_mean':g.opp_mass.mean()})
 add('ALL','ALL',q)
 for c in ['month','jcd','schema','race_no']:
  for k,g in q.groupby(c): add(c,k,g)
 s=pd.DataFrame(out); s.to_csv('analysis_v351_mass_rescue_wave10_summary.csv',index=False,encoding='utf-8-sig')
 edges=[.350,.355,.360,.365,.370,.375]; q['mass_bin']=pd.cut(q.opp_mass,edges,right=False,include_lowest=True); bins=[]
 for k,g in q.groupby('mass_bin',observed=True): bins.append({'mass_bin':str(k),'R':len(g),'HEAD_rate':rate(g.head_hit),'EXACT3_rate':rate(g.exact3),'RESCUE_OPP':int(g.rescue_opportunity.sum()),'RESCUE_OPP_rate':rate(g.rescue_opportunity)})
 pd.DataFrame(bins).to_csv('analysis_v351_mass_rescue_wave10_bins.csv',index=False,encoding='utf-8-sig')
 print('SEPTEMBER_OUTCOMES_USED False'); print('PRODUCTION_CHANGED False'); print('HEAD_EXHIBITION_DIRECT_FEATURE False'); print('SCHEMA_CLASSIFICATION venue_map_plus_explicit_base_fallback_jcd03')
 print('BAND',LO,HI,'R',len(q),'HEAD',int(q.head_hit.sum()),f'HEAD_RATE={rate(q.head_hit):.2f}','EXACT3',int(q.exact3.sum()),f'EXACT3_RATE={rate(q.exact3):.2f}','RESCUE_OPP',int(q.rescue_opportunity.sum()))
 print('\nBY_SCHEMA'); print(s[s.scope.eq('schema')].to_string(index=False)); print('\nBY_VENUE'); print(s[s.scope.eq('jcd')].sort_values(['R','RESCUE_OPP'],ascending=False).to_string(index=False)); print('\nMASS_BINS'); print(pd.DataFrame(bins).to_string(index=False))
if __name__=='__main__': main()
