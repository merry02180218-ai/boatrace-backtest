#!/usr/bin/env python3
"""Wave14: exploratory 2-vs-3 inner attack structure audit for v351 low-mass rescue.
Historical diagnostic only. September 2026 outcomes hard forbidden. Production unchanged.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import research_v351_mass_rescue_wave12_frozen_guard as w12

SRC='analysis_v351_mass_rescue_wave10_rows.csv'
RANKS=['ex_rank','st_rank','turn_rank','straight_rank','orig_avg_rank']

def main():
 b=pd.read_csv(SRC,dtype={'race_code':str}); b.race_code=b.race_code.astype(str).str.zfill(12)
 if (b.race_code.str[:8]>='20260901').any(): raise RuntimeError('September outcome row detected')
 b=b[(b.opp_mass>=w12.LO)&(b.opp_mass<w12.HI)&b.schema.isin(w12.SCHEMAS)].copy()
 f=w12.build_features(b).copy()
 # Lower corrected rank = stronger exhibition/ST profile. Mean available ranks, no outcome used in score.
 f['strength_rank_mean']=f[RANKS].mean(axis=1,skipna=True)
 fi=f.set_index(['race_code','boat'])
 rec=[]
 for _,r in b.iterrows():
  a=w12.combo(r.actual_combo); ts=w12.tickets(r.tickets)
  if not a or a[0]!=1 or not ts: continue
  code=r.race_code
  if (code,2) not in fi.index or (code,3) not in fi.index: continue
  x2=fi.loc[(code,2)]; x3=fi.loc[(code,3)]
  s2=float(x2.strength_rank_mean); s3=float(x3.strength_rank_mean); diff=s2-s3
  grp='BOAT2_STRONGER' if diff<0 else ('BOAT3_STRONGER' if diff>0 else 'TIE')
  actual2,actual3=int(a[1]),int(a[2]); aset={actual2,actual3}; cur=set(ts[0][1:])
  z={'race_code':code,'schema':r.schema,'jcd':int(r.jcd),'strength2':s2,'strength3':s3,'strength2_minus3':diff,'inner_group':grp,
     'actual_second':actual2,'actual_third':actual3,'actual_has2':int(2 in aset),'actual_has3':int(3 in aset),'actual_has_outer':int(any(q>=4 for q in aset)),
     'actual_both23':int(aset=={2,3}),'boat2_second':int(actual2==2),'boat3_second':int(actual2==3),
     'current_first_pair_hit':int(cur==aset),'current_first_has2':int(2 in cur),'current_first_has3':int(3 in cur)}
  for c in RANKS:
   z['boat2_'+c]=x2[c]; z['boat3_'+c]=x3[c]; z['delta2_minus3_'+c]=x2[c]-x3[c]
  rec.append(z)
 o=pd.DataFrame(rec)
 if o.empty: raise RuntimeError('no Wave14 rows')
 o.to_csv('analysis_v351_mass_rescue_wave14_rows.csv',index=False,encoding='utf-8-sig')
 metrics=['actual_has2','actual_has3','actual_has_outer','actual_both23','boat2_second','boat3_second','current_first_pair_hit']
 summ=[]
 for key,g in [('ALL',o),*[(k,g) for k,g in o.groupby('inner_group')]]:
  z={'group':key,'R':len(g),'mean_strength2':g.strength2.mean(),'mean_strength3':g.strength3.mean()}
  for c in metrics: z[c+'_n']=int(g[c].sum()); z[c+'_rate']=100*g[c].mean()
  summ.append(z)
 s=pd.DataFrame(summ); s.to_csv('analysis_v351_mass_rescue_wave14_summary.csv',index=False,encoding='utf-8-sig')
 # Direct 2-vs-3 current-pair subset: which one was the actual KEEP boat in one-replace misses.
 q=o[(o.current_first_has2==1)&(o.current_first_has3==1)&(o.current_first_pair_hit==0)].copy()
 if not q.empty:
  q['keep23']='KEEP2' ; q.loc[(q.actual_has3==1)&(q.actual_has2==0),'keep23']='KEEP3'; q.loc[q.actual_both23==1,'keep23']='BOTH'
  q.to_csv('analysis_v351_mass_rescue_wave14_pair23.csv',index=False,encoding='utf-8-sig')
  p=q.groupby(['inner_group','keep23']).size().rename('R').reset_index()
 else: p=pd.DataFrame(columns=['inner_group','keep23','R'])
 p.to_csv('analysis_v351_mass_rescue_wave14_pair23_summary.csv',index=False,encoding='utf-8-sig')
 # Feature-direction table, independent of composite score.
 feat=[]
 for c in RANKS:
  d=o['delta2_minus3_'+c].dropna(); feat.append({'feature':c,'R':len(d),'boat2_stronger_n':int((d<0).sum()),'boat3_stronger_n':int((d>0).sum()),'tie_n':int((d==0).sum())})
 pd.DataFrame(feat).to_csv('analysis_v351_mass_rescue_wave14_feature_direction.csv',index=False,encoding='utf-8-sig')
 print('SEPTEMBER_OUTCOMES_USED False'); print('PRODUCTION_CHANGED False'); print('HEAD_EXHIBITION_DIRECT_FEATURE False')
 print('WAVE14_R',len(o)); print('\nINNER_GROUP_SUMMARY'); print(s.to_string(index=False)); print('\nPAIR23_MISS_KEEP'); print(p.to_string(index=False)); print('\nFEATURE_DIRECTION'); print(pd.DataFrame(feat).to_string(index=False))
if __name__=='__main__': main()
