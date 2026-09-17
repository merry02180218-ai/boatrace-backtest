from __future__ import annotations
import csv, io, json, urllib.request
from datetime import date,timedelta
import numpy as np, pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

BASE='https://boatracecsv.github.io/data'
SRC='analysis_v289_3head_wave21_allrace_feature_settled.csv'
EX={202602071007,202602120606,202602150404,202602161108,202602171607,202602171911,202602191910,202602270507,202603031807,202603080101,202603081308,202603101810,202603111810,202603122004,202603141405,202603200809,202603211406,202603241009,202603271906,202603281904}
KINDS=['programs/race_cards','programs/recent_national','programs/recent_local']

def fetch(kind,d):
 u=f'{BASE}/{kind}/{d:%Y/%m/%d}.csv'
 try:
  with urllib.request.urlopen(u,timeout=30) as r: return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
 except Exception: return []

def numeric_features(rows,prefix):
 if not rows:return pd.DataFrame()
 z=pd.DataFrame(rows)
 # retain identifiers plus numeric columns; names are source-schema driven and audited in output
 for c in z.columns:
  if c not in ['date','場コード','レース番号','艇番','登録番号']:
   z[c]=pd.to_numeric(z[c],errors='coerce')
 nums=[c for c in z.columns if pd.api.types.is_numeric_dtype(z[c])]
 ids=[c for c in ['場コード','レース番号','艇番','登録番号'] if c in z]
 z=z[ids+nums].copy(); z.columns=ids+[prefix+c for c in nums]
 return z

