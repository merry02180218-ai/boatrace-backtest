#!/usr/bin/env python3
"""Fleet-affine lane-reference wrapper around tracker v9.

v10 keeps v9's joint assignment, immutable anchor memory, thresholds and fallback
caps unchanged. It changes only the dynamic vertical lane-cell reference: instead
of deriving cells directly from the previous raw centers (which can create a
self-reinforcing collapse when one outer row drifts), it fits a robust affine map
from the immutable seed-frame y geometry to the current fleet y geometry, then
clips each boat's residual around that fleet-consistent reference before building
cells. This is generic, result-blind, entry-order agnostic and has no boat/race
special case.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v6 as base
import track_exhibition_boats_v9 as v9

_Y0 = None


def _robust_affine(y0, y):
    X = np.c_[np.ones(len(y0)), y0]
    w = np.ones(len(y0), float)
    beta = np.array([0.0, 1.0], float)
    for _ in range(5):
        beta = np.linalg.lstsq(X * w[:, None], y * w, rcond=None)[0]
        r = y - X @ beta
        med = np.median(r)
        scale = max(2.0, 1.4826 * np.median(np.abs(r - med)))
        w = 1.0 / np.maximum(1.0, np.abs(r - med) / (2.5 * scale))
    return X @ beta


def fleet_affine_cells(centers, order, height, margin=3.0):
    global _Y0
    centers = np.asarray(centers, np.float32)
    if _Y0 is None:
        _Y0 = centers[:, 1].astype(float).copy()

    y = centers[:, 1].astype(float)
    ref_fit = _robust_affine(_Y0, y)

    # Residual allowance is scale-aware and derived only from immutable seed
    # spacing. It allows local perspective motion while preventing a single row
    # from dragging its lane boundary into an adjacent identity.
    y0_order = _Y0[order]
    gaps0 = np.diff(y0_order)
    local_gap = np.empty(6, float)
    for k, idx in enumerate(order):
        neigh = []
        if k > 0:
            neigh.append(gaps0[k - 1])
        if k < len(order) - 1:
            neigh.append(gaps0[k])
        local_gap[int(idx)] = min(neigh) if neigh else 40.0
    residual_cap = np.maximum(12.0, 0.28 * local_gap)
    ref_y = ref_fit + np.clip(y - ref_fit, -residual_cap, residual_cap)

    ys = ref_y[order]
    # A valid fleet projection must remain ordered. If the affine model itself
    # degenerates, fail closed rather than silently widening lanes.
    if np.any(np.diff(ys) <= 10.0):
        return None
    mids = (ys[:-1] + ys[1:]) / 2.0
    cells = {}
    for k, idx in enumerate(order):
        lo = 0.0 if k == 0 else mids[k - 1] + margin
        hi = float(height - 1) if k == len(order) - 1 else mids[k] - margin
        if hi - lo < 18.0:
            return None
        cells[int(idx)] = (float(lo), float(hi))
    return cells


def _rewrite_output(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return
    obj['method'] = 'v9 joint anchor-memory tracker + v10 fleet-affine lane reference cells'
    if obj.get('accepted') and isinstance(obj.get('boats'), dict):
        for rec in obj['boats'].values():
            if 'ses_v9' in rec:
                rec['ses_v10'] = rec.pop('ses_v9')
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    # Detect output path so failure diagnostics can also be relabeled.
    out = Path('exhibition_tracking_v10.json')
    if '--out' in sys.argv:
        try:
            out = Path(sys.argv[sys.argv.index('--out') + 1])
        except Exception:
            pass
    base.dynamic_cells = fleet_affine_cells
    code = 0
    try:
        v9.main()
    except SystemExit as e:
        code = int(e.code or 0)
    finally:
        _rewrite_output(out)
    if code:
        raise SystemExit(code)


if __name__ == '__main__':
    main()
