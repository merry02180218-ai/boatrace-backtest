#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
import run_v329_1head_multistage_exhibition as v329
import run_v330_1head_extended_v329_reference as v330

OUT=Path('/tmp/v331'); OUT.mkdir(parents=True,exist_ok=True)
TA=.6453333333333333; TT=.5980000000000001; TE=-.29666666666666663; TB=.8973333333333333; TBE=-.37666666666666665

def pct(n,d): return 100*n/d if d else float('nan')
def met(z):
 n=len(z); h=int(z.hit.sum()) if n else 0; hh=int(z.head_hit.sum()) if n else 0
 return {'R':n,'exact3':h,'exact3_rate':pct(h,n),'head':hh,'head_rate':pct(hh,n)}
def describe(z,c,t):
 x=pd.to_numeric(z[c],errors='coerce').dropna()
 return {'N':len(x),'mean':float(x.mean()) if len(x) else None,'median':float(x.median()) if len(x) else None,'q25':float(x.quantile(.25)) if len(x) else None,'q75':float(x.quantile(.75)) if len(x) else None,'threshold':t,'threshold_pass_R':int((x>=t).sum()),'threshold_pass_pct':pct(int((x>=t).sum()),len(z))}
def gate(z,mask): return met(z[mask.fillna(False)])
def period(z,label):
 base=met(z)
 ga=z.attack_ready & z.env_ready & z.attack_core.ge(TA)
 gt=z.turn_ready & z.env_ready & z.turn_core.ge(TT)
 ge=z.env_ready & z.env_pair.ge(TE)
 gb=z.best_core_ready & z.env_ready & z.best_core.ge(TB)
 gbe=z.env_ready & z.env_pair.ge(TBE)
 p=v330.fixed_apply(z); skip=z[~z.race_code.isin(set(p.race_code))]
 gates={
  'attack_core':gate(z,z.attack_ready & z.attack_core.ge(TA)),
  'turn_core':gate(z,z.turn_ready & z.turn_core.ge(TT)),
  'env':gate(z,ge), 'bcore':gate(z,gb), 'benv':gate(z,gbe),
  'attack_and_env':gate(z,ga & ge), 'turn_and_env':gate(z,gt & ge),
  'bestcore_and_benv':gate(z,gb & gbe),
 }
 for d in gates.values(): d['exact3_lift_pp']=d['exact3_rate']-base['exact3_rate'] if d['R'] else None; d['head_lift_pp']=d['head_rate']-base['head_rate'] if d['R'] else None
 return {'label':label,'baseline':base,'features':{c:describe(z,c,t) for c,t in [('attack_core',TA),('turn_core',TT),('env_pair',TE),('best_core',TB)]},'gates':gates,'pass':met(p),'skip':met(skip),'grades':{g:met(p[p.v329_grade.eq(g)]) for g in ['S','A','B']}}

def main():
 old=v329.build_dataset().copy()
 if len(old)!=345 or int(old.hit.sum())!=139 or int(old.head_hit.sum())!=290: raise AssertionError('Feb-Jun identity drift')
 ext=v330.build_reference_features(v330.load_reference())
 if len(ext)!=55 or int(ext.hit.sum())!=21 or int(ext.head_hit.sum())!=45: raise AssertionError('Jul-Aug identity drift')
 parts={
  'FEB_APR':old[old.month.astype(str).isin(['2026-02','2026-03','2026-04'])].copy(),
  'MAY':old[old.month.astype(str).eq('2026-05')].copy(),
  'JUNE':old[old.month.astype(str).eq('2026-06')].copy(),
  'JULY':ext[ext.month.astype(str).eq('2026-07')].copy(),
  'AUGUST':ext[ext.month.astype(str).eq('2026-08')].copy(),
  'JUL_AUG':ext.copy(),
 }
 rep={k:period(v,k) for k,v in parts.items()}
 rows=[]
 for per,r in rep.items():
  for name,m in r['gates'].items(): rows.append({'period':per,'gate':name,**m})
 pd.DataFrame(rows).to_csv(OUT/'analysis_v331_gate_metrics.csv',index=False)
 drows=[]
 for per,r in rep.items():
  for name,m in r['features'].items(): drows.append({'period':per,'feature':name,**m})
 pd.DataFrame(drows).to_csv(OUT/'analysis_v331_feature_distributions.csv',index=False)
 (OUT/'result_v331.json').write_text(json.dumps(rep,indent=2,sort_keys=True),encoding='utf-8')
 lines=['# v331 component / route stability diagnostic','', '- Diagnostic only; no tuning/promotion. Jul/Aug NON-PRISTINE reference only; September outcomes unread.']
 for per in ['FEB_APR','MAY','JUNE','JULY','AUGUST','JUL_AUG']:
  r=rep[per]; lines += ['',f'## {per}',f"- baseline: {r['baseline']}",f"- fixed v329 PASS: {r['pass']}; SKIP: {r['skip']}",f"- grades: {r['grades']}"]
  for g in ['attack_core','turn_core','env','bcore','benv','attack_and_env','turn_and_env','bestcore_and_benv']:
   lines.append(f"- gate {g}: {r['gates'][g]}")
  lines.append(f"- distributions: {r['features']}")
 (OUT/'summary_v331.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)
if __name__=='__main__': main()
