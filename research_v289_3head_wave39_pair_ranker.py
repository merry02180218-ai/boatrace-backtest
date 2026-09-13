from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave37_orderer as w37
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave39_pair_ranker.json'); CUT=.365448; K=5
CS=[.01,.03,.08,.15,.30]

def pair_features(df):
 rows=[]
 for _,r in df.iterrows():
  for combo in base.COMBOS:
   _,a,b=combo.split('-'); a=int(a); b=int(b); z={}
   for met in base.METRICS:
    v3=float(pd.to_numeric(str(r[f'card__艇3_{met}']).replace('%',''),errors='coerce'))
    va=float(pd.to_numeric(str(r[f'card__艇{a}_{met}']).replace('%',''),errors='coerce'))
    vb=float(pd.to_numeric(str(r[f'card__艇{b}_{met}']).replace('%',''),errors='coerce'))
    z[f'second_{met}']=va; z[f'third_{met}']=vb; z[f'second_minus_third_{met}']=va-vb; z[f'b3_minus_second_{met}']=v3-va; z[f'b3_minus_third_{met}']=v3-vb
   rows.append(z)
 return pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan)

def fit_pair(train_df,test_df,C):
 tr=train_df[train_df.settle__actual_combo.astype(str).str.startswith('3-')].copy()
 Xtr=pair_features(tr); yy=[]
 for c in tr.settle__actual_combo.astype(str): yy.extend([int(x==c) for x in base.COMBOS])
 m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=1000,C=C,class_weight='balanced',solver='lbfgs'))
 m.fit(Xtr,np.array(yy)); p=m.predict_proba(pair_features(test_df))[:,1].reshape(len(test_df),len(base.COMBOS)); return p

def top5(s): return [';'.join(base.COMBOS[j] for j in np.argsort(-r)[:K]) for r in s]
def conv(q,col):
 z=q[q.actual3==1]; n=len(z); h=sum(a in t.split(';') for a,t in zip(z.actual,z[col])); return {'head_cases':n,'ticket_hits':h,'conversion':h/n if n else 0.}
def settle(q,col):
 z=q.copy(); z['variant_return']=[base.dutch_return(r,r[col].split(';')) for _,r in z.iterrows()]; m=base.block(z); m['conversion']=conv(z,col); return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna(''); ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
 if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
 Xh=base.build_static(d); y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int); p=np.full(len(d),np.nan); scores={C:np.full((len(d),len(base.COMBOS)),np.nan) for C in CS}
 specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
 for mo,trm in specs:
  tem=d.month==mo; ti=np.flatnonzero(trm.to_numpy()); ei=np.flatnonzero(tem.to_numpy()); p[ei]=w37.head_fit(Xh.iloc[ti],y.iloc[ti].str.startswith('3-').astype(int).to_numpy(),Xh.iloc[ei])
  for C in CS: scores[C][ei]=fit_pair(d.iloc[ti],d.iloc[ei],C)
 d['p3']=p
 for C,s in scores.items(): d[f'top5_C{C}']=top5(s)
 march=d[(d.month=='2026-03')&(d.p3>=CUT)].sort_values(['date','race_code']).reset_index(drop=True); h=len(march)//2; cand=[]
 for C in CS:
  col=f'top5_C{C}'; f=conv(march,col); e=conv(march.iloc[:h],col); l=conv(march.iloc[h:],col); cand.append({'C':C,'full':f,'early':e,'late':l,'worst_half':min(e['conversion'],l['conversion'])})
 chosen=max(cand,key=lambda z:(z['worst_half'],z['full']['conversion'])); col=f"top5_C{chosen['C']}"; out={'pair_feature_count':45,'march_candidates':cand,'chosen':chosen,'months':{}}
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']: out['months'][mo]=settle(d[(d.month==mo)&(d.p3>=CUT)],col)
 hold=d[d.month.isin(['2026-04','2026-05','2026-06'])&(d.p3>=CUT)]; out['apr_jun']=settle(hold,col); out['overlap']=int(hold.race_code.astype(str).isin(ex).sum()); OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
