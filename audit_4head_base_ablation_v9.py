#!/usr/bin/env python3
"""BASE feature-family ablation audit. Fixed .35 cut, Mar-May train; no tuning."""
import json
from pathlib import Path
import pandas as pd,numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
BASE=Path("/tmp/head4_v93_all_parent/v93_all_parent.csv")
DEV={"2026-03","2026-04","2026-05"}
CUT=.35
def fit(tr,feats):
 p=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(max_iter=3000,C=.5))]);p.fit(tr[feats],tr.head4);return p
def family(c):
 if c.startswith("opp_direct_"): return "DIRECT"
 if c.startswith("opp_motor_"): return "MOTOR"
 if c.startswith("opp_nst_"): return "NST"
 if c.startswith("opp_waku_"): return "WAKU_OLD"
 if c.startswith("opp_grade_"): return "GRADE"
 if c.startswith("opp_national_"): return "NATIONAL"
 if c.startswith("opp_local_"): return "LOCAL"
 if "_pl_" in c: return "PLAYER_HISTORY"
 return "OTHER"
def main():
 z=pd.read_csv(BASE,dtype={"race_code":str});z.race_code=z.race_code.astype(str).str.zfill(12);z["month"]=z.race_code.str[:4]+"-"+z.race_code.str[4:6]
 truth=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",usecols=["race_code","head4"],dtype={"race_code":str});truth.race_code=truth.race_code.astype(str).str.zfill(12)
 z=z.merge(truth,on="race_code",how="left",validate="one_to_one");z=z[z.head4.isin([0,1])].copy()
 forbidden=("actual","result","payout","odds","finish","着順","1着","2着","3着")
 feats=[c for c in z.columns if c not in {"head4","race_code","month"} and pd.to_numeric(z[c],errors="coerce").notna().mean()>=.25 and not any(k.lower() in c.lower() for k in forbidden)]
 # Match Waku research BASE: remove old Waku columns.
 feats=[c for c in feats if not c.startswith("opp_waku_b")]
 fams={f:[c for c in feats if family(c)==f] for f in sorted(set(family(c) for c in feats))}
 variants={"BASE":feats}
 for f,cols in fams.items():
  if cols: variants["DROP_"+f]=[c for c in feats if c not in cols]
 tr=z[z.month.isin(DEV)]
 rows=[];coef=[]
 for label,fs in variants.items():
  p=fit(tr,fs);score=p.predict_proba(z[fs])[:,1];sel=z[score>=CUT]
  for m,g in sel.groupby("month"): rows.append({"model":label,"month":m,"R":len(g),"head4":int(g.head4.sum()),"rate":float(g.head4.mean())})
  if label=="BASE":
   cs=p.named_steps["lr"].coef_[0]
   for c,v in sorted(zip(fs,cs),key=lambda x:abs(x[1]),reverse=True):coef.append({"feature":c,"family":family(c),"coef_std":float(v)})
 out=Path("/tmp/head4_base_ablation_v9");out.mkdir(exist_ok=True)
 pd.DataFrame(rows).to_csv(out/"monthly.csv",index=False);pd.DataFrame(coef).to_csv(out/"coefficients.csv",index=False)
 meta={"cut":CUT,"train":"2026-03..05","families":{k:len(v) for k,v in fams.items()},"threshold_retuned":False,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (out/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
 print("FAMILIES",json.dumps(meta,ensure_ascii=False));print("MONTHLY\n"+pd.DataFrame(rows).to_string(index=False));print("TOP_COEF\n"+pd.DataFrame(coef).head(30).to_string(index=False));print("HEAD4_BASE_ABLATION_V9_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
