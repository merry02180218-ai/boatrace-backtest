from pathlib import Path
import json,numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');BC=Path('v288_operational_pre_replay_94_baseline_codes.csv');OUT=Path('research_v289_3head_wave36sc_motor_robustness.json');RAW_CUT=.365448

def predict_block(d,X,y,trm,tem):
 tr=np.flatnonzero(trm.to_numpy());te=np.flatnonzero(tem.to_numpy());p,s=w36.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]);q=d.iloc[te].copy();q['raw_p3']=p;q['top5']=[';'.join(base.COMBOS[j] for j in np.argsort(-r)[:5]) for r in s];return q

def fit_cal(q):
 m=LogisticRegression(C=1e6,solver='lbfgs');m.fit(q[['raw_p3']],q.actual3);return m

def apply_cal(q,m):
 z=float(m.coef_[0][0])*q.raw_p3.to_numpy()+float(m.intercept_[0]);return 1/(1+np.exp(-z))

def metrics(q):
 x=q.copy();x['variant_return']=[base.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()];m=base.block(x);hh=int(x.actual3.sum());m['head_hits']=hh;m['head_rate']=hh/len(x) if len(x) else 0;m['conversion']=m['hits']/hh if hh else 0;m['max_drawdown_yen']=base.maxdd(x.sort_values(['date','race_code'])) if len(x) else 0;return m

def zfit(s,ref):
 mu=float(ref.mean());sd=float(ref.std(ddof=0));return (s-mu)/(sd if sd>1e-12 else 1),mu,sd

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
 if X.shape[1]!=63:raise RuntimeError('feature guard')
 # composites use only existing pre-deadline static fields; positive = boat3 advantage
 racer_cols=[c for c in X.columns if c.startswith('b3_minus_') and any(k in c for k in ['全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','当地3連対率'])]
 motor_cols=[c for c in X.columns if c.startswith('b3_minus_') and any(k in c for k in ['モーター2連対率','モーター3連対率'])]
 if not racer_cols or not motor_cols:raise RuntimeError('composite columns missing')
 feb=d.month=='2026-02';mar=d.month=='2026-03';march=predict_block(d,X,y,feb,mar);mc=fit_cal(march);march['cal_p3']=apply_cal(march,mc);cal_cut=float(1/(1+np.exp(-(float(mc.coef_[0][0])*RAW_CUT+float(mc.intercept_[0])))))
 # Standardization frozen from Feb only. Composite is mean standardized relative gaps.
 rz=[];mz=[];stats={}
 for c in racer_cols:
  z,mu,sd=zfit(pd.to_numeric(X[c],errors='coerce').fillna(pd.to_numeric(X.loc[feb,c],errors='coerce').median()),pd.to_numeric(X.loc[feb,c],errors='coerce').dropna());rz.append(z);stats[c]=[mu,sd]
 for c in motor_cols:
  z,mu,sd=zfit(pd.to_numeric(X[c],errors='coerce').fillna(pd.to_numeric(X.loc[feb,c],errors='coerce').median()),pd.to_numeric(X.loc[feb,c],errors='coerce').dropna());mz.append(z);stats[c]=[mu,sd]
 d['racer_adv']=pd.concat(rz,axis=1).mean(axis=1);d['motor_adv']=pd.concat(mz,axis=1).mean(axis=1)
 march['racer_adv']=d.loc[march.index,'racer_adv'];march['motor_adv']=d.loc[march.index,'motor_adv']
 # predeclared small grid, chosen on March head stability only: maximize head rate, then retain races, no payout/ROI.
 settings=[]
 for rq in [.50,.60,.70]:
  rcut=float(d.loc[feb,'racer_adv'].quantile(rq))
  for mq in [.30,.40,.50]:
   mcut=float(d.loc[feb,'motor_adv'].quantile(mq))
   for penalty in [.03,.05,.08]:
    adj=march.cal_p3-penalty*((march.racer_adv>=rcut)&(march.motor_adv<=mcut)).astype(float);sel=march[adj>=cal_cut];settings.append({'racer_q':rq,'motor_q':mq,'penalty':penalty,'racer_cut':rcut,'motor_cut':mcut,'march_races':len(sel),'march_head_rate':float(sel.actual3.mean()) if len(sel) else 0})
 viable=[s for s in settings if s['march_races']>=int(.85*len(march[march.cal_p3>=cal_cut]))];best=sorted(viable,key=lambda s:(s['march_head_rate'],s['march_races'],-s['penalty']),reverse=True)[0]
 oos={'2026-03':march};chosen=[];raw=[];meta={}
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
  q=predict_block(d,X,y,d.month<mo,d.month==mo);prior=sorted(oos.keys())[-3:];pool=pd.concat([oos[p] for p in prior],ignore_index=True);c=fit_cal(pool);q['cal_p3']=apply_cal(q,c);q['racer_adv']=d.loc[q.index,'racer_adv'];q['motor_adv']=d.loc[q.index,'motor_adv'];mismatch=(q.racer_adv>=best['racer_cut'])&(q.motor_adv<=best['motor_cut']);q['mod_p3']=q.cal_p3-best['penalty']*mismatch.astype(float);chosen.append(q[q.mod_p3>=cal_cut].copy());raw.append(q[q.cal_p3>=cal_cut].copy());meta[mo]={'prior':prior,'mismatch_count':int(mismatch.sum())};oos[mo]=q
 cd=pd.concat(chosen,ignore_index=True);rd=pd.concat(raw,ignore_index=True);pr=['2026-04','2026-05','2026-06'];sh=['2026-07','2026-08']
 def agg(z,ms):return metrics(z[z.month.isin(ms)])
 out={'wave':'36S-C-motor-robustness','feature_count':63,'racer_cols':racer_cols,'motor_cols':motor_cols,'cal_cut':cal_cut,'selection_basis':'March OOS head rate only; no payout/ROI','candidate_settings':settings,'chosen':best,'monthly':{mo:metrics(g) for mo,g in cd.groupby('month')},'apr_jun':agg(cd,pr),'jul_aug':agg(cd,sh),'wave36s_apr_jun':agg(rd,pr),'wave36s_jul_aug':agg(rd,sh),'meta':meta,'v288_overlap':int(cd.race_code.astype(str).isin(ex).sum()),'september_forbidden':True}
 if out['v288_overlap']:raise RuntimeError('v288 overlap')
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
