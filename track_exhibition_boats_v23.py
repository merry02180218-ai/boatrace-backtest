#!/usr/bin/env python3
"""Result-blind v21 tracker with fine-grained rejection attribution.

v22 established that v21's transition gate rejects zero states in the audited
matrix while late verified-bank beam exhaustion persists. v23 deliberately
keeps tracking behaviour unchanged and instruments the remaining pre-transition
path: fleet safety rejection categories plus per _expand_predecessor call
candidate-list sizes and rejection deltas.

No threshold, proposal source, score, beam width, geometry rule, motion rule or
race-specific behaviour is changed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v21 as v21

SAFE = {
    "calls": 0,
    "accepts": 0,
    "rejects": 0,
    "reject_order": 0,
    "reject_gap": 0,
    "reject_edge": 0,
    "reject_duplicate": 0,
    "reject_reverse_corridor": 0,
    "reject_unknown": 0,
}
TRANS = {"calls": 0, "accepts": 0, "rejects": 0}
EXPANSIONS = []

_ORIG_SAFE = v21.v19._safe_state
_ORIG_TRANS = v21.v17._transition
_ORIG_EXPAND = v21.v20._expand_predecessor


def _classify_safe_reject(P, initial_order, initial_x, dir_sign,
                          reverse_cap, width, height):
    P = np.asarray(P)
    ys = P[:, 1]
    if not np.array_equal(np.argsort(ys), np.asarray(initial_order)):
        return "reject_order"
    gaps = np.diff(ys[np.asarray(initial_order)])
    if np.any(gaps <= 4.0):
        return "reject_gap"
    if (np.any(P[:, 0] < 8) or np.any(P[:, 0] > width - 8)
            or np.any(P[:, 1] < 8) or np.any(P[:, 1] > height - 8)):
        return "reject_edge"
    for a in range(6):
        for b in range(a + 1, 6):
            if np.linalg.norm(P[a] - P[b]) < 20.0:
                return "reject_duplicate"
    for i in range(6):
        sign = float(dir_sign[i])
        if sign == 0.0:
            continue
        progress = sign * float(P[i, 0] - initial_x[i])
        if progress < -float(reverse_cap):
            return "reject_reverse_corridor"
    return "reject_unknown"


def _safe_counted(P, scores, initial_order, initial_x, dir_sign,
                  reverse_cap, width, height):
    SAFE["calls"] += 1
    out = _ORIG_SAFE(P, scores, initial_order, initial_x, dir_sign,
                     reverse_cap, width, height)
    if out is None:
        SAFE["rejects"] += 1
        key = _classify_safe_reject(P, initial_order, initial_x, dir_sign,
                                    reverse_cap, width, height)
        SAFE[key] += 1
    else:
        SAFE["accepts"] += 1
    return out


def _transition_counted(*args, **kwargs):
    TRANS["calls"] += 1
    out = _ORIG_TRANS(*args, **kwargs)
    if out is None:
        TRANS["rejects"] += 1
    else:
        TRANS["accepts"] += 1
    return out


def _expand_counted(p, cand_lists, *args, **kwargs):
    before_safe = dict(SAFE)
    before_trans = dict(TRANS)
    lengths = [len(x) for x in cand_lists]
    product_size = int(np.prod(lengths, dtype=np.int64)) if lengths else 0
    out = _ORIG_EXPAND(p, cand_lists, *args, **kwargs)
    safe_delta = {k: SAFE[k] - before_safe[k] for k in SAFE}
    trans_delta = {k: TRANS[k] - before_trans[k] for k in TRANS}
    EXPANSIONS.append({
        "candidate_lengths": lengths,
        "cartesian_states": product_size,
        "safe": safe_delta,
        "transition": trans_delta,
        "output_expansions": len(out),
    })
    return out


def _out_path(argv):
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    return Path("exhibition_tracking_v23.json")


def _annotate(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    obj["tracker_version"] = "v23-diagnostic"
    obj["method"] = "v23 result-blind fine-grained rejection attribution diagnostic"
    obj["v23_diagnostic"] = {
        "safe_state": SAFE,
        "transition": TRANS,
        "expansion_calls": EXPANSIONS,
        "behavior_changed_from_v21": False,
        "quality_thresholds_relaxed": False,
        "purpose": "attribute beam exhaustion to exact fleet-safety category or pre-safe candidate loss",
    }
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    # v21 calls these module objects dynamically, so wrappers observe the exact
    # existing behaviour without replacing any decision rule.
    v21.v19._safe_state = _safe_counted
    v21.v17._transition = _transition_counted
    v21.v20._expand_predecessor = _expand_counted
    code = 0
    try:
        v21.main()
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 2
    finally:
        _annotate(_out_path(sys.argv))
    print(json.dumps({
        "v23_safe": SAFE,
        "v23_transition": TRANS,
        "v23_expansion_calls": len(EXPANSIONS),
    }, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
