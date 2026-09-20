#!/usr/bin/env python3
"""Six-month clean-slate 4HEAD chronological head-model baseline.
Train Mar-May; validation Jun; untouched holdout Jul-Aug. Uses only race-card
pre-race features in this first baseline. No legacy candidate gate/Waku10.
September blocked. Research only.
"""
from __future__ import annotations
import csv,json,math,os
from datetime import date,timedelta
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
ROOT=Path(os.environ["BOATRACECSV_LOCAL_ROOT"]); OUT=Path("/tmp/head4_clean_6m_headmodel");OUT.mkdir(exist_ok=True)
START=date(2026,3,1); END=date(2026,8,31)
DEV={"2026-03","2026-04","2026-05"}; VAL={"2026-06"}; HOLD={"2026-07","2026-08"}
def rows(rel):
 p=ROOT/rel
 if not p.is_file():return []
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def ff(x):
 try:
  v=float(str(x).replace("%","").strip()); return v if math.isfinite(v) else np.nan
 except:return np.nan
def ii(x):
 try:return int(float(x))
 except:return 0
def rc(x):
 s=str(x or "").strip()
 if s.endswith(".0"):s=s[:-2]
 return s.zfill(12)
def boat_col(cols,b,*needles):
 tags=[f"艇{b}",f"{b}枠",f"{b}号艇"]
 for c in cols:
  s=str(c)
  if any(t in s for t in tags) and all(n.lower() in s.lower() for n in needles):return c
 return None
def main():
 out=[]; d=START
 while d<=END:
  ymd=d.strftime("%Y/%m/%d"); cards=rows(f"data/programs/race_cards/{ymd}.csv"); res=rows(f"data/results/realtime/{ymd}.csv")
  rm={rc(x.get("レースコード")):x for x in res}
  for x in cards:
   code=rc(x.get("レースコード")); y=rm.get(code); w=ii((y or {}).get("1着_艇番"))
   if w not in range(1,7):continue
   r={"date":str(d),"month":d.strftime("%Y-%m"),"race_code":code,"head4":int(w==4)}
   cols=list(x)
   specs={"national_win":("全国","勝率"),"national_top2":("全国","2連"),"national_top3":("全国","3連"),
    "local_win":("当地","勝率"),"local_top2":("当地","2連"),"local_top3":("当地","3連"),
    "motor_top2":("モーター","2連"),"motor_top3":("モーター","3連"),"boat_top2":("ボート","2連"),
    "boat_top3":("ボート","3連"),"avg_st":("平均","ST")}
   for b in range(1,7):
    for n,ns in specs.items():
     c=boat_col(cols,b,*ns);r[f"b{b}_{n}"]=ff(x.get(c)) if c else np.nan
   out.append(r)
  d+=timedelta(days=1)
 z=pd.DataFrame(out); feats=[c for c in z if c.startswith("b") and z[c].notna().mean()>=.25]
 tr=z[z.month.isin(DEV)].copy(); va=z[z.month.isin(VAL)].copy(); ho=z[z.month.isin(HOLD)].copy()
 pipe=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=2000,C=.5))])
 pipe.fit(tr[feats],tr.head4)
 for q in (tr,va,ho):q["p"]=pipe.predict_proba(q[feats])[:,1]
 cuts=np.arange(.10,.401,.01); sweep=[]
 for cut in cuts:
  for name,q in [("DEV_MAR_MAY",tr),("VAL_JUN",va),("HOLD_JUL_AUG",ho)]:
   s=q[q.p>=cut];sweep.append({"cut":round(float(cut),2),"period":name,"R":len(s),"head4":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None,"per_month":len(s)/(3 if name=="DEV_MAR_MAY" else 1 if name=="VAL_JUN" else 2)})
 sw=pd.DataFrame(sweep)
 # Selection is based ONLY on DEV+VAL, never HOLD: require >=50/month validation and maximize validation rate, tie by support.
 v=sw[(sw.period=="VAL_JUN")&(sw.R>=50)].sort_values(["rate","R"],ascending=[False,False])
 chosen=float(v.iloc[0].cut) if len(v) else .10
 summary={"all_R":len(z),"features":len(feats),"split":{"dev_R":len(tr),"val_R":len(va),"holdout_R":len(ho)},
  "chosen_cut_from_validation_only":chosen,"chosen_metrics":sw[sw.cut.eq(chosen)].to_dict("records"),
  "holdout_used_for_selection":False,"legacy_candidate_gate_used":False,"waku10_used":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 sw.to_csv(OUT/"threshold_sweep.csv",index=False);pd.concat([tr,va,ho]).to_csv(OUT/"scored.csv",index=False)
 (OUT/"result.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps(summary,ensure_ascii=False,indent=2));print("HEAD4_CLEAN_6M_BASELINE_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
