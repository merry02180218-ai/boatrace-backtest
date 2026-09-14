#!/usr/bin/env python3
"""Result-blind v29 shared robust fleet-consensus similarity-camera transition.

v28 estimated a different leave-one-out robust camera transform for every held-out
boat. The unchanged four-video matrix reached essentially the same dead-frame
depths as v27 while tracker runtime became much worse. That means occasional
single-peer corruption was not the main blocker, and six independently selected
camera transforms can themselves make one joint fleet state internally
inconsistent.

v29 keeps v25 causal proposal reachability, appearance bank/anchors, beam search,
NCC thresholds, immutable reverse-motion gates, fleet geometry and ALL numerical
motion caps unchanged. It changes only the camera representation:
- one shared robust similarity transform is estimated for the whole six-boat
  candidate state;
- enumerate all C(6,3)=20 three-boat similarity fits;
- score each transform by the 4th-smallest residual across all six boats, then
  trimmed mean of the four best residuals and deterministic fit indices;
- this requires a four-boat fleet consensus without adding a new hard threshold;
- apply that ONE transform to all six boats and then apply the unchanged
  24 px/native-frame residual and 20 px/native-frame residual-acceleration caps;
- estimate the preceding interval the same way.

A bad candidate cannot define a valid camera state by itself because a selected
model must explain at least four boats better than competing models. At the same
time all six boats are judged in one common camera coordinate system. No future
frame, result, boat-number rule, race-specific offset, or threshold relaxation is
used.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v25 as v25
import track_exhibition_boats_v27 as v27

DIAG29 = {
    "transition_calls": 0,
    "transition_reject_initial_speed": 0,
    "transition_reject_consensus_fit": 0,
    "transition_reject_relative_residual": 0,
    "transition_reject_relative_acceleration": 0,
    "transition_reject_absolute_speed": 0,
    "transition_reject_reverse": 0,
    "transition_accepts": 0,
    "consensus_fit_calls": 0,
    "consensus_candidate_fits": 0,
}


def _fleet_consensus_similarity_residual(src: np.ndarray, dst: np.ndarray):
    """Return six residual vectors from one robust shared fleet camera model."""
    src = np.asarray(src, np.float32)
    dst = np.asarray(dst, np.float32)
    if src.shape != (6, 2) or dst.shape != (6, 2):
        return None
    DIAG29["consensus_fit_calls"] += 1
    best = None
    for fit_idx in itertools.combinations(range(6), 3):
        idx = list(fit_idx)
        sol = v27._fit_similarity(src[idx], dst[idx])
        if sol is None:
            continue
        DIAG29["consensus_candidate_fits"] += 1
        residuals = []
        finite = True
        for j in range(6):
            pred = v27._apply_similarity(src[j], sol)
            r = dst[j] - pred
            e = float(np.linalg.norm(r))
            if not np.isfinite(e):
                finite = False
                break
            residuals.append((e, r))
        if not finite or len(residuals) != 6:
            continue
        errs = sorted(float(x[0]) for x in residuals)
        # Robust four-boat consensus. The 4th-smallest error is the primary
        # criterion; the mean of those same four is only a deterministic
        # refinement, not a new hard acceptance threshold.
        key = (errs[3], float(np.mean(errs[:4])), tuple(fit_idx))
        if best is None or key < best[0]:
            best = (key, sol)
    if best is None:
        return None
    sol = best[1]
    out = np.zeros((6, 2), np.float32)
    for j in range(6):
        pred = v27._apply_similarity(src[j], sol)
        out[j] = dst[j] - pred
    return out


def _transition_v29(prev, cur, advance, dir_sign, initial_x, reverse_cap,
                    step_reverse_cap, initial_order):
    DIAG29["transition_calls"] += 1
    P0 = np.asarray(prev["centers"], np.float32)
    P1 = np.asarray(cur["centers"], np.float32)
    steps = P1 - P0
    adv = max(1, int(advance))
    pv = prev.get("last_step")

    if pv is None:
        if np.any(np.linalg.norm(steps, axis=1) > 24.0 * adv):
            DIAG29["transition_reject_initial_speed"] += 1
            return None
        rel_cur = steps - np.median(steps, axis=0)
        rel_prev = None
    else:
        pv = np.asarray(pv, np.float32)
        rel_cur = _fleet_consensus_similarity_residual(P0, P1)
        PP = P0 - pv
        rel_prev = _fleet_consensus_similarity_residual(PP, P0)
        if rel_cur is None or rel_prev is None:
            DIAG29["transition_reject_consensus_fit"] += 1
            return None
        rel_accel = rel_cur - rel_prev
        if np.any(np.linalg.norm(rel_cur, axis=1) > 24.0 * adv):
            DIAG29["transition_reject_relative_residual"] += 1
            return None
        if np.any(np.linalg.norm(rel_accel, axis=1) > 20.0 * adv):
            DIAG29["transition_reject_relative_acceleration"] += 1
            return None
        if np.any(np.linalg.norm(steps, axis=1) > 42.0 * adv):
            DIAG29["transition_reject_absolute_speed"] += 1
            return None

    score = float(cur["local_score"])
    for i in range(6):
        sign = float(dir_sign[i])
        sx = float(steps[i, 0])
        if sign != 0.0:
            signed_step = sign * sx
            progress = sign * float(P1[i, 0] - initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap * adv:
                DIAG29["transition_reject_reverse"] += 1
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
    DIAG29["transition_accepts"] += 1
    return score, steps


def _out_path(argv):
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    return Path("exhibition_tracking_v29.json")


def _annotate29(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    obj["tracker_version"] = "v29"
    obj["method"] = "v29 causal trajectory + shared robust four-of-six fleet-consensus similarity-camera transition"
    obj["v29_changes"] = {
        "proposal_reachability": "unchanged v25 causal predecessor prediction",
        "camera_model": "one shared robust fleet similarity transform selected from C(6,3) fits",
        "camera_fit_selection": "minimize 4th-smallest six-boat residual then mean of four best residuals",
        "relative_residual_cap_px_per_native_frame": 24.0,
        "relative_acceleration_cap_px_per_native_frame": 20.0,
        "absolute_screen_step_cap_px_per_native_frame": 42.0,
        "immutable_ncc_threshold_changed": False,
        "reverse_motion_gate_changed": False,
        "fleet_geometry_gate_changed": False,
        "future_frame_feedback": False,
        "result_blind": True,
    }
    obj["v29_diagnostic"] = {k: int(v) for k, v in DIAG29.items()}
    boats = obj.get("boats") or {}
    for b in boats.values():
        if "ses_v25" in b and "ses_v29" not in b:
            b["ses_v29"] = b["ses_v25"]
        elif "ses_v21" in b and "ses_v29" not in b:
            b["ses_v29"] = b["ses_v21"]
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    v25._transition_v25 = _transition_v29
    code = 0
    try:
        v25.main()
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 2
    finally:
        _annotate29(_out_path(sys.argv))
    print(json.dumps({"v29_diagnostic": DIAG29}, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
