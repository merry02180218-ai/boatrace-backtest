#!/usr/bin/env python3
"""Inference-only scorer for frozen HEAD4_V291_COMP7 downstream artifacts.

This module MUST NOT train, refit, calibrate, tune, or read outcomes.  It consumes
only the JSON state produced by freeze_4head_v291_downstream_artifacts.py and
pre-result feature rows supplied by the LIVE feature builder.

It implements:
- POST frozen logistic inference
- ENV_ENTRY frozen logistic inference
- v283 SECOND PLAYER_START listwise probabilities
- v283 conditional THIRD COND_BASE probabilities
- frozen TOP2XTOP2 / alpha2=.60 Top4 pair ordering

Missing artifact structure, missing feature keys, malformed candidate sets, or
policy mismatch fail closed via FrozenInferenceError.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parent
DEFAULT_ARTIFACT = ROOT / "artifacts" / "head4_v291_downstream_20260630.json"
POLICY = "HEAD4_V291_COMP7"
CUTOFF = "2026-06-30"
BOATS = (1, 2, 3, 5, 6)
PAIR_MODE = "TOP2XTOP2"
ALPHA2 = 0.60
TOP_N = 4
EXPECTED_THRESHOLDS = {"PRE": 0.28, "POST": 0.25, "ENV_ENTRY": 0.224790, "COMPOSITE": 7.0}


class FrozenInferenceError(RuntimeError):
    """Fail-closed production inference error."""


def _as_float(v: Any) -> float:
    if v is None:
        return float("nan")
    try:
        x = float(v)
    except (TypeError, ValueError):
        return float("nan")
    return x


def _validate_state(state: Mapping[str, Any], coef_key: str) -> None:
    features = list(state.get("features") or [])
    if not features:
        raise FrozenInferenceError("empty frozen feature list")
    n = len(features)
    for key in ("imputer_median", "scaler_mean", "scaler_scale", coef_key):
        vals = state.get(key)
        if not isinstance(vals, list) or len(vals) != n:
            raise FrozenInferenceError(f"invalid frozen state length: {key}")
        a = np.asarray(vals, dtype=float)
        if not np.isfinite(a).all():
            raise FrozenInferenceError(f"non-finite frozen state: {key}")
    scale = np.asarray(state["scaler_scale"], dtype=float)
    if (scale <= 0).any():
        raise FrozenInferenceError("non-positive frozen scaler scale")
    if coef_key == "coef":
        try:
            z = float(state["intercept"])
        except (KeyError, TypeError, ValueError) as e:
            raise FrozenInferenceError("invalid frozen logistic intercept") from e
        if not math.isfinite(z):
            raise FrozenInferenceError("non-finite frozen logistic intercept")


def validate_artifact(a: Mapping[str, Any]) -> None:
    if a.get("schema") != "head4_v291_downstream_artifact_v1":
        raise FrozenInferenceError("artifact schema mismatch")
    if a.get("policy") != POLICY:
        raise FrozenInferenceError("artifact policy mismatch")
    if a.get("frozen_training_cutoff") != CUTOFF:
        raise FrozenInferenceError("artifact cutoff mismatch")
    if a.get("production_inference_only") is not True:
        raise FrozenInferenceError("artifact not marked inference-only")
    for k in ("jul_aug_labels_used", "september_labels_used", "v96_production_signal_used"):
        if a.get(k) is not False:
            raise FrozenInferenceError(f"prohibited artifact metadata: {k}")
    if a.get("v283_pair_policy") != {"mode": PAIR_MODE, "alpha2": ALPHA2, "top_n": TOP_N}:
        raise FrozenInferenceError("v283 pair policy mismatch")
    got_thr = a.get("thresholds")
    if not isinstance(got_thr, dict) or any(abs(float(got_thr.get(k, float("nan"))) - v) > 1e-12 for k, v in EXPECTED_THRESHOLDS.items()):
        raise FrozenInferenceError("production thresholds mismatch")
    parity = a.get("parity")
    if not isinstance(parity, dict) or parity.get("status") != "PASS":
        raise FrozenInferenceError("artifact parity is not PASS")
    if str(parity.get("cutoff")) != CUTOFF:
        raise FrozenInferenceError("parity cutoff mismatch")
    _validate_state(a.get("POST", {}), "coef")
    _validate_state(a.get("ENV_ENTRY", {}), "coef")
    _validate_state(a.get("v283_SECOND", {}), "beta")
    _validate_state(a.get("v283_COND_THIRD", {}), "beta")


def load_artifact(path: str | Path = DEFAULT_ARTIFACT) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FrozenInferenceError(f"missing frozen artifact: {p}")
    try:
        a = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise FrozenInferenceError(f"cannot read frozen artifact: {p}") from e
    validate_artifact(a)
    return a


def _vector(row: Mapping[str, Any], state: Mapping[str, Any]) -> np.ndarray:
    features = list(state["features"])
    # Absent feature keys indicate a feature-builder/schema failure and must not be
    # silently imputed. Present-but-NaN values use the exact frozen median imputer.
    missing = [f for f in features if f not in row]
    if missing:
        raise FrozenInferenceError("missing LIVE feature keys: " + ",".join(missing[:12]))
    x = np.asarray([_as_float(row[f]) for f in features], dtype=float)
    med = np.asarray(state["imputer_median"], dtype=float)
    x = np.where(np.isnan(x), med, x)
    if not np.isfinite(x).all():
        raise FrozenInferenceError("non-finite LIVE feature after frozen imputation")
    mean = np.asarray(state["scaler_mean"], dtype=float)
    scale = np.asarray(state["scaler_scale"], dtype=float)
    return (x - mean) / scale


def _linear(row: Mapping[str, Any], state: Mapping[str, Any], coef_key: str) -> float:
    x = _vector(row, state)
    w = np.asarray(state[coef_key], dtype=float)
    v = float(x @ w)
    if not math.isfinite(v):
        raise FrozenInferenceError("non-finite frozen linear score")
    return v


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def score_logistic(row: Mapping[str, Any], state: Mapping[str, Any]) -> float:
    z = float(state["intercept"]) + _linear(row, state, "coef")
    return _sigmoid(z)


def score_post(row: Mapping[str, Any], artifact: Mapping[str, Any]) -> float:
    return score_logistic(row, artifact["POST"])


def score_env_entry(row: Mapping[str, Any], artifact: Mapping[str, Any]) -> float:
    return score_logistic(row, artifact["ENV_ENTRY"])


def _softmax(items: Sequence[tuple[Any, float]]) -> dict[Any, float]:
    if not items:
        raise FrozenInferenceError("empty softmax candidate set")
    s = np.asarray([v for _, v in items], dtype=float)
    if not np.isfinite(s).all():
        raise FrozenInferenceError("non-finite listwise score")
    e = np.exp(s - s.max())
    den = float(e.sum())
    if not math.isfinite(den) or den <= 0:
        raise FrozenInferenceError("invalid listwise normalizer")
    return {k: float(v / den) for (k, _), v in zip(items, e)}


def score_second(rows: Sequence[Mapping[str, Any]], artifact: Mapping[str, Any]) -> dict[int, float]:
    if len(rows) != 5:
        raise FrozenInferenceError(f"SECOND requires exactly 5 rows, got {len(rows)}")
    boats = [int(r.get("boat", 0)) for r in rows]
    if sorted(boats) != list(BOATS) or len(set(boats)) != 5:
        raise FrozenInferenceError(f"SECOND boat set mismatch: {boats}")
    state = artifact["v283_SECOND"]
    vals = [(int(r["boat"]), _linear(r, state, "beta")) for r in rows]
    return _softmax(vals)


def score_conditional_third(rows: Sequence[Mapping[str, Any]], artifact: Mapping[str, Any]) -> dict[tuple[int, int], float]:
    if len(rows) != 20:
        raise FrozenInferenceError(f"conditional THIRD requires exactly 20 rows, got {len(rows)}")
    state = artifact["v283_COND_THIRD"]
    groups: dict[int, list[tuple[int, float]]] = {s: [] for s in BOATS}
    seen: set[tuple[int, int]] = set()
    for r in rows:
        s = int(r.get("second_boat", 0))
        t = int(r.get("third_boat", 0))
        if s not in BOATS or t not in BOATS or s == t:
            raise FrozenInferenceError(f"invalid conditional pair: {s}>{t}")
        if (s, t) in seen:
            raise FrozenInferenceError(f"duplicate conditional pair: {s}>{t}")
        seen.add((s, t))
        groups[s].append((t, _linear(r, state, "beta")))
    expected = {(s, t) for s in BOATS for t in BOATS if s != t}
    if seen != expected:
        raise FrozenInferenceError("conditional THIRD pair universe mismatch")
    out: dict[tuple[int, int], float] = {}
    for s in BOATS:
        if len(groups[s]) != 4:
            raise FrozenInferenceError(f"conditional THIRD group {s} does not have 4 rows")
        p = _softmax(groups[s])
        for t, v in p.items():
            out[(s, int(t))] = float(v)
    return out


def _joint_order(p2: Mapping[int, float], pc: Mapping[tuple[int, int], float]) -> list[tuple[int, int]]:
    z = []
    for s in BOATS:
        for t in BOATS:
            if s == t:
                continue
            try:
                ps = float(p2[s])
                pt = float(pc[(s, t)])
            except (KeyError, TypeError, ValueError) as e:
                raise FrozenInferenceError(f"missing v283 probability for {s}>{t}") from e
            if not (math.isfinite(ps) and math.isfinite(pt) and ps > 0 and pt > 0):
                raise FrozenInferenceError(f"invalid v283 probability for {s}>{t}")
            sc = ALPHA2 * math.log(max(ps, 1e-12)) + (1.0 - ALPHA2) * math.log(max(pt, 1e-12))
            z.append((sc, s, t))
    z.sort(key=lambda x: (-x[0], x[1], x[2]))
    return [(s, t) for _, s, t in z]


def v283_top4(p2: Mapping[int, float], pc: Mapping[tuple[int, int], float]) -> list[tuple[int, int]]:
    """Replicate frozen v283 TOP2XTOP2 ordering and return exactly four pairs."""
    if set(p2) != set(BOATS):
        raise FrozenInferenceError("SECOND probability boat universe mismatch")
    if len(pc) != 20:
        raise FrozenInferenceError("conditional THIRD probability universe mismatch")
    base = _joint_order(p2, pc)
    sr = sorted(BOATS, key=lambda s: (-float(p2[s]), s))
    cr = {
        s: sorted((t for t in BOATS if t != s), key=lambda t: (-float(pc[(s, t)]), t))
        for s in BOATS
    }
    s1, s2 = sr[:2]
    pool = [(s, cr[s][k]) for k in (0, 1) for s in (s1, s2)]
    base_rank = {pair: idx for idx, pair in enumerate(base)}
    top4 = sorted(pool, key=lambda pair: base_rank[pair])
    if len(top4) != TOP_N or len(set(top4)) != TOP_N:
        raise FrozenInferenceError("v283 TOP2XTOP2 did not produce exactly four unique pairs")
    return top4


def infer_downstream(
    post_row: Mapping[str, Any],
    env_row: Mapping[str, Any],
    second_rows: Sequence[Mapping[str, Any]],
    conditional_rows: Sequence[Mapping[str, Any]],
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    """Run all frozen downstream inference without any training or outcome access."""
    validate_artifact(artifact)
    post = score_post(post_row, artifact)
    env = score_env_entry(env_row, artifact)
    p2 = score_second(second_rows, artifact)
    pc = score_conditional_third(conditional_rows, artifact)
    pairs = v283_top4(p2, pc)
    return {
        "policy": POLICY,
        "POST": post,
        "ENV_ENTRY": env,
        "p2": p2,
        "conditional_third": {f"{s}>{t}": v for (s, t), v in pc.items()},
        "pairs": [[4, s, t] for s, t in pairs],
        "production_inference_only": True,
        "frozen_training_cutoff": CUTOFF,
    }


if __name__ == "__main__":
    a = load_artifact()
    print(json.dumps({
        "status": "ARTIFACT_VALID",
        "policy": a["policy"],
        "frozen_training_cutoff": a["frozen_training_cutoff"],
        "pair_policy": a["v283_pair_policy"],
    }, ensure_ascii=False, indent=2))
