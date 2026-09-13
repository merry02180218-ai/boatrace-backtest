#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import run_v299_1head_trifecta3_policy_search as v299
import run_v312_1head_opponent_outer_gate as v312
import run_v320_1head_exact3_ticket_policy as v320
import run_v326_1head_ticketaware_exhibition as v326

ROOT=Path(__file__).resolve().parent
V308=ROOT/'analysis_v308_1head_volume_opponent_joint_best_selected.csv'
V320=ROOT/'analysis_v320_1head_exact3_ticket_policy_best_race.csv'
OUT=Path('/tmp/v327'); OUT.mkdir(parents=True,exist_ok=True)

PRE_FEATURES=[
 'p_head','opp_mass','second_top1_prob','second_top2_mass','second_margin12',
 'third_top1_mean_for_top2_second','third_top1_min_for_top2_second',
 'ticket_prob1','ticket_prob2','ticket_prob3','ticket_mass3','ticket_gap34','ticket_entropy20'
]
EX_FEATURES=list(v326.RULE_FEATURES)
LOGIT_FEATURES=PRE_FEATURES+EX_FEATURES

def pct(n,d): return 100*n/d if d else float('nan')
def metrics(x):
 n=len(x); h=int(x.hit.sum()) if n else 0; hh=int(x.head_hit.sum()) if n else 0
 return {'R':n,'H':h,'exact3_rate':pct(h,n),'head_H':hh,'head_rate':pct(hh,n)}

def entropy(prob):
 a=np.array(list(prob.values()),float); a=a[a>0]
 return float(-(a*np.log(a)).sum()) if len(a) else float('nan')

def build_preconfidence():
 frozen=pd.read_csv(V320,dtype={'race_code':str}); frozen.race_code=frozen.race_code.astype(str).str.zfill(12)
 frozen['hit']=pd.to_numeric(frozen.hit,errors='coerce').fillna(0).astype(int)
 frozen['head_hit']=pd.to_numeric(frozen.head_hit,errors='coerce').fillna(0).astype(int)
 if len(frozen)!=345 or int(frozen.hit.sum())!=139 or int(frozen.head_hit.sum())!=290: raise AssertionError('v320 identity drift')
 base=pd.read_csv(V308,dtype={'race_code':str}); base.race_code=base.race_code.astype(str).str.zfill(12)
 base=base[base.race_code.isin(set(frozen.race_code))][['race_code','p_head','opp_mass']].drop_duplicates('race_code')
 if len(base)!=345: raise AssertionError(f'v308 confidence coverage {len(base)} != 345')
 d,p3,p4=v312.load_cache(); d.race_code=d.race_code.astype(str).str.zfill(12)
 ids=set(frozen.race_code); q=d[d.race_code.isin(ids)]
 if len(q)!=345 or int(q.head_hit.sum())!=290: raise AssertionError('v313 cache identity drift')
 p2,pc=v320.build_factorized(d,p3,p4)
 rows=[]
 for _,r in frozen.iterrows():
  code=r.race_code; tm=str(r['month'])
  a=p2[tm][code]; c=pc[tm][code]
  sr=sorted(a,key=lambda b:(-a[b],b)); s1,s2=sr[:2]
  b1=max([t for t in a if t!=s1],key=lambda t:(c[(s1,t)],-t))
  b2=max([t for t in a if t!=s2],key=lambda t:(c[(s2,t)],-t))
  prob=v299.pair_prob(a,c,.70); order=v299.STRATEGIES['HYBRID'](a,c,prob)
  top3=order[:3]; tickets=';'.join(f'1-{s}-{t}' for s,t in top3)
  if tickets!=str(r.tickets): raise AssertionError(f'ticket identity drift {code}: {tickets} != {r.tickets}')
  vals=[prob[x] for x in top3]
  row={'race_code':code,
       'second_top1_prob':float(a[s1]),'second_top2_mass':float(a[s1]+a[s2]),'second_margin12':float(a[s1]-a[s2]),
       'third_top1_mean_for_top2_second':float((c[(s1,b1)]+c[(s2,b2)])/2),
       'third_top1_min_for_top2_second':float(min(c[(s1,b1)],c[(s2,b2)])),
       'ticket_prob1':float(vals[0]),'ticket_prob2':float(vals[1]),'ticket_prob3':float(vals[2]),
       'ticket_mass3':float(sum(vals)),'ticket_gap34':float(prob[order[2]]-prob[order[3]]),'ticket_entropy20':entropy(prob)}
  rows.append(row)
 z=frozen.merge(base,on='race_code',how='left',validate='1:1').merge(pd.DataFrame(rows),on='race_code',how='left',validate='1:1')
 if z[PRE_FEATURES].isna().any().any(): raise AssertionError('missing PRE confidence feature')
 return z

