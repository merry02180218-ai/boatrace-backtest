#!/usr/bin/env python3
"""Offline verifier for head4_v291_downstream_inference.py.

Uses only a synthetic frozen artifact.  No race outcomes, network, or fitting.
"""
from __future__ import annotations

import math

import head4_v291_downstream_inference as h


def state(features, weights, intercept=None):
    q = {
        "features": list(features),
        "imputer_median": [0.0] * len(features),
        "scaler_mean": [0.0] * len(features),
        "scaler_scale": [1.0] * len(features),
    }
    if intercept is None:
        q.update({"kind": "standardized_listwise_linear", "beta": list(weights)})
    else:
        q.update({"kind": "standardized_logistic", "coef": list(weights), "intercept": float(intercept)})
    return q


def artifact():
    return {
        "schema": "head4_v291_downstream_artifact_v1",
        "policy": h.POLICY,
        "frozen_training_cutoff": h.CUTOFF,
        "production_inference_only": True,
        "jul_aug_labels_used": False,
        "september_labels_used": False,
        "v96_production_signal_used": False,
        "v283_pair_policy": {"mode": h.PAIR_MODE, "alpha2": h.ALPHA2, "top_n": h.TOP_N},
        "thresholds": dict(h.EXPECTED_THRESHOLDS),
        "parity": {"status": "PASS", "cutoff": h.CUTOFF},
        "POST": state(["x", "z"], [1.0, -0.5], 0.2),
        "ENV_ENTRY": state(["e"], [0.7], -0.1),
        "v283_SECOND": state(["s"], [1.0]),
        "v283_COND_THIRD": state(["t"], [1.0]),
    }


def main():
    a = artifact()
    h.validate_artifact(a)

    # Logistic math is exact frozen standardize -> linear -> sigmoid.
    p = h.score_post({"x": 1.0, "z": 2.0}, a)
    assert abs(p - (1.0 / (1.0 + math.exp(-0.2)))) < 1e-12
    e = h.score_env_entry({"e": 2.0}, a)
    assert abs(e - (1.0 / (1.0 + math.exp(-1.3)))) < 1e-12

    # Present NaN follows the frozen median imputer, but an absent schema key is a
    # hard failure rather than a silent LIVE feature substitution.
    assert math.isfinite(h.score_post({"x": float("nan"), "z": 0.0}, a))
    try:
        h.score_post({"x": 1.0}, a)
        raise AssertionError("absent LIVE feature key was accepted")
    except h.FrozenInferenceError:
        pass

    second_rows = [
        {"boat": 1, "s": 2.0}, {"boat": 2, "s": 1.5}, {"boat": 3, "s": 0.5},
        {"boat": 5, "s": 0.0}, {"boat": 6, "s": -0.5},
    ]
    p2 = h.score_second(second_rows, a)
    assert abs(sum(p2.values()) - 1.0) < 1e-12
    assert sorted(p2, key=lambda b: (-p2[b], b))[:2] == [1, 2]

    cond_rows = []
    # Make each SECOND candidate prefer lower-numbered available THIRD boats.
    for s in h.BOATS:
        rem = [t for t in h.BOATS if t != s]
        for rank, t in enumerate(rem):
            cond_rows.append({"second_boat": s, "third_boat": t, "t": 4.0 - rank})
    pc = h.score_conditional_third(cond_rows, a)
    for s in h.BOATS:
        assert abs(sum(pc[(s, t)] for t in h.BOATS if t != s) - 1.0) < 1e-12

    top4 = h.v283_top4(p2, pc)
    assert len(top4) == 4 and len(set(top4)) == 4
    assert set(s for s, _ in top4) == {1, 2}
    assert all(t in h.BOATS and t != s for s, t in top4)

    out = h.infer_downstream(
        {"x": 1.0, "z": 2.0}, {"e": 2.0}, second_rows, cond_rows, a
    )
    assert out["policy"] == h.POLICY
    assert out["production_inference_only"] is True
    assert out["frozen_training_cutoff"] == h.CUTOFF
    assert out["pairs"] == [[4, s, t] for s, t in top4]

    # Artifact safety flags and pair policy are hard guards.
    bad = artifact(); bad["jul_aug_labels_used"] = True
    try:
        h.validate_artifact(bad)
        raise AssertionError("Jul/Aug contamination flag was accepted")
    except h.FrozenInferenceError:
        pass
    bad = artifact(); bad["v283_pair_policy"] = {"mode": "JOINT", "alpha2": .60, "top_n": 4}
    try:
        h.validate_artifact(bad)
        raise AssertionError("wrong v283 pair policy was accepted")
    except h.FrozenInferenceError:
        pass

    print("PASS: frozen HEAD4_V291_COMP7 downstream inference verifier")


if __name__ == "__main__":
    main()
