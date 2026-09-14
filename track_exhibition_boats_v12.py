#!/usr/bin/env python3
"""Result-blind temporal motion-memory wrapper around tracker v9.

v12 keeps v9 candidate generation, dynamic lane cells, immutable anchor memory,
NCC thresholds, fallback caps and fail-closed behavior.  It replaces only the
per-frame joint scoring with a generic multi-frame motion-memory term: each boat
keeps a short history of selected screen-space steps and candidates are scored
against the robust recent velocity/acceleration pattern in addition to the current
LK prediction and fleet motion.  This is intended to reject high-NCC wake/background
tracks that are locally plausible for one frame but temporally inconsistent.

No race result, boat-number rule, race-specific offset, or relaxed threshold is used.
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import deque
from pathlib import Path

import cv2
import numpy as np

import track_exhibition_boats_v9 as v9

_DIR_SIGN = np.zeros(6, dtype=np.float32)
_INITIAL_X = np.zeros(6, dtype=np.float32)
_STEP_HIST = [deque(maxlen=4) for _ in range(6)]
_REVERSE_CAP = 96.0
_STEP_REVERSE_CAP = 24.0


def temporal_joint(cand_lists, centers, preds, cells, fleet, advance, min_ncc):
    best = None
    best_score = -1e100
    adv = max(1, int(advance))
    for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
        pts = []
        score = 0.0
        ok = True
        chosen_steps = []
        for i, j in enumerate(idxs):
            c, ad, an, is_fb = cand_lists[i][j]
            c = np.asarray(c, dtype=np.float32)
            ylo, yhi = cells[i]
            if not (ylo <= float(c[1]) <= yhi):
                ok = False; break
            step_vec = c - centers[i]
            if np.linalg.norm(step_vec) > 24.0 * adv:
                ok = False; break

            sign = float(_DIR_SIGN[i])
            if sign != 0.0:
                cumulative = sign * float(c[0] - _INITIAL_X[i])
                step_dir = sign * float(step_vec[0])
                if cumulative < -_REVERSE_CAP:
                    ok = False; break
                if step_dir < -_STEP_REVERSE_CAP * adv:
                    ok = False; break

            if not is_fb:
                identity = max(float(ad), float(an))
                if identity < min_ncc:
                    ok = False; break
                if abs(float(c[1] - preds[i][1])) > 10.0 * adv:
                    ok = False; break
                score += 1.8 * float(ad) + 1.8 * float(an) + 0.8 * identity
                score -= 0.010 * np.linalg.norm(c - preds[i])
                score -= 0.004 * np.linalg.norm(step_vec - fleet)
            else:
                score -= 1.25

            # Multi-frame temporal likelihood. Use only prior selected steps; no
            # future frame or result information. Robust median limits one bad step.
            if _STEP_HIST[i]:
                hist = np.asarray(list(_STEP_HIST[i]), dtype=np.float32)
                med = np.median(hist, axis=0)
                dev = np.linalg.norm(step_vec - med)
                score -= 0.020 * float(dev)
                if len(hist) >= 2:
                    prev = hist[-1]
                    accel = np.linalg.norm(step_vec - prev)
                    score -= 0.012 * float(accel)
                    # Hard guard only for a dramatic reversal against stable history.
                    xhist = hist[:, 0]
                    stable_sign = np.sign(np.median(xhist))
                    if abs(float(np.median(xhist))) >= 3.0 and stable_sign * float(step_vec[0]) < -18.0 * adv:
                        ok = False; break
            chosen_steps.append(step_vec)
            pts.append(c)
        if not ok:
            continue

        P = np.asarray(pts, np.float32)
        ys = P[:, 1]
        order = np.argsort(centers[:, 1])
        if not np.array_equal(np.argsort(ys), order):
            continue
        if np.any(np.diff(ys[order]) <= 4.0):
            continue
        for a in range(6):
            for b in range(a + 1, 6):
                if np.linalg.norm(P[a] - P[b]) < 20.0:
                    ok = False; break
            if not ok:
                break
        if not ok:
            continue
        if score > best_score:
            best_score = score
            best = idxs

    if best is not None:
        for i, j in enumerate(best):
            c = np.asarray(cand_lists[i][j][0], dtype=np.float32)
            _STEP_HIST[i].append(c - centers[i])
    return best, best_score


def _rewrite_output(path: Path, meta_path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return
    obj['method'] = 'v9 anchor-memory tracker + v12 result-blind temporal motion-memory joint assignment'
    obj['v12_temporal_motion_memory'] = {
        'seed_meta': str(meta_path),
        'history_frames': 4,
        'direction_sign': {str(i + 1): int(_DIR_SIGN[i]) for i in range(6)},
        'reverse_cap_px': round(float(_REVERSE_CAP), 3),
        'step_reverse_cap_px_per_native_frame': round(float(_STEP_REVERSE_CAP), 3),
        'note': 'greedy joint assignment with multi-frame motion likelihood; thresholds inherited from v9',
    }
    if obj.get('accepted') and isinstance(obj.get('boats'), dict):
        for rec in obj['boats'].values():
            if 'ses_v9' in rec:
                rec['ses_v12'] = rec.pop('ses_v9')
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    global _DIR_SIGN, _INITIAL_X, _REVERSE_CAP, _STEP_REVERSE_CAP, _STEP_HIST
    _STEP_HIST = [deque(maxlen=4) for _ in range(6)]
    out = Path('exhibition_tracking_v12.json')
    if '--out' in sys.argv:
        try:
            out = Path(sys.argv[sys.argv.index('--out') + 1])
        except Exception:
            pass

    if '--seed-meta' not in sys.argv:
        raise SystemExit('--seed-meta is required for v12')
    mi = sys.argv.index('--seed-meta')
    meta_path = Path(sys.argv[mi + 1])
    del sys.argv[mi:mi + 2]

    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    rows = meta.get('row_details') or {}
    for boat in range(1, 7):
        dx = float((rows.get(str(boat)) or {}).get('dominant_dx') or 0.0)
        if abs(dx) >= 4.0:
            _DIR_SIGN[boat - 1] = 1.0 if dx > 0 else -1.0

    if '--seed-json' not in sys.argv:
        raise SystemExit('--seed-json is required')
    si = sys.argv.index('--seed-json')
    seed_path = Path(sys.argv[si + 1])
    seed_obj = json.loads(seed_path.read_text(encoding='utf-8'))
    _INITIAL_X = np.asarray([float(seed_obj[str(i)][0]) for i in range(1, 7)], dtype=np.float32)

    video = Path(sys.argv[1])
    cap = cv2.VideoCapture(str(video))
    width = float(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920.0)
    cap.release()
    _REVERSE_CAP = max(48.0, 0.05 * width)
    _STEP_REVERSE_CAP = max(12.0, 0.0125 * width)

    v9.joint_assign = temporal_joint
    code = 0
    try:
        v9.main()
    except SystemExit as e:
        code = int(e.code or 0)
    finally:
        _rewrite_output(out, meta_path)
    if code:
        raise SystemExit(code)


if __name__ == '__main__':
    main()
