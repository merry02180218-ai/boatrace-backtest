#!/usr/bin/env python3
"""Resolve all active HEAD4 watchdog targets for one scheduler tick.

Pure scheduling helper. It reads only the result-blind watchlist plus optional
completed artifact names. No BOAT RACE endpoint is accessed.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

JST=ZoneInfo('Asia/Tokyo')
SAFETY_SECONDS=75

def parse_now(v:str|None)->datetime:
    if not v:
        return datetime.now(JST)
    dt=datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt=dt.replace(tzinfo=JST)
    return dt.astimezone(JST)

def resolve(watchlist:dict, now:datetime, completed:set[str]|None=None)->dict:
    completed=completed or set()
    day=now.strftime('%Y%m%d')
    if str(watchlist.get('date','')) != day:
        return {'date':day,'now_jst':now.isoformat(),'count':0,'include':[],
                'reason':f"date_mismatch:{watchlist.get('date')}"}
    out=[]
    for t in watchlist.get('targets',[]):
        hh,mm=map(int,str(t['deadline_jst']).split(':'))
        dl=now.replace(hour=hh,minute=mm,second=0,microsecond=0)
        start=dl-timedelta(minutes=float(t.get('watch_minutes_before',35)))
        safe=dl-timedelta(seconds=SAFETY_SECONDS)
        jcd=f"{int(t['jcd']):02d}"
        race=int(t['race'])
        artifact=f"head4-120r-watchdog-{day}-{jcd}-{race}"
        if artifact in completed:
            continue
        if start <= now < safe:
            out.append({
              'target_date':day,
              'jcd':jcd,
              'race':race,
              'deadline_jst':str(t['deadline_jst']),
              'pre_run_id':str(t['pre_run_id']),
              'pre_artifact_name':str(t['pre_artifact_name']),
              'state_run_id':str(t['state_run_id']),
              'state_artifact_name':str(t['state_artifact_name']),
              'artifact_name':artifact,
              'race_code':str(t.get('race_code') or f'{day}{jcd}{race:02d}'),
            })
    out.sort(key=lambda x:(x['deadline_jst'],x['jcd'],x['race']))
    return {'date':day,'now_jst':now.isoformat(),'count':len(out),'include':out,'reason':'ok'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--watchlist',required=True)
    ap.add_argument('--now-jst')
    ap.add_argument('--completed-names')
    ap.add_argument('--out')
    a=ap.parse_args()
    z=json.loads(Path(a.watchlist).read_text(encoding='utf-8'))
    completed=set()
    if a.completed_names and Path(a.completed_names).exists():
        completed={x.strip() for x in Path(a.completed_names).read_text(encoding='utf-8').splitlines() if x.strip()}
    r=resolve(z,parse_now(a.now_jst),completed)
    s=json.dumps(r,ensure_ascii=False,separators=(',',':'))
    if a.out:
        Path(a.out).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(s)
    print('HEAD4_WATCHDOG_RESOLVE_OK',r['count'])

if __name__=='__main__':
    main()
