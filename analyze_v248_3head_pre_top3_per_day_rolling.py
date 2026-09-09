#!/usr/bin/env python3
from pathlib import Path
import numpy as np, pandas as pd
SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT=Path('analysis_v248_3head_pre_top3_per_day_rolling.csv')
SUM=Path('summary_v248_3head_pre_top3_per_day_rolling.md')
KEEP=-0.1999999999999999; RESCUE=0.5672342857142857

def final_mask(q):
 b=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
 return (b&(pd.to_numeric(q.f__c_b3_minus_b5_st,errors='coerce')>=KEEP))|((q.bet==1)&(~b)&(pd.to_numeric(q.f__c_attack3_stretch,errors='coerce')<=RESCUE))
def precols(q):
 bad=('pair_','p3','odds','comp','top_n','raw_top','ticket','hit','ret','profit','bet','invalid','result','settle')
 cur=('attack3','wall12','_st','_ex','lap','turn','straight','orig','tilt','exh','tenji','display')
 return [c for c in q if c.startswith('f__') and not any(x in c.lower() for x in bad) and not any(x in c.lower() for x in cur)]
def score(train,test,cols):
 y=train._target.astype(int); fs=[]
 for c in cols:
  x=pd.to_numeric(train[c],errors='coerce'); a=x[y==1].dropna(); b=x[y==0].dropna(); sd=x.std()
  if len(a)>=5 and len(b)>=20 and np.isfinite(sd) and sd>1e-12:
   e=(a.mean()-b.mean())/sd
   if np.isfinite(e): fs.append((abs(e),e,c))
 fs=sorted(fs,reverse=True)[:12]; s=pd.Series(0.,index=test.index)
 for _,e,c in fs:
  tr=pd.to_numeric(train[c],errors='coerce'); te=pd.to_numeric(test[c],errors='coerce'); med=tr.median(); sd=tr.std()
  if np.isfinite(sd) and sd>1e-12: s+=np.sign(e)*((te.fillna(med)-med)/sd).clip(-4,4)
 return s,';'.join(c for _,_,c in fs)
def main():
 q=pd.read_csv(SRC,dtype={'race_code':str}); q.date=q.date.astype(str); q['month']=q.date.str[:7]; q['_target']=final_mask(q).astype(int)
 if q._target.sum()!=182: raise RuntimeError('target mismatch')
 cols=precols(q); months=sorted(q.month.unique()); rows=[]
 # true rolling: prior months only; first 2 months warmup
 for i,m in enumerate(months):
  if i<2: continue
  tr=q[q.month.isin(months[:i])]; te=q[q.month==m].copy(); te['_score'],used=score(tr,te,cols)
  for k in (1,2,3,4,5):
   pick=te.sort_values(['date','_score'],ascending=[True,False]).groupby('date',group_keys=False).head(k)
   rows.append(dict(month=m,top_per_day=k,days=te.date.nunique(),candidates=len(pick),target_total=int(te._target.sum()),captured=int(pick._target.sum()),features=used))
 out=pd.DataFrame(rows); out['recall']=out.captured/out.target_total; out['avg_candidates_per_day']=out.candidates/out.days; out.to_csv(OUT,index=False)
 L=['# v248 strict PRE top-N per day rolling audit','','- Training uses only chronologically prior months.','- Current-race exhibition-derived features are excluded exactly as v247.','- Tests practical daily caps Top1..Top5.','','|Top/day|days|candidates|avg/day|targets|captured|recall|','|---:|---:|---:|---:|---:|---:|---:|']
 for k in (1,2,3,4,5):
  z=out[out.top_per_day==k]; tar=z.target_total.sum(); cap=z.captured.sum(); days=z.days.sum(); cand=z.candidates.sum()
  L.append(f'|{k}|{days}|{cand}|{cand/days:.2f}|{tar}|{cap}|{100*cap/tar:.2f}%|')
 L+=['','## Monthly Top3/day','|month|days|candidates|targets|captured|recall|','|---|---:|---:|---:|---:|---:|']
 for _,r in out[out.top_per_day==3].iterrows(): L.append(f'|{r.month}|{int(r.days)}|{int(r.candidates)}|{int(r.target_total)}|{int(r.captured)}|{100*r.recall:.2f}%|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
