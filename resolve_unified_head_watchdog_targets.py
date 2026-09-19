#!/usr/bin/env python3
"""Resolve active targets from a model-tagged unified HEAD live watchlist."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

JST=ZoneInfo("Asia/Tokyo")
SAFETY_SECONDS=75
ALLOWED_MODELS={"1HEAD","4HEAD"}

def parse_now(v):
    if not v:return datetime.now(JST)
    d=datetime.fromisoformat(v)
    if d.tzinfo is None:d=d.replace(tzinfo=JST)
    return d.astimezone(JST)

def resolve(z,now,completed=None):
    completed=completed or set(); day=now.strftime("%Y%m%d"); out=[]
    if str(z.get("date",""))!=day:
        return {"date":day,"now_jst":now.isoformat(),"count":0,"include":[],"reason":"date_mismatch:"+str(z.get("date"))}
    for t in z.get("targets",[]):
        model=str(t["model"]).upper()
        if model not in ALLOWED_MODELS: raise ValueError("unsupported model "+model)
        hh,mm=map(int,str(t["deadline_jst"]).split(":"))
        dl=now.replace(hour=hh,minute=mm,second=0,microsecond=0)
        start=dl-timedelta(minutes=float(t.get("watch_minutes_before",35)))
        if not(start<=now<dl-timedelta(seconds=SAFETY_SECONDS)):continue
        jcd=f'{int(t["jcd"]):02d}'; race=int(t["race"])
        artifact=str(t.get("artifact_name") or f'head-live-{model.lower()}-{day}-{jcd}-{race}')
        if artifact in completed:continue
        x=dict(t); x.update(model=model,target_date=day,jcd=jcd,race=race,
          race_code=str(t.get("race_code") or f"{day}{jcd}{race:02d}"),artifact_name=artifact)
        out.append(x)
    out.sort(key=lambda x:(x["deadline_jst"],x["model"],x["jcd"],x["race"]))
    return {"date":day,"now_jst":now.isoformat(),"count":len(out),"include":out,"reason":"ok"}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--watchlist",required=True);ap.add_argument("--now-jst")
    ap.add_argument("--completed-names");ap.add_argument("--out");a=ap.parse_args()
    z=json.loads(Path(a.watchlist).read_text(encoding="utf-8")); completed=set()
    if a.completed_names and Path(a.completed_names).exists():
        completed={x.strip() for x in Path(a.completed_names).read_text().splitlines() if x.strip()}
    r=resolve(z,parse_now(a.now_jst),completed)
    if a.out:Path(a.out).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,separators=(",",":")));print("UNIFIED_HEAD_WATCHDOG_RESOLVE_OK",r["count"])
if __name__=="__main__":main()
