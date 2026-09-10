#!/usr/bin/env python3
from pathlib import Path
import numpy as np, pandas as pd
SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT=Path('analysis_v268_3head_waku10_profit_overlay.csv')
SUM=Path('summary_v268_3head_waku10_profit_overlay.md')
KEEP=-0.1999999999999999; RESCUE=0.5672342857142857

def target(q):
 b=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
 return (b&(pd.to_numeric(q.f__c_b3_minus_b5_st,errors='coerce')>=KEEP))|((q.bet==1)&(~b)&(pd.to_numeric(q.f__c_attack3_stretch,errors='coerce')<=RESCUE))
def precols(q):
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
def metrics(z):
 n=len(z); ret=float(pd.to_numeric(z.ret,errors='coerce').fillna(0).sum()); hit=int(pd.to_numeric(z.trifecta_hit,errors='coerce').fillna(0).sum()); stake=n*10000
 return n,hit,ret,ret/stake*100 if stake else np.nan,ret-stake

def main():
 q=pd.read_csv(SRC,dtype={'race_code':str}); q.date=q.date.astype(str); q['month']=q.date.str[:7]; q['_target']=target(q).astype(int)
 cs=precols(q); ms=sorted(q.month.unique()); pred=[]
 for i,m in enumerate(ms):
  if i<2: continue
  tr=q[q.month.isin(ms[:i])]; te=q[q.month==m].copy(); te['_score']=fit_score(tr,te,cs); pred.append(te[['month','race_code','_score']])
 p=pd.concat(pred,ignore_index=True); p['_pct']=p.groupby('month')['_score'].rank(pct=True,method='first'); p['grade']=np.where(p._pct>=.70,'S',np.where(p._pct>=.20,'A','B'))
 z=q.merge(p[['race_code','grade']],on='race_code'); z=z[(z._target==1)&z.grade.isin(['S','A'])].copy()
 if len(z)!=104 or int(z.trifecta_hit.sum())!=39 or abs(float(z.ret.sum())-1200350)>1e-9: raise RuntimeError('canonical 104/39/1200350 not reproduced')
 train=z[z.month<='2026-06']; test=z[z.month>='2026-07']; w=[c for c in z if 'waku' in c.lower()]
 rows=[]
 for c in w:
  vals=pd.to_numeric(train[c],errors='coerce').dropna()
  for qq in np.linspace(.10,.90,17):
   t=float(vals.quantile(qq))
   for op in ('<=','>='):
    def mask(df):
     x=pd.to_numeric(df[c],errors='coerce'); return x<=t if op=='<=' else x>=t
    a=train[mask(train)]; b=test[mask(test)]; na,ha,ra,roia,pa=metrics(a); nb,hb,rb,roib,pb=metrics(b)
    if na<20: continue
    rows.append(dict(feature=c,op=op,threshold=t,train_n=na,train_hits=ha,train_ret=ra,train_roi=roia,train_profit=pa,nonpristine_n=nb,nonpristine_hits=hb,nonpristine_ret=rb,nonpristine_roi=roib,nonpristine_profit=pb,all_n=na+nb,all_ret=ra+rb,all_roi=(ra+rb)/((na+nb)*10000)*100,all_profit=(ra+rb)-(na+nb)*10000))
 r=pd.DataFrame(rows).sort_values(['train_profit','train_roi'],ascending=False); r.to_csv(OUT,index=False)
 bt=metrics(train); be=metrics(test); ba=metrics(z)
 robust=r[(r.train_profit>bt[4])&(r.nonpristine_profit>=0)].sort_values(['train_profit','nonpristine_profit'],ascending=False)
 L=['# v268 3-head Waku10 profit overlay','','- Canonical chain reproduced first: v249 S+A -> v243 final -> v242 tickets/Dutch.','- Rule search uses only 2026-02 through 2026-06 canonical final bets.','- 2026-07/08 are NON-PRISTINE and are shown only as robustness evidence, never pristine validation.','- Search is Waku10 features only; one-dimensional thresholds; minimum 20 train bets.','',f'Baseline Feb-Jun: N={bt[0]}, hits={bt[1]}, ROI={bt[3]:.2f}%, profit={bt[4]:+.0f}',f'Baseline Jul-Aug NON-PRISTINE: N={be[0]}, hits={be[1]}, ROI={be[3]:.2f}%, profit={be[4]:+.0f}',f'Baseline All: N={ba[0]}, hits={ba[1]}, ROI={ba[3]:.2f}%, profit={ba[4]:+.0f}','','## Robust candidates (train profit improves and Jul/Aug profit >= 0)','|feature|op|threshold|Feb-Jun N|Feb-Jun ROI|Feb-Jun profit|Jul-Aug N|Jul-Aug ROI|Jul-Aug profit|All ROI|All profit|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for _,x in robust.head(20).iterrows(): L.append(f"|{x.feature}|{x.op}|{x.threshold:.12g}|{int(x.train_n)}|{x.train_roi:.2f}%|{x.train_profit:+.0f}|{int(x.nonpristine_n)}|{x.nonpristine_roi:.2f}%|{x.nonpristine_profit:+.0f}|{x.all_roi:.2f}%|{x.all_profit:+.0f}|")
 SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
