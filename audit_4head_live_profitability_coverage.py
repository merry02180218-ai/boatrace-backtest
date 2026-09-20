#!/usr/bin/env python3
"""Strict executable-history coverage audit for current 4HEAD LIVE policy.
No Waku10 reconstruction/backfill. Missing historical Waku10 is fail-closed.
This stage establishes the unbiased executable denominator before ROI.
"""
from __future__ import annotations
import os,json
from pathlib import Path
import pandas as pd
OUT=Path("/tmp/head4_live_profitability");OUT.mkdir(exist_ok=True)
def main():
 p=pd.read_csv(os.environ["PARENT_EXHIBITION"],dtype={"race_code":str});p["race_code"]=p.race_code.astype(str).str.zfill(12)
 v=pd.read_csv(os.environ["V93_REBUILT"],dtype={"race_code":str});v["race_code"]=v.race_code.astype(str).str.zfill(12)
 miss=pd.read_csv(os.environ["MISSINGNESS"],dtype={"race_code":str});miss["race_code"]=miss.race_code.astype(str).str.zfill(12)
 hp=pd.read_csv(os.environ["HEADPROB_SCORED"],dtype={"race_code":str});hp["race_code"]=hp.race_code.astype(str).str.zfill(12)
 if p.date.astype(str).str.startswith("2026-09").any():raise RuntimeError("SEPTEMBER ACCESS")
 vc=set(v.race_code);hc=set(hp.race_code)
 z=p.merge(miss[["race_code","reason"]],on="race_code",how="left")
 z["historical_waku10_observed"]=z.reason.eq("rebuilt")
 z["v93_rebuilt"]=z.race_code.isin(vc);z["headprob_covered"]=z.race_code.isin(hc)
 z["strict_pre_executable"]=z.historical_waku10_observed & z.v93_rebuilt & z.headprob_covered
 z["struct_ready_bool"]=z.struct_ready.astype(str).str.lower().isin(["true","1"])
 z["strict_post_executable"]=z.strict_pre_executable & z.struct_ready_bool
 z["month"]=z.date.astype(str).str[:7]
 def agg(g):
  return {"parent_R":len(g),"observed_waku10_R":int(g.historical_waku10_observed.sum()),"strict_pre_executable_R":int(g.strict_pre_executable.sum()),"strict_post_executable_R":int(g.strict_post_executable.sum()),"pre_execution_rate":float(g.strict_pre_executable.mean()),"post_execution_rate":float(g.strict_post_executable.mean())}
 out={"policy":"NO_WAKU10_RECONSTRUCTION_OR_BACKFILL__FAIL_CLOSED","overall":agg(z),"by_month":{m:agg(g) for m,g in z.groupby("month")},"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 z.to_csv(OUT/"strict_executable_rows.csv",index=False);(OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n");print(json.dumps(out,ensure_ascii=False,indent=2));print("HEAD4_LIVE_PROFIT_COVERAGE_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()
