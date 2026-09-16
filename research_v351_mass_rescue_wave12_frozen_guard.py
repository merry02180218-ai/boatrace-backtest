#!/usr/bin/env python3
"""Wave12: result-independent frozen one-replace guard for v351 low-mass band.

Research only. September 2026 outcomes hard excluded. HEAD model is untouched.
Threshold is chosen on May using a Feb-Apr model, then the opponent model is
refit on Feb-May and evaluated once on frozen June.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct
import run_v326_1head_ticketaware_exhibition as v326

SRC='analysis_v351_mass_rescue_wave10_rows.csv'
SCHEMAS={'lap+turn+straight','lap+turn'}
LO,HI=.350,.375
INNER_END='20260501'; TRAIN_END='20260601'; TEST_END='20260701'
THRESHOLDS=[-.10,-.075,-.05,-.025,0,.025,.05,.075,.10,.15,.20,.25]
FEATURES=['boat','selected','ex','st','ex_rank','st_rank','turn_rank','straight_rank','orig_avg_rank']

def combo(x):
 p=str(x).replace('>','-').replace(' ','').split('-')
 return tuple(map(int,p[:3])) if len(p)>=3 and all(z.isdigit() for z in p[:3]) else None

def tickets(x):
 out=[]
 for q in str(x).replace('|',';').replace(',',';').split(';'):
  c=combo(q)
  if c and c[0]==1: out.append(c)
 return out

def model():
 return Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=2000,class_weight='balanced'))])

def build_features(base):
 wanted=set(base.race_code); days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted}); dayset=set(days); last=max(days)
 sums=defaultdict(list); allv=[]; feat={}; d=date(2025,10,1)
 while d<=last:
  ymd=d.strftime('%Y/%m/%d'); strows=rows(f'data/previews/stt/{ymd}.csv'); bias=v326.st_bias(sums,allv)
  if d in dayset:
   tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv')); stt=v326.bycode(strows); orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
   for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(2,7):
     if b in ex and b in st:
      o=os.get(b,{})
      feat[(code,b)]={'ex':ex[b],'st':st[b],'turn':o.get('turn',np.nan),'straight':o.get('straight',np.nan),'orig_avg':o.get('avg',np.nan)}
  v326.update_st(strows,sums,allv); d+=timedelta(days=1)
 rec=[]
 for _,r in base.iterrows():
  a=combo(r.actual_combo); ts=tickets(r.tickets)
  if not a or a[0]!=1 or not ts: continue  # opponent labels exist only when HEAD actually hit
  actual=set(a[1:]); cur=set(ts[0][1:])
  for b in range(2,7):
   f=feat.get((r.race_code,b))
   if f is None: continue
   rec.append({'race_code':r.race_code,'schema':r.schema,'jcd':int(r.jcd),'boat':b,'selected':int(b in cur),'target':int(b in actual),**f})
 z=pd.DataFrame(rec)
 if z.empty: raise RuntimeError('no feature rows')
 z['ex_rank']=z.groupby('race_code').ex.rank(method='average',ascending=True); z['st_rank']=z.groupby('race_code').st.rank(method='average',ascending=True)
 for c in ['turn','straight','orig_avg']: z[c+'_rank']=z.groupby('race_code')[c].rank(method='average',ascending=True)
 return z

def proposals(scored,base):
 bm=base.set_index('race_code'); out=[]
 for code,g in scored.groupby('race_code'):
  if len(g)!=5 or code not in bm.index: continue
  r=bm.loc[code]; a=combo(r.actual_combo); ts=tickets(r.tickets)
  if not a or a[0]!=1 or not ts: continue
  actual=set(a[1:]); cur=set(ts[0][1:]); sg=g[g.selected.eq(1)].sort_values('p',ascending=False); og=g[g.selected.eq(0)].sort_values('p',ascending=False)
  if len(sg)!=2 or og.empty: continue
  keep=int(sg.iloc[0].boat); drop=int(sg.iloc[1].boat); rep=int(og.iloc[0].boat); proposal={keep,rep}
  out.append({'race_code':code,'schema':r.schema,'jcd':int(r.jcd),'baseline_hit':int(cur==actual),'proposal_hit':int(proposal==actual),'margin':float(og.iloc[0].p-sg.iloc[1].p),'keep_boat':keep,'drop_boat':drop,'replacement':rep,'current_pair':'-'.join(map(str,sorted(cur))),'proposal_pair':'-'.join(map(str,sorted(proposal))),'actual_pair':'-'.join(map(str,sorted(actual)))})
 return pd.DataFrame(out)

def eval_threshold(q,th):
 ov=q.margin>=th; final=np.where(ov,q.proposal_hit,q.baseline_hit)
 rescue=int((ov&(q.baseline_hit==0)&(q.proposal_hit==1)).sum()); damage=int((ov&(q.baseline_hit==1)&(q.proposal_hit==0)).sum())
 return {'threshold':th,'R':len(q),'overrides':int(ov.sum()),'baseline_hits':int(q.baseline_hit.sum()),'final_hits':int(final.sum()),'delta_hits':int(final.sum()-q.baseline_hit.sum()),'rescues':rescue,'damages':damage,'net_rescue':rescue-damage}

def main():
 base=pd.read_csv(SRC,dtype={'race_code':str}); base.race_code=base.race_code.astype(str).str.zfill(12)
 if (base.race_code.str[:8]>='20260901').any(): raise RuntimeError('September outcome row detected')
 base=base[(base.opp_mass>=LO)&(base.opp_mass<HI)&base.schema.isin(SCHEMAS)].copy()
 if base.empty: raise RuntimeError('main-schema low-mass band empty')
 z=build_features(base)
 # May threshold selection: fit Feb-Apr only, score May once.
 inner=z[z.race_code.str[:8]<INNER_END].copy(); may=z[(z.race_code.str[:8]>=INNER_END)&(z.race_code.str[:8]<TRAIN_END)].copy()
 if inner.race_code.nunique()<30 or may.empty: raise RuntimeError('insufficient inner train/May validation')
 m1=model(); m1.fit(inner[FEATURES],inner.target); may['p']=m1.predict_proba(may[FEATURES])[:,1]; mq=proposals(may,base)
 grid=pd.DataFrame([eval_threshold(mq,t) for t in THRESHOLDS])
 # Deterministic train-only choice: max net rescue, then max final hits, then fewer overrides, then higher threshold.
 best=grid.sort_values(['net_rescue','final_hits','overrides','threshold'],ascending=[False,False,True,False]).iloc[0]; chosen=float(best.threshold)
 # Refit through May; June is untouched until now.
 train=z[z.race_code.str[:8]<TRAIN_END].copy(); june=z[(z.race_code.str[:8]>=TRAIN_END)&(z.race_code.str[:8]<TEST_END)].copy()
 m2=model(); m2.fit(train[FEATURES],train.target); june['p']=m2.predict_proba(june[FEATURES])[:,1]; jq=proposals(june,base)
 if jq.empty: raise RuntimeError('June frozen set empty')
 jq['override']=(jq.margin>=chosen).astype(int); jq['final_hit']=np.where(jq.override.eq(1),jq.proposal_hit,jq.baseline_hit); jq['rescue']=((jq.override==1)&(jq.baseline_hit==0)&(jq.proposal_hit==1)).astype(int); jq['damage']=((jq.override==1)&(jq.baseline_hit==1)&(jq.proposal_hit==0)).astype(int)
 jq.to_csv('analysis_v351_mass_rescue_wave12_june.csv',index=False,encoding='utf-8-sig'); grid.to_csv('analysis_v351_mass_rescue_wave12_may_thresholds.csv',index=False,encoding='utf-8-sig')
 out=[{'scope':'ALL','key':'ALL',**eval_threshold(jq,chosen)}]
 for c in ['schema','jcd']:
  for k,g in jq.groupby(c): out.append({'scope':c,'key':str(k),**eval_threshold(g,chosen)})
 s=pd.DataFrame(out); s.to_csv('analysis_v351_mass_rescue_wave12_summary.csv',index=False,encoding='utf-8-sig')
 print('SEPTEMBER_OUTCOMES_USED False'); print('PRODUCTION_CHANGED False'); print('HEAD_EXHIBITION_DIRECT_FEATURE False'); print('LOW_MASS_BAND',LO,HI); print('SCHEMAS',sorted(SCHEMAS))
 print('INNER_TRAIN_R',inner.race_code.nunique(),'MAY_R',len(mq),'FULL_TRAIN_R',train.race_code.nunique(),'JUNE_R',len(jq)); print('CHOSEN_THRESHOLD_FROM_MAY',chosen)
 print('\nMAY_THRESHOLD_GRID'); print(grid.to_string(index=False)); print('\nJUNE_FROZEN'); print(s.to_string(index=False))
if __name__=='__main__': main()
