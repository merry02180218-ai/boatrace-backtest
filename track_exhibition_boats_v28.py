#!/usr/bin/env python3
"""Result-blind v28 robust peer-consensus similarity-camera transition model.

v27 fit each held-out boat's camera transform from the other five boats at once.
The unchanged four-video matrix still exhausted every beam, with large residual
and residual-acceleration rejection counts. One wrong peer candidate can bias a
five-peer least-squares transform enough to make an otherwise sane held-out
candidate look impossible.

v28 keeps v25 causal proposal reachability, appearance bank/anchors, beam
search, NCC thresholds, immutable reverse-motion gates, fleet geometry and all
numerical motion caps unchanged. It changes only camera estimation:
- for each held-out boat, use the OTHER five boats only;
- enumerate all C(5,3)=10 three-peer similarity fits;
- validate each fit on the two peers not used for fitting;
- choose the fit with the smallest robust validation loss (max error, then mean
  error as deterministic tie-break);
- judge the held-out boat with that peer-consensus transform;
- use the same robust procedure for the preceding interval before applying the
  unchanged 24 px/native-frame residual and 20 px/native-frame residual-
  acceleration caps.

Thus a single bad peer cannot dominate the camera estimate. This is a robust
coordinate-model correction, not threshold relaxation. It uses current/past
result-blind centers only; no future frame, race result, boat-number special
case or race-specific offset is used.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v25 as v25
import track_exhibition_boats_v27 as v27

DIAG28 = {
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


def _robust_loo_similarity_residual(src: np.ndarray, dst: np.ndarray):
    """Held-out residuals using robust consensus among the other five boats."""
    src = np.asarray(src, np.float32)
    dst = np.asarray(dst, np.float32)
    if src.shape != (6, 2) or dst.shape != (6, 2):
        return None
    out = np.zeros((6, 2), np.float32)
    DIAG28["consensus_fit_calls"] += 1
    all_idx = np.arange(6)
    for held in range(6):
        peers = [int(j) for j in all_idx if int(j) != held]
        best = None
        for fit_idx in itertools.combinations(peers, 3):
            fit_idx = list(fit_idx)
            val_idx = [j for j in peers if j not in fit_idx]
            sol = v27._fit_similarity(src[fit_idx], dst[fit_idx])
            if sol is None:
                continue
            DIAG28["consensus_candidate_fits"] += 1
            errs = []
            for j in val_idx:
                pred = v27._apply_similarity(src[j], sol)
                errs.append(float(np.linalg.norm(dst[j] - pred)))
            if len(errs) != 2 or not np.all(np.isfinite(errs)):
                continue
            # Minimax validation resists a fit that explains one validation
            # peer perfectly while sacrificing the other. Mean is only a
            # deterministic tie-break; neither quantity is a new hard gate.
            key = (max(errs), float(np.mean(errs)), tuple(fit_idx))
            if best is None or key < best[0]:
                best = (key, sol)
        if best is None:
            return None
        pred = v27._apply_similarity(src[held], best[1])
        out[held] = dst[held] - pred
    return out


def _transition_v28(prev, cur, advance, dir_sign, initial_x, reverse_cap,
                    step_reverse_cap, initial_order):
    DIAG28["transition_calls"] += 1
    P0 = np.asarray(prev["centers"], np.float32)
    P1 = np.asarray(cur["centers"], np.float32)
    steps = P1 - P0
    adv = max(1, int(advance))
    pv = prev.get("last_step")

    if pv is None:
        if np.any(np.linalg.norm(steps, axis=1) > 24.0 * adv):
            DIAG28["transition_reject_initial_speed"] += 1
            return None
        rel_cur = steps - np.median(steps, axis=0)
        rel_prev = None
    else:
        pv = np.asarray(pv, np.float32)
        rel_cur = _robust_loo_similarity_residual(P0, P1)
        PP = P0 - pv
        rel_prev = _robust_loo_similarity_residual(PP, P0)
        if rel_cur is None or rel_prev is None:
            DIAG28["transition_reject_consensus_fit"] += 1
            return None
        rel_accel = rel_cur - rel_prev
        if np.any(np.linalg.norm(rel_cur, axis=1) > 24.0 * adv):
            DIAG28["transition_reject_relative_residual"] += 1
            return None
        if np.any(np.linalg.norm(rel_accel, axis=1) > 20.0 * adv):
            DIAG28["transition_reject_relative_acceleration"] += 1
            return None
        if np.any(np.linalg.norm(steps, axis=1) > 42.0 * adv):
            DIAG28["transition_reject_absolute_speed"] += 1
            return None

    score = float(cur["local_score"])
    for i in range(6):
        sign = float(dir_sign[i])
        sx = float(steps[i, 0])
        if sign != 0.0:
            signed_step = sign * sx
            progress = sign * float(P1[i, 0] - initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap * adv:
                DIAG28["transition_reject_reverse"] += 1
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
    DIAG28["transition_accepts"] += 1
    return score, steps


def _out_path(argv):
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    return Path("exhibition_tracking_v28.json")


def _annotate28(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    obj["tracker_version"] = "v28"
    obj["method"] = "v28 causal trajectory + robust peer-consensus leave-one-out similarity-camera transition"
    obj["v28_changes"] = {
        "proposal_reachability": "unchanged v25 causal predecessor prediction",
        "camera_model": "per-boat robust C(5,3) peer-consensus similarity; held-out boat never fits itself",
        "camera_fit_validation": "two unused peers; minimize max error then mean error",
        "relative_residual_cap_px_per_native_frame": 24.0,
        "relative_acceleration_cap_px_per_native_frame": 20.0,
        "absolute_screen_step_cap_px_per_native_frame": 42.0,
        "immutable_ncc_threshold_changed": False,
        "reverse_motion_gate_changed": False,
        "fleet_geometry_gate_changed": False,
        "future_frame_feedback": False,
        "result_blind": True,
    }
    obj["v28_diagnostic"] = {k: int(v) for k, v in DIAG28.items()}
    boats = obj.get("boats") or {}
    for b in boats.values():
        if "ses_v25" in b and "ses_v28" not in b:
            b["ses_v28"] = b["ses_v25"]
        elif "ses_v21" in b and "ses_v28" not in b:
            b["ses_v28"] = b["ses_v21"]
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    v25._transition_v25 = _transition_v28
    code = 0
    try:
        v25.main()
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 2
    finally:
        _annotate28(_out_path(sys.argv))
    print(json.dumps({"v28_diagnostic": DIAG28}, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
