#!/usr/bin/env python3
"""v14: diagnose wins vs losses inside frozen 4HEAD candidates. Descriptive only, no threshold tuning."""
import json
from pathlib import Path
import numpy as np,pandas as pd
import audit_4head_frozen_ph_rel43_v13 as v13
OUT=Path("/tmp/head4_frozen_winloss_v14");OUT.mkdir(exist_ok=True)
def main():
 v13.main()
 z=pd.read_csv("/tmp/head4_frozen_ph_rel43_v13/frozen_detail.csv",dtype={"race_code":str})
 # Add all available Waku10 features, preserving already-frozen candidate membership.
 w=v13.w10.build_waku(z.race_code.astype(str).str.zfill(12).tolist())
 z.race_code=z.race_code.astype(str).str.zfill(12);z=z.merge(w,on="race_code",how="left",validate="one_to_one",suffixes=("","_dup"))
 num=[]
 forbidden=("head4","actual","result","payout","odds","finish","着順","1着","2着","3着")
 for c in z.columns:
  if any(k.lower() in c.lower() for k in forbidden):continue
  x=pd.to_numeric(z[c],errors="coerce")
  if x.notna().mean()>=.25 and x.nunique(dropna=True)>1:num.append(c)
 rows=[]
 for per,months in [("DEV_MAR_MAY",["2026-03","2026-04","2026-05"]),("VAL_JUN",["2026-06"]),("HOLD_JUL_AUG",["2026-07","2026-08"])]:
  g=z[z.month.isin(months)]
  for c in num:
   x=pd.to_numeric(g[c],errors="coerce");a=x[g.head4.eq(1)].dropna();b=x[g.head4.eq(0)].dropna()
   if len(a)<3 or len(b)<3:continue
   sd=float(np.sqrt((a.var(ddof=1)+b.var(ddof=1))/2)) if len(a)>1 and len(b)>1 else np.nan
   d=float((a.mean()-b.mean())/sd) if np.isfinite(sd) and sd>0 else 0.0
   rows.append({"period":per,"feature":c,"win_N":len(a),"loss_N":len(b),"win_mean":float(a.mean()),"loss_mean":float(b.mean()),"std_diff":d,"abs_std_diff":abs(d)})
 df=pd.DataFrame(rows).sort_values(["period","abs_std_diff"],ascending=[True,False]);df.to_csv(OUT/"feature_winloss.csv",index=False)
 for per in df.period.unique():
  print("\nTOP",per);print(df[df.period.eq(per)].head(30).to_string(index=False))
 meta={"diagnostic_only":True,"threshold_search":False,"candidate_membership":"frozen p>=.36 + ready + ORIG>=-.06","SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 (OUT/"meta.json").write_text(json.dumps(meta,indent=2)+"\n");print(json.dumps(meta));print("HEAD4_FROZEN_WINLOSS_V14_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
