#!/usr/bin/env python3
"""Result-blind timing policy for 1-head v351 LIVE exhibition acquisition."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timedelta, timezone

JST=timezone(timedelta(hours=9))


def parse_jst(s:str)->datetime:
    x=datetime.fromisoformat(s)
    if x.tzinfo is None:x=x.replace(tzinfo=JST)
    return x.astimezone(JST)


def window(deadline:datetime, now:datetime)->dict:
    remain=(deadline-now).total_seconds()
    if remain<=0: mode='EXPIRED'
    elif remain<=5*60: mode='FINAL5'
    elif remain<=10*60: mode='TRY10'
    elif remain<=12*60: mode='TRY12'
    elif remain<=15*60: mode='TRY15'
    else: mode='WAIT'
    return {
        'mode':mode,'remaining_seconds':remain,'remaining_minutes':remain/60.0,
        'should_fetch_exhibition':mode in {'TRY15','TRY12','TRY10','FINAL5'},
        'final_fail_close_if_not_ready':mode in {'FINAL5','EXPIRED'},
        'result_or_payout_used':False,
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--deadline-jst',required=True)
    ap.add_argument('--now-jst',default='')
    args=ap.parse_args()
    dl=parse_jst(args.deadline_jst); now=parse_jst(args.now_jst) if args.now_jst else datetime.now(JST)
    if dl.date()!=now.date():
        raise SystemExit(f'date parity failed: deadline={dl.date()} now={now.date()}')
    out={'deadline_jst':dl.isoformat(),'now_jst':now.isoformat(),**window(dl,now)}
    print(json.dumps(out,ensure_ascii=False))
    return 0

if __name__=='__main__':raise SystemExit(main())
