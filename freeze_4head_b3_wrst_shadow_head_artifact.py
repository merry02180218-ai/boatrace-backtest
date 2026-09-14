#!/usr/bin/env python3
"""Freeze the B3_WR_ST PRE/POST head models for prospective shadow use only.

The builder is historical-only: labels after 2026-06-30 are never read. Before
serializing the final models it reproduces the official June walk-forward
B3_WR_ST PRE/POST prediction fingerprints captured from run 34818957616.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from backtest import rows, i
from backtest_v3 import ingest_motor
from backtest_v4 import ingest_prior_day_preview
from backtest_v5_ev import process_features
import analyze_4head_waku10_ablation_20260914 as src

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "artifacts" / "head4_b3_wrst_shadow_head_20260630.json"
REPORT = ROOT / "artifacts" / "head4_b3_wrst_shadow_head_parity_20260630.json"
CUTOFF = date(2026, 6, 30)
JUNE_START = pd.Timestamp("2026-06-01")
JULY_START = pd.Timestamp("2026-07-01")
EXPECTED = {
    "PRE": {"rows": 4488, "sha256": "04d18ebd46ebc5249622a4a3d54a2549f941a5e93a41f36333de18e96d71dd1d"},
    "POST": {"rows": 4488, "sha256": "a1d6d98c902a99aff58b2d36ee2b1b1eb861c0f91c1476ad6b7a90a6d39222d7"},
}


def finite_list(values):
    out = []
    for x in values:
        v = float(x)
        if not np.isfinite(v):
            raise RuntimeError("non-finite model state")
        out.append(v)
    return out


def serialize(model, features):
    num = model.named_steps["p"].named_transformers_["n"]
    imp = num.named_steps["i"]
    sc = num.named_steps["s"]
    lr = model.named_steps["m"]
    return {
        "kind": "standardized_logistic",
        "features": list(features),
        "imputer_median": finite_list(imp.statistics_),
        "scaler_mean": finite_list(sc.mean_),
        "scaler_scale": finite_list(sc.scale_),
        "coef": finite_list(lr.coef_[0]),
        "intercept": float(lr.intercept_[0]),
        "C": 0.35,
    }


def prediction_digest(race_codes, pred):
    pairs = sorted((str(c).zfill(12), float(p)) for c, p in zip(race_codes, pred))
    payload = "".join(f"{c},{p:.10f}\n" for c, p in pairs)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_frame():
    cache = {}
    hist = defaultdict(list)
    seen = set()
    d = src.PRELOAD_START
    while d < src.START:
        ingest_motor(hist, seen, d)
        if d >= src.START - timedelta(days=12):
            ingest_prior_day_preview(cache, d)
        d += timedelta(days=1)

    data = []
    while d <= CUTOFF:
        ymd = d.strftime("%Y/%m/%d")
        tkz = src.by_code(f"data/previews/tkz/{ymd}.csv")
        stt = src.by_code(f"data/previews/stt/{ymd}.csv")
        orig = src.by_code(f"data/previews/original_exhibition/{ymd}.csv")
        frozen = []
        for r, x, s4, _s5, _dc in process_features(d, cache, hist):
            z = {"date": str(d), "race_code": str(r["レースコード"]).zfill(12)}
            z.update(src.raw_features(x, s4))
            z.update(src.post_features(r["レースコード"], tkz, stt, orig))
            frozen.append(z)
        result = {str(r["レースコード"]).zfill(12): r for r in rows(f"data/results/realtime/{ymd}.csv")}
        for z in frozen:
            z["y4head"] = int(i(result.get(z["race_code"], {}).get("1着_艇番")) == 4)
            data.append(z)
        ingest_prior_day_preview(cache, d)
        ingest_motor(hist, seen, d)
        d += timedelta(days=1)

    q = pd.DataFrame(data)
    q["_date"] = pd.to_datetime(q.date)
    if q.empty or q._date.max().date() > CUTOFF:
        raise RuntimeError("training cutoff breach")
    return q


def main():
    pre_cols, post_cols = src.cols_for("B3_WR_ST")
    df = build_frame()
    tr = df[df._date < JUNE_START].copy()
    te = df[(df._date >= JUNE_START) & (df._date < JULY_START)].copy()
    parity = {}

    for name, cols in (("PRE", pre_cols), ("POST", post_cols)):
        m = src.make_model(cols)
        m.fit(tr[cols], tr.y4head.astype(int))
        pred = m.predict_proba(te[cols])[:, 1]
        got = {"rows": int(len(te)), "sha256": prediction_digest(te.race_code, pred)}
        parity[name] = {**got, "expected": EXPECTED[name]}
        if got != EXPECTED[name]:
            raise RuntimeError(f"{name} June parity failed: {got} != {EXPECTED[name]}")

    final = {}
    for name, cols in (("PRE", pre_cols), ("POST", post_cols)):
        m = src.make_model(cols)
        m.fit(df[cols], df.y4head.astype(int))
        final[name] = serialize(m, cols)

    artifact = {
        "policy_id": "HEAD4_B3_WR_ST_SHADOW_V1",
        "research_shadow_only": True,
        "production_modified": False,
        "training_label_start": str(src.START),
        "training_label_cutoff": str(CUTOFF),
        "jul_aug_labels_used": False,
        "september_labels_used": False,
        "variant": "B3_WR_ST",
        "models": final,
        "s_thresholds": {"PRE": 0.28, "POST": 0.25, "ENV_ENTRY": 0.224790},
        "official_reference_run": 34818957616,
        "june_walkforward_parity": parity,
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "PASS",
        "artifact": str(ARTIFACT.relative_to(ROOT)),
        "training_rows": int(len(df)),
        "training_head4_rate": float(df.y4head.mean()),
        "june_rows": int(len(te)),
        "parity": parity,
        "production_modified": False,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
