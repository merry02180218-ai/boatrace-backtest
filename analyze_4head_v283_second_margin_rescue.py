#!/usr/bin/env python3
"""Validate v283 rescue semantics; September never read."""
from pathlib import Path
import json, numpy as np, pandas as pd
import audit_4head_86r_independent as cand
import audit_4head_86r_v283_closing_odds as audit
from head4_v291_downstream_inference import load_artifact, score_second, score_conditional_third, v283_top4, BOATS
OUT=Path('/tmp/head4_v283_second_margin'); OUT.mkdir(parents=True,exist_ok=True)
GAPS=[.01,.02,.03,.04,.05,.075,.10,.15,.20]; THIRD_GAP=.10; STAKE=100

def build(start='2026-04-01',end='2026-08-31'):
 if str(end)>='2026-09-01': raise RuntimeError('September outcome access blocked')
 cx=cand.rebuild(start,end); codes=set(cx.race_code.astype(str).str.zfill(12)); d=audit.source_rows(codes); long=audit.build_long_all(d); art=load_artifact(); sf=list(art['v283_SECOND']['features']); cf=list(art['v283_COND_THIRD']['features'])
 truth={str(r.race_code).zfill(12):(int(float(r.winner)),int(float(r.second)),int(float(r.third))) for _,r in d.iterrows() if str(r.get('valid_result','0')) in ('1','1.0')}; rows=[]
 for code,g in long.groupby('race_code'):
  sr=[]
  for _,r in g.iterrows(): x={'boat':int(r.boat)}; x.update({f:r[f] for f in sf}); sr.append(x)
  p2=score_second(sr,art); pc=score_conditional_third(audit.conditional_rows(g,sf,cf),art); so=sorted(BOATS,key=lambda s:(-float(p2[s]),s)); actual=truth.get(str(code)); ar=so.index(actual[1])+1 if actual and actual[0]==4 else np.nan
  rows.append({'date':str(g.date.iloc[0]),'month':str(g.date.iloc[0])[:7],'race_code':str(code),'head4':int(actual is not None and actual[0]==4),'actual_second':actual[1] if actual and actual[0]==4 else np.nan,'actual_third':actual[2] if actual and actual[0]==4 else np.nan,'second_rank':ar,'second_order':'-'.join(map(str,so)),'second_gap23':float(p2[so[1]]-p2[so[2]]),'p2':p2,'pc':pc})
 df=pd.DataFrame(rows)
 if start=='2026-04-01' and end=='2026-08-31': assert len(df)==164,len(df)
 return df,art

def pairs(row,sgap=None,tgap=None):
 p2=row.p2; pc=row.pc; so=sorted(BOATS,key=lambda s:(-float(p2[s]),s)); seconds=so[:3] if sgap is not None and float(p2[so[1]]-p2[so[2]])<=sgap else so[:2]; out=[]
 for s in seconds:
  ts=sorted((t for t in BOATS if t!=s),key=lambda t:(-float(pc[(s,t)]),t)); use=ts[:3] if tgap is not None and float(pc[(s,ts[1])]-pc[(s,ts[2])])<=tgap else ts[:2]; out += [(s,t) for t in use]
 base=v283_top4(p2,pc); return list(dict.fromkeys(base+[x for x in out if x not in base]))
def capture(df,sgap):
 q=df[df.head4.eq(1)]; return sum((int(r.actual_second),int(r.actual_third)) in pairs(r,sgap,None) for _,r in q.iterrows())
def main():
 df,art=build(); dev=df[df.month.isin(['2026-04','2026-05','2026-06'])]; scan=[]
 for g in GAPS:
  pp=dev.apply(lambda r:pairs(r,g,None),axis=1); scan.append({'gap':g,'dev_capture':capture(dev,g),'dev_added_tickets':int(sum(len(x)-4 for x in pp))})
 sc=pd.DataFrame(scan); basecap=capture(dev,None); sc['incremental_capture']=sc.dev_capture-basecap; sc['efficiency']=sc.incremental_capture/sc.dev_added_tickets.replace(0,np.nan); eligible=sc[sc.incremental_capture>0]; chosen=float((eligible.sort_values(['efficiency','incremental_capture','gap'],ascending=[False,False,True]).iloc[0] if len(eligible) else sc.iloc[0]).gap)
 print('HEAD4_V283_SECOND_MARGIN_VALIDATION_OK'); print('CHOSEN_SECOND_GAP',chosen); print('SEPTEMBER_UNREAD')
if __name__=='__main__':main()
