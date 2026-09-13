import json,numpy as np,pandas as pd
from pathlib import Path
import research_v289_3head_wave31_nonlinear_gate as b
import research_v289_3head_wave36_lda_stable_gate as w
S=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');C=Path('v288_operational_pre_replay_94_baseline_codes.csv');O=Path('research_v289_3head_wave36x_extended_learning.json');CUT=.365448

def E(x):
 x=x.copy();x['variant_return']=[b.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()];m=b.block(x);m['head_hits']=int(x.actual3.sum());m['head_rate']=m['head_hits']/len(x) if len(x) else 0;m['conversion']=m['hits']/m['head_hits'] if m['head_hits'] else 0;return m

def main():
 d=pd.read_csv(S,dtype=str).fillna('');
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(C,dtype=str).race_code.astype(str));
 if len(ex)!=94:raise RuntimeError('baseline guard')
 d=d[~d.race_code.astype(str).isin(ex)];d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];X=b.build_static(d);y=d.settle__actual_combo.astype(str);d['actual3']=y.str.startswith('3-').astype(int)
 if X.shape[1]!=63:raise RuntimeError('feature guard')
 def P(tr,te):
  a=np.flatnonzero(tr.to_numpy());z=np.flatnonzero(te.to_numpy());p,s=w.fit_predict(X.iloc[a],y.iloc[a],X.iloc[z]);q=d.iloc[z].copy();q['p3']=p;q['top5']=[';'.join(b.COMBOS[j] for j in np.argsort(-r)[:5]) for r in s];return q[q.p3>=CUT]
 e=[]
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:e.append(P(d.month<mo,d.month==mo))
 e=pd.concat(e);f=pd.concat([P(d.month<='2026-06',d.month==mo) for mo in ['2026-07','2026-08']]);out={'expanding_monthly':{mo:E(g) for mo,g in e.groupby('month')},'frozen_monthly':{mo:E(g) for mo,g in f.groupby('month')},'expanding_apr_aug':E(e),'expanding_jul_aug':E(e[e.month.isin(['2026-07','2026-08'])]),'frozen_jul_aug':E(f),'overlap':int(e.race_code.astype(str).isin(ex).sum())};ae=out['expanding_monthly']['2026-08'];af=out['frozen_monthly']['2026-08'];out['aug_learning_delta']={'races':ae['races']-af['races'],'hits':ae['hits']-af['hits'],'roi_points':ae['roi_pct']-af['roi_pct'],'profit_yen':ae['profit_yen']-af['profit_yen']};O.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
