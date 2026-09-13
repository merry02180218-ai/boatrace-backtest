from pathlib import Path
import json,numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');BC=Path('v288_operational_pre_replay_94_baseline_codes.csv');OUT=Path('research_v289_3head_wave36s_smooth_calibration.json');RAW_CUT=.365448;SHRINK=.50

def predict_block(d,X,y,trm,tem):
 tr=np.flatnonzero(trm.to_numpy());te=np.flatnonzero(tem.to_numpy());p,s=w36.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]);q=d.iloc[te].copy();q['raw_p3']=p;q['top5']=[';'.join(base.COMBOS[j] for j in np.argsort(-r)[:5]) for r in s];return q

def fit_cal(q):
 m=LogisticRegression(C=1e6,solver='lbfgs');m.fit(q[['raw_p3']],q.actual3);return m

def apply_params(q,coef,intercept):
 z=coef*q.raw_p3.to_numpy()+intercept;return 1/(1+np.exp(-z))

def metrics(q):
 x=q.copy();x['variant_return']=[base.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()];m=base.block(x);hh=int(x.actual3.sum());m['head_hits']=hh;m['head_rate']=hh/len(x) if len(x) else 0;m['conversion']=m['hits']/hh if hh else 0;m['max_drawdown_yen']=base.maxdd(x.sort_values(['date','race_code'])) if len(x) else 0;return m

def agg(df,months):return metrics(df[df.month.isin(months)])

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
 if X.shape[1]!=63:raise RuntimeError('feature guard')
 march=predict_block(d,X,y,d.month=='2026-02',d.month=='2026-03');mc=fit_cal(march);mcoef=float(mc.coef_[0][0]);mint=float(mc.intercept_[0]);cal_cut=float(apply_params(pd.DataFrame({'raw_p3':[RAW_CUT]}),mcoef,mint)[0])
 oos={'2026-03':march};months=['2026-04','2026-05','2026-06','2026-07','2026-08'];roll=[];shr=[];raw=[];meta={}
 for mo in months:
  q=predict_block(d,X,y,d.month<mo,d.month==mo);prior=sorted(oos.keys())[-3:];pool=pd.concat([oos[p] for p in prior],ignore_index=True);c=fit_cal(pool);coef=float(c.coef_[0][0]);inter=float(c.intercept_[0]);scoef=SHRINK*mcoef+(1-SHRINK)*coef;sinter=SHRINK*mint+(1-SHRINK)*inter
  q['roll_p3']=apply_params(q,coef,inter);q['shrink_p3']=apply_params(q,scoef,sinter);qr=q[q.roll_p3>=cal_cut].copy();qs=q[q.shrink_p3>=cal_cut].copy();qraw=q[q.raw_p3>=RAW_CUT].copy();roll.append(qr);shr.append(qs);raw.append(qraw);meta[mo]={'prior_oos_months':prior,'pool_rows':len(pool),'coef':coef,'intercept':inter,'shrink_weight_to_march':SHRINK,'selected_roll':len(qr),'selected_shrink':len(qs),'selected_raw':len(qraw)};oos[mo]=q
 rld=pd.concat(roll,ignore_index=True);shd=pd.concat(shr,ignore_index=True);rwd=pd.concat(raw,ignore_index=True);pr=['2026-04','2026-05','2026-06'];shadow=['2026-07','2026-08']
 out={'wave':'36S-smooth-calibration','raw_cut':RAW_CUT,'calibrated_cut_from_march':cal_cut,'shrink_weight_to_march':SHRINK,'meta':meta,'rolling_monthly':{mo:metrics(g) for mo,g in rld.groupby('month')},'shrink_monthly':{mo:metrics(g) for mo,g in shd.groupby('month')},'raw_monthly':{mo:metrics(g) for mo,g in rwd.groupby('month')},'rolling_apr_jun':agg(rld,pr),'shrink_apr_jun':agg(shd,pr),'raw_apr_jun':agg(rwd,pr),'rolling_jul_aug':agg(rld,shadow),'shrink_jul_aug':agg(shd,shadow),'raw_jul_aug':agg(rwd,shadow),'overlap_rolling':int(rld.race_code.astype(str).isin(ex).sum()),'overlap_shrink':int(shd.race_code.astype(str).isin(ex).sum())}
 if out['overlap_rolling'] or out['overlap_shrink']:raise RuntimeError('v288 overlap')
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
