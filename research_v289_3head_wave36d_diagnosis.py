from pathlib import Path
import json,numpy as np,pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');BC=Path('v288_operational_pre_replay_94_baseline_codes.csv');OUT=Path('research_v289_3head_wave36d_diagnosis.json');CUT=.365448

def score(d,X,y,mo):
 tr=np.flatnonzero((d.month<mo).to_numpy());te=np.flatnonzero((d.month==mo).to_numpy());p,s=w36.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]);q=d.iloc[te].copy();q['p3']=p;q['top5']=[';'.join(base.COMBOS[j] for j in np.argsort(-r)[:5]) for r in s];return q[q.p3>=CUT].copy()
def metr(q):
 x=q.copy();x['variant_return']=[base.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()];m=base.block(x);m['head_hits']=int(x.actual3.sum());m['head_rate']=float(x.actual3.mean());m['conversion']=m['hits']/m['head_hits'] if m['head_hits'] else 0;m['p3_mean']=float(x.p3.mean());m['p3_median']=float(x.p3.median());wins=x.loc[x.variant_return>0,'variant_return'];m['winning_return_mean']=float(wins.mean()) if len(wins) else 0;m['winning_return_median']=float(wins.median()) if len(wins) else 0;return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
 if X.shape[1]!=63 or d.date.max()>'2026-08-31':raise RuntimeError('guard')
 qs=[]
 for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:qs.append(score(d,X,y,mo))
 z=pd.concat(qs);monthly={mo:metr(g) for mo,g in z.groupby('month')}
 # p3 calibration bands
 z['pband']=pd.cut(z.p3,[CUT,.40,.45,.50,.60,1.01],include_lowest=True).astype(str);bands={}
 for (mo,b),g in z.groupby(['month','pband'],observed=True):bands.setdefault(mo,{})[b]={'races':len(g),'head_rate':float(g.actual3.mean()),'conversion':float(sum(g.apply(lambda r:r.actual in str(r.top5).split(';'),axis=1)) / max(1,int(g.actual3.sum())))}
 # static feature drift among selected races vs Apr-May reference
 xn=X.loc[z.index].apply(pd.to_numeric,errors='coerce');ref=xn[z.month.isin(['2026-04','2026-05'])];mu=ref.mean();sd=ref.std().replace(0,np.nan);drift={}
 for mo in ['2026-06','2026-07','2026-08']:
  g=xn[z.month==mo];v=((g.mean()-mu)/sd).abs().sort_values(ascending=False).head(12);drift[mo]=[{ 'feature':str(k),'abs_std_shift':float(vv)} for k,vv in v.items() if np.isfinite(vv)]
 # venue mix using race_code prefix if explicit venue column absent
 venue_col=next((c for c in ['場コード','jcd','venue_code','stadium_code'] if c in z.columns),None);venues={}
 if venue_col:
  for mo,g in z.groupby('month'):venues[mo]=g[venue_col].value_counts(normalize=True).head(10).to_dict()
 out={'wave':'36D','monthly':monthly,'p3_bands':bands,'feature_drift_vs_apr_may':drift,'venue_column':venue_col,'venue_mix':venues,'overlap':int(z.race_code.astype(str).isin(ex).sum()),'note':'diagnostic only; no outcome-derived tuning'};OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
