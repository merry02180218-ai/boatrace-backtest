#!/usr/bin/env python3
"""Build the adopted 3-head A head-gate daily shadow cache.

This is NOT a betting runner.  It freezes only the pre-exhibition components of
3HEAD_A_PRECISION_V1:
  - enhanced PRE percentile >= .925
  - boat3 prior-day motor EWMA-rank edge vs boat2 >= +.20
  - race number 1..12

The final exhibition-rank==1 condition is evaluated later by
run_3head_a_live_gate_shadow.py.

Research parity contract:
- enhanced feature names are selected exactly from the frozen Oct-2025..Feb-2026
  pre-race construction, as in Wave22;
- PRE is a 42-day Logistic model with C=.08, balanced class weights,
  liblinear, random_state=161;
- score is the percentile of current raw probability against training raw
  probabilities;
- motor state is updated only from races strictly before the target date;
- target-day results/payouts are never requested or used.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "research"))

from run_3head_funsite_broad50_wave16 import (  # noqa: E402
    build_pre_enhanced,
    choose_features,
    pct_ref,
)
from run_3head_funsite_broad50_wave6 import fetch  # noqa: E402
from run_3head_wave19_motor_exhibition_gate import (  # noqa: E402
    bycode,
    ival,
    new_motor,
    motor_summary,
    rank_map,
    actual_st_by_boat,
    update_motor,
)
from threehead_head_gate_a_adopted import (  # noqa: E402
    PRE_PERCENTILE_MIN,
    MOTOR_EWMA_RANK_EDGE_VS2_MIN,
    RACE_NO_MIN,
    RACE_NO_MAX,
)

FEATURE_FREEZE_MONTHS = [
    ("2025-10-01", "2025-10-31"),
    ("2025-11-01", "2025-11-30"),
    ("2025-12-01", "2025-12-31"),
    ("2026-01-01", "2026-01-31"),
    ("2026-02-01", "2026-02-28"),
]
MOTOR_START = pd.Timestamp("2025-07-01")


def parse_day(s: str) -> pd.Timestamp:
    d = pd.Timestamp(datetime.strptime(s, "%Y-%m-%d").date())
    if d < pd.Timestamp("2026-03-01"):
        raise RuntimeError("A daily shadow target must be 2026-03-01 or later")
    return d


def freeze_feature_names() -> list[str]:
    frames = []
    audits = []
    for a, b in FEATURE_FREEZE_MONTHS:
        x, _, audit = build_pre_enhanced(a, b, False)
        if x.empty:
            raise RuntimeError(f"feature-freeze source empty: {a}..{b}")
        frames.append(x)
        audits.append(audit)
    all_data = pd.concat(frames, ignore_index=True, sort=False)
    _, enh, _ = choose_features(all_data)
    if len(enh) != 370:
        raise RuntimeError(f"frozen enhanced feature count changed: {len(enh)} != 370")
    return enh


def build_pre_for_target(day: pd.Timestamp, enh: list[str]):
    hist_start = (day - pd.Timedelta(days=42)).strftime("%Y-%m-%d")
    hist_end = (day - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    target_s = day.strftime("%Y-%m-%d")

    hx, hr, ha = build_pre_enhanced(hist_start, hist_end, True)
    tx, _, ta = build_pre_enhanced(target_s, target_s, False)

    if hx.empty or hr.empty or tx.empty:
        raise RuntimeError(
            f"PRE source incomplete hist_rows={len(hx)} results={len(hr)} target_rows={len(tx)}"
        )

    hist = hx.merge(hr[["rc", "result_winner"]], on="rc", how="inner")
    hist["y"] = (hist.result_winner == 3).astype(int)
    if len(hist) < 500 or hist.y.nunique() < 2:
        raise RuntimeError(f"PRE training support too small: {len(hist)}")

    missing_hist = [c for c in enh if c not in hist.columns]
    missing_target = [c for c in enh if c not in tx.columns]
    if missing_hist or missing_target:
        raise RuntimeError(
            f"PRE feature schema mismatch hist_missing={missing_hist[:5]} "
            f"target_missing={missing_target[:5]}"
        )

    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(
            C=.08,
            class_weight="balanced",
            solver="liblinear",
            max_iter=1800,
            random_state=161,
        ),
    )
    model.fit(hist[enh], hist.y)
    ptr = model.predict_proba(hist[enh])[:, 1]
    p = model.predict_proba(tx[enh])[:, 1]

    out = tx[["rc", "date", "venue", "race_no"]].copy()
    out["pre_score"] = pct_ref(ptr, p)
    out["pre_raw_probability"] = p
    return out, {
        "history_start": hist_start,
        "history_end": hist_end,
        "training_rows": int(len(hist)),
        "target_rows": int(len(tx)),
        "history_source_audit": ha,
        "target_source_audit": ta,
    }


def prefetch_motor(day: pd.Timestamp):
    days = list(pd.date_range(MOTOR_START, day))
    cache = {}
    tasks = []
    for d in days:
        tasks.append((d, "programs/race_cards"))
        if d < day:
            tasks.append((d, "results/realtime"))
    with ThreadPoolExecutor(max_workers=24) as ex:
        fut = {ex.submit(fetch, kind, d.date()): (d.normalize(), kind) for d, kind in tasks}
        for f in as_completed(fut):
            d, kind = fut[f]
            try:
                cache[(d, kind)] = f.result()
            except Exception:
                cache[(d, kind)] = []
    return days, cache


def build_target_motor_edges(day: pd.Timestamp):
    state = defaultdict(new_motor)
    global_venue = defaultdict(new_motor)
    days, cache = prefetch_motor(day)
    target_rows = []
    audit = {
        "motor_start": str(MOTOR_START.date()),
        "target_date": str(day.date()),
        "prior_days_with_cards": 0,
        "prior_result_events": 0,
        "target_card_rows": 0,
        "same_day_results_requested": False,
    }

    for d in sorted(days):
        d = d.normalize()
        cards = bycode(cache.get((d, "programs/race_cards"), []))

        if d == day:
            for code, rc in cards.items():
                venue = str(rc.get("レース場コード", "")).zfill(2)
                per = {}
                for b in range(1, 7):
                    mid = ival(rc.get(f"艇{b}_モーター番号"))
                    s = state[(venue, mid)] if mid is not None else new_motor()
                    per[b] = motor_summary(s, global_venue[venue], d)
                target_rows.append({
                    "rc": int(code),
                    "post_motor_rank_edge2": float(
                        per[2]["ewma_rank"] - per[3]["ewma_rank"]
                    ),
                    "motor3_ewma_rank": float(per[3]["ewma_rank"]),
                    "motor2_ewma_rank": float(per[2]["ewma_rank"]),
                })
                audit["target_card_rows"] += 1
            continue

        if cards:
            audit["prior_days_with_cards"] += 1
        results = bycode(cache.get((d, "results/realtime"), []))
        for code, rr in results.items():
            rc = cards.get(code)
            if rc is None:
                continue
            venue = str(rc.get("レース場コード", "")).zfill(2)
            rm = rank_map(rr)
            stm = actual_st_by_boat(rr)
            for b in range(1, 7):
                mid = ival(rc.get(f"艇{b}_モーター番号"))
                if mid is None:
                    continue
                update_motor(
                    state[(venue, mid)],
                    rm.get(b),
                    stm.get(b, np.nan),
                    d,
                )
                update_motor(
                    global_venue[venue],
                    rm.get(b),
                    stm.get(b, np.nan),
                    d,
                )
                audit["prior_result_events"] += 1

    if not target_rows:
        raise RuntimeError("no target-day motor rows")
    return pd.DataFrame(target_rows).drop_duplicates("rc"), audit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--out")
    args = ap.parse_args()
    day = parse_day(args.date)

    enh = freeze_feature_names()
    pre, pre_audit = build_pre_for_target(day, enh)
    motor, motor_audit = build_target_motor_edges(day)

    q = pre.merge(motor, on="rc", how="left", validate="one_to_one")
    rn = pd.to_numeric(q.race_no, errors="coerce")
    score = pd.to_numeric(q.pre_score, errors="coerce")
    edge = pd.to_numeric(q.post_motor_rank_edge2, errors="coerce")
    q["pre_motor_pass"] = (
        rn.between(RACE_NO_MIN, RACE_NO_MAX)
        & score.notna()
        & (score >= PRE_PERCENTILE_MIN)
        & edge.notna()
        & (edge >= MOTOR_EWMA_RANK_EDGE_VS2_MIN)
    )

    candidates = {}
    for _, r in q[q.pre_motor_pass].sort_values(["race_no", "rc"]).iterrows():
        code = str(int(r.rc)).zfill(12)
        candidates[code] = {
            "race_no": int(r.race_no),
            "pre_score": float(r.pre_score),
            "pre_raw_probability": float(r.pre_raw_probability),
            "post_motor_rank_edge2": float(r.post_motor_rank_edge2),
            "motor3_ewma_rank": float(r.motor3_ewma_rank),
            "motor2_ewma_rank": float(r.motor2_ewma_rank),
        }

    out_path = Path(args.out or f"live_outputs/a_precision/{day:%Y%m%d}/a_pre_motor_cache.joblib")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "policy": "3HEAD_A_PRECISION_V1_SHADOW",
        "date": day.strftime("%Y%m%d"),
        "target_result_or_payout_used": False,
        "target_exhibition_used": False,
        "prior_settled_results_used_for_causal_training": True,
        "thresholds": {
            "race_min": RACE_NO_MIN,
            "race_max": RACE_NO_MAX,
            "pre_min": PRE_PERCENTILE_MIN,
            "motor_edge_vs2_min": MOTOR_EWMA_RANK_EDGE_VS2_MIN,
            "exhibition_rank_required": 1,
        },
        "enhanced_pre_feature_count": len(enh),
        "pre_audit": pre_audit,
        "motor_audit": motor_audit,
        "pre_motor_candidates": candidates,
        "all_rows": q,
    }
    joblib.dump(payload, out_path, compress=3)

    manifest = {
        "policy": payload["policy"],
        "target_date": str(day.date()),
        "cache_path": str(out_path),
        "enhanced_pre_feature_count": len(enh),
        "all_race_rows": int(len(q)),
        "pre_motor_candidate_count": len(candidates),
        "pre_motor_candidate_race_codes": list(candidates),
        "target_result_or_payout_used": False,
        "target_exhibition_used": False,
        "prior_settled_results_used_for_causal_training": True,
        "motor_same_day_results_requested": False,
    }
    manifest_path = out_path.with_name("a_pre_motor_manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
