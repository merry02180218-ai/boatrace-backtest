from pathlib import Path
import csv,io,json,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score,accuracy_score
import research_v289_3head_wave31_nonlinear_gate as base
import research_v289_3head_wave36_lda_stable_gate as w36

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); OUT=Path('research_v289_3head_wave44_attack_mode.json')
CUT=.365448; BASEURL='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/data/results/realtime/'
MODES=['MAKURI','MAKURI_SASHI']

def normcode(x):
 s=''.join(c for c in str(x or '') if c.isdigit()); return s.zfill(12) if s else ''
def normmode(x):
 s=str(x or '').replace(' ','').replace('　','').strip()
 if s=='まくり': return 'MAKURI'
 if s=='まくり差し': return 'MAKURI_SASHI'
 return 'OTHER'
def fetch_day(ds):
 ymd=ds.replace('-','/')+'.csv'
 try:
  with urllib.request.urlopen(BASEURL+ymd,timeout=30) as r: txt=r.read().decode('utf-8-sig')
  return {normcode(z.get('レースコード')):normmode(z.get('決まり手')) for z in csv.DictReader(io.StringIO(txt))}
 except Exception:return {}
def aligned_probs(model,X):
 p=model.predict_proba(X); out=np.zeros((len(X),len(base.COMBOS)))
 for j,c in enumerate(model.classes_):
  if c in base.COMBOS: out[:,base.COMBOS.index(c)]=p[:,j]
 return out
def fit_attack(train,Xtr,test,Xte):
 m=train.actual3.eq(1)&train.attack_mode.isin(MODES); idx=np.flatnonzero(m.to_numpy())
 if len(idx)<30: raise RuntimeError('insufficient attack-mode training rows')
 ym=(train.attack_mode.iloc[idx]=='MAKURI_SASHI').astype(int)
 mode=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15,solver='lbfgs'))
 mode.fit(Xtr.iloc[idx],ym); ps=mode.predict_proba(Xte)[:,1]
 scores=[]
 for md in MODES:
  mm=m&(train.attack_mode==md); ii=np.flatnonzero(mm.to_numpy())
  clf=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15,solver='lbfgs'))
  clf.fit(Xtr.iloc[ii],train.actual.iloc[ii]); scores.append(aligned_probs(clf,Xte))
 mix=(1-ps[:,None])*scores[0]+ps[:,None]*scores[1]
 return ps,mix,mode

def rankstr(score): return [';'.join(base.COMBOS[j] for j in np.argsort(-r)) for r in score]
def hitset(q,col): return {(str(r.race_code),str(r.actual)) for _,r in q.iterrows() if r.actual3==1 and str(r.actual) in str(r[col]).split(';')[:5]}
def rankblock(q,col):
 hh=int(q.actual3.sum()); hs=len(hitset(q,col)); return {'races':len(q),'head_hits':hh,'top5_hits':hs,'top5_rate_given_head':hs/hh if hh else 0.}
def topology(q):
 z=q[(q.actual3==1)&q.attack_mode.isin(MODES)].copy(); out={}
 for md,g in z.groupby('attack_mode'):
  sec=g.actual.str.split('-').str[1]; third=g.actual.str.split('-').str[2]; pair=sec+'-'+third
  out[md]={'rows':len(g),'second_counts':sec.value_counts().to_dict(),'third_counts':third.value_counts().to_dict(),'pair_counts':pair.value_counts().head(10).to_dict()}
 return out
def money(q,col):
 z=q.copy(); z['variant_return']=[base.dutch_return(r,str(r[col]).split(';')[:5]) for _,r in z.iterrows()]; m=base.block(z); mm={mo:base.block(g) for mo,g in z.groupby('month')}; m.update({'monthly':mm,'min_month_roi_pct':min((x['roi_pct'] for x in mm.values()),default=None),'red_months':sum(x['roi_pct']<100 for x in mm.values()),'max_drawdown_yen':base.maxdd(z.sort_values(['date','race_code']))}); return m

