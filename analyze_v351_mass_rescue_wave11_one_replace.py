#!/usr/bin/env python3
"""Wave11: decompose [0.350,0.375) HEAD-hit exact3 misses for one-opponent rescue.
Historical diagnostic only. September outcomes are hard forbidden. Production unchanged.
"""
from __future__ import annotations
import ast
import pandas as pd
import numpy as np
SRC='analysis_v351_mass_rescue_wave10_rows.csv'

def parse_actual(x):
 p=str(x).replace('>','-').split('-')
 try: return tuple(map(int,p[:3])) if len(p)>=3 else None
 except: return None

def parse_tickets(x):
 out=[]
 for z in str(x).split(';'):
  p=z.replace('>','-').split('-')
  try:
   t=tuple(map(int,p[:3]))
   if len(t)==3 and t[0]==1: out.append(t)
  except: pass
 return out

def rate(n,d): return 100*n/d if d else np.nan

def main():
 z=pd.read_csv(SRC,dtype={'race_code':str}); z.race_code=z.race_code.astype(str).str.zfill(12)
 if (z.race_code.str[:8]>='20260901').any(): raise RuntimeError('September outcome row detected')
 q=z[(z.head_hit==1)&(z.exact3==0)].copy()
 if len(q)!=81: print('WARN_RESCUE_R',len(q))
 rows=[]
 for _,r in q.iterrows():
  a=parse_actual(r.actual_combo); ts=parse_tickets(r.tickets)
  if not a or a[0]!=1 or not ts: continue
  actual_pair=set(a[1:3]); union=set(); first_pair=set(ts[0][1:3])
  for t in ts: union.update(t[1:3])
  first_keep=len(first_pair & actual_pair)
  union_keep=len(union & actual_pair)
  # one replacement is sufficient for first pair iff exactly one actual opponent is already in it.
  cls='KEEP_ONE_REPLACE_ONE' if first_keep==1 else ('REPLACE_BOTH' if first_keep==0 else 'ORDER_ONLY')
  # union ticket set can supply a keepable opponent even when first pair cannot.
  ucls='UNION_HAS_BOTH' if union_keep==2 else ('UNION_KEEP_ONE' if union_keep==1 else 'UNION_REPLACE_BOTH')
  rows.append({**r.to_dict(),'actual2':a[1],'actual3':a[2],
   'first_second':ts[0][1],'first_third':ts[0][2],
   'first_keep_count':first_keep,'union_keep_count':union_keep,
   'first_rescue_class':cls,'union_rescue_class':ucls,
   'actual2_in_first':int(a[1] in first_pair),'actual3_in_first':int(a[2] in first_pair),
   'actual2_in_union':int(a[1] in union),'actual3_in_union':int(a[2] in union)})
 o=pd.DataFrame(rows)
 if o.empty: raise RuntimeError('no Wave11 rows')
 o.to_csv('analysis_v351_mass_rescue_wave11_one_replace_rows.csv',index=False,encoding='utf-8-sig')
 summ=[]
 for scope,col in [('ALL',None),('schema','schema'),('jcd','jcd'),('mass_bin',None)]:
  groups=[('ALL',o)] if scope=='ALL' else (list(o.groupby(col)) if col else [])
  for k,g in groups:
   c=g.first_rescue_class.value_counts(); u=g.union_rescue_class.value_counts()
   summ.append({'scope':scope,'key':str(k),'R':len(g),
    'FIRST_KEEP1_REPLACE1':int(c.get('KEEP_ONE_REPLACE_ONE',0)),
    'FIRST_KEEP1_REPLACE1_rate':rate(c.get('KEEP_ONE_REPLACE_ONE',0),len(g)),
    'FIRST_REPLACE_BOTH':int(c.get('REPLACE_BOTH',0)),
    'UNION_HAS_BOTH':int(u.get('UNION_HAS_BOTH',0)),
    'UNION_KEEP_ONE':int(u.get('UNION_KEEP_ONE',0)),
    'UNION_REPLACE_BOTH':int(u.get('UNION_REPLACE_BOTH',0))})
 s=pd.DataFrame(summ)
 s.to_csv('analysis_v351_mass_rescue_wave11_one_replace_summary.csv',index=False,encoding='utf-8-sig')
 # Boat-level keepability: which current first-pair position is more often the correct one.
 boat=[]
 for pos,bcol in [('SECOND','first_second'),('THIRD','first_third')]:
  for b,g in o.groupby(bcol):
   hit=((g.actual2.eq(b))|(g.actual3.eq(b))).astype(int)
   boat.append({'position':pos,'boat':int(b),'R':len(g),'KEEPABLE':int(hit.sum()),'KEEPABLE_rate':100*hit.mean()})
 pd.DataFrame(boat).to_csv('analysis_v351_mass_rescue_wave11_keepability.csv',index=False,encoding='utf-8-sig')
 print('SEPTEMBER_OUTCOMES_USED False'); print('PRODUCTION_CHANGED False'); print('HEAD_EXHIBITION_DIRECT_FEATURE False')
 print('WAVE11_R',len(o)); print('\nFIRST_PAIR_RESCUE'); print(o.first_rescue_class.value_counts().to_string())
 print('\nUNION_RESCUE'); print(o.union_rescue_class.value_counts().to_string())
 print('\nBY_SCHEMA'); print(s[s.scope.eq('schema')].to_string(index=False))
 print('\nKEEPABILITY'); print(pd.DataFrame(boat).to_string(index=False))
if __name__=='__main__': main()
