#!/usr/bin/env python3
from collections import defaultdict
from datetime import date
from statistics import mean
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from backtest import rows
from backtest_v3 import CORR
from backtest_v51_lane_corrected_tickets import ff, rank_scores
import run_v326_1head_ticketaware_exhibition as v326

BASE=['one_ex','one_st','sec_ex_mean_margin','sec_st_mean_margin']
GROUPS={
 'half': ['one_half','sec_half_mean_margin','third_half_mean_margin','covered_half_weak_margin','uncovered_half_dominance'],
 'lap': ['one_lap','sec_lap_mean_margin','third_lap_mean_margin','covered_lap_weak_margin','uncovered_lap_dominance'],
 'turn':['one_turn','sec_turn_mean_margin','third_turn_mean_margin','covered_turn_weak_margin','uncovered_turn_dominance'],
 'straight':['one_straight','sec_straight_mean_margin','third_straight_mean_margin','covered_straight_weak_margin','uncovered_straight_dominance'],
}

def metric(label):
 s=(label or '').replace(' ','').replace('　','')
 if '半周' in s and 'ラップ' in s:return 'half'
 if '直線' in s:return 'straight'
 if 'まわり' in s or '回り' in s or 'ターン' in s:return 'turn'
 if '一周' in s:return 'lap'
 return ''
def avg(a):return float(np.mean(a)) if a else np.nan
def mx(a):return max(a) if a else np.nan
def mn(a):return min(a) if a else np.nan
def mm(g,u,m):return avg([m[b] for b in g])-mx([m[b] for b in u]) if g and u else np.nan
def mw(g,u,m):return mn([m[b] for b in g])-mx([m[b] for b in u]) if g and u else np.nan

def original_scores(row):
 out={}; complete={k:False for k in GROUPS}
 if not row:return out,complete
 for k in range(1,5):
  typ=metric(row.get(f'計測項目{k}',''))
  if not typ:continue
  vals={b:ff(row.get(f'艇{b}_値{k}')) for b in range(1,7)}
  if not all(v is not None for v in vals.values()):continue
  # Existing CORR has no half-lap channel; do not borrow one-lap correction for half-lap.
  corrkey={'lap':'一周','turn':'まわり足','straight':'直線'}.get(typ)
  if corrkey: vals={b:v+CORR[b].get(corrkey,0) for b,v in vals.items()}
  out[typ]=rank_scores(vals,True);complete[typ]=True
 return out,complete

def features(base,ex,st,orig):
 seconds,thirds,covered,uncovered,sec_un,third_un=v326.ticket_groups(base)
 z={}
 z['one_ex']=ex[1];z['one_st']=st[1];z['sec_ex_mean_margin']=mm(seconds,sec_un,ex);z['sec_st_mean_margin']=mm(seconds,sec_un,st)
 for typ,m in orig.items():
  z[f'one_{typ}']=m[1];z[f'sec_{typ}_mean_margin']=mm(seconds,sec_un,m);z[f'third_{typ}_mean_margin']=mm(thirds,third_un,m)
  z[f'covered_{typ}_weak_margin']=mw(covered,uncovered,m)
  z[f'uncovered_{typ}_dominance']=mx([m[b] for b in uncovered])-mx([m[b] for b in covered]) if uncovered else -1.0
 return z

