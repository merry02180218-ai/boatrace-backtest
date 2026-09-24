#!/usr/bin/env python3
"""INNER12 Shadow V3: strong 3-head branch inside B-only.

POSTHOC SHADOW ONLY.

Parent:
- Shadow V2 B-only branch:
  A=false, B=true
  A: attack_gap_3minus4_waku_st >= .038
  B: post_gap_b3_vs_b5_pred <= -.09

Strong prior-only 3-head subgate:
- pre_pair_absdiff_prior_recent3_st >= .04

Optional current-exhibition confirmation tier:
- strong prior-only subgate
- AND post_b3_ex_st <= .10

September outcomes remain unread. Production unchanged.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import pandas as pd

V2=Path(os.environ.get("INNER12_V2_ROWS","/tmp/v2/shadow_v2_all_base_rows.csv"))
OUT=Path(os.environ.get("INNER12_V3_OUTDIR","/tmp/inner12_shadow_3head_v3"))
OUT.mkdir(parents=True,exist_ok=True)

MONTHS=("2026-06","2026-07","2026-08")
PRIOR_GAP_MIN=.04
EX3_MAX=.10

ROUTE_COLS=[
    "route_3_family","route_3_makuri","route_3_makurisashi",
    "route_4_family","route_5_family","route_1_escape","route_outer_wide"
]

def summarize(df):
    out={"R":int(len(df))}
    for c in ROUTE_COLS:
        v=pd.to_numeric(df[c],errors="coerce").fillna(0)
        out[c+"_H"]=int(v.sum())
        out[c+"_rate"]=float(v.mean()) if len(df) else None
    return out

def by_month(df):
    return {m:summarize(df[df.month.eq(m)]) for m in MONTHS}

def main():
    if not V2.exists():raise RuntimeError(f"MISSING_V2_{V2}")
    d=pd.read_csv(V2,dtype={"race_code":str})
    d["race_code"]=d.race_code.astype(str).str.zfill(12)
    d=d[d.month.isin(MONTHS)].copy()

    b=d[d.branch_name.eq("B_only")].copy()
    if len(b)!=32:
        raise RuntimeError(f"EXPECTED_B_ONLY_32_GOT_{len(b)}")

    prior_gap=pd.to_numeric(b["pre_pair_absdiff_prior_recent3_st"],errors="coerce")
    ex3=pd.to_numeric(b["post_b3_ex_st"],errors="coerce")

    strong=b[prior_gap.ge(PRIOR_GAP_MIN)].copy()
    confirm=b[prior_gap.ge(PRIOR_GAP_MIN)&ex3.le(EX3_MAX)].copy()

    # Threshold robustness is descriptive only; V3 fixed rule remains .04.
    robustness=[]
    for cut in (.03,.035,.04,.045,.05):
        z=b[prior_gap.ge(cut)]
        row={"kind":"prior_gap","cut":cut,**summarize(z)}
        for m in MONTHS:
            q=z[z.month.eq(m)]
            row[m+"_R"]=int(len(q))
            row[m+"_3rate"]=float(q.route_3_family.mean()) if len(q) else None
        robustness.append(row)
    for cut in (.09,.10,.11,.12):
        z=b[ex3.le(cut)]
        row={"kind":"ex3_max","cut":cut,**summarize(z)}
        for m in MONTHS:
            q=z[z.month.eq(m)]
            row[m+"_R"]=int(len(q))
            row[m+"_3rate"]=float(q.route_3_family.mean()) if len(q) else None
        robustness.append(row)

    strong.to_csv(OUT/"strong_prior_selected.csv",index=False)
    confirm.to_csv(OUT/"strong_prior_plus_exhibition.csv",index=False)
    pd.DataFrame(robustness).to_csv(OUT/"threshold_robustness.csv",index=False)

    meta={
        "model_id":"INNER12_NOVEL_NONOVERLAP_3HEAD_SHADOW_V3",
        "status":"POSTHOC_SHADOW_ONLY",
        "parent_branch":"B_only from Shadow V2",
        "fixed_strong_rule":{
            "pre_pair_absdiff_prior_recent3_st_min":PRIOR_GAP_MIN,
        },
        "optional_confirmation":{
            "post_b3_ex_st_max":EX3_MAX,
        },
        "interpretation":{
            "prior_gap":"boats1/2 have materially different recent-3 actual-ST histories despite Stage-A dual-lag context",
            "confirmation":"boat3 also shows a fast current exhibition start",
        },
        "base_B_only":summarize(b),
        "base_B_only_monthly":by_month(b),
        "strong_prior":summarize(strong),
        "strong_prior_monthly":by_month(strong),
        "strong_plus_exhibition":summarize(confirm),
        "strong_plus_exhibition_monthly":by_month(confirm),
        "august_already_seen":True,
        "september_outcomes_read":False,
        "same_day_results_used_for_features":False,
        "production_changed":False,
        "note":"Do not promote. This is posthoc shadow research; use a future unseen period for validation."
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

    print("INNER12_3HEAD_SHADOW_V3_OK")
    print("BASE_B_ONLY",json.dumps(meta["base_B_only"],ensure_ascii=False))
    print("STRONG_PRIOR",json.dumps(meta["strong_prior"],ensure_ascii=False))
    print("STRONG_PRIOR_MONTHLY",json.dumps(meta["strong_prior_monthly"],ensure_ascii=False))
    print("STRONG_PLUS_EXHIBITION",json.dumps(meta["strong_plus_exhibition"],ensure_ascii=False))
    print("STRONG_PLUS_EXHIBITION_MONTHLY",json.dumps(meta["strong_plus_exhibition_monthly"],ensure_ascii=False))
    print("POSTHOC_SHADOW_ONLY")
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
