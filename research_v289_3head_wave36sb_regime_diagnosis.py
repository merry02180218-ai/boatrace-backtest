from pathlib import Path
import json,numpy as np,pandas as pd
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36s_smooth_calibration as s
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv');BC=Path('v288_operational_pre_replay_94_baseline_codes.csv');OUT=Path('research_v289_3head_wave36sb_regime_diagnosis.json')
def ret(q): return np.array([base.dutch_return(r,str(r.top5).split(';')) for _,r in q.iterrows()],float)
def block(q):
 r=ret(q);hh=int(q.actual3.sum());hits=int((r>0).sum());return {'races':len(q),'head_hits':hh,'head_rate':hh/len(q) if len(q) else 0,'ticket_hits':hits,'conversion':hits/hh if hh else 0,'roi_pct':float(r.sum()/len(q)/100) if len(q) else 0,'profit_yen':int(r.sum()-len(q)*10000) if len(q) else 0,'median_positive_return_yen':float(np.median(r[r>0])) if np.any(r>0) else 0}
def family(name):
 n=name.lower()
 if 'st' in n:return 'ST'
 if 'motor' in n or 'モーター' in name:return 'motor'
 if 'boat' in n or 'ボート' in name:return 'boat'
 if '勝率' in name or '2連対率' in name or '3連対率' in name or '当地' in name:return 'racer_strength'
 if 'minus' in n:return 'relative_gap'
 return 'other'
def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str));d=d[~d.race_code.astype(str).isin(ex)].copy();d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True);d['month']=d.date.str[:7];d['actual']=d.settle__actual_combo.astype(str);d['actual3']=d.actual.str.startswith('3-').astype(int);X=base.build_static(d);y=d.actual
 if X.shape[1]!=63:raise RuntimeError('feature guard')
 march=s.predict_block(d,X,y,d.month=='2026-02',d.month=='2026-03');mc=s.fit_cal(march);cut=float(s.apply_params(pd.DataFrame({'raw_p3':[s.RAW_CUT]}),float(mc.coef_[0][0]),float(mc.intercept_[0]))[0]);oos={'2026-03':march};sel=[]
 for mo in ['2026-04','2026-05','2026-06']:
  q=s.predict_block(d,X,y,d.month<mo,d.month==mo);prior=sorted(oos)[-3:];c=s.fit_cal(pd.concat([oos[p] for p in prior],ignore_index=True));q['cal_p3']=s.apply_params(q,float(c.coef_[0][0]),float(c.intercept_[0]));z=q[q.cal_p3>=cut].copy();sel.append(z);oos[mo]=q
 z=pd.concat(sel,ignore_index=True).sort_values(['date','race_code']).reset_index(drop=True);mid=len(z)//2;z['half']=np.where(np.arange(len(z))<mid,'early','late')
 fmap=pd.DataFrame(X,index=d.index);key=d[['race_code']].copy();fs=pd.concat([key.reset_index(drop=True),fmap.reset_index(drop=True)],axis=1);z=z.merge(fs,on='race_code',how='left',validate='one_to_one')
 e=z[z.half=='early'];l=z[z.half=='late'];drifts=[]
 for c in X.columns:
  a=pd.to_numeric(e[c],errors='coerce');b=pd.to_numeric(l[c],errors='coerce');pool=pd.concat([a,b]);sd=float(pool.std(ddof=0));diff=float(b.mean()-a.mean()) if a.notna().any() and b.notna().any() else 0;drifts.append({'feature':c,'family':family(c),'early_mean':float(a.mean()),'late_mean':float(b.mean()),'std_effect':diff/sd if sd>0 else 0})
 drifts=sorted(drifts,key=lambda x:abs(x['std_effect']),reverse=True)
 fam={}
 for r in drifts: fam.setdefault(r['family'],[]).append(abs(r['std_effect']))
 fam={k:{'mean_abs_effect':float(np.mean(v)),'max_abs_effect':float(np.max(v))} for k,v in fam.items()}
 bands=[0,.4,.45,.5,.6,1.01];pb={}
 for h,g in z.groupby('half'):
  pb[h]={}
  for lo,hi in zip(bands[:-1],bands[1:]):
   q=g[(g.raw_p3>lo)&(g.raw_p3<=hi)];pb[h][f'({lo},{hi}]']=block(q)
 out={'wave':'36S-B-regime-diagnosis','rules_unchanged':True,'apr_jun':block(z),'early':block(e),'late':block(l),'top_feature_drifts':drifts[:20],'family_drift_summary':fam,'raw_p3_bands':pb,'raw_p3_mean':{'early':float(e.raw_p3.mean()),'late':float(l.raw_p3.mean())},'cal_p3_mean':{'early':float(e.cal_p3.mean()),'late':float(l.cal_p3.mean())},'feature_count':X.shape[1],'v288_overlap':int(z.race_code.astype(str).isin(ex).sum()),'september_forbidden':True}
 if out['v288_overlap']:raise RuntimeError('v288 overlap')
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
