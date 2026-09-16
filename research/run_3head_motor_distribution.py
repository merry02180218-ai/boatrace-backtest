from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd

SRC='research_v289_3head_motor_protection.csv'

def desc(z):
 x=pd.to_numeric(z.motor_adv,errors='coerce').dropna()
 return {'n':int(len(z)),'motor_n':int(len(x)),'mean':float(x.mean()) if len(x) else None,'q10':float(x.quantile(.10)) if len(x) else None,'q25':float(x.quantile(.25)) if len(x) else None,'median':float(x.median()) if len(x) else None,'q75':float(x.quantile(.75)) if len(x) else None,'q90':float(x.quantile(.90)) if len(x) else None,'share_le_0':float((x<=0).mean()) if len(x) else None,'share_le_m025':float((x<=-.025).mean()) if len(x) else None,'share_ge_0':float((x>=0).mean()) if len(x) else None}

def met(z,rule):
 gap,exm,stm,mm=rule
 off=z[(z.base_gap>=gap)&(z.ex_adv<=exm)&(z.st_adv<=stm)&(z.motor_adv<=mm)]
 bb=int((off.category=='broken').sum()); rl=int((off.category=='rescued').sum())
 return {'off_races':int(len(off)),'broken_blocked':bb,'rescues_lost':rl,'net_off':bb-rl}

def main():
 p=Path(SRC)
 if not p.exists(): raise SystemExit(f'missing {SRC}; run motor protection first')
 r=pd.read_csv(p)
 # This file was produced with hard source cutoff < 2026-09-01; no September outcomes are present.
 march=r[r.month==3].copy()
 summaries={c:desc(march[march.category==c]) for c in ['rescued','broken','unchanged_hit','unchanged_miss']}
 b=pd.to_numeric(march[march.category=='broken'].motor_adv,errors='coerce').dropna(); q=pd.to_numeric(march[march.category=='rescued'].motor_adv,errors='coerce').dropna()
 pool=pd.concat([b,q],ignore_index=True).dropna()
 # Candidate motor cutpoints come ONLY from March event distribution, not Apr-Jun outcomes.
 qs=sorted(set(round(float(pool.quantile(v)),4) for v in [.10,.25,.50,.75,.90])) if len(pool) else [0.0]
 qs=sorted(set(qs+[0.0]))
 rules=[]
 for gap in [0,.005,.01,.02]:
  for exm in [.15,.20,.25,.30]:
   for stm in [.15,.20,.25,.30]:
    for mm in qs:
     rule=(gap,exm,stm,mm); m=met(march,rule)
     # Require actual March coverage and at least one blocked broken; otherwise cannot freeze.
     if m['off_races'] and m['broken_blocked']:
      rules.append({'base_gap_min':gap,'ex_adv_max':exm,'st_adv_max':stm,'motor_adv_max':mm,'march':m})
 rules=sorted(rules,key=lambda a:(a['march']['net_off'],a['march']['broken_blocked'],-a['march']['rescues_lost'],-a['march']['off_races']),reverse=True)
 frozen=rules[0] if rules and rules[0]['march']['net_off']>0 else None
 monthly={}
 if frozen:
  fr=(frozen['base_gap_min'],frozen['ex_adv_max'],frozen['st_adv_max'],frozen['motor_adv_max'])
  for m in range(4,9):
   monthly[str(m)]=met(r[r.month==m],fr); monthly[str(m)]['non_pristine']=m in [7,8]
 out={'phase':'MOTOR_DISTRIBUTION_FIRST','march_distribution':summaries,'march_motor_cutpoints':qs,'frozen_march_rule':None if frozen is None else {k:v for k,v in frozen.items() if k!='march'},'march_metrics':None if frozen is None else frozen['march'],'apr_aug_frozen_monthly':monthly,'apr_jun_all_positive':bool(frozen) and all(monthly[str(m)]['net_off']>0 for m in [4,5,6]),'top_march_rules':rules[:20],'candidate_selected_using_apr_jun':False,'exact_v288_exclusion_preserved':True,'september_outcomes_read':False,'production_changed':False}
 Path('research_v289_3head_motor_distribution.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
