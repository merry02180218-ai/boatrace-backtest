#!/usr/bin/env python3
"""Clean-slate 4HEAD long-backtest coverage preflight.

This does NOT score or read target outcomes. It inventories the historical,
pre-decision inputs needed to extend the exact current-LIVE replay to >=6 months.
No legacy v20/v74/v83 eligibility gate is applied. No Waku10 reconstruction.
September 2026 is blocked.
"""
from __future__ import annotations
import csv,json,os
from datetime import date,timedelta
from pathlib import Path
from collections import defaultdict

ROOT=Path(os.environ.get("BOATRACECSV_LOCAL_ROOT","."))
START=date.fromisoformat(os.environ.get("START_DATE","2025-11-01"))
END=date.fromisoformat(os.environ.get("END_DATE","2026-08-31"))
if END>=date(2026,9,1): raise RuntimeError("SEPTEMBER_BLOCKED")

def rows(rel):
 p=ROOT/rel
 if not p.is_file(): return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def rc(x):
 s=str(x or "").strip()
 if s.endswith(".0"):s=s[:-2]
 return s.zfill(12)

def codes(rel):
 return {rc(r.get("レースコード","")) for r in rows(rel) if r.get("レースコード")}

def main():
 bym=defaultdict(lambda:defaultdict(int)); d=START
 while d<=END:
  y=d.strftime("%Y/%m/%d"); m=d.strftime("%Y-%m")
  card=codes(f"data/programs/race_cards/{y}.csv")
  tkz=codes(f"data/previews/tkz/{y}.csv")
  stt=codes(f"data/previews/stt/{y}.csv")
  orig=codes(f"data/previews/original_exhibition/{y}.csv")
  od3=codes(f"data/previews/od3/{y}.csv")
  x=bym[m]; x["days"]+=1; x["card_R"]+=len(card)
  for name,s in (("tkz",tkz),("stt",stt),("orig",orig),("od3",od3)):
   x[name+"_R"]+=len(card&s); x[name+"_day"]+=int(bool(s))
  x["exhibition_all3_R"]+=len(card&tkz&stt&orig)
  x["preclose_all4_R"]+=len(card&tkz&stt&orig&od3)
  d+=timedelta(days=1)
 out={"start":str(START),"end":str(END),"policy":"CLEAN_SLATE_NO_LEGACY_GATE__NO_WAKU10_BACKFILL","by_month":{},"SEPTEMBER_OUTCOMES_READ":False}
 for m,x in sorted(bym.items()):
  n=x["card_R"]
  out["by_month"][m]={**x,
   "exhibition_all3_rate":x["exhibition_all3_R"]/n if n else 0,
   "preclose_all4_rate":x["preclose_all4_R"]/n if n else 0}
 print(json.dumps(out,ensure_ascii=False,indent=2))
 Path("/tmp/head4_long_preflight").mkdir(exist_ok=True)
 Path("/tmp/head4_long_preflight/result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print("HEAD4_LONG_BACKTEST_PREFLIGHT_OK")
 print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
