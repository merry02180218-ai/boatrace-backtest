#!/usr/bin/env python3
"""Frozen posthoc shadow candidate for INNER12 strict 4HEAD-nonoverlap regime.

This file does NOT claim pristine validation.
August had already been seen during salvage analysis, so the rule is shadow-only.

Fixed rule:
- exact existing 4HEAD production nonfire
- Stage-A candidate already present in Stage-B rows
- boat4 prior_late20_rate <= 0.20 OR boat5 prior_late20_rate >= 0.40

Target diagnostic:
outer WIDE = 3M + 3MS + 4M + 4MS + 5M + 5MS

September outcomes are never read here.
Production is unchanged.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import pandas as pd

STAGEB=Path(os.environ.get("INNER12_STAGEB_ROWS","/tmp/inner12_stageb_route_discovery_v1/factor_rows.csv"))
HEAD4=Path(os.environ.get("HEAD4_RACE_DETAIL","/tmp/head4_ph5_live_walkforward/race_detail.csv"))
OUT=Path(os.environ.get("INNER12_SHADOW_OUTDIR","/tmp/inner12_novel_shadow_v1"))
OUT.mkdir(parents=True,exist_ok=True)

MONTHS=("2026-06","2026-07","2026-08")
B4_LATE20_MAX=0.20
B5_LATE20_MIN=0.40

def rate(df,c):
    return float(pd.to_numeric(df[c],errors="coerce").fillna(0).mean()) if len(df) else None

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

    b4=pd.to_numeric(strict["attack_b4_prior_late20_rate"],errors="coerce")
    b5=pd.to_numeric(strict["attack_b5_prior_late20_rate"],errors="coerce")
    shadow=strict[(b4<=B4_LATE20_MAX)|(b5>=B5_LATE20_MIN)].copy()

    cols=[
        "route_outer_wide","route_outer_core","route_1_escape",
        "route_3_family","route_4_family","route_5_family",
        "route_3_makuri","route_3_makurisashi",
        "route_4_makuri","route_4_makurisashi",
        "route_5_makuri","route_5_makurisashi",
    ]
    monthly=[]
    for mon in MONTHS:
        z=shadow[shadow.month.eq(mon)]
        row={"month":mon,"R":int(len(z))}
        for c in cols:
            row[c+"_H"]=int(pd.to_numeric(z[c],errors="coerce").fillna(0).sum())
            row[c+"_rate"]=rate(z,c)
        monthly.append(row)

    total={"R":int(len(shadow))}
    for c in cols:
        total[c+"_H"]=int(pd.to_numeric(shadow[c],errors="coerce").fillna(0).sum())
        total[c+"_rate"]=rate(shadow,c)

    shadow.to_csv(OUT/"selected_races.csv",index=False)
    pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
    meta={
        "model_id":"INNER12_NOVEL_NONOVERLAP_SHADOW_V1",
        "status":"POSTHOC_SHADOW_ONLY",
        "rule":{
            "existing4_production_nonfire":True,
            "b4_prior_late20_rate_max":B4_LATE20_MAX,
            "OR_b5_prior_late20_rate_min":B5_LATE20_MIN,
        },
        "target":"outer_wide",
        "outer_wide_definition":["3_makuri","3_makurisashi","4_makuri","4_makurisashi","5_makuri","5_makurisashi"],
        "august_was_already_seen_before_freeze":True,
        "september_outcomes_read":False,
        "same_day_results_used_for_features":False,
        "production_changed":False,
        "monthly":monthly,
        "total":total,
        "note":"Use as shadow research candidate only; not production-valid without a new unseen confirmation period."
    }
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print("INNER12_NOVEL_NONOVERLAP_SHADOW_V1_OK")
    print("RULE",json.dumps(meta["rule"],ensure_ascii=False))
    print("MONTHLY",json.dumps(monthly,ensure_ascii=False))
    print("TOTAL",json.dumps(total,ensure_ascii=False))
    print("POSTHOC_SHADOW_ONLY")
    print("SEPTEMBER_UNREAD")
    print("PRODUCTION_UNCHANGED")

if __name__=="__main__":
    main()
