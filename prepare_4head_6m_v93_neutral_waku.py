#!/usr/bin/env python3
"""Prepare six-month all-race v93-compatible opponent primitives without Waku10 backfill.
Missing historical Waku10 is represented by an empty same-race row so race-card fallbacks apply.
No future/result-derived Waku reconstruction is allowed. September blocked.
"""
import os
from pathlib import Path
import pandas as pd
import build_4head_clean_long_dataset as clean
clean.main()
ds=pd.read_csv("/tmp/head4_clean_long_dataset/dataset.csv",dtype={"race_code":str})
ds["race_code"]=ds.race_code.astype(str).str.zfill(12)
parent=ds[(ds.month>="2026-03")&(ds.month<="2026-08")&ds.struct_ready.astype(str).str.lower().isin(["true","1"])].copy()
out=Path("/tmp/head4_6m_parent");out.mkdir(exist_ok=True)
pp=out/"parent.csv";parent.to_csv(pp,index=False);os.environ["PARENT_EXHIBITION"]=str(pp)
import rebuild_4head_v93_all_parent as reb
orig=reb.rows
def safe_rows(rel):
    z=orig(rel)
    if z or "data/programs/waku10/" not in rel:return z
    cardrel=rel.replace("data/programs/waku10/","data/programs/race_cards/")
    cards=orig(cardrel)
    return [{"レースコード":x.get("レースコード","")} for x in cards]
reb.rows=safe_rows
reb.ex.rows=safe_rows
reb.A=reb.date(2026,3,1)
reb.main()
z=pd.read_csv("/tmp/head4_v93_all_parent/v93_all_parent.csv",dtype={"race_code":str})
meta={"parent_R":int(len(parent)),"v93_R":int(len(z)),"shared_historical_waku10_used":True,"waku10_backfill_used":False,"waku_source":"Boatcast shared historical Mar-Jun + BoatraceCSV existing Jul-Aug","SEPTEMBER_OUTCOMES_READ":False}
Path("/tmp/head4_v93_all_parent/6m_meta.json").write_text(__import__("json").dumps(meta,ensure_ascii=False,indent=2)+"\n")
print("SIX_MONTH_V93_READY",meta)
