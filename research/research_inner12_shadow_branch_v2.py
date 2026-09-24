#!/usr/bin/env python3
"""INNER12 novel non-overlap Shadow V2: attack-geometry branch gate.

This is POSTHOC SHADOW ONLY, not production.

Base Shadow V1:
- exact existing 4HEAD production nonfire
- Stage-A candidate already present in Stage-B rows
- boat4 prior_late20_rate <= .20 OR boat5 prior_late20_rate >= .40

New fixed branch geometry:
A = boat3 Waku10 mean ST - boat4 Waku10 mean ST >= .038
B = corrected predicted actual ST3 - ST5 <= -.09
V2 strong gate = exactly one of A/B is true (XOR).

Interpretation:
- A-only: boat4 has a meaningful course-ST edge over boat3; mixed 3/4 attack branch.
- B-only: boat3 has a large predicted-start edge over boat5 without A; 3-leaning branch.
- both: ambiguous/conflicting geometry; historically weak.
- neither: weak external-attack geometry; reject branch.

All features are pre-race/current-exhibition causal features already frozen before
same-day outcomes are loaded. September outcomes are not read.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import pandas as pd

STAGEB=Path(os.environ.get("INNER12_STAGEB_ROWS","/tmp/stageb/factor_rows.csv"))
HEAD4=Path(os.environ.get("HEAD4_RACE_DETAIL","/tmp/nonoverlap/head4_ph5_live_walkforward/race_detail.csv"))
OUT=Path(os.environ.get("INNER12_BRANCH_OUTDIR","/tmp/inner12_shadow_branch_v2"))
OUT.mkdir(parents=True,exist_ok=True)

MONTHS=("2026-06","2026-07","2026-08")
B4_LATE20_MAX=.20
B5_LATE20_MIN=.40
GAP34_WAKU_ST_MIN=.038
PRED3_VS5_MAX=-.09

ROUTE_COLS=[
    "route_outer_wide","route_outer_core","route_1_escape",
    "route_3_family","route_4_family","route_5_family",
    "route_3_makuri","route_3_makurisashi",
    "route_4_makuri","route_4_makurisashi",
    "route_5_makuri","route_5_makurisashi",
]

def rate(df,c):
    return float(pd.to_numeric(df[c],errors="coerce").fillna(0).mean()) if len(df) else None

def summarize(df):
    z={"R":int(len(df))}
    for c in ROUTE_COLS:
        v=pd.to_numeric(df[c],errors="coerce").fillna(0)
        z[c+"_H"]=int(v.sum())
        z[c+"_rate"]=float(v.mean()) if len(df) else None
    return z

def main():
    if not STAGEB.exists(): raise RuntimeError(f"MISSING_STAGEB_{STAGEB}")
    if not HEAD4.exists(): raise RuntimeError(f"MISSING_HEAD4_{HEAD4}")

    f=pd.read_csv(STAGEB,dtype={"race_code":str})
    h=pd.read_csv(HEAD4,dtype={"race_code":str})
    f["race_code"]=f.race_code.astype(str).str.zfill(12)
    h["race_code"]=h.race_code.astype(str).str.zfill(12)
    f=f[f.month.isin(MONTHS)].copy()
    h=h[h.date.astype(str).str[:7].isin(MONTHS)].copy()
    if h.race_code.duplicated().any(): raise RuntimeError("DUP_HEAD4_RACECODE")

    hm=h.set_index("race_code")["production_bet"].to_dict()
    f["head4_production_bet"]=pd.to_numeric(f.race_code.map(hm),errors="coerce")
    strict=f[f.head4_production_bet.eq(0)].copy()

    b4late=pd.to_numeric(strict["attack_b4_prior_late20_rate"],errors="coerce")
    b5late=pd.to_numeric(strict["attack_b5_prior_late20_rate"],errors="coerce")
    base=strict[(b4late<=B4_LATE20_MAX)|(b5late>=B5_LATE20_MIN)].copy()

    gap34=pd.to_numeric(base["attack_gap_3minus4_waku_st"],errors="coerce")
    pred35=pd.to_numeric(base["post_gap_b3_vs_b5_pred"],errors="coerce")
    base["branch_A"]=gap34.ge(GAP34_WAKU_ST_MIN).astype(int)
    base["branch_B"]=pred35.le(PRED3_VS5_MAX).astype(int)
    base["branch_name"]="neither"
    base.loc[(base.branch_A==1)&(base.branch_B==0),"branch_name"]="A_only"
    base.loc[(base.branch_A==0)&(base.branch_B==1),"branch_name"]="B_only"
    base.loc[(base.branch_A==1)&(base.branch_B==1),"branch_name"]="both"
    base["shadow_v2_selected"]=base.branch_name.isin(["A_only","B_only"]).astype(int)

    selected=base[base.shadow_v2_selected.eq(1)].copy()

    monthly=[]
    for mon in MONTHS:
        row={"month":mon,"base_shadow":summarize(base[base.month.eq(mon)]),
             "v2_selected":summarize(selected[selected.month.eq(mon)])}
        for branch in ("A_only","B_only","both","neither"):
            row[branch]=summarize(base[(base.month.eq(mon))&(base.branch_name.eq(branch))])
        monthly.append(row)

    branch_total={branch:summarize(base[base.branch_name.eq(branch)])
                  for branch in ("A_only","B_only","both","neither")}

    base.to_csv(OUT/"shadow_v2_all_base_rows.csv",index=False)
    selected.to_csv(OUT/"shadow_v2_selected.csv",index=False)

    flat=[]
    for mon in MONTHS:
        for branch in ("A_only","B_only","both","neither"):
            z=base[(base.month.eq(mon))&(base.branch_name.eq(branch))]
            r={"month":mon,"branch":branch,**summarize(z)}
            flat.append(r)
    pd.DataFrame(flat).to_csv(OUT/"branch_monthly.csv",index=False)

    meta={
        "model_id":"INNER12_NOVEL_NONOVERLAP_SHADOW_V2",
        "status":"POSTHOC_SHADOW_ONLY",
        "base_shadow_rule":{
            "existing4_production_nonfire":True,
            "b4_prior_late20_rate_max":B4_LATE20_MAX,
            "OR_b5_prior_late20_rate_min":B5_LATE20_MIN,
        },
        "branch_rule":{
            "A":"attack_gap_3minus4_waku_st >= 0.038",
            "B":"post_gap_b3_vs_b5_pred <= -0.09",
            "selected":"A XOR B",
            "A_only_interpretation":"4 has course-ST edge over 3; mixed 3/4 attack branch",
            "B_only_interpretation":"3 has large predicted ST edge over 5; 3-leaning branch",
            "both":"ambiguous/conflicting; reject",
            "neither":"weak attack geometry; reject",
        },
        "selection_period_used_for_discovery":"posthoc Jun-Aug salvage analysis",
        "august_already_seen":True,
        "september_outcomes_read":False,
        "same_day_results_used_for_features":False,
        "production_changed":False,
        "total_base_shadow":summarize(base),
        "total_v2_selected":summarize(selected),
        "branch_total":branch_total,
        "monthly":monthly,
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

    print("INNER12_NOVEL_NONOVERLAP_SHADOW_V2_OK")
    print("TOTAL_BASE",json.dumps(meta["total_base_shadow"],ensure_ascii=False))
    print("TOTAL_V2",json.dumps(meta["total_v2_selected"],ensure_ascii=False))
    print("BRANCH_TOTAL",json.dumps(branch_total,ensure_ascii=False))
    print("MONTHLY",json.dumps(monthly,ensure_ascii=False))
    print("POSTHOC_SHADOW_ONLY")
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
