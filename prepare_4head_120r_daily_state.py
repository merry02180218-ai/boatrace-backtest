#!/usr/bin/env python3
"""Build once-per-day causal state for fast HEAD4 120R last-minute inference.

Operational rule:
- prior completed dates, including September 2026, are allowed;
- target-date results are never read;
- no payout/odds endpoints are used.

State contains:
- all-player causal history keyed by registration number;
- ST lane-bias state through target_date-1.

This replaces per-race history replay in the last-minute path.
"""
from __future__ import annotations
import argparse,json,time,csv
from collections import defaultdict,deque
from datetime import date,timedelta
from pathlib import Path
from statistics import mean

START=date(2025,10,1)
NEWFEATURE_MOTOR_START=date(2025,11,1)
BOATS=range(1,7)

def _ii(x,d=0):
    try:return int(float(x))
    except:return d

def _ff(x):
    try:return float(x)
    except:return None

def blank():
    return {'n':0,'w':0,'p2':0,'nf':defaultdict(int),'wf':defaultdict(int),'p2f':defaultdict(int),'r':deque(maxlen=30)}

def local_rows(root, rel):
    p=Path(root)/rel
    if not p.is_file(): return []
    with p.open(encoding='utf-8-sig',newline='') as fh:
        return list(csv.DictReader(fh))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--target-date',required=True);ap.add_argument('--out',required=True);ap.add_argument('--data-root',required=True);a=ap.parse_args()
    target=date.fromisoformat(a.target_date)
    if target<=START:raise SystemExit('target_date too early')
    t0=time.perf_counter()
    players=defaultdict(blank); motors=defaultdict(lambda:[0,0]); motors_newfeature=defaultdict(lambda:[0,0]); st_sums=defaultdict(list); st_all=[]
    days=0; races=0; result_days=0
    d=START
    while d<target:
        ymd=d.strftime('%Y/%m/%d')
        cards=local_rows(a.data_root,f'data/programs/race_cards/{ymd}.csv')
        results={str(r.get('レースコード','')).zfill(12):r for r in local_rows(a.data_root,f'data/results/realtime/{ymd}.csv')}
        strows=local_rows(a.data_root,f'data/previews/stt/{ymd}.csv')
        if cards:
            days+=1
            if results: result_days+=1
            for card in sorted(cards,key=lambda r:str(r.get('レースコード','')).zfill(12)):
                code=str(card.get('レースコード','')).zfill(12); rr=results.get(code)
                if rr is None: continue
                w=_ii(rr.get('1着_艇番')); sec=_ii(rr.get('2着_艇番'))
                if w not in BOATS or sec not in BOATS or w==sec: continue
                races+=1
                venue=str(card.get('レース場コード','')).zfill(2)
                for b in BOATS:
                    motor_no=str(card.get(f'艇{b}_モーター番号','')).strip()
                    if venue and motor_no:
                        mk=f'{venue}|{motor_no}'
                        motors[mk][1]+=1
                        motors[mk][0]+=int(w==b)
                        if d>=NEWFEATURE_MOTOR_START:
                            motors_newfeature[mk][1]+=1
                            motors_newfeature[mk][0]+=int(w==b)
                    reg=str(card.get(f'艇{b}_登録番号','')).strip()
                    if not reg: continue
                    s=players[reg]
                    s['n']+=1;s['w']+=int(w==b);s['p2']+=int(w==b or sec==b)
                    s['nf'][b]+=1;s['wf'][b]+=int(w==b);s['p2f'][b]+=int(w==b or sec==b)
                    s['r'].append(int(w==b or sec==b))
        for r in strows:
            for b in BOATS:
                v=_ff(r.get(f'艇{b}_スタート展示'))
                if v is not None and -.30<v<1.0:
                    st_sums[b].append(v);st_all.append(v)
        d+=timedelta(days=1)
    g=mean(st_all) if st_all else .15
    bias={str(b):(mean(st_sums[b])-g if st_sums[b] else 0.0) for b in BOATS}
    pjson={}
    for reg,s in players.items():
        pjson[reg]={
          'n':s['n'],'w':s['w'],'p2':s['p2'],
          'nf':{str(b):int(s['nf'][b]) for b in BOATS},
          'wf':{str(b):int(s['wf'][b]) for b in BOATS},
          'p2f':{str(b):int(s['p2f'][b]) for b in BOATS},
          'recent_p2':list(s['r']),
        }
    out={
      'schema':'head4_120r_daily_state_v1',
      'target_date':target.isoformat(),
      'history_start':START.isoformat(),
      'history_end':(target-timedelta(days=1)).isoformat(),
      'prior_completed_dates_allowed':True,
      'september_prior_results_allowed':True,
      'target_date_results_used':False,
      'payout_used':False,'odds_used':False,
      'players':pjson,
      'motors':{k:{'w':int(v[0]),'n':int(v[1])} for k,v in motors.items()},
      'motors_newfeature_nov2025':{k:{'w':int(v[0]),'n':int(v[1])} for k,v in motors_newfeature.items()},
      'newfeature_motor_history_start':NEWFEATURE_MOTOR_START.isoformat(),
      'st_bias':bias,
      'stats':{'days_loaded':days,'result_days':result_days,'settled_races_loaded':races,'players':len(pjson),'motors':len(motors),'motors_newfeature':len(motors_newfeature)},
      'seconds':time.perf_counter()-t0,
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'status':'HEAD4_120R_DAILY_STATE_READY','history_end':out['history_end'],'stats':out['stats'],'seconds':out['seconds']},ensure_ascii=False))

if __name__=='__main__':main()
