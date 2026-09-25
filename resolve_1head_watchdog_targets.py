#!/usr/bin/env python3
"""Resolve active 1HEAD WATCH targets for the shared HEAD4 watchdog tick.

Pure scheduling helper. Reads only the audited result-blind watchlist and the
set of completed artifact names. No BOAT RACE endpoint is accessed here.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

JST=ZoneInfo("Asia/Tokyo")
SAFETY_SECONDS=75


def parse_now(v:str|None)->datetime:
    if not v:
        return datetime.now(JST)
    dt=datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt=dt.replace(tzinfo=JST)
    return dt.astimezone(JST)


def resolve(watchlist:dict, now:datetime, completed:set[str]|None=None, audit_run_id:str="")->dict:
    completed=completed or set()
    day=now.strftime("%Y%m%d")
    if str(watchlist.get("date",""))!=day:
        return {"date":day,"now_jst":now.isoformat(),"count":0,"include":[],
                "reason":f"date_mismatch:{watchlist.get('date')}"}
    if watchlist.get("target_day_results_used") is not False or watchlist.get("payouts_used") is not False:
        raise RuntimeError("unsafe 1HEAD watchlist")

    out=[]
    for t in watchlist.get("targets",[]):
        if not t.get("deadline_jst"):
            continue
        raw_deadline=str(t["deadline_jst"])
        if "T" in raw_deadline:
            dl=datetime.fromisoformat(raw_deadline)
            if dl.tzinfo is None:
                dl=dl.replace(tzinfo=JST)
            dl=dl.astimezone(JST)
        else:
            hh,mm=map(int,raw_deadline.split(":"))
            dl=now.replace(hour=hh,minute=mm,second=0,microsecond=0)
        start=dl-timedelta(minutes=float(t.get("watch_minutes_before",35)))
        safe=dl-timedelta(seconds=SAFETY_SECONDS)
        code=str(t.get("race_code","")).zfill(12)
        jcd=f"{int(code[8:10]):02d}"
        race=int(code[10:12])
        artifact=f"head1-current-live-{day}-{jcd}-{race}"
        if artifact in completed:
            continue
        if start<=now<safe:
            out.append({
                "race_code":code,
                "deadline_jst":dl.isoformat(),
                "audit_run_id":str(audit_run_id),
                "artifact_name":artifact,
                "pre_band":str(t.get("pre_band","")),
            })
    out.sort(key=lambda x:(x["deadline_jst"],x["race_code"]))
    return {"date":day,"now_jst":now.isoformat(),"count":len(out),"include":out,"reason":"ok"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--watchlist",required=True)
    ap.add_argument("--audit-run-id",default="")
    ap.add_argument("--now-jst")
    ap.add_argument("--completed-names")
    ap.add_argument("--out")
    a=ap.parse_args()

    z=json.loads(Path(a.watchlist).read_text(encoding="utf-8"))
    completed=set()
    if a.completed_names and Path(a.completed_names).exists():
        completed={x.strip() for x in Path(a.completed_names).read_text(encoding="utf-8").splitlines() if x.strip()}
    r=resolve(z,parse_now(a.now_jst),completed,a.audit_run_id)
    if a.out:
        Path(a.out).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,separators=(",",":")))
    print("HEAD1_WATCHDOG_RESOLVE_OK",r["count"])


if __name__=="__main__":
    main()