def one_d_candidates(disc,val):
 out=[]
 for feat in PRE_FEATURES:
  for t in np.unique(np.quantile(disc[feat],np.arange(.10,.91,.10))):
   for op in ('>=','<='):
    a=disc[disc[feat]>=t] if op=='>=' else disc[disc[feat]<=t]
    b=val[val[feat]>=t] if op=='>=' else val[val[feat]<=t]
    dm,vm=metrics(a),metrics(b)
    out.append({'kind':'pre1d','feature':feat,'op':op,'threshold':float(t),**{f'disc_{k}':v for k,v in dm.items()},**{f'val_{k}':v for k,v in vm.items()}})
 return pd.DataFrame(out)

def combo_candidates(disc,val,pretab):
 out=[]
 preok=pretab[(pretab.disc_R>=25)&(pretab.val_R>=10)].sort_values(['val_exact3_rate','val_R'],ascending=False).head(12)
 for _,pr in preok.iterrows():
  for ef in EX_FEATURES:
   rd=disc[v326.feature_ready(disc,ef)]; rv=val[v326.feature_ready(val,ef)]
   if len(rd)<20 or len(rv)<10: continue
   for et in np.unique(np.quantile(rd[ef],[.25,.5,.75])):
    for eop in ('>=','<='):
     pmaskd=(disc[pr.feature]>=pr.threshold) if pr.op=='>=' else (disc[pr.feature]<=pr.threshold)
     pmaskv=(val[pr.feature]>=pr.threshold) if pr.op=='>=' else (val[pr.feature]<=pr.threshold)
     emaskd=(disc[ef]>=et) if eop=='>=' else (disc[ef]<=et)
     emaskv=(val[ef]>=et) if eop=='>=' else (val[ef]<=et)
     a=disc[pmaskd & emaskd & v326.feature_ready(disc,ef)]
     b=val[pmaskv & emaskv & v326.feature_ready(val,ef)]
     dm,vm=metrics(a),metrics(b)
     out.append({'kind':'pre_ex','pre_feature':pr.feature,'pre_op':pr.op,'pre_threshold':float(pr.threshold),'ex_feature':ef,'ex_op':eop,'ex_threshold':float(et),**{f'disc_{k}':v for k,v in dm.items()},**{f'val_{k}':v for k,v in vm.items()}})
 return pd.DataFrame(out)

def logit_candidates(disc,val):
 tr=disc.dropna(subset=LOGIT_FEATURES).copy(); va=val.dropna(subset=LOGIT_FEATURES).copy()
 if len(tr)<40 or len(va)<15:return pd.DataFrame(),None
 m=Pipeline([('sc',StandardScaler()),('lr',LogisticRegression(C=.15,max_iter=3000))]); m.fit(tr[LOGIT_FEATURES],tr.hit)
 pdsc=m.predict_proba(tr[LOGIT_FEATURES])[:,1]; pv=m.predict_proba(va[LOGIT_FEATURES])[:,1]
 out=[]
 for t in np.unique(np.quantile(pdsc,np.arange(.10,.91,.05))):
  a=tr[pdsc>=t]; b=va[pv>=t]; dm,vm=metrics(a),metrics(b)
  out.append({'kind':'logit','threshold':float(t),**{f'disc_{k}':v for k,v in dm.items()},**{f'val_{k}':v for k,v in vm.items()}})
 return pd.DataFrame(out),m

