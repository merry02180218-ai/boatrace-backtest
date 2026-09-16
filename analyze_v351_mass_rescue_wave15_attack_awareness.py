#!/usr/bin/env python3
"""Wave15: 1-head awareness of stronger boat2/boat3 -> finishing structure.
Historical diagnostic only. September 2026 outcomes hard forbidden. Production unchanged.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

SRC='analysis_v351_mass_rescue_wave14_rows.csv'

def band(x: float) -> str:
 a=abs(float(x))
 if a < 0.20: return 'CLOSE_<0.20'
 if a < 0.50: return 'MID_0.20_0.50'
 return 'CLEAR_>=0.50'

def main():
 d=pd.read_csv(SRC,dtype={'race_code':str}); d.race_code=d.race_code.astype(str).str.zfill(12)
 if (d.race_code.str[:8]>='20260901').any(): raise RuntimeError('September outcome row detected')
 if d.empty: raise RuntimeError('no Wave15 source rows')
 d['advantage']=np.where(d.strength2_minus3<0,'BOAT2_STRONGER',np.where(d.strength2_minus3>0,'BOAT3_STRONGER','TIE'))
 d['advantage_abs']=d.strength2_minus3.abs(); d['advantage_band']=d.strength2_minus3.map(band)
 d['strong_boat']=np.where(d.advantage=='BOAT2_STRONGER',2,np.where(d.advantage=='BOAT3_STRONGER',3,0)).astype(int)
 d['weak_boat']=np.where(d.advantage=='BOAT2_STRONGER',3,np.where(d.advantage=='BOAT3_STRONGER',2,0)).astype(int)
 d['second_is_strong']=((d.strong_boat>0)&(d.actual_second==d.strong_boat)).astype(int)
 d['third_is_strong']=((d.strong_boat>0)&(d.actual_third==d.strong_boat)).astype(int)
 d['second_is_weak']=((d.weak_boat>0)&(d.actual_second==d.weak_boat)).astype(int)
 d['third_is_weak']=((d.weak_boat>0)&(d.actual_third==d.weak_boat)).astype(int)
 d['second_is_outer']=(d.actual_second>=4).astype(int); d['third_is_outer']=(d.actual_third>=4).astype(int)
 d['outer_any']=((d.actual_second>=4)|(d.actual_third>=4)).astype(int)
 d['outer_both']=((d.actual_second>=4)&(d.actual_third>=4)).astype(int)
 d.to_csv('analysis_v351_mass_rescue_wave15_rows.csv',index=False,encoding='utf-8-sig')

 metrics=['second_is_strong','third_is_strong','second_is_weak','third_is_weak','second_is_outer','third_is_outer','outer_any','outer_both','actual_has2','actual_has3','actual_both23','current_first_pair_hit']
 rec=[]
 groups=[('ALL',d)]
 groups += [(a,g) for a,g in d.groupby('advantage')]
 groups += [(f'{a}|{b}',g) for (a,b),g in d.groupby(['advantage','advantage_band'])]
 for key,g in groups:
  z={'group':key,'R':len(g),'mean_abs_advantage':g.advantage_abs.mean()}
  for c in metrics: z[c+'_n']=int(g[c].sum()); z[c+'_rate']=100*g[c].mean()
  rec.append(z)
 s=pd.DataFrame(rec); s.to_csv('analysis_v351_mass_rescue_wave15_summary.csv',index=False,encoding='utf-8-sig')

 # Actual second/third boat distributions by advantage and strength band.
 dist=[]
 for (a,b),g in d.groupby(['advantage','advantage_band']):
  for pos,col in [('SECOND','actual_second'),('THIRD','actual_third')]:
   for boat in range(2,7):
    n=int((g[col]==boat).sum())
    dist.append({'advantage':a,'band':b,'position':pos,'boat':boat,'R_group':len(g),'n':n,'rate':100*n/len(g)})
 pd.DataFrame(dist).to_csv('analysis_v351_mass_rescue_wave15_finish_distribution.csv',index=False,encoding='utf-8-sig')

 # Direct outer-boat distribution: which 4/5/6 benefits under 2-strong vs 3-strong.
 outer=[]
 for (a,b),g in d[d.advantage!='TIE'].groupby(['advantage','advantage_band']):
  for boat in [4,5,6]:
   second=int((g.actual_second==boat).sum()); third=int((g.actual_third==boat).sum()); anyn=int(((g.actual_second==boat)|(g.actual_third==boat)).sum())
   outer.append({'advantage':a,'band':b,'boat':boat,'R_group':len(g),'second_n':second,'second_rate':100*second/len(g),'third_n':third,'third_rate':100*third/len(g),'pair_any_n':anyn,'pair_any_rate':100*anyn/len(g)})
 pd.DataFrame(outer).to_csv('analysis_v351_mass_rescue_wave15_outer_distribution.csv',index=False,encoding='utf-8-sig')

 print('SEPTEMBER_OUTCOMES_USED False'); print('PRODUCTION_CHANGED False'); print('HEAD_EXHIBITION_DIRECT_FEATURE False')
 print('WAVE15_R',len(d)); print('\nATTACK_AWARENESS_SUMMARY'); print(s.to_string(index=False)); print('\nFINISH_DISTRIBUTION'); print(pd.DataFrame(dist).to_string(index=False)); print('\nOUTER_DISTRIBUTION'); print(pd.DataFrame(outer).to_string(index=False))
if __name__=='__main__': main()
