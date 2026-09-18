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

def ticket_list(p2,pc):
 pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
 top=v299.STRATEGIES['HYBRID'](p2,pc,pair)[:3]
 out=[f'1-{s}-{t}' for s,t in top]
 if len(out)!=3 or len(set(out))!=3: raise RuntimeError('invalid ticket set')
 return out

def wall3_shadow(p2,pc,x,watch_pass):
 ex=x['corrected_ex']; st=x['corrected_st']; straight=x['corrected_straight']; avg=x['corrected_orig_avg']
 gaps={
  'ex':float(ex['3'])-float(ex['4']),
  'st':float(st['3'])-float(st['4']),
  'straight':float(straight['3'])-float(straight['4']),
  'orig_avg':float(avg['3'])-float(avg['4']),
 }
 wall_score=(prod.WALL3_SHADOW_W_EX*gaps['ex']+prod.WALL3_SHADOW_W_ST*gaps['st']+
             prod.WALL3_SHADOW_W_STRAIGHT*gaps['straight']+prod.WALL3_SHADOW_W_ORIG_AVG*gaps['orig_avg'])
 attack4=(prod.WALL3_SHADOW_W_EX*float(ex['4'])+prod.WALL3_SHADOW_W_ST*float(st['4'])+
          prod.WALL3_SHADOW_W_STRAIGHT*float(straight['4'])+prod.WALL3_SHADOW_W_ORIG_AVG*float(avg['4']))
 risk=max(0.0,-wall_score) if attack4>=prod.WALL3_SHADOW_ATTACK4_MIN else 0.0
 applied=bool(watch_pass and risk>0)
 if not watch_pass:
  return {'profile':prod.WALL3_SHADOW_PROFILE_NAME,'eligible':False,'applied':False,'risk':risk,'wall_score':wall_score,'attack4_score':attack4,'gaps':gaps,'tickets':[]}
 q2={b:float(p2[b]) for b in BOATS}; q3={(int(s),int(t)):float(v) for (s,t),v in pc.items()}
 if applied:
  q2[4]*=math.exp(prod.WALL3_SHADOW_SECOND_G2*risk); q2[3]*=math.exp(-prod.WALL3_SHADOW_SECOND_G2*risk); q2=norm(q2)
  out={}
  for s in BOATS:
   q={t:q3[(s,t)] for t in BOATS if t!=s}
   if 4 in q:q[4]*=math.exp(prod.WALL3_SHADOW_THIRD_G3*risk)
   if 3 in q:q[3]*=math.exp(-prod.WALL3_SHADOW_THIRD_G3*risk)
   q=norm(q)
   for t,v in q.items():out[(s,t)]=v
  q3=out
 return {'profile':prod.WALL3_SHADOW_PROFILE_NAME,'eligible':True,'applied':applied,'risk':risk,'wall_score':wall_score,'attack4_score':attack4,'gaps':gaps,'tickets':ticket_list(q2,q3)}

