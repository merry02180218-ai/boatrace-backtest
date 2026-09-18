#!/usr/bin/env python3
from pathlib import Path
import json, os
import pandas as pd

POL=Path("artifacts/head4_156r_roi_expansion_20260918.json")
OUT=Path("/tmp/head4_156r_policy_parity"); OUT.mkdir(parents=True,exist_ok=True)

def main():
    p=json.loads(POL.read_text(encoding="utf-8"))
    grid_path=os.environ.get("EXPANDED_GRID")
    if not grid_path: raise RuntimeError("EXPANDED_GRID missing")
    g=pd.read_csv(grid_path)
    q=g[
      (g.comp_floor==3.5) &
      (g.quality_cut==.75) &
      (g.head_floor==.16) &
      (g.mass_floor==.30) &
      (g.st_floor==-.80) &
      (g.orig_floor==-.35)
    ].copy()
    if len(q)!=1: raise RuntimeError(f"policy row count {len(q)}")
    r=q.iloc[0]
    checks={
      "R": int(r.all_R)==156,
      "added_R": int(r.added_R)==36,
      "head4": int(r.all_head4)==65,
      "exact3": int(r.all_exact3)==37,
      "ROI": abs(float(r.all_ROI)-128.59)<0.05,
      "support_ROI": abs(float(r.support_ROI)-115.05)<0.10,
      "monthly_floor": abs(float(r.monthly_floor_ROI)-91.58)<0.10,
      "policy_profile": p.get("profile")=="HEAD4_156R_ROI_EXPANSION_V1",
    }
    if not all(checks.values()):
        raise RuntimeError({"checks":checks,"row":r.to_dict()})
    out={"checks":checks,"row":r.to_dict(),"policy":p["selection"],
         "SEPTEMBER_OUTCOMES_READ":False,"AUDIT_OK":True}
    (OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
    print("HEAD4_156R_POLICY_PARITY_OK")
if __name__=="__main__": main()
