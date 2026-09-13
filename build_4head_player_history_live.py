#!/usr/bin/env python3
"""Build frozen v221-style player-history primitives for HEAD4 live inference.

Historical outcomes are used only to update causal pre-race player state. The target
day is never read from results, and this module performs no fitting, calibration,
threshold selection, ROI evaluation, odds access, or payout access.
"""
from __future__ import annotations
import argparse,csv,io,json
from collections import defaultdict,deque
from datetime import date,timedelta
from pathlib import Path
from typing import Any
from backtest import rows
from backtest_v4 import clean_name

BOATS=(1,2,3,4,5,6)
REQUIRED=("all_win","all_p2","frame_win","frame_p2","recent_p2")
class PlayerHistoryBuildError(RuntimeError): pass

def _ff(x,d=0.0):
    try:return float(x)
    except:return d

def _ii(x,d=0):
    try:return int(float(x))
    except:return d

def _blank():
    return {'n':0,'w':0,'p2':0,'nf':defaultdict(int),'wf':defaultdict(int),'p2f':defaultdict(int),'r':deque(maxlen=30)}

def _pstat(s:dict[str,Any],b:int)->dict[str,float]:
    n=s['n'];nf=s['nf'][b];r=list(s['r'])
    return {
      'all_win':(s['w']+2/6)/(n+2),
      'all_p2':(s['p2']+2/3)/(n+2),
      'frame_win':(s['wf'][b]+3*.125)/(nf+3),
      'frame_p2':(s['p2f'][b]+3*.25)/(nf+3),
      'recent_p2':sum(r)/len(r) if r else 1/3,
    }

def _bycode(rs):return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}

def _read_any(path:str):
    p=Path(path)
    if p.exists():
        s=p.read_text(encoding='utf-8-sig')
        return list(csv.DictReader(io.StringIO(s)))
    return rows(path)

def build(target_card:dict[str,Any],target_date:date,history_start:date)->dict[str,Any]:
    code=str(target_card.get('レースコード','')).zfill(12)
    if len(code)!=12 or not code.isdigit():raise PlayerHistoryBuildError('invalid target race_code')
    if history_start>=target_date:raise PlayerHistoryBuildError('history_start must be before target_date')
    names={b:clean_name(target_card.get(f'艇{b}_選手名','')) for b in BOATS}
    if any(not names[b] for b in BOATS):raise PlayerHistoryBuildError('missing target player name')
    if len(set(names.values()))!=6:raise PlayerHistoryBuildError('duplicate target player identity')
    state={name:_blank() for name in names.values()};seen={name:0 for name in names.values()}
    d=history_start
    while d<target_date:
        ymd=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv'); results=_bycode(rows(f'data/results/realtime/{ymd}.csv'))
        for card in sorted(cards,key=lambda r:str(r.get('レースコード','')).zfill(12)):
            rc=str(card.get('レースコード','')).zfill(12)
            hits=[]
            for b in BOATS:
                name=clean_name(card.get(f'艇{b}_選手名',''))
                if name in state:hits.append((b,name))
            if not hits:continue
            rr=results.get(rc)
            if rr is None:raise PlayerHistoryBuildError(f'missing causal result for target-player history race {rc}')
            w=_ii(rr.get('1着_艇番'));sec=_ii(rr.get('2着_艇番'))
            if w not in BOATS or sec not in BOATS or w==sec:raise PlayerHistoryBuildError(f'invalid causal result {rc}')
            for b,name in hits:
                s=state[name];s['n']+=1;s['w']+=int(w==b);s['p2']+=int(w==b or sec==b)
                s['nf'][b]+=1;s['wf'][b]+=int(w==b);s['p2f'][b]+=int(w==b or sec==b);s['r'].append(int(w==b or sec==b));seen[name]+=1
        d+=timedelta(days=1)
    flat={}
    for b,name in names.items():
        st=_pstat(state[name],b)
        for k in REQUIRED:flat[f'b{b}_pl_{k}']=round(float(st[k]),12)
    return {
      'schema':'head4_player_history_live_v1','race_code':code,'target_date':target_date.isoformat(),
      'history_start':history_start.isoformat(),'history_end':(target_date-timedelta(days=1)).isoformat(),
      'player_flat':flat,'history_races_seen_by_boat':{str(b):seen[names[b]] for b in BOATS},
      'same_day_results_used':False,'historical_outcomes_use':'causal_feature_state_only',
      'model_fitting_used':False,'calibration_used':False,'threshold_tuning_used':False,
      'odds_used':False,'payout_used':False,'v96_used':False,
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--race-cards',required=True);ap.add_argument('--race-code',required=True)
    ap.add_argument('--target-date',required=True);ap.add_argument('--history-start',default='2025-10-01');ap.add_argument('--out',required=True);a=ap.parse_args()
    cards=_bycode(_read_any(a.race_cards));code=str(a.race_code).zfill(12)
    if code not in cards:raise SystemExit(f'missing target PRE row {code}')
    td=date.fromisoformat(a.target_date);hs=date.fromisoformat(a.history_start)
    z=build(cards[code],td,hs);Path(a.out).write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'READY','race_code':code,'history_end':z['history_end'],'out':a.out},ensure_ascii=False))
if __name__=='__main__':main()
