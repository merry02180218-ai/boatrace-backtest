#!/usr/bin/env python3
from __future__ import annotations
"""v364: regression for formally promoted 5->6 ST live ticket rerank.

Uses a historical causal row only to reconstruct pre-race inputs. The race
outcome/payout is never supplied to the LIVE finalizer.
"""
from pathlib import Path
import argparse, json, math, pickle, subprocess, sys

import onehead_production_profile as prod

BOATS=(2,3,4,5,6)
CODE='202605141610'
EXPECTED_PRE=['1-2-3','1-2-4','1-3-2']
EXPECTED_OFFICIAL=['1-2-3','1-2-6','1-3-2']

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

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--prepared',required=True,type=Path)
    ap.add_argument('--outdir',required=True,type=Path)
    a=ap.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)

    x=pickle.load(a.prepared.open('rb'))
    r=next(rr for rr in x['rows']['LIVE165'] if str(rr['race_code']).zfill(12)==CODE)
    p2,pc=inverse_opponent_core(r)
    inp={
      'race_code':CODE,
      'pre_class':'HISTORICAL_CAUSAL_REGRESSION',
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
    ip=a.outdir/'input.json';op=a.outdir/'final.json'
    ip.write_text(json.dumps(inp,ensure_ascii=False,indent=2))
    subprocess.check_call([sys.executable,'run_1head_v351_live_finalize.py','--input',str(ip),'--out',str(op)])
    z=json.loads(op.read_text())

    if z['status']!='PASS' or z['attention_level']!='WATCH':raise RuntimeError(f'gate drift {z}')
    if z['pre_five6_tickets']!=EXPECTED_PRE:raise RuntimeError(f'pre-five6 drift {z["pre_five6_tickets"]}')
    if z['tickets']!=EXPECTED_OFFICIAL:raise RuntimeError(f'official five6 drift {z["tickets"]}')
    if not z.get('five6_ticket_promoted') or not z.get('five6_ticket_applied'):raise RuntimeError(f'five6 promotion not applied {z}')
    if z.get('ticket_profile')!=prod.FIVE6_LIVE_TICKET_PROFILE_NAME:raise RuntimeError(f'profile drift {z.get("ticket_profile")}')
    if abs(float(z.get('five6_shadow_score6'))-.68)>1e-9:raise RuntimeError(f'score6 drift {z.get("five6_shadow_score6")}')
    if abs(float(z.get('five6_shadow_st_gap_6_minus_5'))-.8)>1e-9:raise RuntimeError(f'st gap drift {z.get("five6_shadow_st_gap_6_minus_5")}')
    if z.get('result_or_payout_used') is not False or not z.get('chronology_guard'):raise RuntimeError('causality guard failed')
    if not prod.FIVE6_LIVE_TICKET_PROMOTED:raise RuntimeError('promotion flag false')

    result={
      'race_code':CODE,
      'pre_five6_tickets':z['pre_five6_tickets'],
      'official_tickets':z['tickets'],
      'ticket_profile':z['ticket_profile'],
      'five6_ticket_applied':z['five6_ticket_applied'],
      'score6':z['five6_shadow_score6'],
      'st_gap_6_minus_5':z['five6_shadow_st_gap_6_minus_5'],
      'result_or_payout_used':False,
      'SEPTEMBER_OUTCOMES_READ':False,
      'AUDIT_OK':True,
    }
    (a.outdir/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
