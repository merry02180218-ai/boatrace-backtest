#!/usr/bin/env python3
"""Result-blind v21 beam with explicit rejection attribution.

v21 reaches late frames with many verified-bank proposals but can still produce
zero feasible temporal expansions.  Before changing any safety threshold, v22
measures whether those dead ends are caused by current-frame fleet-state safety
or by predecessor transition/motion consistency.

Tracking behaviour is intentionally unchanged: v22 delegates to v21 and only
wraps the existing v19 safe-state and v17 transition gates with counters.  The
same fail-closed/NCC/geometry/motion gates remain authoritative.  This is a
result-blind diagnostic step used to choose the next principled tracker change.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import track_exhibition_boats_v21 as v21

COUNTERS = {
    "safe_state_calls": 0,
    "safe_state_rejects": 0,
    "safe_state_accepts": 0,
    "transition_calls": 0,
    "transition_rejects": 0,
    "transition_accepts": 0,
}

_ORIG_SAFE = v21.v19._safe_state
_ORIG_TRANSITION = v21.v17._transition


def _safe_counted(*args, **kwargs):
    COUNTERS["safe_state_calls"] += 1
    out = _ORIG_SAFE(*args, **kwargs)
    if out is None:
        COUNTERS["safe_state_rejects"] += 1
    else:
        COUNTERS["safe_state_accepts"] += 1
    return out


def _transition_counted(*args, **kwargs):
    COUNTERS["transition_calls"] += 1
    out = _ORIG_TRANSITION(*args, **kwargs)
    if out is None:
        COUNTERS["transition_rejects"] += 1
    else:
        COUNTERS["transition_accepts"] += 1
    return out


def _out_path(argv):
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    return Path("exhibition_tracking_v21.json")


def _annotate(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    obj["tracker_version"] = "v22-diagnostic"
    obj["method"] = "v22 result-blind v21 rejection-attribution diagnostic"
    obj["v22_diagnostic"] = {
        **COUNTERS,
        "behavior_changed_from_v21": False,
        "quality_thresholds_relaxed": False,
        "purpose": "attribute verified-bank beam exhaustion to fleet-state safety vs temporal transition rejection",
    }
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    # v20._expand_predecessor resolves these module globals at runtime.
    v21.v19._safe_state = _safe_counted
    v21.v17._transition = _transition_counted
    code = 0
    try:
        v21.main()
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 2
    finally:
        _annotate(_out_path(sys.argv))
    print(json.dumps({"v22_rejection_attribution": COUNTERS}, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
