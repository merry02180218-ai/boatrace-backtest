#!/usr/bin/env python3
"""Result-blind v27 leave-one-out similarity-camera transition model.

v26 removed same-frame shared translation before residual/acceleration gates and
materially increased accepted transitions, but three available unchanged-matrix
artifacts still exhausted their beams. A translation-only camera model cannot
represent zoom/rotation, so perspective rows can acquire artificial residual
acceleration even when boat identity is physically sane.

v27 keeps v25 causal proposal reachability, immutable appearance anchors/bank,
beam search, reverse-motion corridor, NCC thresholds, fleet order/separation/
edge checks, and every numerical motion safety cap unchanged. It changes only
the shared-camera coordinate model used by the later-step residual and
acceleration gates:
- for each boat, fit a 2-D similarity transform (translation + uniform scale +
  rotation) from the OTHER five boats between predecessor and current frame;
- evaluate the held-out boat residual against that transform, preventing the
  boat being judged from explaining away its own candidate error;
- reconstruct the previous interval from predecessor raw last_step and compute
  the same leave-one-out similarity residual there;
- apply the unchanged 24 px/native-frame residual cap and 20 px/native-frame
  residual-acceleration cap;
- retain the unchanged 42 px/native-frame absolute raw screen-step ceiling and
  immutable slit-direction reverse gates.

This is a coordinate-model correction, not threshold relaxation. It uses only
current/past result-blind centers, no future frame, race result, boat-number
special case, or race-specific offset.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v25 as v25

DIAG27 = {
    "transition_calls": 0,
    "transition_reject_initial_speed": 0,
    "transition_reject_similarity_fit": 0,
    "transition_reject_relative_residual": 0,
    "transition_reject_relative_acceleration": 0,
    "transition_reject_absolute_speed": 0,
    "transition_reject_reverse": 0,
    "transition_accepts": 0,
}


def _fit_similarity(src: np.ndarray, dst: np.ndarray):
    """Least-squares 2-D similarity: [x',y'] = sR[x,y] + t."""
    src = np.asarray(src, np.float64)
    dst = np.asarray(dst, np.float64)
    if src.shape[0] < 2 or src.shape != dst.shape or src.shape[1] != 2:
        return None
    rows = []
    vals = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([x, -y, 1.0, 0.0])
        vals.append(u)
        rows.append([y, x, 0.0, 1.0])
        vals.append(v)
    A = np.asarray(rows, np.float64)
    b = np.asarray(vals, np.float64)
    try:
        sol, _, rank, _ = np.linalg.lstsq(A, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    if int(rank) < 4 or not np.all(np.isfinite(sol)):
        return None
    return sol


def _apply_similarity(pt: np.ndarray, sol: np.ndarray):
    x, y = float(pt[0]), float(pt[1])
    a, b, tx, ty = [float(z) for z in sol]
    return np.asarray([a * x - b * y + tx, b * x + a * y + ty], np.float32)


def _loo_similarity_residual(src: np.ndarray, dst: np.ndarray):
    """Held-out residual for each boat using transform fit on other five boats."""
    src = np.asarray(src, np.float32)
    dst = np.asarray(dst, np.float32)
    out = np.zeros((6, 2), np.float32)
    for i in range(6):
        keep = np.ones(6, dtype=bool)
        keep[i] = False
        sol = _fit_similarity(src[keep], dst[keep])
        if sol is None:
            return None
        pred = _apply_similarity(src[i], sol)
        out[i] = dst[i] - pred
    return out


def _transition_v27(prev, cur, advance, dir_sign, initial_x, reverse_cap,
                    step_reverse_cap, initial_order):
    DIAG27["transition_calls"] += 1
    P0 = np.asarray(prev["centers"], np.float32)
    P1 = np.asarray(cur["centers"], np.float32)
    steps = P1 - P0
    adv = max(1, int(advance))
    pv = prev.get("last_step")

    if pv is None:
        if np.any(np.linalg.norm(steps, axis=1) > 24.0 * adv):
            DIAG27["transition_reject_initial_speed"] += 1
            return None
        rel_cur = steps - np.median(steps, axis=0)
        rel_prev = None
    else:
        pv = np.asarray(pv, np.float32)
        # Current interval: each boat is held out of the camera transform that
        # judges it, so a wrong candidate cannot absorb its own error.
        rel_cur = _loo_similarity_residual(P0, P1)
        # Previous interval can be reconstructed causally from raw last_step.
        PP = P0 - pv
        rel_prev = _loo_similarity_residual(PP, P0)
        if rel_cur is None or rel_prev is None:
            DIAG27["transition_reject_similarity_fit"] += 1
            return None
        rel_accel = rel_cur - rel_prev
        if np.any(np.linalg.norm(rel_cur, axis=1) > 24.0 * adv):
            DIAG27["transition_reject_relative_residual"] += 1
            return None
        if np.any(np.linalg.norm(rel_accel, axis=1) > 20.0 * adv):
            DIAG27["transition_reject_relative_acceleration"] += 1
            return None
        if np.any(np.linalg.norm(steps, axis=1) > 42.0 * adv):
            DIAG27["transition_reject_absolute_speed"] += 1
            return None

    score = float(cur["local_score"])
    for i in range(6):
        sign = float(dir_sign[i])
        sx = float(steps[i, 0])
        if sign != 0.0:
            signed_step = sign * sx
            progress = sign * float(P1[i, 0] - initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap * adv:
                DIAG27["transition_reject_reverse"] += 1
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
    DIAG27["transition_accepts"] += 1
    # Preserve raw screen step for v25 causal proposal prediction and for
    # reconstructing the previous interval on the next update.
    return score, steps


def _out_path(argv):
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    return Path("exhibition_tracking_v27.json")


def _annotate27(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    obj["tracker_version"] = "v27"
    obj["method"] = "v27 causal trajectory + leave-one-out similarity-camera residual transition"
    obj["v27_changes"] = {
        "proposal_reachability": "unchanged v25 causal predecessor prediction",
        "camera_model": "per-boat leave-one-out 2D similarity from other five boats",
        "relative_residual_cap_px_per_native_frame": 24.0,
        "relative_acceleration_cap_px_per_native_frame": 20.0,
        "absolute_screen_step_cap_px_per_native_frame": 42.0,
        "immutable_ncc_threshold_changed": False,
        "reverse_motion_gate_changed": False,
        "fleet_geometry_gate_changed": False,
        "future_frame_feedback": False,
        "result_blind": True,
    }
    obj["v27_diagnostic"] = {k: int(v) for k, v in DIAG27.items()}
    boats = obj.get("boats") or {}
    for b in boats.values():
        if "ses_v25" in b and "ses_v27" not in b:
            b["ses_v27"] = b["ses_v25"]
        elif "ses_v21" in b and "ses_v27" not in b:
            b["ses_v27"] = b["ses_v21"]
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    v25._transition_v25 = _transition_v27
    code = 0
    try:
        v25.main()
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 2
    finally:
        _annotate27(_out_path(sys.argv))
    print(json.dumps({"v27_diagnostic": DIAG27}, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