def choose(c):
 if c.empty:return None
 ok=c[(c.disc_R>=25)&(c.val_R>=15)&(c.val_exact3_rate>=50)]
 if ok.empty: ok=c[(c.disc_R>=20)&(c.val_R>=10)&(c.val_exact3_rate>=48)]
 if ok.empty:return None
 return ok.sort_values(['val_R','val_exact3_rate','disc_exact3_rate'],ascending=[False,False,False]).iloc[0].to_dict()

def apply_rule(df,best,model=None):
 if best is None:return df.iloc[0:0]
 if best['kind']=='pre1d':
  return df[df[best['feature']]>=best['threshold']] if best['op']=='>=' else df[df[best['feature']]<=best['threshold']]
 if best['kind']=='pre_ex':
  z=df[v326.feature_ready(df,best['ex_feature'])].copy()
  a=z[best['pre_feature']]>=best['pre_threshold'] if best['pre_op']=='>=' else z[best['pre_feature']]<=best['pre_threshold']
  b=z[best['ex_feature']]>=best['ex_threshold'] if best['ex_op']=='>=' else z[best['ex_feature']]<=best['ex_threshold']
  return z[a&b]
 z=df.dropna(subset=LOGIT_FEATURES).copy(); z['pass_prob']=model.predict_proba(z[LOGIT_FEATURES])[:,1]
 return z[z.pass_prob>=best['threshold']]

def main():
 pre=build_preconfidence(); ex=v326.build_dataset()
 y=pre.merge(ex[['race_code']+EX_FEATURES+list(set(v326.RULE_READY.values()))],on='race_code',how='left',validate='1:1')
 if len(y)!=345 or int(y.hit.sum())!=139 or int(y.head_hit.sum())!=290: raise AssertionError('v327 merged identity drift')
 y.to_csv(OUT/'v327_dataset.csv',index=False)
 disc=y[y.month.astype(str).isin(['2026-02','2026-03','2026-04'])].copy(); val=y[y.month.astype(str).eq('2026-05')].copy(); fwd=y[y.month.astype(str).eq('2026-06')].copy()
 pretab=one_d_candidates(disc,val); combotab=combo_candidates(disc,val,pretab); logtab,model=logit_candidates(disc,val)
 pretab.to_csv(OUT/'v327_pre1d_candidates.csv',index=False); combotab.to_csv(OUT/'v327_pre_ex_candidates.csv',index=False); logtab.to_csv(OUT/'v327_logit_candidates.csv',index=False)
 candidates=[]
 for tab in (pretab,combotab,logtab):
  b=choose(tab)
  if b is not None:candidates.append(b)
 if candidates:
  best=sorted(candidates,key=lambda r:(r['val_R'],r['val_exact3_rate'],r['disc_exact3_rate']),reverse=True)[0]
 else: best=None
 use_model=model if best and best['kind']=='logit' else None
 passed=apply_rule(fwd,best,use_model); skipped=fwd[~fwd.race_code.isin(set(passed.race_code))]
 fm,sm,bm=metrics(passed),metrics(skipped),metrics(fwd)
 forward=bool(fm['R']>=10 and fm['exact3_rate']>=50 and fm['exact3_rate']>=bm['exact3_rate'])
 summary=['# v327 PRE-confidence + exhibition','',f'- RECONCILE 345 / 290 / 139','- Jul/Aug unopened; September outcomes unread.','',f'- FROZEN_CANDIDATE: {best}',f'- June baseline: {bm}',f'- June PASS: {fm}',f'- June SKIP: {sm}',f'- FORWARD_SUPPORTED={forward}']
 (OUT/'summary_v327.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
 print('\n'.join(summary),flush=True)

if __name__=='__main__': main()
