#!/usr/bin/env python3
"""Add current exhibition/original-exhibition features to clean 6m 4HEAD baseline.
The .36 baseline was selected using Jun only. This audit does not tune a new
production gate: it reports fixed, interpretable exhibition strata on DEV/VAL/
HOLD separately. Jul-Aug remains evaluation only. September blocked.
"""
from __future__ import annotations
import csv,json,math,os,sys
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"]);OUT=Path("/tmp/head4_clean_6m_exhibition");OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parent))
import analyze_4head_exhibition_original_trainonly as ex
START=date(2026,3,1);END=date(2026,8,31);DEV={"2026-03","2026-04","2026-05"};VAL={"2026-06"};HOLD={"2026-07","2026-08"}
def rows(rel):
 p=ROOT/rel
 if not p.is_file():return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def ff(x):
 try:
  v=float(str(x).replace("%","").strip());return v if math.isfinite(v) else np.nan
 except:return np.nan
def ii(x):
 try:return int(float(x))
 except:return 0
def rc(x):
 s=str(x or "").strip()
 if s.endswith(".0"):s=s[:-2]
 return s.zfill(12)
def bc(cols,b,*ns):
 tags=[f"艇{b}",f"{b}枠",f"{b}号艇"]
 for c in cols:
  s=str(c)
  if any(t in s for t in tags) and all(n.lower() in s.lower() for n in ns):return c
 return None
def main():
 raw=[];d=START
 specs={"national_win":("全国","勝率"),"national_top2":("全国","2連"),"national_top3":("全国","3連"),"local_win":("当地","勝率"),"local_top2":("当地","2連"),"local_top3":("当地","3連"),"motor_top2":("モーター","2連"),"motor_top3":("モーター","3連"),"boat_top2":("ボート","2連"),"boat_top3":("ボート","3連"),"avg_st":("平均","ST")}
 while d<=END:
  y=d.strftime("%Y/%m/%d");cards=rows(f"data/programs/race_cards/{y}.csv");rm={rc(r.get("レースコード")):r for r in rows(f"data/results/realtime/{y}.csv")}
  for x in cards:
   code=rc(x.get("レースコード"));w=ii((rm.get(code) or {}).get("1着_艇番"))
   if w not in range(1,7):continue
   r={"date":str(d),"month":d.strftime("%Y-%m"),"race_code":code,"head4":int(w==4)};cols=list(x)
   for b in range(1,7):
    for n,ns in specs.items():
     c=bc(cols,b,*ns);r[f"b{b}_{n}"]=ff(x.get(c)) if c else np.nan
   raw.append(r)
  d+=timedelta(days=1)
 z=pd.DataFrame(raw);feats=[c for c in z if c.startswith("b") and z[c].notna().mean()>=.25]
 tr=z[z.month.isin(DEV)].copy();va=z[z.month.isin(VAL)].copy();ho=z[z.month.isin(HOLD)].copy()
 pipe=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=2000,C=.5))]);pipe.fit(tr[feats],tr.head4)
 for q in (tr,va,ho):q["p"]=pipe.predict_proba(q[feats])[:,1]
 z=pd.concat([tr,va,ho]);base=z[z.p>=.36].copy()
 ex.rows=rows;ef=ex.build_ex(set(base.race_code));ef["race_code"]=ef.race_code.astype(str).str.zfill(12);base=base.merge(ef,on="race_code",how="left")
 base["ready"]=pd.to_numeric(base.basic_complete,errors="coerce").fillna(0).eq(1)&pd.to_numeric(base.orig_avg_available,errors="coerce").fillna(0).eq(1)
 tests={"BASE":np.ones(len(base),dtype=bool),"READY":base.ready,
  "ST_GE_M080":base.ready&pd.to_numeric(base.st4_adv_inside,errors="coerce").ge(-.80),
  "ST_GE_M060":base.ready&pd.to_numeric(base.st4_adv_inside,errors="coerce").ge(-.60),
  "ORIG_GE_M035":base.ready&pd.to_numeric(base.orig4_adv_inside,errors="coerce").ge(-.35),
  "ORIG_GE_M006":base.ready&pd.to_numeric(base.orig4_adv_inside,errors="coerce").ge(-.06),
  "ST_M080_ORIG_M035":base.ready&pd.to_numeric(base.st4_adv_inside,errors="coerce").ge(-.80)&pd.to_numeric(base.orig4_adv_inside,errors="coerce").ge(-.35),
  "ST_M060_ORIG_M006":base.ready&pd.to_numeric(base.st4_adv_inside,errors="coerce").ge(-.60)&pd.to_numeric(base.orig4_adv_inside,errors="coerce").ge(-.06)}
 rec=[]
 for name,mask in tests.items():
  for per,months in [("DEV_MAR_MAY",DEV),("VAL_JUN",VAL),("HOLD_JUL_AUG",HOLD)]:
   s=base[mask&base.month.isin(months)];rec.append({"gate":name,"period":per,"R":len(s),"H":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
 out={"baseline_cut":.36,"baseline_R":len(base),"tests":rec,"thresholds_predeclared_from_current_live_structures":True,"holdout_used_for_tuning":False,"legacy_candidate_gate_used":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 pd.DataFrame(rec).to_csv(OUT/"gate_compare.csv",index=False);base.to_csv(OUT/"detail.csv",index=False);(OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(out,ensure_ascii=False,indent=2));print("HEAD4_CLEAN_6M_EXHIBITION_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
