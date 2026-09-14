#!/usr/bin/env python3
"""Result-blind v25 causal camera-compensated trajectory reachability.

v24 proved that late beam loss in Kiryu6 / Kiryu12 standard / Kiryu12 varied is
primarily predecessor-reachability loss before fleet safety evaluation.  A
fixed 24 px/native-frame Euclidean radius is brittle when screen motion contains
shared camera pan.  v25 therefore changes reachability from a zero-velocity
circle to a causal trajectory-centered corridor derived only from the previous
accepted step.

Principles:
- keep v21 immutable anchors, verified appearance bank, NCC thresholds, fleet
  order/separation/edge checks, reverse-motion corridor and beam logic;
- predict each next center from the predecessor's previous accepted displacement;
- merge proposals inside the same 24 px/native-frame radius around that causal
  prediction, rather than blindly widening a circle around the old center;
- replace the fixed raw screen-step cap after the first step with three hard
  causal guards: residual from robust fleet screen motion <=24 px/native-frame,
  individual acceleration <=20 px/native-frame, and absolute screen step
  <=42 px/native-frame;
- retain all immutable direction/reverse gates and fail closed on ambiguity;
- no race result, future frame, boat-number rule or race-specific offset.

The wider absolute screen-step ceiling is not a free threshold relaxation: a
candidate beyond the old radius is admitted only when it is close to the causal
prediction and passes acceleration, fleet-motion, geometry, identity and
reverse-direction gates.
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

import track_exhibition_boats_v21 as v21

v20 = v21.v20
v19 = v21.v19
v17 = v21.v17

# Child-center -> causal previous displacement hints gathered only from already
# accepted temporal expansions. Multiple hypotheses at the same center are
# robustly aggregated by median.
_STEP_HINTS = defaultdict(list)
DIAG = {
    "merge_calls": 0,
    "predicted_merge_calls": 0,
    "admitted_outside_old_radius": 0,
    "transition_calls": 0,
    "transition_reject_initial_speed": 0,
    "transition_reject_fleet_residual": 0,
    "transition_reject_acceleration": 0,
    "transition_reject_absolute_speed": 0,
    "transition_reject_reverse": 0,
    "transition_accepts": 0,
}


def _key(center):
    c = np.asarray(center, np.float32)
    return (round(float(c[0]) * 2.0) / 2.0,
            round(float(c[1]) * 2.0) / 2.0)


def _step_hint(center):
    seq = _STEP_HINTS.get(_key(center)) or []
    if not seq:
        return None
    arr = np.asarray(seq, np.float32)
    return np.median(arr, axis=0)


def _merge_v25(global_opts, local_opts, bank_opts, prev_center, advance, keep):
    DIAG["merge_calls"] += 1
    adv = max(1, int(advance))
    radius = 24.0 * adv
    prev = np.asarray(prev_center, np.float32)
    hint = _step_hint(prev)
    predicted = prev if hint is None else prev + hint
    if hint is not None:
        DIAG["predicted_merge_calls"] += 1

    raw = [(c, s, s, "immutable") for c, s in list(local_opts) + list(global_opts)]
    raw += list(bank_opts)
    raw.sort(key=lambda z: (0.72 * float(z[1]) + 0.28 * float(z[2])), reverse=True)
    pool = []
    for c, imm, aux, source in raw:
        c = np.asarray(c, np.float32)
        if float(np.linalg.norm(c - predicted)) > radius:
            continue
        if float(np.linalg.norm(c - prev)) > radius:
            DIAG["admitted_outside_old_radius"] += 1
        if any(np.linalg.norm(c - q[0]) < 8.0 for q in pool):
            continue
        pool.append((c, float(imm), float(aux), source))
        if len(pool) >= max(1, int(keep)):
            break
    return pool


def _transition_v25(prev, cur, advance, dir_sign, initial_x, reverse_cap,
                    step_reverse_cap, initial_order):
    DIAG["transition_calls"] += 1
    P0 = prev["centers"]
    P1 = cur["centers"]
    steps = P1 - P0
    adv = max(1, int(advance))
    pv = prev.get("last_step")

    if pv is None:
        if np.any(np.linalg.norm(steps, axis=1) > 24.0 * adv):
            DIAG["transition_reject_initial_speed"] += 1
            return None
    else:
        pv = np.asarray(pv, np.float32)
        robust_prev = np.median(pv, axis=0)
        fleet_residual = steps - robust_prev
        acceleration = steps - pv
        if np.any(np.linalg.norm(fleet_residual, axis=1) > 24.0 * adv):
            DIAG["transition_reject_fleet_residual"] += 1
            return None
        if np.any(np.linalg.norm(acceleration, axis=1) > 20.0 * adv):
            DIAG["transition_reject_acceleration"] += 1
            return None
        if np.any(np.linalg.norm(steps, axis=1) > 42.0 * adv):
            DIAG["transition_reject_absolute_speed"] += 1
            return None

    score = float(cur["local_score"])
    for i in range(6):
        sign = float(dir_sign[i])
        sx = float(steps[i, 0])
        if sign != 0.0:
            signed_step = sign * sx
            progress = sign * float(P1[i, 0] - initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap * adv:
                DIAG["transition_reject_reverse"] += 1
                return None
            if signed_step < 0.0:
                score -= 0.18 * min(-signed_step, step_reverse_cap * adv)
            else:
                score += 0.018 * min(signed_step, 24.0 * adv)
            if progress < 0.0:
                score -= 0.055 * min(-progress, reverse_cap)
        if pv is not None:
            score -= 0.024 * float(np.linalg.norm(steps[i] - pv[i]))

    robust = np.median(steps, axis=0)
    score -= 0.004 * float(np.sum(np.linalg.norm(steps - robust, axis=1)))
    DIAG["transition_accepts"] += 1
    return score, steps


def _expand_predecessor_v25(p, cand_lists, initial_order, initial_x, dir_sign,
                            reverse_cap, W, H, advance, step_reverse_cap,
                            per_path_keep):
    local_exp = []
    for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
        P = np.asarray([cand_lists[i][j][0] for i, j in enumerate(idxs)], np.float32)
        imm_scores = np.asarray([cand_lists[i][j][1] for i, j in enumerate(idxs)], float)
        aux_scores = np.asarray([cand_lists[i][j][2] for i, j in enumerate(idxs)], float)
        sources = [cand_lists[i][j][3] for i, j in enumerate(idxs)]
        s = v19._safe_state(P, imm_scores, initial_order, initial_x, dir_sign,
                            reverse_cap, W, H)
        if s is None:
            continue
        tr = _transition_v25(p, s, advance, dir_sign, initial_x, reverse_cap,
                             step_reverse_cap, initial_order)
        if tr is None:
            continue
        tr_score, step_vec = tr
        tr_score += 0.035 * float(np.sum(np.maximum(0.0, aux_scores - imm_scores)))
        local_exp.append((float(tr_score), s, step_vec, aux_scores, sources))

    local_exp.sort(key=lambda z: z[0], reverse=True)
    out = local_exp[:max(1, int(per_path_keep))]
    # Register only candidates that have passed immutable identity, fleet safety,
    # direction and causal transition gates. This is proposal memory, not a
    # future-frame correction.
    for _score, s, step_vec, _aux, _sources in out:
        for i in range(6):
            key = _key(s["centers"][i])
            bucket = _STEP_HINTS[key]
            bucket.append(np.asarray(step_vec[i], np.float32).copy())
            if len(bucket) > 24:
                del bucket[:-24]
    return out


def _out_path(argv):
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    return Path("exhibition_tracking_v25.json")


def _annotate(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    obj["tracker_version"] = "v25"
    obj["method"] = "v25 causal camera-compensated trajectory reachability + verified appearance bank"
    obj["v25_changes"] = {
        "merge_center": "previous center + median causal previous-step hint",
        "prediction_radius_px_per_native_frame": 24.0,
        "fleet_residual_cap_px_per_native_frame": 24.0,
        "acceleration_cap_px_per_native_frame": 20.0,
        "absolute_screen_step_cap_px_per_native_frame": 42.0,
        "immutable_ncc_threshold_changed": False,
        "reverse_motion_gate_changed": False,
        "fleet_geometry_gate_changed": False,
        "future_frame_feedback": False,
        "result_blind": True,
    }
    obj["v25_diagnostic"] = {k: int(v) for k, v in DIAG.items()}
    boats = obj.get("boats") or {}
    for b in boats.values():
        if "ses_v21" in b and "ses_v25" not in b:
            b["ses_v25"] = b["ses_v21"]
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    v21._merge = _merge_v25
    v20._expand_predecessor = _expand_predecessor_v25
    code = 0
    try:
        v21.main()
    except SystemExit as exc:
        code = int(exc.code or 0) if isinstance(exc.code, (int, type(None))) else 2
    finally:
        _annotate(_out_path(sys.argv))
    print(json.dumps({"v25_diagnostic": DIAG}, ensure_ascii=False))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
