#!/usr/bin/env python3
"""Exact all-race PRE-parent -> exhibition structural coverage audit.
Apr-Aug only; September outcomes/odds are blocked. Production unchanged.
This stage deliberately proves whether the archive can carry the exact LIVE
parent into post-exhibition scoring before claiming final-BET parity.
"""
from __future__ import annotations
import csv,json,os,sys
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"]); START=date(2025,10,1); A=date(2026,4,1); B=date(2026,8,31)
WIN=-0.0299361318939513; REN2=-7.080000000000001; PLAYER=.215605
sys.path.insert(0,str(Path(__file__).resolve().parent))
import analyze_4head_exhibition_original_trainonly as ex
def rows(rel):
 p=ROOT/rel
 if not p.is_file(): return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def ff(x):
 try:return float(str(x).replace("%","").strip())
 except:return np.nan
def ii(x):
 try:return int(float(x))
 except:return 0
def rc(x):
 s=str(x).strip()
 if s.endswith(".0"):s=s[:-2]
 return s.zfill(12)
def venue(c):return str(c.get("レース場コード","")).zfill(2)
def mk(c,b):return (venue(c),str(c.get(f"艇{b}_モーター番号","")).strip())
def main():
 mh=defaultdict(lambda:[0,0]); ph=defaultdict(lambda:[0,0]); parent=[]; d=START
 while d<=B:
  ymd=d.strftime("%Y/%m/%d"); cards=rows(f"data/programs/race_cards/{ymd}.csv")
  if d>=A:
   for c in cards:
    a4=mh[mk(c,4)]; a3=mh[mk(c,3)]
    w4=a4[0]/a4[1] if a4[1] else np.nan; w3=a3[0]/a3[1] if a3[1] else np.nan
    wd=w4-w3 if np.isfinite(w4) and np.isfinite(w3) else np.nan
    rd=ff(c.get("艇4_モーター2連対率"))-ff(c.get("艇3_モーター2連対率"))
    reg=str(c.get("艇4_登録番号","")).strip(); pp=ph[reg]; pw=pp[0]/pp[1] if pp[1] else np.nan
    miss=not(np.isfinite(wd) and np.isfinite(rd) and np.isfinite(pw))
    if miss or (wd>=WIN and rd>=REN2 and pw>=PLAYER):
     parent.append({"date":str(d),"race_code":rc(c.get("レースコード","")),"parent_missing":int(miss)})
  rmap={rc(r.get("レースコード","")):r for r in rows(f"data/results/realtime/{ymd}.csv")}
  for c in cards:
   rr=rmap.get(rc(c.get("レースコード",""))); w=ii((rr or {}).get("1着_艇番"))
   if w not in range(1,7):continue
   for b in range(1,7):
    k=mk(c,b)
    if k[1]:mh[k][1]+=1;mh[k][0]+=int(w==b)
    reg=str(c.get(f"艇{b}_登録番号","")).strip()
    if reg:ph[reg][1]+=1;ph[reg][0]+=int(w==b)
  d+=timedelta(days=1)
 q=pd.DataFrame(parent); wanted=set(q.race_code)
 # Rebind archive reader so exhibition builder uses the exact checked-out historical tree.
 ex.rows=rows
 ef=ex.build_ex(wanted); ef["race_code"]=ef.race_code.astype(str).str.zfill(12)
 z=q.merge(ef,on="race_code",how="left",validate="one_to_one")
 z["basic_complete"]=pd.to_numeric(z.basic_complete,errors="coerce").fillna(0).astype(int)
 z["orig_avg_available"]=pd.to_numeric(z.orig_avg_available,errors="coerce").fillna(0).astype(int)
 z["struct_ready"]=z.basic_complete.eq(1)&z.orig_avg_available.eq(1)&pd.to_numeric(z.st4_adv_inside,errors="coerce").notna()&pd.to_numeric(z.orig4_adv_inside,errors="coerce").notna()
 z["old164_struct"]=z.struct_ready&pd.to_numeric(z.st4_adv_inside,errors="coerce").ge(-.6000000000000001)&pd.to_numeric(z.orig4_adv_inside,errors="coerce").ge(-.057777777777777706)
 z["newfeature_struct"]=z.struct_ready&pd.to_numeric(z.st4_adv_inside,errors="coerce").ge(-.80)&pd.to_numeric(z.orig4_adv_inside,errors="coerce").ge(-.35)
 daily=z.groupby("date").agg(parent=("race_code","size"),struct_ready=("struct_ready","sum"),old164_struct=("old164_struct","sum"),newfeature_struct=("newfeature_struct","sum"))
 out={"parent_R":int(len(z)),"days":int(daily.shape[0]),"struct_ready_R":int(z.struct_ready.sum()),"struct_ready_rate":float(z.struct_ready.mean()),"old164_struct_R":int(z.old164_struct.sum()),"newfeature_struct_R":int(z.newfeature_struct.sum()),"daily":{"parent_mean":float(daily.parent.mean()),"struct_ready_mean":float(daily.struct_ready.mean()),"newfeature_struct_mean":float(daily.newfeature_struct.mean()),"newfeature_struct_p95":float(daily.newfeature_struct.quantile(.95)),"newfeature_struct_max":int(daily.newfeature_struct.max())},"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 Path("/tmp/head4_exact_final").mkdir(exist_ok=True); z.to_csv("/tmp/head4_exact_final/parent_exhibition.csv",index=False); Path("/tmp/head4_exact_final/result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(out,ensure_ascii=False,indent=2)); print("HEAD4_EXACT_FINAL_STAGE1_OK"); print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
