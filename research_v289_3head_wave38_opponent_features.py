from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave37_orderer as w37
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave38_opponent_features.json'); CUT=.365448; K=5
OPP=[1,2,4,5,6]

def expanded(df):
 x=base.build_static(df).copy()
 for met in base.METRICS:
  vals={b:base.num(df[f'card__艇{b}_{met}']) for b in range(1,7)}
  for b in OPP:x[f'b{b}_{met}']=vals[b]
  for a in OPP:
   for b in OPP:
    if a<b:x[f'b{a}_minus_b{b}_{met}']=vals[a]-vals[b]
 bad=[c for c in x if any(s in c for s in ['節D','着順','settle','closing','odds','払戻'])]
 if bad:raise RuntimeError(str(bad[:5]))
 return x.replace([np.inf,-np.inf],np.nan)

def order_score(Xtr,y,Xte,C):
 m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=1000,C=C,solver='lbfgs'))
 m.fit(Xtr,y); pc=m.predict_proba(Xte); s=np.zeros((len(Xte),len(base.COMBOS)))
 for j,c in enumerate(m.classes_):
  if c in base.COMBOS:s[:,base.COMBOS.index(c)]=pc[:,j]
 return s

def top5(s):return [';'.join(base.COMBOS[j] for j in np.argsort(-r)[:K]) for r in s]
def conv(q,col):
 z=q[q.actual3==1]; n=len(z); h=sum(a in t.split(';') for a,t in zip(z.actual,z[col])); return {'head_cases':n,'ticket_hits':h,'conversion':h/n if n else 0.}
def settle(q,col):
 z=q.copy();z['variant_return']=[base.dutch_return(r,r[col].split(';')) for _,r in z.iterrows()];m=base.block(z);m['conversion']=conv(z,col);return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna(''); ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7]
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 Xh=base.build_static(d); Xe=expanded(d); y=d.settle__actual_combo.astype(str);d['actual']=y;d['actual3']=y.str.startswith('3-').astype(int);p=np.full(len(d),np.nan)
 configs=[('static63',.15),('expanded',.03),('expanded',.08),('expanded',.15),('expanded',.30)]; scores={f'{a}_C{c}':np.full((len(d),len(base.COMBOS)),np.nan) for a,c in configs}
 specs=[('2026-03',d.month=='2026-02'),('2026-04',d.month<'2026-04'),('2026-05',d.month<'2026-05'),('2026-06',d.month<'2026-06'),('2026-07',d.month<='2026-06'),('2026-08',d.month<='2026-06')]
 for mo,trm in specs:
  te=d.month==mo; ti=np.flatnonzero(trm.to_numpy()); ei=np.flatnonzero(te.to_numpy()); yt=y.iloc[ti]; mask=yt.str.startswith('3-').to_numpy();p[ei]=w37.head_fit(Xh.iloc[ti],yt.str.startswith('3-').astype(int).to_numpy(),Xh.iloc[ei])
  for typ,C in configs:
   key=f'{typ}_C{C}'; xx=Xh if typ=='static63' else Xe;scores[key][ei]=order_score(xx.iloc[ti].iloc[np.flatnonzero(mask)],yt.iloc[np.flatnonzero(mask)],xx.iloc[ei],C)
 d['p3']=p
 for k,s in scores.items():d['top5_'+k]=top5(s)
 march=d[(d.month=='2026-03')&(d.p3>=CUT)].sort_values(['date','race_code']).reset_index(drop=True);h=len(march)//2;cand=[]
 for k in scores:
  col='top5_'+k;f=conv(march,col);e=conv(march.iloc[:h],col);l=conv(march.iloc[h:],col);cand.append({'method':k,'full':f,'early':e,'late':l,'worst_half':min(e['conversion'],l['conversion'])})
 chosen=max(cand,key=lambda z:(z['worst_half'],z['full']['conversion']));col='top5_'+chosen['method'];out={'expanded_feature_count':Xe.shape[1],'march_candidates':cand,'chosen':chosen,'months':{}}
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:out['months'][mo]=settle(d[(d.month==mo)&(d.p3>=CUT)],col)
 hold=d[d.month.isin(['2026-04','2026-05','2026-06'])&(d.p3>=CUT)];out['apr_jun']=settle(hold,col);out['overlap']=int(hold.race_code.astype(str).isin(ex).sum());OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
