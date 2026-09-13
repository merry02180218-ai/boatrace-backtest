from pathlib import Path
import json,numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');BC=Path('v288_operational_pre_replay_94_baseline_codes.csv');OUT=Path('research_v289_3head_wave36c_monthly_calibration.json');RAW_CUT=.365448

def predict_block(d,X,y,trm,tem):
 tr=np.flatnonzero(trm.to_numpy());te=np.flatnonzero(tem.to_numpy());p,s=w36.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]);q=d.iloc[te].copy();q['raw_p3']=p;q['top5']=[';'.join(base.COMBOS[j] for j in np.argsort(-r)[:5]) for r in s];return q

def fit_cal(q):
 m=LogisticRegression(C=1e6,solver='lbfgs');m.fit(q[['raw_p3']],q.actual3);return m

def metrics(q):
 x=q.copy();x['variant_return']=[base.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()];m=base.block(x);hh=int(x.actual3.sum());m['head_hits']=hh;m['head_rate']=hh/len(x) if len(x) else 0;m['conversion']=m['hits']/hh if hh else 0;m['max_drawdown_yen']=base.maxdd(x.sort_values(['date','race_code'])) if len(x) else 0;return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
 if X.shape[1]!=63:raise RuntimeError('feature guard')
 march=predict_block(d,X,y,d.month=='2026-02',d.month=='2026-03');cal=fit_cal(march);cal_cut=float(cal.predict_proba(pd.DataFrame({'raw_p3':[RAW_CUT]}))[:,1][0])
 months=['2026-04','2026-05','2026-06','2026-07','2026-08'];prev=march;calibrated=[];raw=[];calmeta={}
 for mo in months:
  q=predict_block(d,X,y,d.month<mo,d.month==mo);c=fit_cal(prev);q['cal_p3']=c.predict_proba(q[['raw_p3']])[:,1];qc=q[q.cal_p3>=cal_cut].copy();qr=q[q.raw_p3>=RAW_CUT].copy();calibrated.append(qc);raw.append(qr);calmeta[mo]={'prior_month':str(prev.month.iloc[0]),'coef':float(c.coef_[0][0]),'intercept':float(c.intercept_[0]),'selected_cal':len(qc),'selected_raw':len(qr)};prev=q
 cdf=pd.concat(calibrated,ignore_index=True);rdf=pd.concat(raw,ignore_index=True)
 out={'wave':'36C-monthly-platt','raw_cut':RAW_CUT,'calibrated_cut_from_march':cal_cut,'calibration_meta':calmeta,'calibrated_monthly':{mo:metrics(g) for mo,g in cdf.groupby('month')},'raw_monthly':{mo:metrics(g) for mo,g in rdf.groupby('month')}}
 out['calibrated_apr_jun']=metrics(cdf[cdf.month.isin(['2026-04','2026-05','2026-06'])]);out['raw_apr_jun']=metrics(rdf[rdf.month.isin(['2026-04','2026-05','2026-06'])]);out['calibrated_jul_aug']=metrics(cdf[cdf.month.isin(['2026-07','2026-08'])]);out['raw_jul_aug']=metrics(rdf[rdf.month.isin(['2026-07','2026-08'])]);out['overlap']=int(cdf.race_code.astype(str).isin(ex).sum())
 if out['overlap']:raise RuntimeError('v288 overlap')
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
