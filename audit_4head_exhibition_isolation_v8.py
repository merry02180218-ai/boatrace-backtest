#!/usr/bin/env python3
"""Isolation audit: build_ex must be invariant when all result/payout reads are blocked."""
import json,os
from pathlib import Path
import pandas as pd
import analyze_4head_exhibition_original_trainonly as ex
import build_4head_clean_long_dataset as clean

clean.main()
ds=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",dtype={"race_code":str})
ds["race_code"]=ds.race_code.astype(str).str.zfill(12)
wanted=set(ds[(ds.month>="2026-03")&(ds.month<="2026-08")].race_code)
orig_rows=ex.rows

def blocked_rows(rel):
    q=str(rel).lower()
    if "data/results/" in q or "payout" in q:
        raise RuntimeError("FORBIDDEN_RESULT_READ_IN_BUILD_EX:"+str(rel))
    return orig_rows(rel)

# Reference build: build_ex's normal path.
ref=ex.build_ex(wanted).sort_values("race_code").reset_index(drop=True)
# Isolated build: any attempted result/payout access fails hard.
ex.rows=blocked_rows
iso=ex.build_ex(wanted).sort_values("race_code").reset_index(drop=True)
ex.rows=orig_rows

if list(ref.columns)!=list(iso.columns): raise RuntimeError("COLUMN_MISMATCH")
if len(ref)!=len(iso): raise RuntimeError("ROWCOUNT_MISMATCH")
if not ref.race_code.equals(iso.race_code): raise RuntimeError("RACECODE_MISMATCH")
cols=[c for c in ref.columns if c!="race_code"]
diff=[]
for c in cols:
 a=ref[c];b=iso[c]
 eq=(a.eq(b)|(a.isna()&b.isna()))
 if not bool(eq.all()): diff.append({"column":c,"mismatch":int((~eq).sum())})
out={"wanted_R":len(wanted),"ref_R":len(ref),"iso_R":len(iso),"mismatch_columns":diff,
     "result_reads_blocked":True,"SEPTEMBER_OUTCOMES_READ":False,"PRODUCTION_CHANGED":False}
Path("/tmp/head4_exhibition_isolation_v8").mkdir(exist_ok=True)
Path("/tmp/head4_exhibition_isolation_v8/report.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(out,ensure_ascii=False,indent=2))
if diff: raise RuntimeError("EXHIBITION_ISOLATION_MISMATCH")
print("HEAD4_EXHIBITION_ISOLATION_V8_OK");print("SEPTEMBER_UNREAD")
