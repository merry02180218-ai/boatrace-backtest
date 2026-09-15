#!/usr/bin/env python3
"""Historical-only v351 opponent-pair ranking audit.
Hard excludes September 2026 outcomes. Builds per-boat causal exhibition features,
walk-forward OOF ranks boats 2..6, then uses a final temporal holdout.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows
from backtest_v51_lane_corrected_tickets import corrected_direct,ff
import run_v326_1head_ticketaware_exhibition as v326

SCHEMAS={'lap+turn+straight','lap+turn','half+turn+straight','base'}
FEATURES=['boat','ex','st','turn','straight','orig_avg']
HOLDOUT_START='20260701'

def parse_combo(x):
 p=str(x).replace('>','-').replace(' ','').split('-')
 return tuple(map(int,p[:3])) if len(p)>=3 and all(z.isdigit() for z in p[:3]) else None

def main():
 base=pd.read_csv('analysis_v351_schema_correct_rebuild.csv',dtype={'race_code':str})
 base.race_code=base.race_code.astype(str).str.zfill(12)
 # Non-negotiable result blind guard.
 base=base[(base.race_code.str[:8]<'20260901')&base.schema.isin(SCHEMAS)&base.schema_ready.eq(1)].copy()
 actual_col=next((c for c in ['actual_combo','actual','result_combo'] if c in base.columns),None)
 if actual_col is None: raise RuntimeError('actual combo column not found')
 base['actual_tuple']=base[actual_col].map(parse_combo)
 base=base[base.actual_tuple.map(lambda x: bool(x) and x[0]==1)].copy()
 wanted=set(base.race_code); days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted})
 sums=defaultdict(list);allv=[];feat={};d=date(2025,10,1);last=max(days);dayset=set(days)
 while d<=last:
  ymd=d.strftime('%Y/%m/%d');strows=rows(f'data/previews/stt/{ymd}.csv');bias=v326.st_bias(sums,allv)
  if d in dayset:
   tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv'));stt=v326.bycode(strows);orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
   for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(2,7):
     if b not in ex or b not in st or b not in os: continue
     feat[(code,b)]={'ex':ex[b],'st':st[b],'turn':os[b].get('turn',np.nan),'straight':os[b].get('straight',np.nan),'orig_avg':os[b].get('avg',np.nan)}
  v326.update_st(strows,sums,allv);d+=timedelta(days=1)
 rec=[]
 for _,r in base.sort_values('race_code').iterrows():
  pair=set(r.actual_tuple[1:])
  for b in range(2,7):
   f=feat.get((r.race_code,b));
   if not f: continue
   rec.append({'race_code':r.race_code,'schema':r.schema,'boat':b,'target':int(b in pair),**f})
 z=pd.DataFrame(rec); z=z.dropna(subset=FEATURES).sort_values(['race_code','boat']).copy();z['p']=np.nan
 # Walk-forward by race: train only strictly earlier races, schema-specific when sample allows.
 races=sorted(z.race_code.unique())
 for code in races:
  test=z[z.race_code.eq(code)]
  for schema,te in test.groupby('schema'):
   tr=z[(z.race_code<code)&z.schema.eq(schema)]
   if tr.race_code.nunique()<30 or tr.target.nunique()<2: continue
   m=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=2000,class_weight='balanced'))])
   m.fit(tr[FEATURES],tr.target);z.loc[te.index,'p']=m.predict_proba(te[FEATURES])[:,1]
 z.to_csv('analysis_v351_opponent_boat_oof.csv',index=False,encoding='utf-8-sig')
 out=[]
 for code,g in z[z.p.notna()].groupby('race_code'):
  if len(g)!=5:continue
  actual=set(g.loc[g.target.eq(1),'boat']);pred=set(g.nlargest(2,'p').boat)
  if len(actual)!=2:continue
  out.append({'race_code':code,'schema':g.schema.iloc[0],'pair_hit':int(pred==actual),'pred_pair':'-'.join(map(str,sorted(pred))),'actual_pair':'-'.join(map(str,sorted(actual))),'holdout':int(code[:8]>=HOLDOUT_START)})
 q=pd.DataFrame(out);q.to_csv('analysis_v351_opponent_pair_oof.csv',index=False,encoding='utf-8-sig')
 if q.empty:print('NO_PAIR_ROWS');return
 s=q.groupby(['schema','holdout']).agg(R=('pair_hit','size'),PAIR_HIT=('pair_hit','sum'),PAIR_RATE=('pair_hit','mean')).reset_index();s.PAIR_RATE*=100
 s.to_csv('analysis_v351_opponent_pair_summary.csv',index=False,encoding='utf-8-sig');print(s.to_string(index=False));print('TOTAL',len(q),'PAIR',int(q.pair_hit.sum()),'RATE',100*q.pair_hit.mean());print('HOLDOUT_START',HOLDOUT_START)
if __name__=='__main__':main()
