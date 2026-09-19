#!/usr/bin/env python3
"""Build a result-blind 1HEAD unified PRE feed from the prepared v351 daily cache."""
import argparse,csv,glob,json,subprocess
from pathlib import Path

def deadline(date,jcd,race):
 p=subprocess.run(["python","fetch_boatrace_deadline.py","--date",date,"--jcd",str(jcd),"--race",str(race)],capture_output=True,text=True,check=True)
 return p.stdout.strip().splitlines()[-1][-5:]

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--date",required=True);ap.add_argument("--cache-dir",required=True);ap.add_argument("--run-id",required=True);ap.add_argument("--artifact",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 day=a.date.replace("-",""); rows=[]
 pc=Path(a.cache_dir)/"pre_candidates.csv"
 with pc.open(newline="",encoding="utf-8") as f:
  for r in csv.DictReader(f):
   cls=(r.get("pre_class") or "").strip()
   if not cls: continue
   code=str(r["race_code"]).zfill(12);jcd=int(code[8:10]);race=int(code[10:12])
   rows.append({"model":"1HEAD","adapter":"1head_v351","jcd":f"{jcd:02d}","race":race,"race_code":code,
    "deadline_jst":deadline(day,jcd,race),"watch_minutes_before":35,"pre_class":cls,
    "source":{"pre_run_id":str(a.run_id),"pre_artifact_name":a.artifact},
    "model_payload":{"head_p":r.get("head_p"),"base_tickets":r.get("base_tickets")},
    "result_or_payout_used":False,"chronology_guard":True})
 rows.sort(key=lambda x:(x["deadline_jst"],x["jcd"],x["race"]))
 out={"schema":"unified-head-pre-feed-v1","date":day,"model":"1HEAD","source_profile":"v351",
 "target_day_results_used":False,"payouts_used":False,"targets":rows}
 Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("UNIFIED_1HEAD_PRE_FEED_OK",len(rows))
if __name__=="__main__":main()
