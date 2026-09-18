from __future__ import annotations
import csv, io, json, re, urllib.request, warnings
import numpy as np, pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
warnings.filterwarnings("ignore")
BASE='https://boatracecsv.github.io/data'; SRC='analysis_v289_3head_wave21_allrace_feature_settled.csv'
EX={202602071007,202602120606,202602150404,202602161108,202602171607,202602171911,202602191910,202602270507,202603031807,202603080101,202603081308,202603101810,202603111810,202603122004,202603141405,202603200809,202603211406,202603241009,202603271906,202603281904}
CORE=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','当地3連対率','F本数','L本数','モーター2連対率','モーター3連対率','ボート2連対率','ボート3連対率']
def fetch(kind,d):
 u=f'{BASE}/{kind}/{d:%Y/%m/%d}.csv'
 try:
  with urllib.request.urlopen(u,timeout=30) as r:return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
 except:return []
def num(v):
 try:return float(v)
 except:return np.nan
def recent(row,b,p):
 vals=[]
 for k in range(1,6):
  s=(row.get(f'艇{b}_前{k}節_着順列') or '')
  vals += [int(x) for x in re.findall(r'(?<!\\d)[1-6](?!\\d)',s)]
 a=np.array(vals,float)
 return {f'{p}_starts':len(a),f'{p}_mean':a.mean() if len(a) else np.nan,f'{p}_win':(a==1).mean() if len(a) else np.nan,f'{p}_top2':(a<=2).mean() if len(a) else np.nan,f'{p}_top3':(a<=3).mean() if len(a) else np.nan}
def features(rc,rn,rl):
 o={'rc':int(rc['レースコード']),'venue':str(rc.get('レース場コード','')).zfill(2),'race_no':int(re.sub(r'\D','',str(rc.get('レース回','0'))) or 0)}
 for b in range(1,7):
  for c in CORE:o[f'b{b}_{c}']=num(rc.get(f'艇{b}_{c}'))
  for k,v in recent(rn,b,'rn').items():o[f'b{b}_{k}']=v
  for k,v in recent(rl,b,'rl').items():o[f'b{b}_{k}']=v
 bases=CORE+['rn_starts','rn_mean','rn_win','rn_top2','rn_top3','rl_starts','rl_mean','rl_win','rl_top2','rl_top3']
 for c in bases:
  z=[o.get(f'b{x}_{c}',np.nan) for x in [1,2,4,5,6]]; b3=o.get(f'b3_{c}',np.nan)
  o[f'b3_mean_gap_{c}']=b3-np.nanmean(z) if np.isfinite(b3) and np.isfinite(z).any() else np.nan
  o[f'b3_min_gap_{c}']=b3-np.nanmax(z) if np.isfinite(b3) and np.isfinite(z).any() else np.nan
  for x in [1,2,4,5,6]:o[f'b3_gap{x}_{c}']=b3-o.get(f'b{x}_{c}',np.nan)
 return o
def prefix(score,y,target,minn=20):
 ix=np.argsort(-score); yy=np.asarray(y)[ix]; ss=np.asarray(score)[ix]; cum=np.cumsum(yy); n=np.arange(1,len(yy)+1); rate=cum/n
 ok=np.where((rate>=target)&(n>=minn))[0]
 if not len(ok):return None
 k=int(ok[-1]+1);return {'n':k,'hits':int(cum[k-1]),'rate':float(rate[k-1]),'threshold':float(ss[k-1])}
def model(name):
 if name=='logit':return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.1,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=7))
 if name=='extra':return make_pipeline(SimpleImputer(strategy='median'),ExtraTreesClassifier(n_estimators=500,min_samples_leaf=12,max_features=.65,class_weight='balanced',random_state=7,n_jobs=-1))
 if name=='rf':return make_pipeline(SimpleImputer(strategy='median'),RandomForestClassifier(n_estimators=400,min_samples_leaf=15,max_features=.5,class_weight='balanced',random_state=7,n_jobs=-1))
 return make_pipeline(SimpleImputer(strategy='median'),HistGradientBoostingClassifier(max_iter=220,max_leaf_nodes=15,l2_regularization=2,learning_rate=.05,random_state=7))
