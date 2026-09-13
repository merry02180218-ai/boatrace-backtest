from pathlib import Path
import json,numpy as np,pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');BC=Path('v288_operational_pre_replay_94_baseline_codes.csv');OUT=Path('research_v289_3head_wave36x.json');CUT=.365448

def score(d,X,y,trm,tem):
 tr=np.flatnonzero(trm.to_numpy());te=np.flatnonzero(tem.to_numpy());p,s=w36.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]);q=d.iloc[te].copy();q['p3']=p;q['top5']=[';'.join(base.COMBOS[j] for j in np.argsort(-r)[:5]) for r in s];return q[q.p3>=CUT].copy()

def metrics(q):
 x=q.copy();x['variant_return']=[base.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()];m=base.block(x);hh=int(x.actual3.sum());m['head_hits']=hh;m['head_rate']=hh/len(x) if len(x) else 0;m['conversion']=m['hits']/hh if hh else 0;m['max_drawdown_yen']=base.maxdd(x.sort_values(['date','race_code'])) if len(x) else 0;return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
 if X.shape[1]!=63:raise RuntimeError('feature guard')
 exp=[]
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:exp.append(score(d,X,y,d.month<mo,d.month==mo))
 exp=pd.concat(exp,ignore_index=True);fro=pd.concat([score(d,X,y,d.month<='2026-06',d.month==mo) for mo in ['2026-07','2026-08']],ignore_index=True)
 out={'wave':'36X','gate':CUT,'k':5,'expanding_monthly':{mo:metrics(g) for mo,g in exp.groupby('month')},'frozen_jul_aug_monthly':{mo:metrics(g) for mo,g in fro.groupby('month')}};out['expanding_apr_aug']=metrics(exp);out['expanding_jul_aug']=metrics(exp[exp.month.isin(['2026-07','2026-08'])]);out['frozen_jul_aug']=metrics(fro);a=out['expanding_monthly']['2026-08'];b=out['frozen_jul_aug_monthly']['2026-08'];out['aug_delta_after_learning_july']={'races':a['races']-b['races'],'hits':a['hits']-b['hits'],'roi_points':a['roi_pct']-b['roi_pct'],'profit_yen':a['profit_yen']-b['profit_yen']};out['overlap']=int(exp.race_code.astype(str).isin(ex).sum());OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
