#!/usr/bin/env python3
"""Inference-only helper for HEAD4_B3_WR_ST_SHADOW_V1 PRE/POST models."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np

DEFAULT_ARTIFACT = "artifacts/head4_b3_wrst_shadow_head_20260630.json"
POLICY = "HEAD4_B3_WR_ST_SHADOW_V1"


def load_artifact(path: str = DEFAULT_ARTIFACT) -> dict:
    a = json.loads(Path(path).read_text(encoding="utf-8"))
    if a.get("policy_id") != POLICY or a.get("variant") != "B3_WR_ST":
        raise RuntimeError("wrong B3_WR_ST shadow artifact")
    if a.get("training_label_cutoff") != "2026-06-30":
        raise RuntimeError("unexpected training cutoff")
    if a.get("jul_aug_labels_used") is not False or a.get("september_labels_used") is not False:
        raise RuntimeError("forbidden label provenance")
    return a


def _value(row: Mapping, key: str) -> float:
    try:
        v = float(row.get(key, float("nan")))
    except Exception:
        v = float("nan")
    return v


def score_state(state: Mapping, row: Mapping) -> float:
    features = list(state["features"])
    med = np.asarray(state["imputer_median"], dtype=float)
    mean = np.asarray(state["scaler_mean"], dtype=float)
    scale = np.asarray(state["scaler_scale"], dtype=float)
    coef = np.asarray(state["coef"], dtype=float)
    intercept = float(state["intercept"])
    if not (len(features) == len(med) == len(mean) == len(scale) == len(coef)):
        raise RuntimeError("corrupt model dimensions")
    x = np.asarray([_value(row, k) for k in features], dtype=float)
    missing = ~np.isfinite(x)
    x[missing] = med[missing]
    if np.any(~np.isfinite(x)) or np.any(scale <= 0):
        raise RuntimeError("invalid frozen model state/input")
    z = (x - mean) / scale
    logit = float(intercept + np.dot(z, coef))
    if logit >= 0:
        p = 1.0 / (1.0 + math.exp(-logit))
    else:
        e = math.exp(logit)
        p = e / (1.0 + e)
    if not 0.0 <= p <= 1.0:
        raise RuntimeError("invalid probability")
    return p


def score_pre(row: Mapping, artifact: Mapping) -> float:
    return score_state(artifact["models"]["PRE"], row)


def score_post(row: Mapping, artifact: Mapping) -> float:
    return score_state(artifact["models"]["POST"], row)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features-json", required=True)
    ap.add_argument("--stage", choices=["PRE", "POST"], required=True)
    ap.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    a = ap.parse_args()
    row = json.loads(Path(a.features_json).read_text(encoding="utf-8"))
    art = load_artifact(a.artifact)
    p = score_pre(row, art) if a.stage == "PRE" else score_post(row, art)
    print(json.dumps({"policy": POLICY, "stage": a.stage, "p4head": p, "result_or_payout_used": False}))


if __name__ == "__main__":
    main()
