#!/usr/bin/env python3
from __future__ import annotations

import copy
import math

import numpy as np

from build_4head_a_live_live import ALiveBuildError, assemble, expected_features
from head4_v273_a_live_inference import FrozenARankError, classify, load_artifact, score_a


def main() -> None:
    a = load_artifact()
    fs = expected_features(a)
    assert fs == a["A_SCORE"]["features"]
    assert len(fs) == 17

    # Frozen medians form a deterministic result-blind fixture. Recompute the
    # exact frozen standardized-logistic expression independently of score_a.
    st = a["A_SCORE"]
    base = dict(zip(fs, st["imputer_median"]))
    row = assemble(base, a)
    assert list(row) == fs
    p = score_a(row, a)
    x = np.asarray([row[k] for k in fs], dtype=float)
    zvec = (x - np.asarray(st["scaler_mean"], dtype=float)) / np.asarray(st["scaler_scale"], dtype=float)
    z = float(st["intercept"]) + float(zvec @ np.asarray(st["coef"], dtype=float))
    expected = 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))
    assert abs(p - expected) < 1e-15, (p, expected)

    # S must always win priority without needing A-score eligibility.
    s = classify(.28, .25, .224790, row, a)
    assert s["eligible"] is True and s["layer"] == "S" and s["reason"] == "S_PRIORITY"

    # Outside S but inside A PRE/POST gates must produce a finite frozen score.
    q = classify(.20, .20, .10, row, a)
    assert q["layer"] in ("A", "NONE")
    assert math.isfinite(float(q["A_SCORE_LIVE"]))

    # Missing/non-finite current-day keys fail closed in the assembler.
    for k in fs:
        b = dict(base); b.pop(k)
        try:
            assemble(b, a)
        except ALiveBuildError:
            pass
        else:
            raise AssertionError(f"missing A-LIVE key did not fail closed: {k}")
    b = dict(base); b[fs[0]] = float("nan")
    try:
        assemble(b, a)
    except ALiveBuildError:
        pass
    else:
        raise AssertionError("non-finite A-LIVE key did not fail closed")

    bad = copy.deepcopy(a); bad["A_SCORE"]["features"] = list(reversed(fs))
    try:
        score_a(row, bad)
    except FrozenARankError:
        pass
    else:
        raise AssertionError("artifact schema mutation did not fail closed")

    assert a["jul_aug_labels_used"] is False
    assert a["september_labels_used"] is False
    assert a["mapping"]["outcomes_used_by_mapping"] is False
    print("HEAD4 A-LIVE 17-feature current-day assembler contract PASS")


if __name__ == "__main__":
    main()
