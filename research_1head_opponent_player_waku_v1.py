#!/usr/bin/env python3
"""1HEAD opponent PLAYER_HISTORY + Waku10 DEV diagnostic.
Frozen H078/M375 parent only. No production mutation. September outcomes unread.
"""
import argparse,json,pickle,os
from pathlib import Path
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import run_1head_player_history_expansion as phbase
import research_4head_waku10_rel43_v4 as wsrc
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-opponent-ph-waku-v1"; OUT.mkdir(parents=True,exist_ok=True)
DEV=("2026-02","2026-03","2026-04","2026-05","2026-06"); SUP=("2026-07","2026-08")
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--prepared",required=True,type=Path); a=ap.parse_args()
 x=pickle.load(open(a.prepared,"rb")); rr=x["rows"]
 if len(rr["LIVE165"])!=165 or len(rr["H078_M375"])!=236: raise RuntimeError("frozen universe drift")
 live={str(r["race_code"]).zfill(12) for r in rr["LIVE165"]}
 # Start from the full H078/M375 universe; formal/PH head selection remains frozen downstream.
 d=pd.DataFrame(rr["H078_M375"]); d["race_code"]=d.race_code.astype(str).str.zfill(12)
 d["month"]=d.race_code.str.slice(0,4)+"-"+d.race_code.str.slice(4,6)
 d=d[d.month.isin(DEV+SUP)].copy()
 target_codes=set(d.race_code)
 from datetime import date
 phrows=phbase.build_canonical_ph_snapshots(target_codes,date(2025,10,1),date(2026,8,31),os.environ["BOATRACECSV_LOCAL_ROOT"])
 ph=pd.DataFrame([{"race_code":k,**v} for k,v in phrows.items()])
 ph["race_code"]=ph.race_code.astype(str).str.zfill(12)
 w=wsrc.build_waku(d.race_code.tolist()); w["race_code"]=w.race_code.astype(str).str.zfill(12)
 z=d.merge(ph,on="race_code",how="left",validate="one_to_one",suffixes=("","_ph")).merge(w,on="race_code",how="left",validate="one_to_one")
 rows=[]
 for _,r in z.iterrows():
  parts=str(r.actual_combo).split("-"); actual=set(map(int,parts[1:])) if len(parts)==3 and parts[0]=="1" else set()
  for b in (2,3,4,5,6):
   q={"race_code":r.race_code,"month":str(r.month),"boat":b,"actual_opponent":int(b in actual)}
   for k in ("all_win","all_p2","frame_win","frame_p2","recent_p2"): q["pl_"+k]=r.get(f"b{b}_pl_{k}")
   for col in w.columns:
    cl=col.lower()
    if col!="race_code" and (f"b{b}" in cl or f"_{b}_" in cl): q["waku__"+col]=r.get(col)
   rows.append(q)
 q=pd.DataFrame(rows); q.to_csv(OUT/"boat_rows.csv",index=False)
 dev=q[q.month.isin(DEV)]; sig=[]
 for col in [x for x in q.columns if x.startswith("pl_") or x.startswith("waku__")]:
  x=pd.to_numeric(dev[col],errors="coerce"); y=dev.actual_opponent
  if x.notna().sum()<30: continue
  sig.append({"feature":col,"n":int(x.notna().sum()),"actual_mean":float(x[y.eq(1)].mean()),"other_mean":float(x[y.eq(0)].mean()),"delta":float(x[y.eq(1)].mean()-x[y.eq(0)].mean())})
 s=pd.DataFrame(sig)
 if len(s): s=s.sort_values("delta",key=lambda x:x.abs(),ascending=False)
 s.to_csv(OUT/"dev_signal.csv",index=False)
 # DEV-only transparent opponent-membership reranker. SUPPORT labels remain unopened here.
 feats=[x for x in q.columns if x.startswith("pl_") or x.startswith("waku__")]
 usable=[x for x in feats if pd.to_numeric(dev[x],errors="coerce").notna().sum()>=30]
 X=dev[usable].apply(pd.to_numeric,errors="coerce"); y=dev.actual_opponent.astype(int)
 model=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(C=.25,max_iter=2000,class_weight="balanced"))])
 model.fit(X,y)
 q["opp_score"]=model.predict_proba(q[usable].apply(pd.to_numeric,errors="coerce"))[:,1]
 # Result-free frozen ranking output; evaluation of SUPPORT will be a separate next stage.
 rank=q.sort_values(["race_code","opp_score"],ascending=[True,False]).copy()
 rank["opp_rank"]=rank.groupby("race_code").cumcount()+1
 rank.to_csv(OUT/"frozen_opponent_ranking.csv",index=False)
 coef=model.named_steps["lr"].coef_[0]
 cf=pd.DataFrame({"feature":usable,"coef":coef}).sort_values("coef",key=lambda s:s.abs(),ascending=False)
 cf.to_csv(OUT/"dev_model_coefficients.csv",index=False)
 meta={"stage":"DEV_MODEL_FROZEN","parent_R":int(z.race_code.nunique()),"dev_R":int(z[z.month.isin(DEV)].race_code.nunique()),"support_R":int(z[z.month.isin(SUP)].race_code.nunique()),"selection_used_support_outcomes":False,"september_outcomes_read":False,"production_changed":False,"ph_missing":int(z["b1_pl_recent_p2"].isna().sum()),"waku_columns":int(len(w.columns)-1),"model_features":len(usable),"top_model_coefficients":cf.head(20).to_dict("records"),"top":s.head(20).to_dict("records") if len(s) else []}
 (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)); print(json.dumps(meta,ensure_ascii=False))
if __name__=="__main__": main()
