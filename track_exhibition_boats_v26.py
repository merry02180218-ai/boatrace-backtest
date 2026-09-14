#!/usr/bin/env python3
"""Result-blind v26 shared-camera relative-motion transition model.

v25 proved causal predecessor prediction admits many proposals that the old
zero-velocity reachability circle discarded, but all four unchanged technical
samples still fail closed. Artifact diagnostics show most v25 transition
rejections come from comparing the current six-boat screen steps directly to
the *previous* fleet median step and from raw per-boat acceleration. That mixes
shared camera acceleration with true boat-relative acceleration.

v26 keeps v25 proposal reachability, immutable appearance anchors/bank, beam
search, reverse-motion corridor, NCC thresholds, fleet order/separation/edge
checks, and absolute screen-step safety ceiling. It changes only the later-step
motion decomposition:
- compute the robust median screen step of the six boats for the current frame;
- subtract that current shared screen motion before applying the 24 px/native
  frame residual gate;
- compare current boat-relative motion with previous boat-relative motion for
  the 20 px/native-frame acceleration gate;
- retain the unchanged absolute 42 px/native-frame screen-step ceiling;
- retain immutable direction/reverse gates and fail closed on ambiguity.

This is not a free threshold relaxation: the same numerical residual and
acceleration caps are applied in a coordinate system compensated for causal
same-frame shared camera motion. No future frame, race result, boat-number rule,
or race-specific offset is used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v25 as v25

DIAG26 = {
    "transition_calls": 0,
    "transition_reject_initial_speed": 0,
    "transition_reject_relative_residual": 0,
    "transition_reject_relative_acceleration": 0,
    "transition_reject_absolute_speed": 0,
    "transition_reject_reverse": 0,
    "transition_accepts": 0,
}


def _transition_v26(prev, cur, advance, dir_sign, initial_x, reverse_cap,
                    step_reverse_cap, initial_order):
    DIAG26["transition_calls"] += 1
    P0 = prev["centers"]
    P1 = cur["centers"]
    steps = P1 - P0
    adv = max(1, int(advance))
    pv = prev.get("last_step")

    if pv is None:
        if np.any(np.linalg.norm(steps, axis=1) > 24.0 * adv):
            DIAG26["transition_reject_initial_speed"] += 1
            return None
        rel_cur = steps - np.median(steps, axis=0)
        rel_prev = None
    else:
        pv = np.asarray(pv, np.float32)
        robust_cur = np.median(steps, axis=0)
        robust_prev = np.median(pv, axis=0)
        rel_cur = steps - robust_cur
        rel_prev = pv - robust_prev
        rel_accel = rel_cur - rel_prev
        if np.any(np.linalg.norm(rel_cur, axis=1) > 24.0 * adv):
            DIAG26["transition_reject_relative_residual"] += 1
            return None
        if np.any(np.linalg.norm(rel_accel, axis=1) > 20.0 * adv):
            DIAG26["transition_reject_relative_acceleration"] += 1
            return None
        if np.any(np.linalg.norm(steps, axis=1) > 42.0 * adv):
            DIAG26["transition_reject_absolute_speed"] += 1
            return None

    score = float(cur["local_score"])
    for i in range(6):
        sign = float(dir_sign[i])
        sx = float(steps[i, 0])
        if sign != 0.0:
            signed_step = sign * sx
            progress = sign * float(P1[i, 0] - initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap * adv:
                DIAG26["transition_reject_reverse"] += 1
                return None
            if signed_step < 0.0:
                score -= 0.18 * min(-signed_step, step_reverse_cap * adv)
            else:
                score += 0.018 * min(signed_step, 24.0 * adv)
            if progress < 0.0:
                score -= 0.055 * min(-progress, reverse_cap)
        if rel_prev is not None:
            score -= 0.024 * float(np.linalg.norm(rel_cur[i] - rel_prev[i]))

    score -= 0.004 * float(np.sum(np.linalg.norm(rel_cur, axis=1)))
    DIAG26["transition_accepts"] += 1
    return score, steps


def _out_path(argv):
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    return Path("exhibition_tracking_v26.json")


def _annotate26(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    obj["tracker_version"] = "v26"
    obj["method"] = "v26 causal trajectory + current shared-camera relative-motion transition"
    obj["v26_changes"] = {
        "proposal_reachability": "unchanged v25 causal predecessor prediction",
        "relative_motion_reference": "current six-boat median screen step",
        "relative_residual_cap_px_per_native_frame": 24.0,
        "relative_acceleration_cap_px_per_native_frame": 20.0,
        "absolute_screen_step_cap_px_per_native_frame": 42.0,
        "immutable_ncc_threshold_changed": False,
        "reverse_motion_gate_changed": False,
        "fleet_geometry_gate_changed": False,
        "future_frame_feedback": False,
        "result_blind": True,
    }
    obj["v26_diagnostic"] = {k: int(v) for k, v in DIAG26.items()}
    boats = obj.get("boats") or {}
    for b in boats.values():
        if "ses_v25" in b and "ses_v26" not in b:
            b["ses_v26"] = b["ses_v25"]
        elif "ses_v21" in b and "ses_v26" not in b:
            b["ses_v26"] = b["ses_v21"]
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    v25._transition_v25 = _transition_v26
    code = 0
    try:
        v25.main()
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 2
    finally:
        _annotate26(_out_path(sys.argv))
    print(json.dumps({"v26_diagnostic": DIAG26}, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
