#!/usr/bin/env python3
"""Historical-only v351 opponent-pair ranking audit Wave2.
Hard excludes September 2026 outcomes. Adds exact same-race ticket-pair baseline,
coverage/date diagnostics, pooled fallback for sparse schemas, walk-forward OOF.
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
from backtest_v51_lane_corrected_tickets import corrected_direct
import run_v326_1head_ticketaware_exhibition as v326
SCHEMAS={'lap+turn+straight','lap+turn','half+turn+straight','base'}
FEATURES=['boat','ex','st','turn','straight','orig_avg']
HOLDOUT_START='20260701'
def parse_combo(x):
 p=str(x).replace('>','-').replace(' ','').split('-');return tuple(map(int,p[:3])) if len(p)>=3 and all(z.isdigit() for z in p[:3]) else None
def parse_tickets(x):
 out=[]
 for q in str(x).replace('|',';').replace(',',';').split(';'):
  c=parse_combo(q)
  if c and c[0]==1:out.append(c)
 return out
def main():
 base=pd.read_csv('analysis_v351_schema_correct_rebuild.csv',dtype={'race_code':str});base.race_code=base.race_code.astype(str).str.zfill(12)
 base=base[(base.race_code.str[:8]<'20260901')&base.schema.isin(SCHEMAS)&base.schema_ready.eq(1)].copy()
 ac=next((c for c in ['actual_combo','actual','result_combo'] if c in base),None);tc=next((c for c in ['tickets','ticket_set','base_tickets'] if c in base),None)
 if ac is None or tc is None:raise RuntimeError('actual/ticket columns missing')
 base['actual_tuple']=base[ac].map(parse_combo);base['tickets_parsed']=base[tc].map(parse_tickets);base=base[base.actual_tuple.map(lambda x:bool(x) and x[0]==1)].copy()
 print('BASE_DATE_RANGE',base.race_code.str[:8].min(),base.race_code.str[:8].max(),'R',len(base));print('BASE_BY_MONTH');print(base.assign(month=base.race_code.str[:6]).groupby(['month','schema']).size().to_string())
 wanted=set(base.race_code);days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted});sums=defaultdict(list);allv=[];feat={};d=date(2025,10,1);last=max(days);dayset=set(days)
 while d<=last:
  ymd=d.strftime('%Y/%m/%d');strows=rows(f'data/previews/stt/{ymd}.csv');bias=v326.st_bias(sums,allv)
  if d in dayset:
   tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv'));stt=v326.bycode(strows);orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
   for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(2,7):
     if b in ex and b in st and b in os:feat[(code,b)]={'ex':ex[b],'st':st[b],'turn':os[b].get('turn',np.nan),'straight':os[b].get('straight',np.nan),'orig_avg':os[b].get('avg',np.nan)}
  v326.update_st(strows,sums,allv);d+=timedelta(days=1)
 rec=[]
 for _,r in base.sort_values('race_code').iterrows():
  pair=set(r.actual_tuple[1:]);ticket_pairs={frozenset(t[1:]) for t in r.tickets_parsed}
  for b in range(2,7):
   f=feat.get((r.race_code,b));
   if f:rec.append({'race_code':r.race_code,'schema':r.schema,'boat':b,'target':int(b in pair),'baseline_pair_hit':int(frozenset(pair) in ticket_pairs),**f})
 z=pd.DataFrame(rec).dropna(subset=FEATURES).sort_values(['race_code','boat']).copy();z['p']=np.nan;z['train_scope']=''
 print('FEATURE_DATE_RANGE',z.race_code.str[:8].min() if len(z) else 'NONE',z.race_code.str[:8].max() if len(z) else 'NONE','ROWS',len(z),'RACES',z.race_code.nunique())
 for code in sorted(z.race_code.unique()):
  for schema,te in z[z.race_code.eq(code)].groupby('schema'):
   tr=z[(z.race_code<code)&z.schema.eq(schema)];scope='schema'
   if tr.race_code.nunique()<30:tr=z[z.race_code<code];scope='pooled'
   if tr.race_code.nunique()<30 or tr.target.nunique()<2:continue
   m=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=2000,class_weight='balanced'))]);m.fit(tr[FEATURES],tr.target);z.loc[te.index,'p']=m.predict_proba(te[FEATURES])[:,1];z.loc[te.index,'train_scope']=scope
 z.to_csv('analysis_v351_opponent_boat_oof.csv',index=False,encoding='utf-8-sig');out=[]
 bmap=base.set_index('race_code')
 for code,g in z[z.p.notna()].groupby('race_code'):
  if len(g)!=5:continue
  actual=set(g[g.target.eq(1)].boat);pred=set(g.nlargest(2,'p').boat)
  if len(actual)!=2:continue
  br=bmap.loc[code];bp={frozenset(t[1:]) for t in br.tickets_parsed}
  out.append({'race_code':code,'schema':g.schema.iloc[0],'pair_hit':int(pred==actual),'baseline_pair_hit':int(frozenset(actual) in bp),'pred_pair':'-'.join(map(str,sorted(pred))),'actual_pair':'-'.join(map(str,sorted(actual))),'holdout':int(code[:8]>=HOLDOUT_START),'train_scope':g.train_scope.iloc[0]})
 q=pd.DataFrame(out);q.to_csv('analysis_v351_opponent_pair_oof.csv',index=False,encoding='utf-8-sig')
 if q.empty:print('NO_PAIR_ROWS');return
 print('OOF_DATE_RANGE',q.race_code.str[:8].min(),q.race_code.str[:8].max());print('OOF_BY_MONTH');print(q.assign(month=q.race_code.str[:6]).groupby(['month','schema']).size().to_string())
 s=q.groupby(['schema','holdout']).agg(R=('pair_hit','size'),PAIR_HIT=('pair_hit','sum'),PAIR_RATE=('pair_hit','mean'),BASE_HIT=('baseline_pair_hit','sum'),BASE_RATE=('baseline_pair_hit','mean')).reset_index();s[['PAIR_RATE','BASE_RATE']]*=100;s['DELTA_PP']=s.PAIR_RATE-s.BASE_RATE
 s.to_csv('analysis_v351_opponent_pair_summary.csv',index=False,encoding='utf-8-sig');print(s.to_string(index=False));print('TOTAL',len(q),'NEW',int(q.pair_hit.sum()),100*q.pair_hit.mean(),'BASE',int(q.baseline_pair_hit.sum()),100*q.baseline_pair_hit.mean(),'DELTA_PP',100*(q.pair_hit.mean()-q.baseline_pair_hit.mean()));print('HOLDOUT_START',HOLDOUT_START,'HOLDOUT_R',int(q.holdout.sum()))
if __name__=='__main__':main()
