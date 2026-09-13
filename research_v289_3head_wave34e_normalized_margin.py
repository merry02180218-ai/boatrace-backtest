from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave31_nonlinear_gate as base
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); B=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('analysis_v289_3head_wave34e_normalized_margin.csv'); OUTJ=Path('research_v289_3head_wave34e_normalized_margin.json'); OUTM=Path('research_v289_3head_wave34e_normalized_margin.md')
BASE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070}; QS=[.90,.93,.95,.97,.98,.99]; AGREES=[.55,.67,.78,.89,1.0]; SDQS=[.50,.67,.80,1.0]; KS=[3,5,7]; N=9

def fit(trainX,train_combo,testX,seed):
 imp=SimpleImputer(strategy='median'); A=imp.fit_transform(trainX); C=imp.transform(testX); sc=StandardScaler().fit(A); A=sc.transform(A); C=sc.transform(C); y=train_combo.str.startswith('3-').astype(int).to_numpy(); pidx=np.flatnonzero(y==1); nidx=np.flatnonzero(y==0); rng=np.random.default_rng(seed); raw=[]; norm=[]
 for _ in range(N):
  p=A[rng.choice(pidx,len(pidx),replace=True)].mean(0); n=A[rng.choice(nidx,len(nidx),replace=True)].mean(0); dp=np.sqrt(((C-p)**2).mean(1)); dn=np.sqrt(((C-n)**2).mean(1)); raw.append(dn-dp); norm.append((dn-dp)/(dn+dp+1e-9))
 R=np.column_stack(raw); Z=np.column_stack(norm); mask=y==1; cond=make_pipeline(StandardScaler(),LogisticRegression(max_iter=600,C=.20,solver='lbfgs')); cond.fit(A[mask],train_combo.to_numpy()[mask]); pc=cond.predict_proba(C); order=np.zeros((len(testX),len(base.COMBOS)))
 for j,c in enumerate(cond.classes_):
  if c in base.COMBOS: order[:,base.COMBOS.index(c)]=pc[:,j]
 return R.mean(1),Z.mean(1),Z.std(1),(Z>0).mean(1),order

def block(q,k):
 q=q.copy(); q['variant_return']=[base.dutch_return(r,str(r[f'top{k}']).split(';')) for _,r in q.iterrows()]; m=base.block(q); mm={mo:base.block(g) for mo,g in q.groupby('month')}; m.update(monthly=mm,min_month_roi_pct=min((z['roi_pct'] for z in mm.values()),default=None),red_months=sum(z['roi_pct']<100 for z in mm.values()),max_drawdown_yen=base.maxdd(q.sort_values(['date','race_code']))); return q,m

def main():
 df=pd.read_csv(SRC,dtype=str).fillna(''); assert df.date.max()<='2026-08-31'; bd=pd.read_csv(B,dtype=str).fillna(''); ex=set(bd.race_code); assert len(ex)==94 and bd.route.value_counts().to_dict()=={'S':55,'A':21,'B':18}; df=df[~df.race_code.isin(ex)]; df=df[(df.settle__usable=='1')&(df.closing_odds__ok=='1')].copy().reset_index(drop=True); df['month']=df.date.str[:7]; X=base.build_static(df); assert X.shape[1]==63; combo=df.settle__actual_combo.astype(str); n=len(df); raw=np.full(n,np.nan); nm=np.full(n,np.nan); ns=np.full(n,np.nan); ag=np.full(n,np.nan); scores=np.full((n,len(base.COMBOS)),np.nan)
 def run(tm,sm,seed):
  tr=np.flatnonzero(tm.to_numpy()); te=np.flatnonzero(sm.to_numpy()); a,b,c,d,e=fit(X.iloc[tr],combo.iloc[tr],X.iloc[te],seed); raw[te]=a; nm[te]=b; ns[te]=c; ag[te]=d; scores[te]=e
 run(df.month=='2026-02',df.month=='2026-03',3450)
 for i,mo in enumerate(['2026-04','2026-05','2026-06'],1):run(df.month<mo,df.month==mo,3450+i)
 frozen=df.month<='2026-06'
 for i,mo in enumerate(['2026-07','2026-08'],4):run(frozen,df.month==mo,3450+i)
 df['raw_mean']=raw; df['norm_mean']=nm; df['norm_sd']=ns; df['agreement']=ag
 for k in KS:df[f'top{k}']=['' if not np.isfinite(scores[i]).any() else ';'.join(base.COMBOS[j] for j in np.argsort(-np.nan_to_num(scores[i],nan=-1))[:k]) for i in range(n)]
 march=df[df.month=='2026-03'].copy(); cand=[]
 for mode in ['raw_mean','norm_mean']:
  for qv in QS:
   cut=float(march[mode].quantile(qv))
   for ac in AGREES:
    for sdq in SDQS:
     sdcut=float(march.norm_sd.quantile(sdq))
     for k in KS:
      z=march[(march[mode]>=cut)&(march.agreement>=ac)&(march.norm_sd<=sdcut)]; _,m=block(z,k)
      if 30<=m['races']<=300:m.update(mode=mode,cut=cut,agreement_cut=ac,sd_cut=sdcut,sd_quantile=sdq,k=k); cand.append(m)
 if not cand:raise RuntimeError('no March candidates')
 ch=max(cand,key=lambda x:(x['roi_pct'],-x['races'])); mode=ch['mode']; cut=ch['cut']; ac=ch['agreement_cut']; sdcut=ch['sd_cut']; k=ch['k']
 def sel(ms):
  q=df[df.month.isin(ms)].copy(); return q[(q[mode]>=cut)&(q.agreement>=ac)&(q.norm_sd<=sdcut)]
 sh,hm=block(sel(['2026-04','2026-05','2026-06']),k); ss,sm=block(sel(['2026-07','2026-08']),k); assert not pd.concat([sh,ss]).race_code.isin(ex).any(); pd.concat([sh.assign(period='holdout'),ss.assign(period='shadow')]).to_csv(OUT,index=False,encoding='utf-8-sig'); cmb={'races':94+hm['races'],'hits':52+hm['hits'],'stake_yen':940000+hm['stake_yen'],'payout_yen':1622070+hm['payout_yen']}; cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']; dec='RESEARCH_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION'; out={'wave':'34e-normalized-margin','march_selection':ch,'holdout':hm,'shadow':sm,'combined':cmb,'overlap':0,'decision':dec}; OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 lines=['# Wave34e normalized prototype margin','',f"- March: {ch['races']}R / ROI {ch['roi_pct']:.3f}% / {mode} / agreement>={ac} / sdq={ch['sd_quantile']} / top{k}",f"- Apr-Jun: {hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen",f"- min month {hm['min_month_roi_pct']:.3f}% / red {hm['red_months']} / DD {hm['max_drawdown_yen']:,.0f}",f"- Jul-Aug shadow ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,}",f"- combined ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,}",f"- decision {dec}",'','## Monthly']+[f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,}" for mo,z in hm['monthly'].items()]; OUTM.write_text('\n'.join(lines)+'\n'); print('\n'.join(lines))
if __name__=='__main__':main()
