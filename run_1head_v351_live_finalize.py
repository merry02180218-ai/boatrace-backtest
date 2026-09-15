#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,time
from pathlib import Path
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
BOATS=(2,3,4,5,6)

def norm(q):
 s=sum(max(float(v),0.0) for v in q.values())
 if not math.isfinite(s) or s<=0: raise RuntimeError('invalid probability mass')
 return {k:max(float(v),0.0)/s for k,v in q.items()}

def opponent_core(ex,st,straight,orig_avg):
 return {b:prod.ATTACK_CORE_W_ONE_EX*float(ex[str(b)])+prod.ATTACK_CORE_W_ONE_ST*float(st[str(b)])+prod.ATTACK_CORE_W_ONE_STRAIGHT*float(straight[str(b)])+prod.ATTACK_CORE_W_ONE_ORIG_AVG*float(orig_avg[str(b)]) for b in BOATS}
def adjust(p2,pc,core):
 a2=norm({b:float(p2[str(b)])*math.exp(prod.OPPONENT_CORE_SECOND_G2*(core[b]-.5)) for b in BOATS})
 a3={}
 for s in BOATS:
  q=norm({t:float(pc[f'{s}-{t}'])*math.exp(prod.OPPONENT_CORE_THIRD_G3*(core[t]-.5)) for t in BOATS if t!=s})
  for t,v in q.items(): a3[(s,t)]=v
 return a2,a3
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
 t0=time.perf_counter();x=json.loads(a.input.read_text())
 if x.get('result_or_payout_used') is not False: raise RuntimeError('result/payout guard failed')
 if not x.get('chronology_guard'): raise RuntimeError('chronology guard failed')
 if x.get('production_profile')!=prod.PROFILE_NAME: raise RuntimeError('profile mismatch')
 if not x.get('exhibition_ready'): raise RuntimeError('exhibition not ready')
 ph=float(x['final_head_p']); head_pass=ph>=prod.HEAD_CUTOFF and float(x['opp_mass'])>=prod.OPPONENT_MASS_MIN and bool(x['head_exhibition_pass'])
 tickets=[];core={}
 if head_pass:
  core=opponent_core(x['corrected_ex'],x['corrected_st'],x['corrected_straight'],x['corrected_orig_avg'])
  p2,pc=adjust(x['p2'],x['pc'],core);pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA);top=v299.STRATEGIES['HYBRID'](p2,pc,pair)[:3];tickets=[f'1-{s}-{t}' for s,t in top]
  if len(tickets)!=3 or len(set(tickets))!=3: raise RuntimeError('invalid ticket set')
 out={k:x.get(k) for k in ['race_code','pre_class','legacy_pre_p','deadline_jst','evaluated_at_jst','minutes_to_deadline','training_cutoff','exhibition_hashes']}
 out.update({'status':'PASS' if head_pass else 'DROP','production_profile':prod.PROFILE_NAME,'final_head_p':ph,'head_cutoff':prod.HEAD_CUTOFF,'opp_mass':float(x['opp_mass']),'head_exhibition_pass':bool(x['head_exhibition_pass']),'tickets':tickets,'opponent_core':core,'result_or_payout_used':False,'chronology_guard':True,'finalized':True,'scoring_ms':(time.perf_counter()-t0)*1000})
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