def main():
 d=pd.read_csv(SRC,dtype=str).fillna('');
 if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
 ex=set(pd.read_csv(BC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]; d['actual']=d.settle__actual_combo.astype(str); d['actual3']=d.actual.str.startswith('3-').astype(int); d['code_norm']=d.race_code.map(normcode)
 days=sorted(d.date.unique()); maps={}
 with ThreadPoolExecutor(max_workers=12) as pool:
  fut={pool.submit(fetch_day,x):x for x in days}
  for f in as_completed(fut): maps[fut[f]]=f.result()
 d['attack_mode']=[maps.get(dt,{}).get(cd,'OTHER') for dt,cd in zip(d.date,d.code_norm)]
 X=base.build_static(d)
 if X.shape[1]!=63: raise RuntimeError('feature guard')
 # March frozen Wave36 and attack-mode OOS: Feb -> Mar.
 tr=d.month=='2026-02'; te=d.month=='2026-03'; ti=np.flatnonzero(tr.to_numpy()); ei=np.flatnonzero(te.to_numpy())
 p3,oldsc=w36.fit_predict(X.iloc[ti],d.actual.iloc[ti],X.iloc[ei]); ps,newsc,modeclf=fit_attack(d.iloc[ti].reset_index(drop=True),X.iloc[ti].reset_index(drop=True),d.iloc[ei].reset_index(drop=True),X.iloc[ei].reset_index(drop=True))
 mar=d.iloc[ei].copy(); mar['p3']=p3; mar['old_rank']=rankstr(oldsc); mar['new_rank']=rankstr(newsc); mar['mode_psashi']=ps; sel=mar[mar.p3>=CUT].sort_values(['date','race_code']).reset_index(drop=True); old=hitset(sel,'old_rank'); new=hitset(sel,'new_rank'); mid=len(sel)//2
 early=sel.iloc[:mid]; late=sel.iloc[mid:]
 known=mar[(mar.actual3==1)&mar.attack_mode.isin(MODES)].copy(); kidx=known.index.to_numpy()-ei[0] if len(known) else np.array([],int)
 # ei are contiguous by month in this source; use explicit position mapping for safety.
 pos={idx:j for j,idx in enumerate(ei)}; kk=np.array([pos[i] for i in known.index],int) if len(known) else np.array([],int)
 yk=(known.attack_mode=='MAKURI_SASHI').astype(int).to_numpy(); pred=(ps[kk]>=.5).astype(int) if len(kk) else np.array([],int)
 auc=float(roc_auc_score(yk,ps[kk])) if len(set(yk))==2 else None; acc=float(accuracy_score(yk,pred)) if len(yk) else None
 march={'selected_races':len(sel),'old':rankblock(sel,'old_rank'),'new':rankblock(sel,'new_rank'),'retained':len(old&new),'lost':len(old-new),'rescued':len(new-old),'net':len(new)-len(old),'early_old':rankblock(early,'old_rank'),'early_new':rankblock(early,'new_rank'),'late_old':rankblock(late,'old_rank'),'late_new':rankblock(late,'new_rank'),'mode_auc':auc,'mode_accuracy':acc,'known_mode_head3_rows':len(known)}
 passed=(march['net']>=1 and march['lost']<=2 and march['early_new']['top5_hits']>=march['early_old']['top5_hits'] and march['late_new']['top5_hits']>=march['late_old']['top5_hits'])
 out={'wave':'44-attack-mode','label_source':'BoatraceCSV results/realtime 決まり手; evaluation/training target only','feature_count':63,'feb_topology':topology(d[d.month=='2026-02']),'march_topology':topology(d[d.month=='2026-03']),'march_oos':march,'march_gate_pass':passed,'v288_overlap':0,'september_forbidden':True}
 if passed:
  frames=[]
  for mo in ['2026-04','2026-05','2026-06','2026-07','2026-08']:
   tr=d.month<mo; te=d.month==mo; ti=np.flatnonzero(tr.to_numpy()); ei=np.flatnonzero(te.to_numpy()); p,osc=w36.fit_predict(X.iloc[ti],d.actual.iloc[ti],X.iloc[ei]); _,nsc,_=fit_attack(d.iloc[ti].reset_index(drop=True),X.iloc[ti].reset_index(drop=True),d.iloc[ei].reset_index(drop=True),X.iloc[ei].reset_index(drop=True)); q=d.iloc[ei].copy(); q['p3']=p; q['old_rank']=rankstr(osc); q['new_rank']=rankstr(nsc); frames.append(q[q.p3>=CUT])
  ev=pd.concat(frames,ignore_index=True); pristine=ev[ev.month.isin(['2026-04','2026-05','2026-06'])]; shadow=ev[ev.month.isin(['2026-07','2026-08'])]
  pm=money(pristine,'new_rank'); om=money(pristine,'old_rank'); sm=money(shadow,'new_rank'); ov=int(ev.race_code.astype(str).isin(ex).sum());
  if ov: raise RuntimeError('v288 overlap')
  cmb={'races':94+pm['races'],'hits':52+pm['hits'],'stake_yen':940000+pm['stake_yen'],'payout_yen':1622070+pm['payout_yen']}; cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
  out.update({'apr_jun_old_money':om,'apr_jun_new_money':pm,'jul_aug_nonpristine':sm,'combined_baseline_plus_addon':cmb,'v288_overlap':ov,'decision':'RESEARCH_CANDIDATE' if pm['roi_pct']>=om['roi_pct'] and pm['red_months']<=1 else 'NO_ADOPTION'})
 else: out['decision']='NO_ADOPTION_MARCH_GATE'
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
