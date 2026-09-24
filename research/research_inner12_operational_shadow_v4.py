#!/usr/bin/env python3
"""INNER12 operational Shadow V4.

POSTHOC SHADOW ONLY.

Routing:
- A_only -> buy both heads 3 and 4.
- B_only + pre_pair_absdiff_prior_recent3_st >= .04 -> buy head 3 only.
- all other branches -> no bet.

This freezes the user's proposed operational interpretation without changing
production. September outcomes are not read here.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import pandas as pd

V2=Path(os.environ.get("INNER12_V2_ROWS","/tmp/v2/shadow_v2_all_base_rows.csv"))
OUT=Path(os.environ.get("INNER12_V4_OUTDIR","/tmp/inner12_operational_shadow_v4"))
OUT.mkdir(parents=True,exist_ok=True)

MONTHS=("2026-06","2026-07","2026-08")
B_STRONG_GAP=.04

def main():
    if not V2.exists(): raise RuntimeError(f"MISSING_V2_{V2}")
    d=pd.read_csv(V2,dtype={"race_code":str})
    d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.month.isin(MONTHS)].copy()

    d["v4_action"]="PASS"
    d["v4_heads"]=""
    d.loc[d.branch_name.eq("A_only"),"v4_action"]="A_DUAL_3_4"
    d.loc[d.branch_name.eq("A_only"),"v4_heads"]="3|4"

    gap=pd.to_numeric(d["pre_pair_absdiff_prior_recent3_st"],errors="coerce")
    bstrong=d.branch_name.eq("B_only") & gap.ge(B_STRONG_GAP)
    d.loc[bstrong,"v4_action"]="B_3HEAD"
    d.loc[bstrong,"v4_heads"]="3"

    selected=d[d.v4_action.ne("PASS")].copy()
    selected["head_slots"]=selected.v4_heads.map(lambda s:len(str(s).split("|")) if s else 0)
    selected["head_hit"]=[
        int(str(int(w)) in str(h).split("|"))
        for w,h in zip(pd.to_numeric(selected.winner,errors="coerce").fillna(0),selected.v4_heads)
    ]

    monthly=[]
    for m in MONTHS:
        z=selected[selected.month.eq(m)]
        a=z[z.v4_action.eq("A_DUAL_3_4")]
        b=z[z.v4_action.eq("B_3HEAD")]
        monthly.append({
            "month":m,
            "selected_R":int(len(z)),
            "head_hits":int(z.head_hit.sum()),
            "race_head_hit_rate":float(z.head_hit.mean()) if len(z) else None,
            "head_slots":int(z.head_slots.sum()),
            "hit_per_head_slot":float(z.head_hit.sum()/z.head_slots.sum()) if z.head_slots.sum() else None,
            "A_dual_R":int(len(a)),
            "A_dual_hits":int(a.head_hit.sum()),
            "A_dual_rate":float(a.head_hit.mean()) if len(a) else None,
            "B_3head_R":int(len(b)),
            "B_3head_hits":int(b.head_hit.sum()),
            "B_3head_rate":float(b.head_hit.mean()) if len(b) else None,
        })

    total={
        "selected_R":int(len(selected)),
        "head_hits":int(selected.head_hit.sum()),
        "race_head_hit_rate":float(selected.head_hit.mean()) if len(selected) else None,
        "head_slots":int(selected.head_slots.sum()),
        "hit_per_head_slot":float(selected.head_hit.sum()/selected.head_slots.sum()) if selected.head_slots.sum() else None,
        "A_dual_R":int((selected.v4_action=="A_DUAL_3_4").sum()),
        "A_dual_hits":int(selected.loc[selected.v4_action.eq("A_DUAL_3_4"),"head_hit"].sum()),
        "B_3head_R":int((selected.v4_action=="B_3HEAD").sum()),
        "B_3head_hits":int(selected.loc[selected.v4_action.eq("B_3HEAD"),"head_hit"].sum()),
    }

    selected.to_csv(OUT/"selected_races.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)

    meta={
        "model_id":"INNER12_NOVEL_OPERATIONAL_SHADOW_V4",
        "status":"POSTHOC_SHADOW_ONLY",
        "routing":{
            "A_only":"heads 3 and 4",
            "B_only_and_recent3_gap_ge_0.04":"head 3 only",
            "both":"PASS",
            "neither":"PASS",
            "B_only_without_strong_gap":"PASS",
        },
        "monthly":monthly,
        "total":total,
        "september_outcomes_read":False,
        "same_day_results_used_for_features":False,
        "production_changed":False,
        "note":"Head selection only. Opponent/ticket construction and ROI are not yet validated."
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

    print("INNER12_OPERATIONAL_SHADOW_V4_OK")
    print("MONTHLY",json.dumps(monthly,ensure_ascii=False))
    print("TOTAL",json.dumps(total,ensure_ascii=False))
    print("POSTHOC_SHADOW_ONLY")
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
