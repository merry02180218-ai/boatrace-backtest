#!/usr/bin/env python3
"""Wave16: temporal stability of Wave15 2/3 attack-awareness outer-boat structure.
Historical diagnostic only; September 2026 outcomes forbidden. Production unchanged.
"""
from __future__ import annotations
import pandas as pd

SRC='analysis_v351_mass_rescue_wave15_rows.csv'
ADV=['BOAT2_STRONGER','BOAT3_STRONGER']
OUTERS=[4,5,6]
CLEAR='CLEAR_>=0.50'

def any_hit(g, boat):
 return ((g.actual_second==boat)|(g.actual_third==boat)).astype(int)

def main():
 d=pd.read_csv(SRC,dtype={'race_code':str}); d.race_code=d.race_code.astype(str).str.zfill(12)
 if (d.race_code.str[:8]>='20260901').any(): raise RuntimeError('September outcome row detected')
 d['month']=d.race_code.str[:6]
 z=d[(d.advantage.isin(ADV))&(d.advantage_band==CLEAR)].copy()
 if z.empty: raise RuntimeError('no clear-advantage rows')
 # Month-by-month stability for every outer boat. No selection hidden.
 rows=[]
 for (m,a),g in z.groupby(['month','advantage']):
  for b in OUTERS:
   h=any_hit(g,b)
   rows.append({'month':m,'advantage':a,'boat':b,'R':len(g),'pair_any_n':int(h.sum()),'pair_any_rate':100*h.mean(),
                'second_n':int((g.actual_second==b).sum()),'second_rate':100*(g.actual_second==b).mean(),
                'third_n':int((g.actual_third==b).sum()),'third_rate':100*(g.actual_third==b).mean()})
 monthly=pd.DataFrame(rows); monthly.to_csv('analysis_v351_mass_rescue_wave16_monthly.csv',index=False,encoding='utf-8-sig')

 # Strict temporal target discovery: choose outer using Feb-Apr only; tie -> lower boat id.
 train=z[z.month.isin(['202602','202603','202604'])]
 chosen={}
 discovery=[]
 for a in ADV:
  g=train[train.advantage==a]
  vals=[]
  for b in OUTERS:
   n=int(any_hit(g,b).sum()); rate=(n/len(g) if len(g) else -1)
   vals.append((rate,-b,b,n,len(g)))
  best=max(vals); chosen[a]=best[2]
  for rate,_,b,n,R in vals:
   discovery.append({'advantage':a,'boat':b,'train_R':R,'train_hit_n':n,'train_hit_rate':100*rate if R else float('nan'),'selected':int(b==chosen[a])})
 pd.DataFrame(discovery).to_csv('analysis_v351_mass_rescue_wave16_discovery.csv',index=False,encoding='utf-8-sig')

 # Freeze targets and evaluate May then June without retuning.
 frozen=[]
 for m in ['202605','202606']:
  for a in ADV:
   g=z[(z.month==m)&(z.advantage==a)]; b=chosen[a]
   h=any_hit(g,b) if len(g) else pd.Series(dtype=int)
   frozen.append({'month':m,'advantage':a,'frozen_target':b,'R':len(g),'target_hit_n':int(h.sum()) if len(g) else 0,
                  'target_hit_rate':100*h.mean() if len(g) else float('nan'),
                  'target_second_n':int((g.actual_second==b).sum()),'target_third_n':int((g.actual_third==b).sum())})
 frozen=pd.DataFrame(frozen); frozen.to_csv('analysis_v351_mass_rescue_wave16_frozen.csv',index=False,encoding='utf-8-sig')

 # Explicitly audit Wave15 post-hoc mapping 2strong->4, 3strong->5 against all months.
 post={'BOAT2_STRONGER':4,'BOAT3_STRONGER':5}; pr=[]
 for (m,a),g in z.groupby(['month','advantage']):
  b=post[a]; h=any_hit(g,b)
  pr.append({'month':m,'advantage':a,'posthoc_target':b,'R':len(g),'hit_n':int(h.sum()),'hit_rate':100*h.mean(),
             'second_n':int((g.actual_second==b).sum()),'third_n':int((g.actual_third==b).sum())})
 postdf=pd.DataFrame(pr); postdf.to_csv('analysis_v351_mass_rescue_wave16_posthoc_mapping.csv',index=False,encoding='utf-8-sig')

 print('SEPTEMBER_OUTCOMES_USED False'); print('PRODUCTION_CHANGED False'); print('HEAD_EXHIBITION_DIRECT_FEATURE False')
 print('CLEAR_R',len(z)); print('FROZEN_TARGETS',chosen)
 print('\nDISCOVERY_FEB_APR'); print(pd.DataFrame(discovery).to_string(index=False))
 print('\nFROZEN_MAY_JUNE'); print(frozen.to_string(index=False))
 print('\nPOSTHOC_2TO4_3TO5_MONTHLY'); print(postdf.to_string(index=False))
 print('\nALL_OUTER_MONTHLY'); print(monthly.to_string(index=False))
if __name__=='__main__': main()
