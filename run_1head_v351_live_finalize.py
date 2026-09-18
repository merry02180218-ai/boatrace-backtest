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

def ticket_pair_probs(p2,pc,tickets):
 pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
 out={}
 for ticket in tickets:
  a,s,t=map(int,str(ticket).split('-'))
  if a!=1 or s not in BOATS or t not in BOATS or s==t: raise RuntimeError(f'invalid formal ticket {ticket}')
  out[ticket]=float(pair[(s,t)])
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
 tickets=[];pre_wall3_tickets=[];pre_five6_tickets=[];final_pair_prob_map={};core={};shadow={'profile':prod.WALL3_LIVE_TICKET_PROFILE_NAME,'eligible':False,'applied':False,'risk':0.0,'wall_score':None,'attack4_score':None,'gaps':{},'tickets':[]}
 five6={'profile':prod.FIVE6_LIVE_TICKET_PROFILE_NAME,'eligible':False,'applied':False,'score6':None,'st_gap_6_minus_5':None,'tickets':[]}
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
  pre_five6_tickets=tickets[:]
  five6=five6_shadow(post_p2,post_pc,x,head_pass)
  final_p2={b:float(post_p2[b]) for b in BOATS};final_pc={(int(s),int(t)):float(v) for (s,t),v in post_pc.items()}
  if prod.FIVE6_LIVE_TICKET_PROMOTED and five6['applied']:
   tickets=five6['tickets']
   st_gap=float(five6['st_gap_6_minus_5'])
   tmp={}
   for s in BOATS:
    q={t:final_pc[(s,t)] for t in BOATS if t!=s}
    if 6 in q:q[6]*=math.exp(prod.FIVE6_SHADOW_THIRD_G3*st_gap)
    if 5 in q:q[5]*=math.exp(-prod.FIVE6_SHADOW_THIRD_G3*st_gap)
    q=norm(q)
    for t,v in q.items():tmp[(s,t)]=v
   final_pc=tmp
   if ticket_list(final_p2,final_pc)!=tickets: raise RuntimeError('five6 post-probability reconstruction drift')
  final_pair_prob_map=ticket_pair_probs(final_p2,final_pc,tickets)
 out={k:x.get(k) for k in ['race_code','pre_class','legacy_pre_p','deadline_jst','evaluated_at_jst','minutes_to_deadline','training_cutoff','exhibition_hashes']}
 official_stakes=[prod.LIVE_OFFICIAL_STAKE_YEN_PER_TICKET for _ in tickets] if head_pass else []
 stake_shadow_signal=bool(head_pass and ((prod.WALL3_LIVE_TICKET_PROMOTED and shadow['applied']) or (prod.FIVE6_LIVE_TICKET_PROMOTED and five6['applied'])))
 stake_shadow_applied=bool(stake_shadow_signal)
 stake_shadow_stakes=([prod.LIVE_OFFICIAL_STAKE_YEN_PER_TICKET*prod.OVERLAY_STAKE_SHADOW_MULTIPLIER for _ in tickets]
                      if stake_shadow_applied else official_stakes[:])
 allocation_shadow_wall3=bool(head_pass and prod.WALL3_LIVE_TICKET_PROMOTED and shadow['applied'])
 allocation_shadow_five6=bool(head_pass and prod.FIVE6_LIVE_TICKET_PROMOTED and five6['applied'])
 if not head_pass:
  allocation_shadow_signal='DROP'
  allocation_shadow_stakes=[]
 elif allocation_shadow_wall3:
  allocation_shadow_signal='WALL3_RANK3'
  allocation_shadow_stakes=list(prod.WALL3_RANK3_ALLOC_SHADOW_WALL3_STAKES_YEN)
 elif allocation_shadow_five6:
  allocation_shadow_signal='FIVE6_EQUAL2X'
  allocation_shadow_stakes=list(prod.WALL3_RANK3_ALLOC_SHADOW_FIVE6_ONLY_STAKES_YEN)
 else:
  allocation_shadow_signal='NONE'
  allocation_shadow_stakes=list(prod.WALL3_RANK3_ALLOC_SHADOW_NONE_STAKES_YEN)
 allocation_shadow_applied=bool(allocation_shadow_wall3 or allocation_shadow_five6)
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
  'ticket_pair_probs':final_pair_prob_map,
  'pre_wall3_tickets':pre_wall3_tickets,
  'pre_five6_tickets':pre_five6_tickets,
  'ticket_profile':(
   prod.FIVE6_LIVE_TICKET_PROFILE_NAME if (prod.FIVE6_LIVE_TICKET_PROMOTED and five6['applied'])
   else (prod.WALL3_LIVE_TICKET_PROFILE_NAME if (prod.WALL3_LIVE_TICKET_PROMOTED and shadow['applied']) else prod.OPPONENT_CORE_VERSION)
  ),
  'wall3_ticket_promoted':bool(prod.WALL3_LIVE_TICKET_PROMOTED),
  'wall3_ticket_applied':bool(prod.WALL3_LIVE_TICKET_PROMOTED and shadow['applied']),
  'five6_ticket_promoted':bool(prod.FIVE6_LIVE_TICKET_PROMOTED),
  'five6_ticket_applied':bool(prod.FIVE6_LIVE_TICKET_PROMOTED and five6['applied']),
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
  'five6_shadow_research_only':False,
  'official_stakes_yen':official_stakes,
  'official_total_stake_yen':sum(official_stakes),
  'stake_shadow_profile':prod.OVERLAY_STAKE_SHADOW_PROFILE_NAME,
  'stake_shadow_signal':'EITHER_FORMAL_OVERLAY',
  'stake_shadow_applied':stake_shadow_applied,
  'stake_shadow_stakes_yen':stake_shadow_stakes,
  'stake_shadow_total_stake_yen':sum(stake_shadow_stakes),
  'stake_shadow_research_only':bool(prod.OVERLAY_STAKE_SHADOW_RESEARCH_ONLY),
  'allocation_shadow_profile':prod.WALL3_RANK3_ALLOC_SHADOW_PROFILE_NAME,
  'allocation_shadow_signal':allocation_shadow_signal,
  'allocation_shadow_applied':allocation_shadow_applied,
  'allocation_shadow_stakes_yen':allocation_shadow_stakes,
  'allocation_shadow_total_stake_yen':sum(allocation_shadow_stakes),
  'allocation_shadow_research_only':bool(prod.WALL3_RANK3_ALLOC_SHADOW_RESEARCH_ONLY),
  'result_or_payout_used':False,
  'chronology_guard':True,
  'finalized':True,
  'scoring_ms':(time.perf_counter()-t0)*1000
 })
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':main()
