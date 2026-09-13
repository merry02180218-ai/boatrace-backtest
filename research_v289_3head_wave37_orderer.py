from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import research_v289_3head_wave31_nonlinear_gate as base
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave37_orderer.json')
CUT=.365448; K=5

def head_fit(Xtr,y3,Xte):
 m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto')); m.fit(Xtr,y3); return m.predict_proba(Xte)[:,1]
def score_combo_logit(Xtr,y,Xte):
 m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15,solver='lbfgs')); m.fit(Xtr,y); pc=m.predict_proba(Xte); s=np.zeros((len(Xte),len(base.COMBOS)))
 for j,c in enumerate(m.classes_):
  if c in base.COMBOS:s[:,base.COMBOS.index(c)]=pc[:,j]
 return s
def score_combo_extra(Xtr,y,Xte):
 imp=SimpleImputer(strategy='median'); a=imp.fit_transform(Xtr); b=imp.transform(Xte); m=ExtraTreesClassifier(n_estimators=300,min_samples_leaf=8,max_features='sqrt',random_state=37,n_jobs=-1,class_weight='balanced_subsample'); m.fit(a,y); pc=m.predict_proba(b); s=np.zeros((len(Xte),len(base.COMBOS)))
 for j,c in enumerate(m.classes_):
  if c in base.COMBOS:s[:,base.COMBOS.index(c)]=pc[:,j]
 return s
def score_position(Xtr,y,Xte):
 y2=np.array([str(c).split('-')[1] for c in y]); y3=np.array([str(c).split('-')[2] for c in y]); m2=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15)); m3=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15)); m2.fit(Xtr,y2); m3.fit(Xtr,y3); p2=m2.predict_proba(Xte); p3=m3.predict_proba(Xte); s=np.zeros((len(Xte),len(base.COMBOS)))
 for i,c in enumerate(base.COMBOS):
  a,b,c3=c.split('-');
  if a!='3' or b==c3: continue
  if b in m2.classes_ and c3 in m3.classes_: s[:,i]=p2[:,list(m2.classes_).index(b)]*p3[:,list(m3.classes_).index(c3)]
 return s
def topk(score):
 out=[]
 for r in score:
  idx=np.argsort(-np.nan_to_num(r,nan=-1))[:K]; out.append(';'.join(base.COMBOS[j] for j in idx))
 return out
def conv(q,col):
 z=q[q.actual3==1]; hit=sum(a in t.split(';') for a,t in zip(z.actual,z[col])); n=len(z); return {'head_cases':n,'ticket_hits':hit,'conversion':hit/n if n else 0.}
def block(q,col):
 x=q.copy(); x['variant_return']=[base.dutch_return(r,str(r[col]).split(';')) for _,r in x.iterrows()]; m=base.block(x); m['conversion']=conv(x,col); return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna(''); ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)]; d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
 if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
 X=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int); methods={'logit':score_combo_logit,'extra':score_combo_extra,'position':score_position}; scores={k:np.full((len(d),len(base.COMBOS)),np.nan) for k in methods}; p=np.full(len(d),np.nan)
 specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
 for mo,trm in specs:
  tem=d.month==mo; tr=np.flatnonzero(trm.to_numpy()); te=np.flatnonzero(tem.to_numpy()); ytr=y.iloc[tr]; mask=ytr.str.startswith('3-').to_numpy(); p[te]=head_fit(X.iloc[tr],ytr.str.startswith('3-').astype(int).to_numpy(),X.iloc[te])
  for name,fn in methods.items(): scores[name][te]=fn(X.iloc[tr].iloc[np.flatnonzero(mask)],ytr.iloc[np.flatnonzero(mask)],X.iloc[te])
 d['p3']=p
 for name,s in scores.items(): d['top5_'+name]=topk(s)
 march=d[(d.month=='2026-03')&(d.p3>=CUT)].sort_values(['date','race_code']).reset_index(drop=True); h=len(march)//2; cand=[]
 for name in methods:
  full=conv(march,'top5_'+name); early=conv(march.iloc[:h],'top5_'+name); late=conv(march.iloc[h:],'top5_'+name); cand.append({'method':name,'full':full,'early':early,'late':late,'worst_half':min(early['conversion'],late['conversion'])})
 chosen=max(cand,key=lambda z:(z['worst_half'],z['full']['conversion'])); col='top5_'+chosen['method']; out={'march_candidates':cand,'chosen':chosen,'months':{}}
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
  q=d[(d.month==mo)&(d.p3>=CUT)]; out['months'][mo]=block(q,col)
 hold=d[d.month.isin(['2026-04','2026-05','2026-06']) & (d.p3>=CUT)]; out['apr_jun']=block(hold,col); out['overlap']=int(hold.race_code.astype(str).isin(ex).sum()); OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
