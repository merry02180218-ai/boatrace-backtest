#!/usr/bin/env python3
"""August current-LIVE replay gate using BoatraceCSV pre-close od3.
This stage proves market snapshot timing/coverage on the strict executable universe.
No September access. No Waku10 backfill.
"""
from pathlib import Path
import os,json,glob
import pandas as pd
OUT=Path("/tmp/head4_aug_live_od3");OUT.mkdir(exist_ok=True)
def main():
 z=pd.read_csv(os.environ["STRICT_ROWS"],dtype={"race_code":str});z["race_code"]=z.race_code.astype(str).str.zfill(12)
 z=z[(z.month=="2026-08") & z.strict_post_executable.astype(str).str.lower().isin(["true","1"])].copy()
 od=[]
 for p in sorted(glob.glob("data/previews/od3/2026/08/*.csv")):
  q=pd.read_csv(p,dtype={"レースコード":str});q["race_code"]=q["レースコード"].astype(str).str.zfill(12)
  q["deadline"]=q["締切時刻"].astype(str);q["fetched"]=pd.to_datetime(q["取得日時"],errors="coerce")
  od.append(q[["race_code","deadline","fetched"]])
 o=pd.concat(od,ignore_index=True);o=o.drop_duplicates("race_code")
 z=z.merge(o,on="race_code",how="left")
 z["od3_covered"]=z.fetched.notna()
 def lead(r):
  if pd.isna(r.fetched):return None
  d=str(r.date)[:10]; dl=pd.to_datetime(d+" "+str(r.deadline),errors="coerce")
  ft=r.fetched.tz_localize(None) if getattr(r.fetched,"tzinfo",None) else r.fetched
  return (dl-ft).total_seconds()/60 if pd.notna(dl) else None
 z["minutes_before_close"]=z.apply(lead,axis=1)
 out={"aug_strict_post_executable_R":len(z),"od3_covered_R":int(z.od3_covered.sum()),"od3_coverage_rate":float(z.od3_covered.mean()),"median_minutes_before_close":float(z.loc[z.od3_covered,"minutes_before_close"].median()),"min_minutes_before_close":float(z.loc[z.od3_covered,"minutes_before_close"].min()),"max_minutes_before_close":float(z.loc[z.od3_covered,"minutes_before_close"].max()),"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
 z.to_csv(OUT/"aug_strict_od3_rows.csv",index=False);(OUT/"result.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n");print(json.dumps(out,ensure_ascii=False,indent=2));print("HEAD4_AUG_LIVE_OD3_COVERAGE_OK");print("SEPTEMBER_UNREAD")
if __name__=="__main__":main()

# workflow trigger
