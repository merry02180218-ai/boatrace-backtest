#!/usr/bin/env python3
"""Build clean-slate 4HEAD chronological research dataset, Nov 2025-Aug 2026.

All races are the starting universe. PRE features are prior-only. Exhibition
features are joined after PRE computation. Results are attached only after the
decision-time feature rows are frozen. No legacy v20/v74/v83/v93 eligibility
gate. September 2026 is blocked.
"""
from __future__ import annotations
import csv,json,os,sys
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"])
START=date.fromisoformat(os.environ.get("START_DATE","2025-11-01"))
END=date.fromisoformat(os.environ.get("END_DATE","2026-08-31"))
WARMUP=date.fromisoformat(os.environ.get("WARMUP_DATE","2025-10-01"))
if END>=date(2026,9,1): raise RuntimeError("SEPTEMBER_BLOCKED")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import analyze_4head_exhibition_original_trainonly as ex
def rows(rel):
 p=ROOT/rel
 if not p.is_file():return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def ff(x):
 try:return float(str(x).replace("%","").strip())
 except:return np.nan
def ii(x):
 try:return int(float(x))
 except:return 0
def rc(x):
 s=str(x or "").strip()
 if s.endswith(".0"):s=s[:-2]
 return s.zfill(12)
def venue(c):return str(c.get("レース場コード","")).zfill(2)
def mk(c,b):return (venue(c),str(c.get(f"艇{b}_モーター番号","")).strip())
def main():
 mh=defaultdict(lambda:[0,0]); ph=defaultdict(lambda:[0,0]); frozen=[]; truth={}; d=WARMUP
 while d<=END:
  ymd=d.strftime("%Y/%m/%d"); cards=rows(f"data/programs/race_cards/{ymd}.csv")
  if d>=START:
   for c in cards:
    a4,a3=mh[mk(c,4)],mh[mk(c,3)]
    w4=a4[0]/a4[1] if a4[1] else np.nan; w3=a3[0]/a3[1] if a3[1] else np.nan
    wd=w4-w3 if np.isfinite(w4) and np.isfinite(w3) else np.nan
    rd=ff(c.get("艇4_モーター2連対率"))-ff(c.get("艇3_モーター2連対率"))
    reg=str(c.get("艇4_登録番号","")).strip(); pp=ph[reg]; pw=pp[0]/pp[1] if pp[1] else np.nan
    frozen.append({"date":str(d),"month":d.strftime("%Y-%m"),"race_code":rc(c.get("レースコード","")),
      "venue":venue(c),"motor_win_diff_4v3":wd,"motor_2ren_diff_4v3":rd,"player4_all_win":pw,
      "pre_missing":int(not(np.isfinite(wd) and np.isfinite(rd) and np.isfinite(pw)))})
  rmap={rc(r.get("レースコード","")):r for r in rows(f"data/results/realtime/{ymd}.csv")}
  if d>=START:
   for k,r in rmap.items():
    w=ii(r.get("1着_艇番")); truth[k]={"winner":w,"head4":int(w==4) if w in range(1,7) else np.nan}
  for c in cards:
   rr=rmap.get(rc(c.get("レースコード",""))); w=ii((rr or {}).get("1着_艇番"))
   if w not in range(1,7):continue
   for b in range(1,7):
    k=mk(c,b)
    if k[1]:mh[k][1]+=1;mh[k][0]+=int(w==b)
    reg=str(c.get(f"艇{b}_登録番号","")).strip()
    if reg:ph[reg][1]+=1;ph[reg][0]+=int(w==b)
  d+=timedelta(days=1)
 q=pd.DataFrame(frozen); wanted=set(q.race_code)
 ex.rows=rows; ef=ex.build_ex(wanted); ef["race_code"]=ef.race_code.astype(str).str.zfill(12)
 z=q.merge(ef,on="race_code",how="left",validate="one_to_one")
 # Freeze all decision-time columns before attaching target.
 feature_cols=list(z.columns)
 tr=pd.DataFrame([{"race_code":k,**v} for k,v in truth.items()])
 z=z.merge(tr,on="race_code",how="left",validate="one_to_one")
 z["basic_complete"]=pd.to_numeric(z.get("basic_complete"),errors="coerce").fillna(0).astype(int)
 z["orig_avg_available"]=pd.to_numeric(z.get("orig_avg_available"),errors="coerce").fillna(0).astype(int)
 z["struct_ready"]=(z.basic_complete.eq(1)&z.orig_avg_available.eq(1)&
  pd.to_numeric(z.get("st4_adv_inside"),errors="coerce").notna()&
  pd.to_numeric(z.get("orig4_adv_inside"),errors="coerce").notna())
 by={}
 for m,g in z.groupby("month"):
  valid=g.head4.notna(); ready=g.struct_ready
  by[m]={"all_R":int(len(g)),"truth_R":int(valid.sum()),"struct_ready_R":int(ready.sum()),
   "struct_ready_rate":float(ready.mean()),"head4_all_R":int(g.loc[valid,"head4"].sum()),
   "head4_all_rate":float(g.loc[valid,"head4"].mean()) if valid.any() else None}
 out={"start":str(START),"end":str(END),"warmup":str(WARMUP),"all_R":int(len(z)),
  "feature_columns_frozen_before_truth":feature_cols,"by_month":by,
  "legacy_candidate_gate_used":False,"waku10_backfill_used":False,
  "SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 p=Path("/tmp/head4_clean_long_dataset");p.mkdir(exist_ok=True)
 z.to_csv(p/"dataset.csv",index=False);(p/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({k:v for k,v in out.items() if k!="feature_columns_frozen_before_truth"},ensure_ascii=False,indent=2))
 print("HEAD4_CLEAN_LONG_DATASET_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
