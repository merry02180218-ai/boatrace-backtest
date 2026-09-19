#!/usr/bin/env python3
"""Merge model-owned PRE target feeds into one deadline-ordered unified watchlist.

Input feeds are JSON objects with date and targets. Each target must already be
selected by its model's PRE producer. This script does not score or retune models.
"""
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",required=True)
    ap.add_argument("--feed",action="append",required=True,help="JSON feed path; repeatable")
    ap.add_argument("--out",required=True)
    a=ap.parse_args(); targets=[]; sources=[]
    for fp in a.feed:
        z=json.loads(Path(fp).read_text(encoding="utf-8"))
        if str(z.get("date","")).replace("-","") != a.date:
            raise SystemExit(f"date mismatch {fp}: {z.get('date')} != {a.date}")
        sources.append({"path":fp,"model":z.get("model"),"target_count":len(z.get("targets",[]))})
        for raw in z.get("targets",[]):
            t=dict(raw); model=str(t.get("model") or z.get("model") or "").upper()
            if not model.endswith("HEAD"): raise SystemExit(f"missing/invalid model in {fp}: {model}")
            t["model"]=model; t.setdefault("adapter",model.lower())
            t.setdefault("watch_minutes_before",35)
            t["jcd"]=f'{int(t["jcd"]):02d}';t["race"]=int(t["race"])
            t.setdefault("race_code",f'{a.date}{t["jcd"]}{t["race"]:02d}')
            t.setdefault("artifact_name",f'head-live-{model.lower()}-{a.date}-{t["jcd"]}-{t["race"]}')
            targets.append(t)
    targets.sort(key=lambda x:(x["deadline_jst"],x["model"],x["jcd"],x["race"]))
    out={"schema":"unified-head-watchlist-v1","date":a.date,"target_count":len(targets),
         "models":sorted({x["model"] for x in targets}),"sources":sources,
         "target_day_results_used":False,"payouts_used":False,"targets":targets}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("UNIFIED_HEAD_WATCHLIST_OK",len(targets),",".join(out["models"]))
if __name__=="__main__":main()
