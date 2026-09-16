#!/usr/bin/env python3
"""Wave13: explain which current opponent to KEEP vs DROP in Wave11 one-replace cases.
Historical diagnostic only. September 2026 outcomes are hard forbidden. Production unchanged.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import research_v351_mass_rescue_wave12_frozen_guard as w12

SRC10='analysis_v351_mass_rescue_wave10_rows.csv'
SRC11='analysis_v351_mass_rescue_wave11_one_replace_rows.csv'
FEATURES=['ex','st','ex_rank','st_rank','turn_rank','straight_rank','orig_avg_rank']

def main():
 b=pd.read_csv(SRC10,dtype={'race_code':str}); b.race_code=b.race_code.astype(str).str.zfill(12)
 q=pd.read_csv(SRC11,dtype={'race_code':str}); q.race_code=q.race_code.astype(str).str.zfill(12)
 if (b.race_code.str[:8]>='20260901').any() or (q.race_code.str[:8]>='20260901').any():
  raise RuntimeError('September outcome row detected')
 q=q[q.first_rescue_class.eq('KEEP_ONE_REPLACE_ONE')].copy()
 if len(q)!=57: print('WARN_KEEP1_R',len(q))
 # Build the exact same result-independent exhibition feature definitions used by Wave12.
 f=w12.build_features(b[(b.opp_mass>=w12.LO)&(b.opp_mass<w12.HI)&b.schema.isin(w12.SCHEMAS)].copy())
 f=f.set_index(['race_code','boat'])
 rec=[]
 for _,r in q.iterrows():
  actual={int(r.actual2),int(r.actual3)}
  s=int(r.first_second); t=int(r.first_third)
  keep=s if s in actual else t; drop=t if keep==s else s
  if (r.race_code,keep) not in f.index or (r.race_code,drop) not in f.index: continue
  fk=f.loc[(r.race_code,keep)]; fd=f.loc[(r.race_code,drop)]
  z={'race_code':r.race_code,'schema':r.schema,'jcd':int(r.jcd),'keep_boat':keep,'drop_boat':drop,
     'keep_position':'SECOND' if keep==s else 'THIRD','drop_position':'THIRD' if keep==s else 'SECOND'}
  for c in FEATURES:
   z['keep_'+c]=fk[c]; z['drop_'+c]=fd[c]; z['delta_keep_minus_drop_'+c]=fk[c]-fd[c]
  rec.append(z)
 o=pd.DataFrame(rec)
 if o.empty: raise RuntimeError('no Wave13 rows')
 o.to_csv('analysis_v351_mass_rescue_wave13_keepdrop_rows.csv',index=False,encoding='utf-8-sig')
 # Pairwise diagnostic: for raw corrected values lower is better for ex/st; for ranks lower is better.
 summ=[]
 for c in FEATURES:
  d=o['delta_keep_minus_drop_'+c].dropna();
  if d.empty: continue
  summ.append({'feature':c,'R':len(d),'keep_mean':o.loc[d.index,'keep_'+c].mean(),'drop_mean':o.loc[d.index,'drop_'+c].mean(),
               'delta_mean':d.mean(),'keep_better_lower_n':int((d<0).sum()),'keep_better_lower_rate':100*(d<0).mean(),
               'equal_n':int((d==0).sum())})
 s=pd.DataFrame(summ); s.to_csv('analysis_v351_mass_rescue_wave13_feature_summary.csv',index=False,encoding='utf-8-sig')
 pos=o.keep_position.value_counts().rename_axis('keep_position').reset_index(name='R'); pos['rate']=100*pos.R/len(o)
 pos.to_csv('analysis_v351_mass_rescue_wave13_position_summary.csv',index=False,encoding='utf-8-sig')
 # Boat keep/drop table.
 boats=[]
 for boat in range(2,7):
  kn=int((o.keep_boat==boat).sum()); dn=int((o.drop_boat==boat).sum())
  boats.append({'boat':boat,'keep_n':kn,'drop_n':dn,'keep_share_when_selected':100*kn/(kn+dn) if kn+dn else np.nan})
 pd.DataFrame(boats).to_csv('analysis_v351_mass_rescue_wave13_boat_summary.csv',index=False,encoding='utf-8-sig')
 # Schema x position to check whether SECOND/THIRD retention is stable in the main schemas.
 sp=o.groupby(['schema','keep_position']).size().rename('R').reset_index(); totals=o.groupby('schema').size().rename('schema_R')
 sp=sp.join(totals,on='schema'); sp['rate']=100*sp.R/sp.schema_R
 sp.to_csv('analysis_v351_mass_rescue_wave13_schema_position.csv',index=False,encoding='utf-8-sig')
 print('SEPTEMBER_OUTCOMES_USED False'); print('PRODUCTION_CHANGED False'); print('HEAD_EXHIBITION_DIRECT_FEATURE False')
 print('WAVE13_R',len(o)); print('\nPOSITION'); print(pos.to_string(index=False)); print('\nFEATURES'); print(s.to_string(index=False));
 print('\nBOATS'); print(pd.DataFrame(boats).to_string(index=False)); print('\nSCHEMA_POSITION'); print(sp.to_string(index=False))
if __name__=='__main__': main()
