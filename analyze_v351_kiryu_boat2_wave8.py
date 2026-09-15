#!/usr/bin/env python3
"""Wave8: Kiryu boat2 KEEP/DROP diagnostics using causal exhibition features. Historical only."""
from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
import numpy as np,pandas as pd
from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct
import run_v326_1head_ticketaware_exhibition as v326

IN='analysis_v351_kiryu_boat2_wave7.csv';OUT='analysis_v351_kiryu_boat2_wave8.csv';SUM='analysis_v351_kiryu_boat2_wave8_summary.csv'

def main():
 b=pd.read_csv(IN,dtype={'race_code':str});b.race_code=b.race_code.astype(str).str.zfill(12);b=b[b.race_code.str[:8]<'20260901'].copy()
 wanted=set(b.race_code); days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted});dayset=set(days);last=max(days)
 sums=defaultdict(list);allv=[];feat={};d=date(2025,10,1)
 while d<=last:
  y=d.strftime('%Y/%m/%d'); sr=rows(f'data/previews/stt/{y}.csv');bias=v326.st_bias(sums,allv)
  if d in dayset:
   tk=v326.bycode(rows(f'data/previews/tkz/{y}.csv'));st=v326.bycode(sr);orig=v326.bycode(rows(f'data/previews/original_exhibition/{y}.csv'))
   for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
    ex,ss,os=corrected_direct(code,tk,st,orig,bias)
    for boat in range(2,7):
     if boat in ex and boat in ss:
      o=os.get(boat,{})
      feat[(code,boat)]={'ex':ex[boat],'st':ss[boat],'half':o.get('half',np.nan),'turn':o.get('turn',np.nan),'straight':o.get('straight',np.nan),'orig_avg':o.get('avg',np.nan)}
  v326.update_st(sr,sums,allv);d+=timedelta(days=1)
 out=[]
 for _,r in b.iterrows():
  fs=[]
  for boat in range(2,7):
   f=feat.get((r.race_code,boat));
   if f:fs.append({'boat':boat,**f})
  g=pd.DataFrame(fs)
  if len(g)!=5:continue
  for c in ['ex','st','half','turn','straight','orig_avg']:g[c+'_rank']=g[c].rank(method='average',ascending=True)
  two=g[g.boat.eq(2)].iloc[0]
  others=g[g.boat.ne(2)]
  rec={'race_code':r.race_code,'keep2':int(r.actual_has_2),'actual_pair':r.actual_pair,'current_pair':r.current_first_pair}
  for c in ['ex','st','half','turn','straight','orig_avg']:
   rec['b2_'+c]=two[c];rec['b2_'+c+'_rank']=two[c+'_rank'];rec['b2_'+c+'_vs_best']=two[c]-others[c].min() if others[c].notna().any() and pd.notna(two[c]) else np.nan
  out.append(rec)
 q=pd.DataFrame(out).sort_values('race_code');q.to_csv(OUT,index=False,encoding='utf-8-sig')
 metrics=[c for c in q if c.startswith('b2_')]
 s=[]
 for c in metrics:
  a=q[q.keep2.eq(1)][c].dropna();z=q[q.keep2.eq(0)][c].dropna()
  if len(a) and len(z):s.append({'feature':c,'keep_n':len(a),'drop_n':len(z),'keep_mean':a.mean(),'drop_mean':z.mean(),'mean_diff_keep_minus_drop':a.mean()-z.mean(),'keep_median':a.median(),'drop_median':z.median()})
 sm=pd.DataFrame(s).sort_values('feature');sm.to_csv(SUM,index=False,encoding='utf-8-sig')
 print('KIRYU_R',len(q),'KEEP2',int(q.keep2.sum()),'DROP2',int((1-q.keep2).sum()))
 print(sm.to_string(index=False))
 print('CASES');print(q.to_string(index=False))
 print('SEPTEMBER_OUTCOMES_USED',False);print('PRODUCTION_CHANGED',False)
if __name__=='__main__':main()