def five6_shadow(p2,pc,x,head_pass):
 ex=x['corrected_ex']; st=x['corrected_st']; straight=x['corrected_straight']; avg=x['corrected_orig_avg']
 score6=(prod.WALL3_SHADOW_W_EX*float(ex['6'])+prod.WALL3_SHADOW_W_ST*float(st['6'])+
         prod.WALL3_SHADOW_W_STRAIGHT*float(straight['6'])+prod.WALL3_SHADOW_W_ORIG_AVG*float(avg['6']))
 st_gap=float(st['6'])-float(st['5'])
 applied=bool(head_pass and score6>=prod.FIVE6_SHADOW_SCORE6_MIN and st_gap>=prod.FIVE6_SHADOW_ST_GAP_MIN)
 q2={b:float(p2[b]) for b in BOATS};q3={(int(s),int(t)):float(v) for (s,t),v in pc.items()}
 if applied:
  out={}
  for s in BOATS:
   q={t:q3[(s,t)] for t in BOATS if t!=s}
   if 6 in q:q[6]*=math.exp(prod.FIVE6_SHADOW_THIRD_G3*st_gap)
   if 5 in q:q[5]*=math.exp(-prod.FIVE6_SHADOW_THIRD_G3*st_gap)
   q=norm(q)
   for t,v in q.items():out[(s,t)]=v
  q3=out
 return {
  'profile':prod.FIVE6_SHADOW_PROFILE_NAME,
  'eligible':bool(head_pass),
  'applied':applied,
  'score6':score6,
  'st_gap_6_minus_5':st_gap,
  'tickets':ticket_list(q2,q3) if head_pass else [],
 }

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
 t0=time.perf_counter();x=json.loads(a.input.read_text())
 if x.get('result_or_payout_used') is not False: raise RuntimeError('result/payout guard failed')
 if not x.get('chronology_guard'): raise RuntimeError('chronology guard failed')
 if x.get('production_profile')!=prod.PROFILE_NAME: raise RuntimeError('base profile mismatch')
 if x.get('live_operation_profile') not in (None,prod.LIVE_OPERATION_PROFILE_NAME): raise RuntimeError('live operation profile mismatch')
 if not x.get('exhibition_ready'): raise RuntimeError('exhibition not ready')
 ph=float(x['final_head_p']); mass=float(x['opp_mass'])
 head_pass=ph>=prod.LIVE_HEAD_CUTOFF and mass>=prod.LIVE_OPPONENT_MASS_MIN and bool(x['head_exhibition_pass'])
 watch_pass=head_pass and ph>=prod.WATCH_HEAD_CUTOFF and mass>=prod.WATCH_OPPONENT_MASS_MIN
 tickets=[];pre_wall3_tickets=[];core={};shadow={'profile':prod.WALL3_LIVE_TICKET_PROFILE_NAME,'eligible':False,'applied':False,'risk':0.0,'wall_score':None,'attack4_score':None,'gaps':{},'tickets':[]}
 five6={'profile':prod.FIVE6_SHADOW_PROFILE_NAME,'eligible':False,'applied':False,'score6':None,'st_gap_6_minus_5':None,'tickets':[]}
 if head_pass:
  core=opponent_core(x['corrected_ex'],x['corrected_st'],x['corrected_straight'],x['corrected_orig_avg'])
  p2,pc=adjust(x['p2'],x['pc'],core)
  pre_wall3_tickets=ticket_list(p2,pc)
  shadow=wall3_shadow(p2,pc,x,watch_pass)
  tickets=shadow['tickets'] if (prod.WALL3_LIVE_TICKET_PROMOTED and shadow['applied']) else pre_wall3_tickets
  post_p2={b:float(p2[b]) for b in BOATS};post_pc={(int(s),int(t)):float(v) for (s,t),v in pc.items()}
  if prod.WALL3_LIVE_TICKET_PROMOTED and shadow['applied']:
   risk=float(shadow['risk'])
   post_p2[4]*=math.exp(prod.WALL3_SHADOW_SECOND_G2*risk);post_p2[3]*=math.exp(-prod.WALL3_SHADOW_SECOND_G2*risk);post_p2=norm(post_p2)
   tmp={}
   for s in BOATS:
    q={t:post_pc[(s,t)] for t in BOATS if t!=s}
    if 4 in q:q[4]*=math.exp(prod.WALL3_SHADOW_THIRD_G3*risk)
    if 3 in q:q[3]*=math.exp(-prod.WALL3_SHADOW_THIRD_G3*risk)
    q=norm(q)
    for t,v in q.items():tmp[(s,t)]=v
   post_pc=tmp
   if ticket_list(post_p2,post_pc)!=tickets: raise RuntimeError('wall3 post-probability reconstruction drift')
  five6=five6_shadow(post_p2,post_pc,x,head_pass)
 out={k:x.get(k) for k in ['race_code','pre_class','legacy_pre_p','deadline_jst','evaluated_at_jst','minutes_to_deadline','training_cutoff','exhibition_hashes']}
 out.update({
  'status':'PASS' if head_pass else 'DROP',
  'attention_level':'WATCH' if watch_pass else ('BASIC' if head_pass else 'DROP'),
  'watch_pass':bool(watch_pass),
  'production_profile':prod.PROFILE_NAME,
  'live_operation_profile':prod.LIVE_OPERATION_PROFILE_NAME,
  'watch_profile':prod.WATCH_PROFILE_NAME,
  'final_head_p':ph,
  'head_cutoff':prod.LIVE_HEAD_CUTOFF,
  'opp_mass':mass,
  'opponent_mass_min':prod.LIVE_OPPONENT_MASS_MIN,
  'watch_opponent_mass_min':prod.WATCH_OPPONENT_MASS_MIN,
  'live_env_w':prod.LIVE_EXHIBITION_ENV_W,
  'live_q':prod.LIVE_EXHIBITION_Q,
  'head_exhibition_pass':bool(x['head_exhibition_pass']),
  'tickets':tickets,
  'pre_wall3_tickets':pre_wall3_tickets,
  'ticket_profile':prod.WALL3_LIVE_TICKET_PROFILE_NAME if (prod.WALL3_LIVE_TICKET_PROMOTED and shadow['applied']) else prod.OPPONENT_CORE_VERSION,
  'wall3_ticket_promoted':bool(prod.WALL3_LIVE_TICKET_PROMOTED),
  'wall3_ticket_applied':bool(prod.WALL3_LIVE_TICKET_PROMOTED and shadow['applied']),
  'opponent_core':core,
  'wall3_shadow_profile':shadow['profile'],
  'wall3_shadow_eligible':shadow['eligible'],
  'wall3_shadow_applied':shadow['applied'],
  'wall3_shadow_risk':shadow['risk'],
  'wall3_shadow_wall_score':shadow['wall_score'],
  'wall3_shadow_attack4_score':shadow['attack4_score'],
  'wall3_shadow_gaps':shadow['gaps'],
  'wall3_shadow_tickets':shadow['tickets'],
  'wall3_shadow_research_only':False,
  'five6_shadow_profile':five6['profile'],
  'five6_shadow_eligible':five6['eligible'],
  'five6_shadow_applied':five6['applied'],
  'five6_shadow_score6':five6['score6'],
  'five6_shadow_st_gap_6_minus_5':five6['st_gap_6_minus_5'],
  'five6_shadow_tickets':five6['tickets'],
  'five6_shadow_research_only':True,
  'result_or_payout_used':False,
  'chronology_guard':True,
  'finalized':True,
  'scoring_ms':(time.perf_counter()-t0)*1000
 })
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':main()
