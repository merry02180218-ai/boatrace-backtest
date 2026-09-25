#!/usr/bin/env python3
"""Add official result-blind purchase deadlines to the 1HEAD daily watchlist.

Only BOAT RACE /race/racelist is requested. Results, payouts and odds are not read.
One official schedule page is fetched per active venue and its 12 deadlines are
reused for all WATCH races at that venue.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fetch_boatrace_deadline import parse_deadlines, safe_get


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--watchlist",required=True,type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--watch-minutes-before",type=float,default=35.0)
    a=ap.parse_args()

    z=json.loads(a.watchlist.read_text(encoding="utf-8"))
    day=str(z.get("date",""))
    if len(day)!=8 or not day.isdigit():
        raise RuntimeError(f"invalid watchlist date {day}")
    if z.get("target_day_results_used") is not False or z.get("payouts_used") is not False:
        raise RuntimeError("unsafe watchlist")

    targets=list(z.get("targets") or [])
    schedules={}
    for t in targets:
        code=str(t.get("race_code","")).zfill(12)
        if len(code)!=12 or not code.isdigit() or code[:8]!=day:
            raise RuntimeError(f"invalid race_code {code}")
        jcd=int(code[8:10])
        race=int(code[10:12])
        if not (1<=jcd<=24 and 1<=race<=12):
            raise RuntimeError(f"invalid target {code}")
        if jcd not in schedules:
            resp=safe_get(day,jcd,1)
            schedules[jcd]=parse_deadlines(resp.text)
        t["jcd"]=f"{jcd:02d}"
        t["race"]=race
        t["deadline_jst"]=schedules[jcd][race-1]
        t["watch_minutes_before"]=float(a.watch_minutes_before)

    targets.sort(key=lambda x:(x["deadline_jst"],x["jcd"],x["race"]))
    z["targets"]=targets
    z["target_count"]=len(targets)
    z["deadline_source"]="BOAT RACE official racelist only"
    z["deadline_result_endpoint_requested"]=False
    z["deadline_payout_endpoint_requested"]=False
    z["watch_minutes_before_default"]=float(a.watch_minutes_before)
    out=a.out or a.watchlist
    out.write_text(json.dumps(z,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("HEAD1_WATCHLIST_DEADLINES_OK",len(targets),len(schedules))
    print("TARGET_DAY_RESULTS_UNREAD")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