def main():
 b=pd.read_csv(SRC,low_memory=False);b['date']=pd.to_datetime(b.date);b['rc']=pd.to_numeric(b.race_code_norm,errors='coerce').astype('Int64')
 b=b[(b.settle__usable==1)&(b.closing_odds__ok==1)&(~b.rc.isin(EX))&(b.date>='2026-02-01')&(b.date<'2026-04-01')].copy()
 rows=[]
 for d in pd.date_range('2026-02-01','2026-03-31'):
  parts={k:fetch(k,d.date()) for k in ['programs/race_cards','programs/recent_national','programs/recent_local']}
  if not all(parts.values()):continue
  maps={k:{str(x.get('レースコード','')):x for x in v} for k,v in parts.items()}
  for c in set.intersection(*[set(x) for x in maps.values()]):
   if c.isdigit():rows.append(features(maps['programs/race_cards'][c],maps['programs/recent_national'][c],maps['programs/recent_local'][c]))
 x=pd.DataFrame(rows).drop_duplicates('rc'); d=b[['rc','date','settle__winner']].merge(x,on='rc');d['y']=(d.settle__winner==3).astype(int)
 feats=[c for c in x.columns if c not in ['rc','venue'] and x[c].notna().sum()>=30]
 feb=d[d.date<'2026-03-01'].sort_values(['date','rc']);mar=d[d.date>='2026-03-01'].sort_values(['date','rc'])
 days=sorted(feb.date.dt.date.unique()); cut1=days[int(len(days)*.55)];cut2=days[int(len(days)*.78)]
 tr=feb[feb.date.dt.date<=cut1];v1=feb[(feb.date.dt.date>cut1)&(feb.date.dt.date<=cut2)];v2=feb[feb.date.dt.date>cut2]
 names=['logit','extra','rf','hist']; scores={}
 candidates=[]
 for n in names:
  m=model(n);m.fit(tr[feats],tr.y);s1=m.predict_proba(v1[feats])[:,1];s2=m.predict_proba(v2[feats])[:,1]
  for t in [.50,.45,.40]:
   p=prefix(s1,v1.y,t)
   if p:
    sel=s2.assign(score=s2)[s2>=p['threshold']]; candidates.append({'family':n,'target':t,'threshold':p['threshold'],'v1_n':p['n'],'v1_rate':p['rate'],'v2_n':len(sel),'v2_rate':float(sel.y.mean()) if len(sel) else None})
 # choose only Feb-stable gates: v2 >= target-0.05, max v2 N
 frozen={}
 for t in [.50,.45,.40]:
  q=[z for z in candidates if z['target']==t and z['v2_n']>=20 and z['v2_rate'] is not None and z['v2_rate']>=t-.05]
  frozen[str(t)]=max(q,key=lambda z:(z['v2_n'],z['v2_rate'])) if q else None
 # ensemble rank-average family, selected strictly on Feb split
 ms=[]
 for n in names:
  m=model(n);m.fit(tr[feats],tr.y);ms.append(m)
 def ens(frame):
  arr=np.column_stack([m.predict_proba(frame[feats])[:,1] for m in ms]);return np.mean(pd.DataFrame(arr).rank(pct=True).to_numpy(),axis=1)
 e1,e2=ens(v1),ens(v2)
 for t in [.50,.45,.40]:
  p=prefix(e1,v1.y,t)
  if p:
   sel=v2.assign(score=e2)[e2>=p['threshold']];z={'family':'ensemble','target':t,'threshold':p['threshold'],'v1_n':p['n'],'v1_rate':p['rate'],'v2_n':len(sel),'v2_rate':float(sel.y.mean()) if len(sel) else None};candidates.append(z)
   if z['v2_n']>=20 and z['v2_rate'] is not None and z['v2_rate']>=t-.05:
    old=frozen[str(t)]
    if old is None or (z['v2_n'],z['v2_rate'])>(old['v2_n'],old['v2_rate']):frozen[str(t)]=z
 # one-shot March: refit chosen family on all Feb; ensemble likewise
 results={}
 for key,z in frozen.items():
  if not z:results[key]=None;continue
  if z['family']=='ensemble':
   mm=[model(n) for n in names]
   for m in mm:m.fit(feb[feats],feb.y)
   a=np.column_stack([m.predict_proba(mar[feats])[:,1] for m in mm]);score=np.mean(pd.DataFrame(a).rank(pct=True).to_numpy(),axis=1)
  else:
   m=model(z['family']);m.fit(feb[feats],feb.y);score=m.predict_proba(mar[feats])[:,1]
  sel=mar.assign(score=score)[score>=z['threshold']].copy();sel=sel.sort_values(['date','rc']);half=len(sel)//2
  venues=sel.groupby('venue').y.agg(['count','sum','mean']).sort_values('count',ascending=False).head(12).reset_index().to_dict('records')
  results[key]={'frozen':z,'march_n':len(sel),'march_hits':int(sel.y.sum()),'march_rate':float(sel.y.mean()) if len(sel) else None,'early_n':half,'early_hits':int(sel.iloc[:half].y.sum()),'late_n':len(sel)-half,'late_hits':int(sel.iloc[half:].y.sum()),'venues_top12':venues}
 out={'policy':{'feb_only_selection':True,'march_one_shot':True,'september_outcomes_read':False,'current_meet_used':False},'joined_feb':len(feb),'joined_mar':len(mar),'features':len(feats),'feb_candidates':candidates,'frozen':frozen,'march_results':results}
 open('research_3head_funsite_broad50_result.json','w').write(json.dumps(out,ensure_ascii=False,indent=2,default=str));print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
if __name__=='__main__':main()
