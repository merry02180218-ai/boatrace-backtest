#!/usr/bin/env python3
"""Wave4: causal one-replacement correction for v351 first opponent pair.
Historical only. September 2026 outcomes hard excluded. Production unchanged.
Frozen June evaluation: train < 20260601, score June only.
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
TRAIN_END='20260601'; TEST_START='20260601'; TEST_END='20260701'

def combo(x):
 p=str(x).replace('>','-').replace(' ','').split('-');return tuple(map(int,p[:3])) if len(p)>=3 and all(z.isdigit() for z in p[:3]) else None

def tickets(x):
 out=[]
 for q in str(x).replace('|',';').replace(',',';').split(';'):
  c=combo(q)
  if c and c[0]==1:out.append(c)
 return out

def main():
 base=pd.read_csv('analysis_v351_schema_correct_rebuild.csv',dtype={'race_code':str});base.race_code=base.race_code.astype(str).str.zfill(12)
 base=base[(base.race_code.str[:8]<'20260901')&base.schema.isin(SCHEMAS)&base.schema_ready.eq(1)].copy()
 ac=next(c for c in ['actual_combo','actual','result_combo'] if c in base);tc=next(c for c in ['tickets','ticket_set','base_tickets'] if c in base)
 base['actual']=base[ac].map(combo);base['ts']=base[tc].map(tickets);base=base[base.actual.map(lambda x:bool(x) and x[0]==1)&base.ts.map(bool)].copy()
 wanted=set(base.race_code);days=sorted({date(int(c[:4]),int(c[4:6]),int(c[6:8])) for c in wanted});dayset=set(days);last=max(days)
 sums=defaultdict(list);allv=[];feat={};d=date(2025,10,1)
 while d<=last:
  ymd=d.strftime('%Y/%m/%d');strows=rows(f'data/previews/stt/{ymd}.csv');bias=v326.st_bias(sums,allv)
  if d in dayset:
   tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv'));stt=v326.bycode(strows);orig=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
   for code in [c for c in wanted if c.startswith(d.strftime('%Y%m%d'))]:
    ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
    for b in range(2,7):
     if b in ex and b in st:
      o=os.get(b,{})
      feat[(code,b)]={'ex':ex[b],'st':st[b],'turn':o.get('turn',np.nan),'straight':o.get('straight',np.nan),'orig_avg':o.get('avg',np.nan)}
  v326.update_st(strows,sums,allv);d+=timedelta(days=1)

 rec=[]
 for _,r in base.iterrows():
  actual=set(r.actual[1:]);cur=list(r.ts[0][1:]);curset=set(cur)
  for b in range(2,7):
   f=feat.get((r.race_code,b));
   if not f:continue
   rec.append({'race_code':r.race_code,'schema':r.schema,'boat':b,'selected':int(b in curset),'target':int(b in actual),'cur1':cur[0],'cur2':cur[1],**f})
 z=pd.DataFrame(rec)
 # schema-aware feature availability: never require unavailable original components globally.
 z['ex_rank']=z.groupby('race_code').ex.rank(method='average',ascending=True);z['st_rank']=z.groupby('race_code').st.rank(method='average',ascending=True)
 for c in ['turn','straight','orig_avg']:
  z[c+'_rank']=z.groupby('race_code')[c].rank(method='average',ascending=True)
 features=['boat','selected','ex','st','ex_rank','st_rank','turn_rank','straight_rank','orig_avg_rank']
 for c in features:z[c]=z[c].fillna(z[c].median() if z[c].notna().any() else 0)
 train=z[z.race_code.str[:8]<TRAIN_END].copy();test=z[(z.race_code.str[:8]>=TEST_START)&(z.race_code.str[:8]<TEST_END)].copy()
 if train.race_code.nunique()<30 or test.empty:raise RuntimeError('insufficient frozen train/test')
 model=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=2000,class_weight='balanced'))]);model.fit(train[features],train.target);test['p']=model.predict_proba(test[features])[:,1]
 bmap=base.set_index('race_code');out=[]
 for code,g in test.groupby('race_code'):
  if len(g)!=5:continue
  r=bmap.loc[code];actual=set(r.actual[1:]);cur=set(r.ts[0][1:]);common=actual&cur
  kind='KEEP' if cur==actual else ('REPLACE_ONE' if len(common)==1 else 'REPLACE_BOTH')
  # confidence of selected boats; only one-replacement candidate: retain stronger selected boat, replace weaker with best outsider.
  sg=g[g.selected.eq(1)].sort_values('p',ascending=False);og=g[g.selected.eq(0)].sort_values('p',ascending=False)
  if len(sg)!=2 or og.empty:continue
  keep=int(sg.iloc[0].boat);drop=int(sg.iloc[1].boat);rep=int(og.iloc[0].boat)
  margin=float(og.iloc[0].p-sg.iloc[1].p);proposal={keep,rep}
  union={frozenset(t[1:]) for t in r.ts}
  out.append({'race_code':code,'schema':r.schema,'kind':kind,'baseline_hit':int(cur==actual),'union_hit':int(frozenset(actual) in union),'proposal_hit':int(proposal==actual),'margin':margin,'keep_boat':keep,'drop_boat':drop,'replacement':rep,'actual_pair':'-'.join(map(str,sorted(actual))),'current_pair':'-'.join(map(str,sorted(cur)))})
 q=pd.DataFrame(out).sort_values('race_code');q.to_csv('analysis_v351_one_replace_wave4_june.csv',index=False,encoding='utf-8-sig')
 print('TRAIN_R',train.race_code.nunique(),'TEST_R',len(q),'TEST_RANGE',q.race_code.str[:8].min(),q.race_code.str[:8].max())
 print('JUNE_KIND');print(q.kind.value_counts().to_string())
 print('BASE_FIRST',int(q.baseline_hit.sum()),100*q.baseline_hit.mean(),'UNION',int(q.union_hit.sum()),100*q.union_hit.mean(),'ALWAYS_REPLACE',int(q.proposal_hit.sum()),100*q.proposal_hit.mean())
 rowsum=[]
 # override only when replacement advantage clears threshold; otherwise keep current pair.
 for th in [-.10,-.05,0,.025,.05,.075,.10,.15,.20,.25]:
  ov=q.margin>=th;hit=np.where(ov,q.proposal_hit,q.baseline_hit);false=int(((q.kind=='KEEP')&ov&(q.proposal_hit==0)).sum());rescue=int(((q.kind=='REPLACE_ONE')&ov&(q.proposal_hit==1)).sum())
  rowsum.append({'threshold':th,'R':len(q),'overrides':int(ov.sum()),'override_rate':100*ov.mean(),'hits':int(hit.sum()),'hit_rate':100*hit.mean(),'baseline_hits':int(q.baseline_hit.sum()),'delta_hits':int(hit.sum()-q.baseline_hit.sum()),'false_override_damage':false,'replace_one_rescue':rescue})
 s=pd.DataFrame(rowsum);s.to_csv('analysis_v351_one_replace_wave4_summary.csv',index=False,encoding='utf-8-sig');print(s.to_string(index=False))
 print('SEPTEMBER_OUTCOMES_USED',False);print('PRODUCTION_CHANGED',False)
if __name__=='__main__':main()
