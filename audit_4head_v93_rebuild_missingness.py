#!/usr/bin/env python3
"""Diagnose why exact LIVE-parent v93 rebuild does not cover all parent rows."""
from __future__ import annotations
import csv,json,os
from pathlib import Path
from collections import Counter,defaultdict
import pandas as pd
from backtest import race_features
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"]); OUT=Path("/tmp/head4_v93_missingness");OUT.mkdir(exist_ok=True)
def rows(rel):
 p=ROOT/rel
 if not p.is_file():return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def rc(x):s=str(x).strip();return (s[:-2] if s.endswith(".0") else s).zfill(12)
def main():
 p=pd.read_csv(os.environ["PARENT_EXHIBITION"],dtype={"race_code":str});p["race_code"]=p.race_code.astype(str).str.zfill(12)
 r=pd.read_csv(os.environ["V93_REBUILT"],dtype={"race_code":str});r["race_code"]=r.race_code.astype(str).str.zfill(12);done=set(r.race_code)
 cnt=Counter(); monthly=defaultdict(Counter); venue=defaultdict(Counter); details=[]
 for _,x in p.iterrows():
  code=x.race_code; ds=str(x.date)[:10]; ymd=ds.replace("-","/"); jcd=code[8:10]; m=ds[:7]
  if code in done: reason="rebuilt"
  else:
   cards={rc(q.get("レースコード","")):q for q in rows(f"data/programs/race_cards/{ymd}.csv")}
   wakus={rc(q.get("レースコード","")):q for q in rows(f"data/programs/waku10/{ymd}.csv")}
   tkz={rc(q.get("レースコード","")):q for q in rows(f"data/previews/tkz/{ymd}.csv")}
   stt={rc(q.get("レースコード","")):q for q in rows(f"data/previews/stt/{ymd}.csv")}
   orig={rc(q.get("レースコード","")):q for q in rows(f"data/previews/original_exhibition/{ymd}.csv")}
   if code not in cards: reason="missing_race_card"
   elif code not in wakus: reason="missing_waku10"
   elif not race_features(cards[code],wakus[code]): reason="race_features_unavailable"
   elif code not in tkz: reason="missing_tkz"
   elif code not in stt: reason="missing_stt"
   elif code not in orig: reason="missing_original"
   elif not bool(x.get("basic_complete",False)): reason="stage1_basic_incomplete"
   else: reason="builder_logic_or_schema"
  cnt[reason]+=1;monthly[m][reason]+=1;venue[jcd][reason]+=1;details.append({"date":ds,"race_code":code,"jcd":jcd,"reason":reason})
 out={"total_parent":len(p),"reasons":dict(cnt),"by_month":{k:dict(v) for k,v in monthly.items()},"by_venue":{k:dict(v) for k,v in venue.items()},"SEPTEMBER_OUTCOMES_READ":False}
 pd.DataFrame(details).to_csv(OUT/"missingness_rows.csv",index=False);(OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n");print(json.dumps(out,ensure_ascii=False,indent=2));print("HEAD4_V93_MISSINGNESS_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