def main():
 # Outcomes are loaded only for Feb training and Mar one-shot diagnostic; Sep is never requested/read.
 base=pd.read_csv(SRC,low_memory=False); base['date']=pd.to_datetime(base.date); base['rc']=pd.to_numeric(base.race_code_norm,errors='coerce').astype('Int64')
 base=base[(base.settle__usable==1)&(base.closing_odds__ok==1)&(~base.rc.isin(EX))& (base.date>='2026-02-01')&(base.date<'2026-04-01')].copy()
 allrows=[]
 for ds in pd.date_range('2026-02-01','2026-03-31'):
  d=ds.date(); day={k:fetch(k,d) for k in KINDS}
  # race_cards is authoritative row spine; joins are by shared IDs where present
  rc=pd.DataFrame(day['programs/race_cards'])
  if rc.empty: continue
  rc['__date']=d.isoformat()
  for kind in KINDS[1:]:
   q=pd.DataFrame(day[kind])
   if q.empty: continue
   keys=[c for c in ['場コード','レース番号','艇番','登録番号'] if c in rc.columns and c in q.columns]
   if not keys: continue
   q=numeric_features(day[kind],kind.split('/')[-1]+'__')
   rc=rc.merge(q,on=keys,how='left')
  allrows.append(rc)
 fun=pd.concat(allrows,ignore_index=True)
 # infer race/boat/id columns robustly from documented Japanese schema
 def pick(cols,need):
  for c in cols:
   if all(x in c for x in need): return c
  return None
 racec=pick(fun.columns,['レース','番号']) or ('レース番号' if 'レース番号' in fun else None)
 boatc=pick(fun.columns,['艇','番']) or ('艇番' if '艇番' in fun else None)
 stadium='場コード' if '場コード' in fun else None
 if not racec or not boatc or not stadium: raise RuntimeError(f'identifier columns unresolved: {list(fun.columns)}')
 fun[racec]=pd.to_numeric(fun[racec],errors='coerce'); fun[boatc]=pd.to_numeric(fun[boatc],errors='coerce'); fun[stadium]=pd.to_numeric(fun[stadium],errors='coerce')
 fun['date']=pd.to_datetime(fun['__date']); fun['rc']=(fun.date.dt.strftime('%Y%m%d').astype(int)*10000+fun[stadium].fillna(-1).astype(int)*100+fun[racec].fillna(-1).astype(int)).astype('Int64')
 # numeric boat-level columns -> pivot each boat and relative boat3 gaps
 ignore={racec,boatc,stadium,'rc'}
 for c in fun.columns:
  if c not in ignore and c not in ['__date','date','登録番号']: fun[c]=pd.to_numeric(fun[c],errors='coerce')
 nums=[c for c in fun.columns if c not in ignore and pd.api.types.is_numeric_dtype(fun[c]) and c!='登録番号']
 piv=[]
 for c in nums:
  p=fun.pivot_table(index='rc',columns=boatc,values=c,aggfunc='first')
  if 3 not in p.columns: continue
  o=pd.DataFrame(index=p.index); o[f'b3__{c}']=p[3]
  others=[x for x in [1,2,4,5,6] if x in p.columns]
  if others:o[f'b3mean_gap__{c}']=p[3]-p[others].mean(axis=1)
  for x in others:o[f'b3gap{x}__{c}']=p[3]-p[x]
  piv.append(o)
 X=pd.concat(piv,axis=1).replace([np.inf,-np.inf],np.nan); X=X.loc[:,X.notna().sum()>=20]
 dat=base[['rc','date','settle__winner']].merge(X.reset_index(),on='rc',how='inner'); dat['y']=(dat.settle__winner==3).astype(int)
 feb=dat[(dat.date<'2026-03-01')].sort_values('date'); mar=dat[(dat.date>='2026-03-01')].sort_values('date')
 feats=[c for c in X.columns if c in dat]
 # chronological February holdout selects model C and threshold/volume frontier; March labels untouched until frozen.
 cut=feb.date.quantile(.70); tr=feb[feb.date<=cut]; va=feb[feb.date>cut]
 candidates=[]
 for C in [.03,.1,.3,1,3]:
  m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=C,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0))
  m.fit(tr[feats],tr.y); s=m.predict_proba(va[feats])[:,1]
  order=np.argsort(-s); yy=va.y.to_numpy()[order]; ss=s[order]; cum=np.cumsum(yy); n=np.arange(1,len(yy)+1); rates=cum/n
  for target in [.50,.45,.40]:
   ok=np.where(rates>=target)[0]; k=int(ok[-1]+1) if len(ok) else 0
   if k: candidates.append({'C':C,'target':target,'n':k,'hits':int(cum[k-1]),'rate':float(rates[k-1]),'threshold':float(ss[k-1])})
 # freeze separately for each target by max validation volume, tie higher rate then smaller C
 frozen={}
 for target in [.50,.45,.40]:
  q=[x for x in candidates if x['target']==target]; frozen[str(target)]=max(q,key=lambda x:(x['n'],x['rate'],-x['C'])) if q else None
 results={}
 for key,f in frozen.items():
  if not f: results[key]=None; continue
  m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=f['C'],class_weight='balanced',solver='liblinear',max_iter=2000,random_state=0)); m.fit(feb[feats],feb.y)
  score=m.predict_proba(mar[feats])[:,1]; sel=mar.assign(score=score)[score>=f['threshold']].sort_values('date'); n=len(sel); h=int(sel.y.sum())
  half=n//2
  results[key]={'frozen':f,'march_n':n,'march_hits':h,'march_rate':h/n if n else None,'early':{'n':half,'hits':int(sel.iloc[:half].y.sum()) if half else 0},'late':{'n':n-half,'hits':int(sel.iloc[half:].y.sum()) if n-half else 0}}
 out={'policy':{'feb_selection_only':True,'march_one_shot':True,'september_outcomes_read':False},'funsite_rows':len(fun),'joined_feb':len(feb),'joined_mar':len(mar),'feature_count':len(feats),'feature_names':feats,'validation_candidates':candidates,'results':results}
 open('research_3head_funsite_50pct_model_result.json','w').write(json.dumps(out,ensure_ascii=False,indent=2,default=str)); print(json.dumps({k:v for k,v in out.items() if k!='feature_names' and k!='validation_candidates'},ensure_ascii=False,indent=2,default=str))
if __name__=='__main__': main()
