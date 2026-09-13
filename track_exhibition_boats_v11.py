#!/usr/bin/env python3
"""Result-blind slit-motion corridor wrapper around tracker v9.

v11 deliberately returns to v9's proven dynamic lane cells after v10's fleet-affine
cell experiment regressed all four technical samples.  It keeps v9's joint six-boat
assignment, immutable anchor appearance memory, NCC thresholds and fallback caps
unchanged, and adds only an immutable short-horizon motion-direction sanity guard.

The expected screen-x direction comes from auto_seed_exhibition_motion_v17's
result-blind LK row motion at the slit.  Candidates may fluctuate locally, but a
track is not allowed to run a resolution-scaled distance opposite that immutable
slit direction.  This targets the observed wake/background identity failure where
an outer boat had positive slit LK motion but the tracker ran hundreds of pixels
left while retaining high NCC.  No race result, boat-number rule or race-specific
offset is used.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import cv2
import numpy as np

import track_exhibition_boats_v9 as v9

_DIR_SIGN = np.zeros(6, dtype=np.float32)
_INITIAL_X = np.zeros(6, dtype=np.float32)
_REVERSE_CAP = 96.0
_STEP_REVERSE_CAP = 24.0
_ORIG_JOINT = v9.joint_assign


def motion_corridor_joint(cand_lists, centers, preds, cells, fleet, advance, min_ncc):
    """Apply only generic direction/cumulative sanity filtering, then v9 scoring."""
    filtered = []
    for i, opts in enumerate(cand_lists):
        sign = float(_DIR_SIGN[i])
        keep = []
        for item in opts:
            c = np.asarray(item[0], dtype=np.float32)
            if sign != 0.0:
                cumulative = sign * float(c[0] - _INITIAL_X[i])
                step = sign * float(c[0] - centers[i, 0])
                # Resolution-scaled generous corridor: small counter-motion is
                # permitted, but a wake/background run opposite the slit flow is not.
                if cumulative < -_REVERSE_CAP:
                    continue
                if step < -_STEP_REVERSE_CAP * max(1, int(advance)):
                    continue
            keep.append(item)
        # Empty candidate sets intentionally make the existing joint assignment
        # fail closed; never restore an unsafe fallback merely to obtain a pass.
        filtered.append(keep)
    if any(len(x) == 0 for x in filtered):
        return None, -1e100
    return _ORIG_JOINT(filtered, centers, preds, cells, fleet, advance, min_ncc)


def _rewrite_output(path: Path, meta_path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return
    obj['method'] = (
        'v9 joint anchor-memory tracker + v11 immutable result-blind '
        'slit-motion direction corridor'
    )
    obj['v11_motion_corridor'] = {
        'seed_meta': str(meta_path),
        'direction_sign': {str(i + 1): int(_DIR_SIGN[i]) for i in range(6)},
        'reverse_cap_px': round(float(_REVERSE_CAP), 3),
        'step_reverse_cap_px_per_native_frame': round(float(_STEP_REVERSE_CAP), 3),
    }
    if obj.get('accepted') and isinstance(obj.get('boats'), dict):
        for rec in obj['boats'].values():
            if 'ses_v9' in rec:
                rec['ses_v11'] = rec.pop('ses_v9')
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    global _DIR_SIGN, _INITIAL_X, _REVERSE_CAP, _STEP_REVERSE_CAP

    out = Path('exhibition_tracking_v11.json')
    if '--out' in sys.argv:
        try:
            out = Path(sys.argv[sys.argv.index('--out') + 1])
        except Exception:
            pass

    if '--seed-meta' not in sys.argv:
        raise SystemExit('--seed-meta is required for v11')
    mi = sys.argv.index('--seed-meta')
    try:
        meta_path = Path(sys.argv[mi + 1])
    except Exception:
        raise SystemExit('--seed-meta requires a path')
    # v9 owns the remaining CLI and must not see the v11-only argument.
    del sys.argv[mi:mi + 2]

    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    rows = meta.get('row_details') or {}
    for boat in range(1, 7):
        dx = float((rows.get(str(boat)) or {}).get('dominant_dx') or 0.0)
        # Ignore near-zero/ambiguous slit motion rather than inventing a direction.
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

    v9.joint_assign = motion_corridor_joint
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
