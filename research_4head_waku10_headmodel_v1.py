#!/usr/bin/env python3
"""Waku10 incremental 4HEAD study. Mar-May train, Jun validation, Jul-Aug holdout. September unread."""
import os,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv"); OUT=Path("/tmp/head4_waku10_headmodel_v1");OUT.mkdir(exist_ok=True)
DEV={"2026-03","2026-04","2026-05"};VAL={"2026-06"};HOLD={"2026-07","2026-08"}
def fit_score(tr,qs,feats):
 p=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.5))]);p.fit(tr[feats],tr.head4)
 return [p.predict_proba(q[feats])[:,1] for q in qs]
def main():
 z=pd.read_csv(BASE,dtype={"race_code":str}); z["race_code"]=z.race_code.astype(str).str.zfill(12); z["month"]=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 # Rebuilt v93 parent is intentionally pre-result only. Attach target from the clean dataset only after predictor rows are frozen.
 truth=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",usecols=["race_code","head4"],dtype={"race_code":str})
 truth["race_code"]=truth.race_code.astype(str).str.zfill(12); truth["head4"]=pd.to_numeric(truth.head4,errors="coerce")
 z=z.merge(truth,on="race_code",how="left",validate="one_to_one"); target="head4"
 z=z[z.head4.isin([0,1])].copy()
 numeric=[c for c in z.columns if c not in {target,"head4","race_code","month"} and pd.to_numeric(z[c],errors="coerce").notna().mean()>=.25]
 forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
 numeric=[c for c in numeric if not any(k.lower() in c.lower() for k in forbidden)]
 waku=[c for c in numeric if c.lower().startswith("opp_waku_b")]
 base=[c for c in numeric if c not in waku]
 if not waku: raise RuntimeError("NO_WAKU_FEATURES")
 tr=z[z.month.isin(DEV)].copy();va=z[z.month.isin(VAL)].copy();ho=z[z.month.isin(HOLD)].copy()
 rows=[]
 for label,feats in [("BASE",base),("BASE_WAKU",base+waku)]:
  ps=fit_score(tr,[tr,va,ho],feats)
  for q,p in zip((tr,va,ho),ps): q[label]=p
  # choose threshold on June only, >=50 selections; holdout never selects.
  cand=[]
  for cut in np.arange(.10,.501,.01):
   s=va[va[label]>=cut]
   if len(s)>=50:cand.append((float(s.head4.mean()),len(s),float(cut)))
  chosen=sorted(cand,reverse=True)[0][2]
  for period,q in [("DEV",tr),("VAL",va),("HOLD",ho)]:
   s=q[q[label]>=chosen];rows.append({"model":label,"period":period,"cut":chosen,"R":len(s),"head4":int(s.head4.sum()),"rate":float(s.head4.mean()) if len(s) else None})
 pd.DataFrame(rows).to_csv(OUT/"comparison.csv",index=False)
 meta={"R":len(z),"base_features":len(base),"waku_features":len(waku),"waku_feature_names":waku,"target_source":"clean_dataset_head4_attached_after_pre_result_parent","holdout_used_for_selection":False,"RESULT_FILES_READ":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n");print(pd.DataFrame(rows).to_string(index=False));print(meta);print("WAKU10_HEADMODEL_V1_OK")
if __name__=="__main__":main()
