#!/usr/bin/env python3
"""Build result-blind daily HEAD4 watchdog targets from monitoring_parent PRE rows.

Deadline source is BOAT RACE official /race/racelist only. No result or payout
endpoint is requested. One schedule page is fetched per active target venue.
"""
from __future__ import annotations
import argparse, json, os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import fetch_boatrace_deadline as deadline

JST=ZoneInfo('Asia/Tokyo')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--date',required=True,help='YYYY-MM-DD or YYYYMMDD')
    ap.add_argument('--pre-monitoring',required=True)
    ap.add_argument('--pre-run-id',required=True)
    ap.add_argument('--pre-artifact-name',required=True)
    ap.add_argument('--state-run-id',required=True)
    ap.add_argument('--state-artifact-name',required=True)
    ap.add_argument('--watch-minutes-before',type=int,default=35)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()

    day=datetime.strptime(a.date.replace('-',''),'%Y%m%d').strftime('%Y%m%d')
    z=pd.read_csv(a.pre_monitoring,dtype={'race_code':str})
    if z.empty:
        targets=[]
    else:
        z['race_code']=z.race_code.astype(str).str.zfill(12)
        if 'monitoring_parent' in z:
            z=z[pd.to_numeric(z.monitoring_parent,errors='coerce').fillna(0).eq(1)].copy()
        z['jcd']=z.race_code.str[8:10].astype(int)
        z['rno']=z.race_code.str[10:12].astype(int)

        schedules={}
        metas={}
        for jcd in sorted(z.jcd.unique()):
            # rno is irrelevant to the 12-time table; use 1 for one fetch/venue.
            requested=datetime.now(JST)
            r=deadline.safe_get(day,int(jcd),1)
            fetched=datetime.now(JST)
            times=deadline.parse_deadlines(r.text)
            if len(times)!=12: raise RuntimeError(f'JCD{jcd:02d} deadline count {len(times)}')
            schedules[int(jcd)]=times
            metas[f'{int(jcd):02d}']={
              'source':'BOAT RACE official racelist only',
              'requested_at_jst':requested.isoformat(),
              'fetched_at_jst':fetched.isoformat(),
              'resolved_url':r.url,
              'result_endpoint_requested':False,
              'payout_endpoint_requested':False,
            }

        targets=[]
        for _,r in z.iterrows():
            j=int(r.jcd);rn=int(r.rno);hm=schedules[j][rn-1]
            targets.append({
              'jcd':f'{j:02d}','race':rn,'race_code':str(r.race_code),
              'deadline_jst':hm,'watch_minutes_before':int(a.watch_minutes_before),
              'pre_run_id':str(a.pre_run_id),'pre_artifact_name':a.pre_artifact_name,
              'state_run_id':str(a.state_run_id),'state_artifact_name':a.state_artifact_name,
              'head_prob':float(r.head_prob) if 'head_prob' in r and pd.notna(r.head_prob) else None,
              'pre_reason':str(r.pre_reason) if 'pre_reason' in r else 'WATCH_ONLY',
              'note':'HEAD4_NEWFEATURE_FIXED156_V1 monitoring_parent; result-blind daily watchlist',
            })
        targets.sort(key=lambda x:(x['deadline_jst'],x['jcd'],x['race']))

    out={
      'date':day,
      'profile':'HEAD4_NEWFEATURE_FIXED156_V1',
      'generated_at_jst':datetime.now(JST).isoformat(),
      'source_pre_monitoring':a.pre_monitoring,
      'target_day_results_used':False,
      'payouts_used':False,
      'deadline_source':'BOAT RACE official racelist only',
      'target_count':len(targets),
      'targets':targets,
      'deadline_fetch_meta':metas if z is not None and not z.empty else {},
    }
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'date':day,'targets':len(targets),'out':str(p)},ensure_ascii=False))
    for t in targets:
        print('WATCH',t['deadline_jst'],t['jcd'],t['race'],t['race_code'],f"hp={t['head_prob']}")
    print('HEAD4_NEWFEATURE_WATCHLIST_OK')
    print('TARGET_DAY_RESULTS_UNREAD')

if __name__=='__main__':
    main()
