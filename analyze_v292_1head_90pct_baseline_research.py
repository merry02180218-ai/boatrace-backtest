#!/usr/bin/env python3
"""v292 phase-1: strict 1-head >=90% realized-rate research on frozen v108 features.
Research only. Uses rows through 2026-06-30; never uses Jul/Aug/Sep outcomes.
Every test month trains on earlier months; Platt/quantile thresholds use training OOF only.
The v108 ledger contains current exhibition, so this is POST-capable baseline evidence, not PRE.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler

R=Path(__file__).resolve().parent
SRC=R/'analysis_v108_1head_feasibility.csv'
PREFIX=R/'analysis_v292_1head_90pct'
SUMMARY=R/'summary_v292_1head_90pct_baseline_research.md'
END=pd.Timestamp('2026-06-30')
TEST=['2026-02','2026-03','2026-04','2026-05','2026-06']
VEN=[f'{i:02d}' for i in range(1,25)]
ABS=['one_grade','one_wr','one_local','one_motor','one_waku_wr','one_nst_strength','one_waku_sr_strength','one_past_win','one_meet_st_strength','one_ex','one_st','one_lap','one_turn','one_straight','one_orig_avg','one_direct','one_score']
THR=['threat2','threat3','threat4','threat5','threat6','threat23_max','threat_all_max']
REL=['margin2','margin3','margin23','margin_all','st_margin2','st_margin3','st_margin23','ex_margin23','turn_margin23','straight_margin23']
ALL=ABS+THR+REL
MODELS={
 'LR_ABS_POST':('lr',ABS),
 'LR_ABS_THREAT_POST':('lr',ABS+THR),
 'LR_V109_FULL_POST':('lr',ALL),
 'HGB_V109_FULL_POST':('hgb',ALL),
}
CUTS=[.70,.75,.80,.82,.84,.86,.88,.90,.92,.94,.95,.96,.97,.98]
QS=[.90,.95,.975,.99,.995]
BINS=[0,.50,.60,.70,.75,.80,.85,.90,.95,1.000001]
GAPS=[
 ('BASE_1','boat1 absolute player/motor/form','present','v109 absolute block exists'),
 ('RELATIVE_ATTACK','1v2/1v3 composite score','present','margin2/margin3/margin23/margin_all'),
 ('RELATIVE_ATTACK','1v2/1v3 ST','present','st_margin2/st_margin3/st_margin23'),
 ('RELATIVE_ATTACK','1vAll ST','missing','no explicit all-opponent ST margin'),
 ('RELATIVE_ATTACK','1v2/1v3 direct motor','missing','motor only embedded in composite score'),
 ('RELATIVE_ATTACK','player/course history deltas','missing','no all-win/frame-win/recent-p2 relative ledger'),
 ('WALL_THREAT','boat2/3 composite threat','present','threat2/threat3/threat23_max'),
 ('WALL_THREAT','wall2 collapse / simultaneous attack','partial','structural wall gate absent'),
 ('PRIOR_FORM','meeting ST','present','one_meet_st_strength'),
 ('PRIOR_FORM','prior exhibition/straight/turn/lap','missing','prior-history ledger absent'),
 ('ENV_ENTRY','actual course1 entry','partial','entry is gate only'),
 ('ENV_ENTRY','wind/direction interaction','missing','venue one-hot only'),
 ('POST_EXHIBITION','current display/original display','present','one_ex/st/lap/turn/straight/orig_avg'),
 ('POST_EXHIBITION','1v23 ex/turn/straight','present','existing margin23 features'),
 ('POST_EXHIBITION','1v23 lap + 1vAll display margins','missing','not in v109'),
 ('CONSENSUS','separate PRE/POST/ENV models','missing','v109 monolithic POST-capable model'),
 ('NEGATIVE_RISK','independent boat1-loss guard','missing','no separate nonlinear loss gate'),
]

def auc(y,p):
 return float(roc_auc_score(y,p)) if len(np.unique(y))>1 else float('nan')
def wilson(h,n):
 if not n:return (float('nan'),float('nan'))
 z=1.959963984540054;p=h/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;r=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/d
 return max(0,c-r),min(1,c+r)
def prep():
 d=pd.read_csv(SRC,encoding='utf-8-sig');d['date']=pd.to_datetime(d.date,errors='coerce');d['month']=d.date.dt.strftime('%Y-%m');d['venue']=d.venue.astype(str).str.replace('.0','',regex=False).str.zfill(2)
 for c in ALL+['head_hit','valid_result']:
  if c not in d:raise RuntimeError(f'missing {c}')
 d=d[(pd.to_numeric(d.valid_result,errors='coerce')==1)&(d.date<=END)].copy()
 if (d.date>=pd.Timestamp('2026-07-01')).any():raise RuntimeError('Jul/Aug leakage')
 for c in ALL:d[c]=pd.to_numeric(d[c],errors='coerce')
 d['head_hit']=pd.to_numeric(d.head_hit).astype(int)
 return d.sort_values(['date','race_code']).reset_index(drop=True)
def model(kind,fs):
 if kind=='lr':
  pre=ColumnTransformer([('n',Pipeline([('i',SimpleImputer(strategy='median')),('s',StandardScaler())]),fs),('v',OneHotEncoder(categories=[VEN],handle_unknown='ignore'),['venue'])])
  return Pipeline([('p',pre),('m',LogisticRegression(C=.5,max_iter=2000))])
 pre=ColumnTransformer([('n',SimpleImputer(strategy='median'),fs),('v',OneHotEncoder(categories=[VEN],handle_unknown='ignore',sparse_output=False),['venue'])],sparse_threshold=0)
 return Pipeline([('p',pre),('m',HistGradientBoostingClassifier(learning_rate=.055,max_iter=220,max_leaf_nodes=15,min_samples_leaf=35,l2_regularization=1,random_state=292))])
def fitpred(kind,fs,tr,te):
 m=model(kind,fs);m.fit(tr[fs+['venue']],tr.head_hit);return m.predict_proba(te[fs+['venue']])[:,1]
def oof(kind,fs,tr):
 ms=sorted(tr.month.unique());a=[]
 for i in range(2,len(ms)):
  x=tr[tr.month.isin(ms[:i])];v=tr[tr.month==ms[i]]
  if len(x)<500 or len(v)==0:continue
  q=v[['date','month','race_code','head_hit']].copy();q['p']=fitpred(kind,fs,x,v);a.append(q)
 if not a:raise RuntimeError('no temporal OOF')
 return pd.concat(a,ignore_index=True)
def lg(p):
 p=np.clip(np.asarray(p,float),1e-6,1-1e-6);return np.log(p/(1-p))
def calibrator(o):
 c=LogisticRegression(C=1e6,max_iter=1000);c.fit(lg(o.p).reshape(-1,1),o.head_hit);return c
def cal(c,p):return c.predict_proba(lg(p).reshape(-1,1))[:,1]
def smet(y,p):
 p=np.clip(np.asarray(p,float),1e-6,1-1e-6);y=np.asarray(y,int)
 return auc(y,p),float(brier_score_loss(y,p)),float(log_loss(y,p,labels=[0,1]))
def selmet(g):
 n=len(g);h=int(g.head_hit.sum()) if n else 0;lo,hi=wilson(h,n)
 if n:
  b=g.groupby('test_month').head_hit.agg(['size','mean']);worst=float(b['mean'].min());mm=int(b['size'].min());mc=len(b)
 else:worst=float('nan');mm=mc=0
 return {'R':n,'heads':h,'head_rate':h/n if n else float('nan'),'wilson_lo':lo,'wilson_hi':hi,'months_covered':mc,'worst_month_head_rate':worst,'min_month_R':mm}
def run(d):
 pp=[];fold=[]
 for name,(kind,fs) in MODELS.items():
  for tm in TEST:
   tr=d[d.month<tm];te=d[d.month==tm]
   if len(te)==0:continue
   oo=oof(kind,fs,tr);cc=calibrator(oo);op=cal(cc,oo.p);raw=fitpred(kind,fs,tr,te);pc=cal(cc,raw);qcuts={q:float(np.quantile(op,q)) for q in QS}
   z=te[['date','month','race_code','venue','race','head_hit']].copy();z['model']=name;z['test_month']=tm;z['p_raw']=raw;z['p_cal']=pc
   for q,ct in qcuts.items():z[f'q{q}_sel']=(pc>=ct).astype(int);z[f'q{q}_cut']=ct
   pp.append(z);ar,br,lr=smet(oo.head_hit,oo.p);ac,bc,lc=smet(oo.head_hit,op);fold.append({'model':name,'test_month':tm,'train_rows':len(tr),'test_rows':len(te),'oof_rows':len(oo),'oof_raw_brier':br,'oof_cal_brier':bc})
   print(name,tm,len(tr),len(te),len(oo),flush=True)
 return pd.concat(pp,ignore_index=True),pd.DataFrame(fold)
def metrics(p):
 a=[]
 for n,g in p.groupby('model'):
  for sc in ['p_raw','p_cal']:
   A,B,L=smet(g.head_hit,g[sc]);a.append({'model':n,'score':sc,'scope':'pooled_Feb-Jun','R':len(g),'auc':A,'brier':B,'logloss':L})
  for tm,h in g.groupby('test_month'):
   for sc in ['p_raw','p_cal']:
    A,B,L=smet(h.head_hit,h[sc]);a.append({'model':n,'score':sc,'scope':tm,'R':len(h),'auc':A,'brier':B,'logloss':L})
 return pd.DataFrame(a)
def thresholds(p):
 a=[]
 for n,g in p.groupby('model'):
  for sc in ['p_raw','p_cal']:
   for c in CUTS:a.append({'model':n,'score':sc,'rule':f'>={c:.3f}','cut':c,**selmet(g[g[sc]>=c])})
 return pd.DataFrame(a)
def quantiles(p):
 a=[]
 for n,g in p.groupby('model'):
  for q in QS:a.append({'model':n,'score':'p_cal','rule':f'training_OOF_q{q:.3f}','quantile':q,**selmet(g[g[f'q{q}_sel']==1])})
 return pd.DataFrame(a)
def reliability(p):
 a=[]
 for n,g in p.groupby('model'):
  for sc in ['p_raw','p_cal']:
   x=g.assign(bin=pd.cut(g[sc],BINS,right=False,include_lowest=True))
   for b,h in x.groupby('bin',observed=True):
    H=int(h.head_hit.sum());lo,hi=wilson(H,len(h));a.append({'model':n,'score':sc,'bin':str(b),'R':len(h),'heads':H,'mean_pred':h[sc].mean(),'head_rate':H/len(h),'wilson_lo':lo,'wilson_hi':hi})
 return pd.DataFrame(a)
def pc(x):return '-' if pd.isna(x) else f'{100*x:.2f}%'
def summary(d,p,m,t,q,re):
 L=['# v292 1HEAD 90% baseline research','','- Research-only; not production.','- Frozen v108 features only; POST-capable, not PRE.','- Selection/evaluation ends 2026-06-30. Jul/Aug excluded; Sep outcomes unread.','- Monthly expanding walk-forward. Calibration and quantile cuts are training-OOF only.','','## Existing feature gap','|family|concept|status|note|','|---|---|---|---|']
 L += [f'|{a}|{b}|{c}|{e}|' for a,b,c,e in GAPS]
 L += ['','## Pooled model metrics','|model|score|R|AUC|Brier|LogLoss|','|---|---|---:|---:|---:|---:|']
 for _,r in m[m.scope=='pooled_Feb-Jun'].sort_values(['score','brier']).iterrows():L.append(f'|{r.model}|{r.score}|{int(r.R)}|{r.auc:.4f}|{r.brier:.4f}|{r.logloss:.4f}|')
 c=pd.concat([t.assign(source='fixed_probability'),q.assign(source='training_OOF_quantile')],ignore_index=True,sort=False);hit=c[(c.R>=100)&(c.head_rate>=.90)].sort_values(['R','wilson_lo'],ascending=False)
 L += ['','## >=90% realized zones, R>=100']
 if hit.empty:L.append('- None in Feb-Jun walk-forward. Do not rescue with Jul/Aug.')
 else:
  L += ['|source|model|rule|R|heads|rate|Wilson low|worst month|min month R|','|---|---|---|---:|---:|---:|---:|---:|---:|']
  for _,r in hit.head(30).iterrows():L.append(f'|{r.source}|{r.model}|{r.rule}|{int(r.R)}|{int(r.heads)}|{pc(r.head_rate)}|{pc(r.wilson_lo)}|{pc(r.worst_month_head_rate)}|{int(r.min_month_R)}|')
 best=c[c.R>=100].sort_values(['head_rate','R'],ascending=False).head(15);L += ['','## Best high-confidence zones (R>=100)','|source|model|rule|R|rate|Wilson low|worst month|','|---|---|---|---:|---:|---:|---:|']
 for _,r in best.iterrows():L.append(f'|{r.source}|{r.model}|{r.rule}|{int(r.R)}|{pc(r.head_rate)}|{pc(r.wilson_lo)}|{pc(r.worst_month_head_rate)}|')
 L += ['','## Calibrated reliability >=75% mean score','|model|bin|R|mean p|realized|Wilson low|','|---|---|---:|---:|---:|---:|']
 for _,r in re[(re.score=='p_cal')&(re.mean_pred>=.75)].iterrows():L.append(f'|{r.model}|{r.bin}|{int(r.R)}|{pc(r.mean_pred)}|{pc(r.head_rate)}|{pc(r.wilson_lo)}|')
 L += ['','## Next','- Build v293 direct raw-source dataset with PRE/POST separation.','- Add direct 1v2/1v3 motor and player/course deltas, prior exhibition, 1vAll ST/display margins, wall-collapse risk, ENV_ENTRY, and PRE/POST consensus.','- Reuse the same Feb-Jun expanding walk-forward and training-only calibration. Freeze before prospective validation.']
 return '\n'.join(L)+'\n'
def main():
 d=prep();p,f=run(d);m=metrics(p);t=thresholds(p);q=quantiles(p);re=reliability(p);gap=pd.DataFrame(GAPS,columns=['family','target_concept','status','note'])
 p.to_csv(str(PREFIX)+'_predictions.csv',index=False,encoding='utf-8-sig');m.to_csv(str(PREFIX)+'_model_metrics.csv',index=False,encoding='utf-8-sig');t.to_csv(str(PREFIX)+'_thresholds.csv',index=False,encoding='utf-8-sig');q.to_csv(str(PREFIX)+'_quantiles.csv',index=False,encoding='utf-8-sig');re.to_csv(str(PREFIX)+'_reliability.csv',index=False,encoding='utf-8-sig');gap.to_csv(R/'analysis_v292_1head_feature_gap.csv',index=False,encoding='utf-8-sig')
 SUMMARY.write_text(summary(d,p,m,t,q,re),encoding='utf-8');print(SUMMARY.read_text(),flush=True)
if __name__=='__main__':main()
