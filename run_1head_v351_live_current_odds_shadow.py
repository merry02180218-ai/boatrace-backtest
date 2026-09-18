#!/usr/bin/env python3
from __future__ import annotations
"""Research-only current-odds allocation shadow for 1-head LIVE.

Inputs:
- finalized LIVE JSON (formal tickets/stake already frozen)
- current BOAT RACE official odds3t, fetched live unless --odds-json is supplied

Never fetches result/payout endpoints. Does not mutate official tickets/stakes.
"""
from pathlib import Path
import argparse,json,math

import onehead_production_profile as prod
from boatrace_live_odds3t import fetch_odds3t

def soft_units(odds):
    o=[float(x) for x in odds]
    if any((not math.isfinite(x) or x<=0) for x in o):
        raise RuntimeError(f'invalid odds {o}')
    u=[1,1,1]
    ratio=max(o)/min(o)
    if ratio>=prod.CURRENT_ODDS_SOFT_RATIO_MIN:
        src=max(range(3),key=lambda i:(o[i],i))
        tgt=min(range(3),key=lambda i:(o[i],i))
        u[src]-=1
        u[tgt]+=1
    return u,ratio

def allocate(final,odds_map,fetched_at=None,source='provided'):
    if final.get('result_or_payout_used') is not False or not final.get('chronology_guard'):
        raise RuntimeError('unsafe finalized input')
    tickets=list(final.get('tickets') or [])
    if final.get('status')!='PASS' or len(tickets)!=3:
        return {
          'profile':prod.CURRENT_ODDS_ALLOC_SHADOW_PROFILE_NAME,
          'status':'NO_BET',
          'reason':'formal status is not PASS',
          'tickets':tickets,
          'stakes_yen':[],
          'total_stake_yen':0,
          'research_only':True,
          'result_or_payout_used':False,
          'chronology_guard':True,
        }
    miss=[t for t in tickets if t not in odds_map]
    if miss:raise RuntimeError(f'current odds missing formal tickets {miss}')
    odds=[float(odds_map[t]) for t in tickets]
    soft,ratio=soft_units(odds)
    wall=bool(final.get('wall3_ticket_applied'))
    five=bool(final.get('five6_ticket_applied'))
    if wall:
        signal='WALL3_RANK3'
        stakes=list(prod.WALL3_RANK3_ALLOC_SHADOW_WALL3_STAKES_YEN)
    elif five:
        signal='FIVE6_SOFT2X' if soft!=[1,1,1] else 'FIVE6_EQUAL2X'
        stakes=[200*x for x in soft]
    else:
        signal='SOFT' if soft!=[1,1,1] else 'NONE'
        stakes=[100*x for x in soft]
    return {
      'profile':prod.CURRENT_ODDS_ALLOC_SHADOW_PROFILE_NAME,
      'status':'SHADOW_READY',
      'signal':signal,
      'tickets':tickets,
      'ticket_odds':{t:o for t,o in zip(tickets,odds)},
      'odds_ratio_max_min':ratio,
      'soft_ratio_min':prod.CURRENT_ODDS_SOFT_RATIO_MIN,
      'soft_units':soft,
      'wall3_ticket_applied':wall,
      'five6_ticket_applied':five,
      'stakes_yen':stakes,
      'total_stake_yen':sum(stakes),
      'odds_source':source,
      'odds_fetched_at_jst':fetched_at,
      'research_only':bool(prod.CURRENT_ODDS_ALLOC_SHADOW_RESEARCH_ONLY),
      'result_or_payout_used':False,
      'chronology_guard':True,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--final',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--odds-json',type=Path,default=None,
                    help='test-only JSON: either {"odds":{...}} or direct combo->odds mapping')
    a=ap.parse_args()
    final=json.loads(a.final.read_text())
    if a.odds_json:
        raw=json.loads(a.odds_json.read_text())
        odds=raw.get('odds',raw)
        fetched=raw.get('fetched_at_jst') if isinstance(raw,dict) else None
        source='provided_test_odds'
    else:
        code=str(final.get('race_code','')).zfill(12)
        if len(code)!=12 or not code.isdigit():raise RuntimeError(f'invalid race_code {code}')
        x=fetch_odds3t(code[:8],code[8:10],int(code[10:12]))
        odds=x['odds'];fetched=x.get('fetched_at_jst');source=x.get('source','boatrace_official_live')
    out=allocate(final,odds,fetched,source)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
