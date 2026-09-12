#!/usr/bin/env python3
"""4-head LIVE runner: frozen S/A -> v283 order -> pre-deadline odds -> v291 entry -> adopted variable N.

Production semantics:
- S priority: PRE>=.28, POST>=.25, ENV_ENTRY>=.224790.
- A only outside S: frozen HEAD4_V273_A_LIVE_QMAP (PRE>=.18, POST>=.18, mapped A_SCORE cut).
- Frozen v283 opponent order (TOP2XTOP2, alpha2=.60).
- Preserve v291 entry logic: Top4 composite odds must be >=7.0.
- If entered, formally adopted ticket policy: largest N in [4,16] with composite odds >=4.0.
- Exactly JPY10,000 inverse-odds Dutch, 100-yen Hamilton rounding.
- Official odds3t only, exact 120 combinations, fetched and frozen before deadline.
- No result/payout endpoints. Fail closed on missing/late/incomplete inputs.
"""
from __future__ import annotations
import argparse,json,math,sys,time
from pathlib import Path
from typing import Mapping
import numpy as np

import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v283_4head_conditional_pair_order as v283
import run_20260911_4head_v291_live as base
from head4_v273_a_live_inference import load_artifact,classify

POLICY='HEAD4_V291_COMP7_VARN_F4_N16'
BANK=10000
ENTRY_N=4
ENTRY_COMP=7.0
FLOOR=4.0
MAX_N=16
DEFAULT_AUDIT='live_audit_4head_v291_varn.jsonl'


def comp(vals):
    xs=[float(x) for x in vals]
    if not xs or any((not math.isfinite(x) or x<=0) for x in xs): raise RuntimeError('invalid odds')
    return 1.0/sum(1.0/x for x in xs)


def full_order(p2:Mapping[int,float],pc:Mapping[tuple[int,int],float]):
    pairs=v283.order_policy(dict(p2),dict(pc),0.60,'TOP2XTOP2',1.5)
    tickets=[f'4-{int(s)}-{int(t)}' for s,t in pairs]
    if len(tickets)!=20 or len(set(tickets))!=20: raise RuntimeError(f'v283 full order invariant failed: {len(tickets)}')
    old=base.v283_top4(p2,pc)
    if tickets[:4]!=old: raise RuntimeError(f'v283 Top4 parity failed: {tickets[:4]} != {old}')
    return tickets


def dutch(tickets,odds):
    st=np.asarray(v234.v205.round_dutch(list(map(float,odds)),BANK),dtype=int)
    if len(st)!=len(tickets) or int(st.sum())!=BANK or np.any(st%100!=0) or np.any(st<=0):
        raise RuntimeError('Dutch invariant failed')
    return [{'combo':t,'odds':float(o),'stake':int(s)} for t,o,s in zip(tickets,odds,st)]


def pick_n(order,odds_map):
    entry_vals=[float(odds_map[t]) for t in order[:ENTRY_N]]
    entry_comp=comp(entry_vals)
    if entry_comp<ENTRY_COMP:
        return {'entered':False,'entry_comp':entry_comp,'n':ENTRY_N,'comp':entry_comp,'tickets':order[:ENTRY_N]}
    best=ENTRY_N
    best_comp=entry_comp
    for n in range(ENTRY_N+1,MAX_N+1):
        c=comp([odds_map[t] for t in order[:n]])
        if c>=FLOOR:
            best=n;best_comp=c
        else:
            break
    return {'entered':True,'entry_comp':entry_comp,'n':best,'comp':best_comp,'tickets':order[:best]}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input-json',required=True,help='PRE/POST/ENV_ENTRY + p2 + cond + 17 frozen A feature keys')
    ap.add_argument('--date',required=True,help='YYYYMMDD')
    ap.add_argument('--jcd',required=True,type=int)
    ap.add_argument('--race',required=True,type=int)
    ap.add_argument('--deadline-jst',required=True)
    ap.add_argument('--audit',default=DEFAULT_AUDIT)
    a=ap.parse_args();t0=time.perf_counter();deadline=base.parse_deadline(a.deadline_jst)
    try:
        base.require_before_deadline(deadline,'startup')
        inp=json.loads(Path(a.input_json).read_text(encoding='utf-8'))
        code=f'{a.date}{a.jcd:02d}{a.race:02d}'
        if str(inp.get('race_code','')).zfill(12)!=code: raise RuntimeError('race_code mismatch')
        pre=float(inp['PRE']);post=float(inp['POST']);env=float(inp['ENV_ENTRY'])
        art=load_artifact()
        cls=classify(pre,post,env,inp,art)
        if not cls['eligible']:
            row={'race_code':code,'policy':POLICY,'layer':'NONE','decision':'NO_BET','reason':cls['reason'],
                 'scores':{'PRE':pre,'POST':post,'ENV_ENTRY':env,'A_SCORE_LIVE':cls.get('A_SCORE_LIVE')},
                 'result_or_payout_used':False,'total_stake':0,'seconds':time.perf_counter()-t0}
            row['decision_time_jst']=base.require_before_deadline(deadline,'before audit append').isoformat();row['deadline_jst']=deadline.isoformat()
            base.persist_audit(a.audit,row);print(json.dumps(row,ensure_ascii=False,indent=2));return
        p2=base.parse_p2(inp['p2']);pc=base.parse_cond(inp['cond']);order=full_order(p2,pc)
        odds,meta=base.fetch_odds(a.date,a.jcd,a.race,deadline)
        sel=pick_n(order,odds)
        if not sel['entered']:
            rows=[{'combo':t,'odds':float(odds[t]),'stake':0} for t in sel['tickets']]
            decision='PASS';reason='V291_TOP4_COMPOSITE_LT_7'
        else:
            vals=[float(odds[t]) for t in sel['tickets']];rows=dutch(sel['tickets'],vals);decision='BET';reason='ADOPTED_VARN_F4_N16'
        row={'race_code':code,'policy':POLICY,'base_policy':'HEAD4_V291_COMP7','layer':cls['layer'],'eligible':True,
             'classification':cls,'pair_model':{'branch':'v283 independent','mode':'TOP2XTOP2','alpha2':0.60,'v96_used':False},
             'entry_rule':{'top4_composite_cut':ENTRY_COMP,'top4_composite_odds':sel['entry_comp']},
             'ticket_rule':{'floor':FLOOR,'maxN':MAX_N,'selected_N':sel['n'],'selected_composite_odds':sel['comp']},
             'decision':decision,'reason':reason,'ordered_rank':order,'tickets':rows,'total_stake':int(sum(x['stake'] for x in rows)),
             'odds_snapshot':meta,'snapshot_timestamp_jst':meta.get('fetched_at_jst'),'deadline_jst':deadline.isoformat(),
             'deadline_state':'LIVE_FROZEN_BEFORE_DEADLINE','result_or_payout_used':False}
        row['decision_time_jst']=base.require_before_deadline(deadline,'immediately before audit append').isoformat();row['seconds']=time.perf_counter()-t0
        base.persist_audit(a.audit,row);print(json.dumps(row,ensure_ascii=False,indent=2))
    except Exception as e:
        err={'policy':POLICY,'decision':'ERROR_NO_BET','error':str(e),'deadline_jst':deadline.isoformat(),
             'now_jst':base.now_jst().isoformat(),'result_or_payout_used':False,'seconds':time.perf_counter()-t0}
        print(json.dumps(err,ensure_ascii=False,indent=2),file=sys.stderr);raise SystemExit(2)

if __name__=='__main__':main()
