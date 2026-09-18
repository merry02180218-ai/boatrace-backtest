#!/usr/bin/env python3
from __future__ import annotations
"""v377: regression for research-only overlay stake shadow.

Uses frozen historical causal rows only to reconstruct LIVE inputs.
No result/payout is passed to the finalizer.
"""
from pathlib import Path
import argparse,json,math,pickle,subprocess,sys

import onehead_production_profile as prod

BOATS=(2,3,4,5,6)

def norm(q):
    s=sum(float(v) for v in q.values())
    return {k:float(v)/s for k,v in q.items()}

def inverse_opponent_core(r):
    core={b:float(r[f'core{b}']) for b in BOATS}
    post2={int(k):float(v) for k,v in r['_p2'].items()}
    pre2={b:post2[b]/math.exp(prod.OPPONENT_CORE_SECOND_G2*(core[b]-.5)) for b in BOATS}
    pre2=norm(pre2)
    postpc={(int(s),int(t)):float(v) for (s,t),v in r['_pc'].items()}
    prepc={}
    for s in BOATS:
        q={t:postpc[(s,t)]/math.exp(prod.OPPONENT_CORE_THIRD_G3*(core[t]-.5)) for t in BOATS if t!=s}
        q=norm(q)
        for t,v in q.items():prepc[(s,t)]=v
    return pre2,prepc

def flags(r):
    wall=(float(r['opp_mass'])>=prod.WATCH_OPPONENT_MASS_MIN and bool(r.get('ex_ready',False))
          and float(r['score4'])>=prod.WALL3_SHADOW_ATTACK4_MIN
          and float(r['score4'])>float(r['score3']))
    five=(bool(r.get('ex_ready',False))
          and float(r['score6'])>=prod.FIVE6_SHADOW_SCORE6_MIN
          and float(r['st6'])-float(r['st5'])>=prod.FIVE6_SHADOW_ST_GAP_MIN)
    return bool(wall),bool(five)

def live_input(r):
    p2,pc=inverse_opponent_core(r)
    return {
      'race_code':str(r['race_code']).zfill(12),
      'pre_class':'HISTORICAL_CAUSAL_STAKE_SHADOW_REGRESSION',
      'legacy_pre_p':float(r['p_head']),
      'production_profile':prod.PROFILE_NAME,
      'live_operation_profile':prod.LIVE_OPERATION_PROFILE_NAME,
      'final_head_p':float(r['p_head']),
      'opp_mass':float(r['opp_mass']),
      'head_exhibition_pass':True,
      'exhibition_ready':True,
      'p2':{str(k):v for k,v in p2.items()},
      'pc':{f'{s}-{t}':v for (s,t),v in pc.items()},
      'corrected_ex':{str(b):float(r[f'ex{b}']) for b in BOATS},
      'corrected_st':{str(b):float(r[f'st{b}']) for b in BOATS},
      'corrected_straight':{str(b):float(r[f'straight{b}']) for b in BOATS},
      'corrected_orig_avg':{str(b):float(r[f'avg{b}']) for b in BOATS},
      'deadline_jst':'HISTORICAL_CAUSAL_ONLY',
      'evaluated_at_jst':'HISTORICAL_CAUSAL_ONLY',
      'minutes_to_deadline':None,
      'training_cutoff':'HISTORICAL_CAUSAL_ONLY',
      'exhibition_hashes':{},
      'result_or_payout_used':False,
      'chronology_guard':True,
    }

def run_case(label,r,outdir):
    ip=outdir/f'{label}_input.json';op=outdir/f'{label}_final.json'
    ip.write_text(json.dumps(live_input(r),ensure_ascii=False,indent=2),encoding='utf-8')
    subprocess.check_call([sys.executable,'run_1head_v351_live_finalize.py','--input',str(ip),'--out',str(op)])
    z=json.loads(op.read_text())
    if z['status']!='PASS':raise RuntimeError(f'{label}: status drift {z["status"]}')
    if len(z['tickets'])!=3:raise RuntimeError(f'{label}: ticket count drift')
    if z.get('official_stakes_yen')!=[100,100,100] or z.get('official_total_stake_yen')!=300:
        raise RuntimeError(f'{label}: official stake drift {z.get("official_stakes_yen")}')
    if z.get('stake_shadow_profile')!=prod.OVERLAY_STAKE_SHADOW_PROFILE_NAME:
        raise RuntimeError(f'{label}: shadow profile drift')
    if z.get('stake_shadow_research_only') is not True:
        raise RuntimeError(f'{label}: research-only flag drift')
    if z.get('result_or_payout_used') is not False or not z.get('chronology_guard'):
        raise RuntimeError(f'{label}: causality guard failed')
    return z

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);ap.add_argument('--outdir',required=True,type=Path)
    a=ap.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)
    x=pickle.load(a.prepared.open('rb'))
    rows=sorted(x['rows']['LIVE165'],key=lambda r:str(r['race_code']).zfill(12))
    wall_only=next(r for r in rows if flags(r)==(True,False))
    five_only=next(r for r in rows if flags(r)==(False,True))
    none=next(r for r in rows if flags(r)==(False,False))
    cases={}
    for label,r,expected in [('wall_only',wall_only,True),('five_only',five_only,True),('none',none,False)]:
        z=run_case(label,r,a.outdir)
        if bool(z.get('stake_shadow_applied'))!=expected:
            raise RuntimeError(f'{label}: applied={z.get("stake_shadow_applied")} expected={expected}')
        exp=[200,200,200] if expected else [100,100,100]
        if z.get('stake_shadow_stakes_yen')!=exp:
            raise RuntimeError(f'{label}: shadow stakes={z.get("stake_shadow_stakes_yen")} expected={exp}')
        if z.get('stake_shadow_total_stake_yen')!=sum(exp):
            raise RuntimeError(f'{label}: total shadow stake drift')
        cases[label]={
          'race_code':z['race_code'],
          'wall3_ticket_applied':z['wall3_ticket_applied'],
          'five6_ticket_applied':z['five6_ticket_applied'],
          'tickets':z['tickets'],
          'official_stakes_yen':z['official_stakes_yen'],
          'stake_shadow_applied':z['stake_shadow_applied'],
          'stake_shadow_stakes_yen':z['stake_shadow_stakes_yen'],
          'ticket_profile':z['ticket_profile'],
          'result_or_payout_used':z['result_or_payout_used'],
        }
    result={
      'stake_shadow_profile':prod.OVERLAY_STAKE_SHADOW_PROFILE_NAME,
      'official_staking_changed':False,
      'cases':cases,
      'SEPTEMBER_OUTCOMES_READ':False,
      'RESULT_OR_PAYOUT_USED':False,
      'AUDIT_OK':True,
    }
    (a.outdir/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