def main():
 old=v326.build_dataset().copy();old['race_code']=old.race_code.astype(str).str.zfill(12);old['jcd']=old.race_code.str[8:10].astype(int)
 wanted=set(old.race_code); rec=[]
 for day,g in old.groupby(old.race_code.str[:8]):
  ymd=f'{day[:4]}/{day[4:6]}/{day[6:8]}'
  tkz=v326.bycode(rows(f'data/previews/tkz/{ymd}.csv'));stt=v326.bycode(rows(f'data/previews/stt/{ymd}.csv'));orr=v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
  # use v326 historical ST correction already reconstructed in old for ex/st features
  for _,b in g.iterrows():
   code=b.race_code
   z={k:b[k] for k in BASE}; os,comp=original_scores(orr.get(code,{}));z.update(features(b,{1:b.one_ex,2:0,3:0,4:0,5:0,6:0},{1:b.one_st,2:0,3:0,4:0,5:0,6:0},{})) if False else None
   # keep exact v326 ex/st margins; append independently parsed original channels
   seconds,thirds,covered,uncovered,sec_un,third_un=v326.ticket_groups(b)
   for typ,m in os.items():
    z[f'one_{typ}']=m[1];z[f'sec_{typ}_mean_margin']=mm(seconds,sec_un,m);z[f'third_{typ}_mean_margin']=mm(thirds,third_un,m);z[f'covered_{typ}_weak_margin']=mw(covered,uncovered,m);z[f'uncovered_{typ}_dominance']=mx([m[x] for x in uncovered])-mx([m[x] for x in covered]) if uncovered else -1.0
   r=b.to_dict();r.update(z);r.update({f'has_{k}':int(comp[k]) for k in GROUPS});rec.append(r)
 y=pd.DataFrame(rec)
 # Freeze schema by venue from availability only, never outcome.
 schemas={}
 for jcd,g in y.groupby('jcd'):
  types=[k for k in GROUPS if g[f'has_{k}'].mean()>=.70]
  schemas[jcd]=types
 y['schema']='';y['schema_ready']=0
 for jcd,types in schemas.items():
  feats=BASE+sum((GROUPS[t] for t in types),[])
  ix=y.jcd.eq(jcd);y.loc[ix,'schema']='+'.join(types) if types else 'base'
  y.loc[ix,'schema_ready']=y.loc[ix,feats].notna().all(axis=1).astype(int)
 print('SCHEMAS')
 for jcd in sorted(schemas):print(f'{jcd:02d}',schemas[jcd],int(y.loc[y.jcd.eq(jcd),'schema_ready'].sum()),'/',int(y.jcd.eq(jcd).sum()))
 print('TOTAL',len(y),'SCHEMA_READY',int(y.schema_ready.sum()),'OLD_MODEL_READY',int(y.model_ready.sum()))
 # pooled schema-family chronological OOF: train only on earlier races sharing same schema.
 y=y.sort_values('race_code').copy();y['schema_p']=np.nan
 for schema,g in y.groupby('schema'):
  types=[] if schema=='base' else schema.split('+');feats=BASE+sum((GROUPS[t] for t in types),[]);idx=list(g.index)
  for pos,i in enumerate(idx):
   if not y.loc[i,'schema_ready']:continue
   tr=y.loc[idx[:pos]];tr=tr[tr.schema_ready.eq(1)]
   if len(tr)<30 or tr.head_hit.nunique()<2:continue
   m=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=2000))]);m.fit(tr[feats],tr.head_hit)
   y.loc[i,'schema_p']=m.predict_proba(y.loc[[i],feats])[:,1][0]
 scored=y[y.schema_p.notna()]
 print('OOF_SCORED',len(scored),'HEAD',int(scored.head_hit.sum()),'HEAD_RATE',100*scored.head_hit.mean() if len(scored) else np.nan)
 for cut in [.70,.75,.78,.80,.82,.85]:
  q=scored[scored.schema_p>=cut];print('CUT',cut,'R',len(q),'HEAD',int(q.head_hit.sum()),'HEAD_RATE',100*q.head_hit.mean() if len(q) else np.nan,'EXACT3',int(q.hit.sum()),'EXACT3_RATE',100*q.hit.mean() if len(q) else np.nan)
 y.to_csv('analysis_v351_schema_correct_rebuild.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame([{'jcd':j,'schema':'+'.join(v) if v else 'base'} for j,v in schemas.items()]).to_csv('analysis_v351_schema_map.csv',index=False)
if __name__=='__main__':main()
