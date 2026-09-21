#!/usr/bin/env python3
from pathlib import Path
import json, pandas as pd

SRC=Path("analysis_v243_3head_expand_feature_audit.csv")
OUT=Path("research_v288_source_date_audit.json")

def main():
    q=pd.read_csv(SRC,dtype={"race_code":str})
    dc="date" if "date" in q.columns else None
    if dc is None: raise RuntimeError("missing date column")
    d=pd.to_datetime(q[dc].astype(str),errors="coerce")
    rc=q["race_code"].astype(str).str.zfill(12)
    if d.notna().sum()==0: raise RuntimeError("no valid dates")
    months=d.dt.strftime("%Y-%m").value_counts().sort_index().to_dict()
    out={
      "rows":int(len(q)),
      "unique_races":int(rc.nunique()),
      "date_min":str(d.min().date()),
      "date_max":str(d.max().date()),
      "months":{str(k):int(v) for k,v in months.items()},
      "sep2026_present":bool((d.dt.strftime("%Y-%m")=="2026-09").any()),
      "outcome_values_inspected":False
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print("V288_SOURCE_DATE_AUDIT_OK")
if __name__=="__main__": main()
