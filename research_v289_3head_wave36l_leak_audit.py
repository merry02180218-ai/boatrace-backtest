from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
import research_v289_3head_wave31_nonlinear_gate as base
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('research_v289_3head_wave36l_leak_audit.json'); CUT=.365448
BAD=['settle','payout','odds','着順','actual','return','profit','roi','配当']
def model(): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto'))
def main():
 d=pd.read_csv(SRC,dtype=str).fillna(''); ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)]; d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
 if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
 X=base.build_static(d); features=list(X.columns)
 if len(features)!=63: raise RuntimeError('expected 63 features')
 suspicious=[c for c in features if any(x.lower() in c.lower() for x in BAD)]
 y=d.settle__actual_combo.astype(str).str.startswith('3-').astype(int).to_numpy(); p=np.full(len(d),np.nan); folds=[]
 specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
 for mo,trm in specs:
  tem=d.month==mo; maxtr=d.loc[trm,'date'].max(); mint=d.loc[tem,'date'].min(); causal=maxtr<mint
  if not causal: raise RuntimeError('walk-forward causality failure')
  m=model(); m.fit(X.loc[trm],y[np.flatnonzero(trm.to_numpy())]); p[np.flatnonzero(tem.to_numpy())]=m.predict_proba(X.loc[tem])[:,1]; folds.append([mo,maxtr,mint,causal])
 feb=d.month=='2026-02'; mar=d.month=='2026-03'; rng=np.random.default_rng(3601); ys=y[np.flatnonzero(feb.to_numpy())].copy(); rng.shuffle(ys); m=model(); m.fit(X.loc[feb],ys); auc=float(roc_auc_score(y[np.flatnonzero(mar.to_numpy())],m.predict_proba(X.loc[mar])[:,1]))
 d['p3']=p; d['actual3']=y; temporal={}
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
  z=d[d.month==mo].sort_values(['date','race_code']); h=len(z)//2
  for tag,q in [('early',z.iloc[:h]),('late',z.iloc[h:]),('all',z)]:
   q=q[q.p3>=CUT]; temporal[mo+'-'+tag]={'races':len(q),'head_hits':int(q.actual3.sum()),'head_rate':float(q.actual3.mean()) if len(q) else 0.0,'mean_p3':float(q.p3.mean()) if len(q) else 0.0}
 passed=(not suspicious) and all(x[3] for x in folds) and .40<=auc<=.60
 out={'feature_count':63,'features':features,'suspicious_feature_names':suspicious,'walk_forward_folds':folds,'shuffle_label_auc':auc,'temporal_head_diagnostics':temporal,'audit':'PASS' if passed else 'FAIL'}; OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
