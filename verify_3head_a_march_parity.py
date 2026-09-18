from __future__ import annotations

import json
import pandas as pd

from threehead_head_gate_a_adopted import passes_adopted_head_gate
from run_3head_wave22_march_frozen import (
    MONTHS,
    make_frozen_pre_scores,
)
from run_3head_funsite_broad50_wave16 import build_pre_enhanced, load_canonical
import run_3head_wave19_motor_exhibition_gate as w19

EXPECTED = {
    "n": 52,
    "hits": 21,
    "rate": 21/52,
}

def main():
    raw = {}
    for m,(a,b) in MONTHS.items():
        x,r,audit = build_pre_enhanced(a,b,True)
        raw[m] = (x,r,audit)

    frames = {m:w19.prep_month(x,r) for m,(x,r,_) in raw.items()}

    canon = load_canonical()
    cm = canon[(canon.date>="2026-03-01")&(canon.date<"2026-04-01")][
        ["rc","date","settle__winner"]
    ].copy()
    base_mar = raw["mar"][0].drop(columns=["date"])
    mar = cm.merge(base_mar,on="rc",how="inner")
    mar["date"] = pd.to_datetime(mar["date"])
    mar["y"] = (pd.to_numeric(mar.settle__winner,errors="coerce")==3).astype(int)
    frames["mar"] = mar

    pre_mar, enh_count = make_frozen_pre_scores(frames)

    w19.END = "2026-03-31"
    days,cache = w19.prefetch_sources()
    post,post_audit = w19.build_motor_exhibition(days,cache)

    q = pre_mar.merge(post,on=["rc","date"],how="left",validate="one_to_one")
    q["adopted_pass"] = q.apply(
        lambda r: passes_adopted_head_gate({
            "race_no": r["race_no"],
            "pre_score": r["pre_score"],
            "post_motor_rank_edge2": r.get("post_motor_rank_edge2"),
            "post_ex_rank3": r.get("post_ex_rank3"),
        }),
        axis=1,
    )

    sel = q[q.adopted_pass].copy().sort_values(["date","rc"])
    n = int(len(sel))
    hits = int(sel.y.sum())
    rate = hits/n if n else None

    if n != EXPECTED["n"] or hits != EXPECTED["hits"]:
        raise RuntimeError(
            f"adopted A parity mismatch n={n} hits={hits} "
            f"expected={EXPECTED['n']}/{EXPECTED['hits']}"
        )

    out = {
        "marker": "3HEAD_A_MARCH_PARITY_OK",
        "enhanced_pre_feature_count": int(enh_count),
        "selected_n": n,
        "selected_hits": hits,
        "selected_rate": rate,
        "expected": EXPECTED,
        "race_codes": sel.rc.astype(str).tolist(),
        "source_audit": {m:raw[m][2] for m in raw},
        "post_source_audit": post_audit,
        "september_2026_outcomes_read": False,
        "production_v288_changed": False,
    }
    with open("verify_3head_a_march_parity_result.json","w") as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__ == "__main__":
    main()
