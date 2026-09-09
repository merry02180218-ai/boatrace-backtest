#!/usr/bin/env python3
from pathlib import Path
import numpy as np,pandas as pd
SRC=Path('analysis_v243_3head_expand_feature_audit.csv'); OUT=Path('analysis_v249_3head_pre_rolling_sab_optimize.csv'); SUM=Path('summary_v249_3head_pre_rolling_sab_optimize.md')
KEEP=-0.1999999999999999; RESCUE=0.5672342857142857

def target(q):
 b=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
 return (b&(pd.to_numeric(q.f__c_b3_minus_b5_st,errors='coerce')>=KEEP))|((q.bet==1)&(~b)&(pd.to_numeric(q.f__c_attack3_stretch,errors='coerce')<=RESCUE))
def cols(q):
 bad=('pair_','p3','odds','comp','top_n','raw_top','ticket','hit','ret','profit','bet','invalid','result','settle'); cur=('attack3','wall12','_st','_ex','lap','turn','straight','orig','tilt','exh','tenji','display')
 return [c for c in q if c.startswith('f__') and not any(x in c.lower() for x in bad) and not any(x in c.lower() for x in cur)]
def fit_score(tr,te,cs):
 y=tr._target.astype(int); fs=[]
 for c in cs:
  x=pd.to_numeric(tr[c],errors='coerce'); a=x[y==1].dropna(); b=x[y==0].dropna(); sd=x.std()
  if len(a)>=5 and len(b)>=20 and np.isfinite(sd) and sd>1e-12:
   e=(a.mean()-b.mean())/sd
   if np.isfinite(e): fs.append((abs(e),e,c))
 fs=sorted(fs,reverse=True)[:12]; s=pd.Series(0.,index=te.index)
 for _,e,c in fs:
  a=pd.to_numeric(tr[c],errors='coerce'); x=pd.to_numeric(te[c],errors='coerce'); med=a.median(); sd=a.std()
  if np.isfinite(sd) and sd>1e-12:s+=np.sign(e)*((x.fillna(med)-med)/sd).clip(-4,4)
 return s

def main():
 q=pd.read_csv(SRC,dtype={'race_code':str});q.date=q.date.astype(str);q['month']=q.date.str[:7];q['_target']=target(q).astype(int)
 if q._target.sum()!=182:raise RuntimeError('target mismatch')
 ms=sorted(q.month.unique()); cs=cols(q); pred=[]
 for i,m in enumerate(ms):
  if i<2:continue
  tr=q[q.month.isin(ms[:i])];te=q[q.month==m].copy();te['_score']=fit_score(tr,te,cs);pred.append(te[['month','date','race_code','_score','_target']])
 p=pd.concat(pred,ignore_index=True); rows=[]
 # Search global rolling score percentiles learned from each prior training universe, operationally expressed as rank percentile within each test month.
 p['_pct']=p.groupby('month')['_score'].rank(pct=True,method='first',ascending=True)
 # S/A/B cut grid. Selected=S+A; target >=85% recall, minimize selected volume. B is watchlist outside buy-review set.
 for s_cut in np.arange(.70,.96,.05):
  for a_cut in np.arange(.05,s_cut-.04,.05):
   # S >= s_cut, A >= a_cut and <s; selected S+A means >=a_cut
   sel=p[p._pct>=a_cut]; cap=int(sel._target.sum()); tot=int(p._target.sum()); recall=cap/tot
   S=p[p._pct>=s_cut]; A=p[(p._pct>=a_cut)&(p._pct<s_cut)]; B=p[p._pct<a_cut]
   rows.append(dict(s_cut=s_cut,a_cut=a_cut,selected=len(sel),selected_rate=len(sel)/len(p),captured=cap,target_total=tot,recall=recall,S_n=len(S),S_targets=int(S._target.sum()),A_n=len(A),A_targets=int(A._target.sum()),B_n=len(B),B_targets=int(B._target.sum())))
 r=pd.DataFrame(rows).sort_values(['selected','recall'],ascending=[True,False]);r.to_csv(OUT,index=False)
 ok=r[r.recall>=.85]; best=ok.iloc[0] if len(ok) else r.sort_values('recall',ascending=False).iloc[0]
 a=float(best.a_cut);s=float(best.s_cut); p['grade']=np.where(p._pct>=s,'S',np.where(p._pct>=a,'A','B'))
 L=['# v249 rolling strict-PRE S/A/B optimization','','- Only chronologically prior months train each test month.','- Current-race exhibition-derived features excluded.','- Goal: minimize S+A candidate volume while maintaining >=85% rolling capture of canonical final targets.','- S/A/B thresholds are searched on rolling out-of-time predictions; this threshold search itself is retrospective and must be treated as model selection, not pristine validation.','',f"Best: S percentile >= {s:.2f}; A >= {a:.2f}; S+A candidates {int(best.selected)}/{len(p)} ({100*best.selected_rate:.2f}%); captured {int(best.captured)}/{int(best.target_total)} = {100*best.recall:.2f}%",'', '|grade|candidates|targets|target rate|','|---|---:|---:|---:|']
 for g in ['S','A','B']:
  z=p[p.grade==g];L.append(f'|{g}|{len(z)}|{int(z._target.sum())}|{100*z._target.mean():.2f}%|')
 L+=['','## Monthly S+A','|month|universe|candidates|targets|captured|recall|','|---|---:|---:|---:|---:|---:|']
 for m,z in p.groupby('month'):
  sel=z[z.grade.isin(['S','A'])];tot=int(z._target.sum());cap=int(sel._target.sum());L.append(f'|{m}|{len(z)}|{len(sel)}|{tot}|{cap}|{100*cap/tot if tot else 0:.2f}%|')
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
