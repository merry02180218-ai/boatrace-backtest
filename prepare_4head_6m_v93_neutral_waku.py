#!/usr/bin/env python3
"""Prepare six-month v93 primitives with shared historical Boatcast Waku10. No result-derived Waku reconstruction; September blocked."""
import os,csv
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
def shared_rows(rel):
    z=orig(rel)
    if z or "data/programs/waku10/" not in rel:return z
    p=rel.split("/")
    if len(p)>=6 and p[3]=="2026" and p[4] in {"03","04","05","06"}:
        month,day=p[4],Path(p[5]).stem
        root=Path("data/shared_historical/waku10_boatcast/2026")/month/day
        if not root.is_dir():
            root=Path("data/shared_historical/waku10_boatcast/2026")/month
        out=[]
        for fp in sorted(root.glob(f"{day}_*.txt") if root.name==month else root.glob("*.txt")):
            lines=fp.read_text(encoding="utf-8-sig",errors="ignore").splitlines()
            if len(lines)<8 or not lines[0].startswith("data="): continue
            jo,rr=map(int,fp.stem.split("_")); row={"レースコード":f"2026{month}{day}{jo:02d}{rr:02d}"}
            for b,line in enumerate(lines[2:8],1):
                a=line.split("\t")
                if len(a)<34: continue
                row[f"艇{b}_選手名"]=a[0];row[f"艇{b}_枠番別勝率"]=a[1];row[f"艇{b}_枠番別平均ST"]=a[2];row[f"艇{b}_枠番別平均スタート順"]=a[3]
                for k in range(10):
                    q=4+k*3;row[f"艇{b}_過去{k+1}走_着順"]=a[q];row[f"艇{b}_過去{k+1}走_進入"]=a[q+1];row[f"艇{b}_過去{k+1}走_グレード"]=a[q+2]
            out.append(row)
        if day=="03" and month=="03": print("SHARED_DIAG_20260303",len(out),[x.get("レースコード") for x in out if x.get("レースコード") in {"202603030401","202603030601","202603030701"}])
        return out
    return z
reb.rows=shared_rows
reb.ex.rows=shared_rows
reb.A=reb.date(2026,3,1)
reb.main()
z=pd.read_csv("/tmp/head4_v93_all_parent/v93_all_parent.csv",dtype={"race_code":str})
missing=parent[~parent.race_code.isin(set(z.race_code.astype(str).str.zfill(12)))].copy()
print("MISSING_BY_MONTH",missing.groupby("month").size().to_dict())
print("REBUILT_BY_MONTH",z.assign(month=z.race_code.astype(str).str[:6].str[:4]+"-"+z.race_code.astype(str).str[4:6]).groupby("month").size().to_dict())
print("MISSING_SAMPLE",missing.race_code.head(30).tolist())
meta={"parent_R":int(len(parent)),"v93_R":int(len(z)),"shared_historical_waku10_used":True,"waku10_backfill_used":False,"waku_source":"Boatcast shared historical Mar-Jun + BoatraceCSV existing Jul-Aug","SEPTEMBER_OUTCOMES_READ":False}
Path("/tmp/head4_v93_all_parent/6m_meta.json").write_text(__import__("json").dumps(meta,ensure_ascii=False,indent=2)+"\n")
print("SIX_MONTH_V93_READY",meta)
