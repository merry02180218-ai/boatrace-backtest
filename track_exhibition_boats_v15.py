#!/usr/bin/env python3
"""Result-blind full-cell anchor-lattice beam tracker for exhibition SES.

v15 keeps v13's multi-frame six-boat beam, immutable slit-motion corridor,
geometry/direction/edge hard gates, NCC thresholds, fallback caps, and adaptive
appearance updates unchanged. It addresses the remaining candidate-omission
failure seen in v14: a physically correct path can disappear when every local
search is tied to a temporarily wrong current prediction.

For each frame/boat, v15 supplements the unchanged local dual-memory proposals
with immutable seed-anchor NCC peaks searched across the boat's entire current
lane cell. Those global anchor peaks are generated independently of the current
x prediction, so the existing v13 temporal beam can act as a short-horizon
candidate lattice/Viterbi-like selector instead of being unable to recover a
candidate that was never proposed. Feasibility and quality gates remain v13's;
no race result, boat-number rule, race-specific offset, or threshold relaxation
is used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

import track_exhibition_boats_v13 as v13
import track_exhibition_boats_v9 as v9

_ORIG_DUAL = v9.dual_candidates
_LAST_FRAME_PTR = None
_FRAME_RESPONSES = {}


def _frame_response(cur_g, anchor):
    """Cache one full-frame immutable-anchor NCC response per anchor for this frame."""
    global _LAST_FRAME_PTR, _FRAME_RESPONSES
    ptr = int(cur_g.__array_interface__['data'][0])
    if ptr != _LAST_FRAME_PTR:
        _LAST_FRAME_PTR = ptr
        _FRAME_RESPONSES = {}
    key = id(anchor)
    if key not in _FRAME_RESPONSES:
        h, w = anchor.shape[:2]
        if cur_g.shape[0] < h or cur_g.shape[1] < w:
            _FRAME_RESPONSES[key] = None
        else:
            _FRAME_RESPONSES[key] = cv2.matchTemplate(
                cur_g, anchor, cv2.TM_CCOEFF_NORMED)
    return _FRAME_RESPONSES[key]


def _full_cell_anchor_candidates(cur_g, adaptive, anchor, ylo, yhi, topk):
    """Return distinct immutable-anchor NCC peaks whose centers lie inside the lane cell."""
    resp = _frame_response(cur_g, anchor)
    if resp is None:
        return []
    th, tw = anchor.shape[:2]
    rh, rw = resp.shape[:2]
    # matchTemplate indexes template top-left; convert lane-cell center bounds to response rows.
    r0 = max(0, int(np.floor(float(ylo) - th / 2.0)))
    r1 = min(rh, int(np.ceil(float(yhi) - th / 2.0)) + 1)
    if r1 <= r0:
        return []
    work = resp[r0:r1].copy()
    out = []
    want = max(2, int(topk) + 1)
    nms_x = max(12, tw // 2)
    nms_y = max(8, th // 2)
    for _ in range(want * 3):
        _mn, score, _mnl, loc = cv2.minMaxLoc(work)
        if not np.isfinite(score):
            break
        x = float(loc[0] + tw / 2.0)
        y = float(r0 + loc[1] + th / 2.0)
        c = np.asarray([x, y], dtype=np.float32)
        an = v9.patch_ncc(cur_g, anchor, c)
        ad = v9.patch_ncc(cur_g, adaptive, c)
        out.append((c, float(ad), float(an), 'full_cell_anchor'))
        yy0 = max(0, loc[1] - nms_y); yy1 = min(work.shape[0], loc[1] + nms_y + 1)
        xx0 = max(0, loc[0] - nms_x); xx1 = min(work.shape[1], loc[0] + nms_x + 1)
        work[yy0:yy1, xx0:xx1] = -2.0
        if len(out) >= want:
            break
    return out


def _lattice_dual_candidates(cur_g, adaptive_t, anchor_t, pred, ylo, yhi,
                             search_x, search_y, topk):
    """Merge unchanged local proposals with state-independent full-cell anchor peaks."""
    pool = list(_ORIG_DUAL(
        cur_g, adaptive_t, anchor_t, pred, ylo, yhi,
        search_x, search_y, topk))
    pool.extend(_full_cell_anchor_candidates(
        cur_g, adaptive_t, anchor_t, ylo, yhi, topk))
    pool.sort(key=lambda z: (max(float(z[1]), float(z[2])),
                             float(z[1]) + float(z[2])), reverse=True)
    kept = []
    limit = max(5, 2 * int(topk) + 2)
    for item in pool:
        if any(float(np.linalg.norm(item[0] - old[0])) < 10.0 for old in kept):
            continue
        kept.append(item)
        if len(kept) >= limit:
            break
    return kept


def _patch_output(path: Path) -> None:
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return
    obj['method'] = 'v15 result-blind full-cell anchor-lattice multi-frame beam tracker'
    obj['tracker_version'] = 'v15'
    obj['v15_changes'] = {
        'temporal_core': 'unchanged v13 multi-hypothesis beam',
        'local_candidates': 'unchanged v9 dual-memory matcher',
        'lattice_candidates': 'immutable seed-anchor NCC peaks across entire current lane cell',
        'candidate_dependence': 'global anchor peaks independent of current x prediction',
        'hard_gates': 'unchanged from v13',
        'ncc_and_fallback_thresholds': 'unchanged from v13',
        'result_blind': True,
    }
    boats = obj.get('boats') or {}
    for b in boats.values():
        if 'ses_v13' in b and 'ses_v15' not in b:
            b['ses_v15'] = b.pop('ses_v13')
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    v9.dual_candidates = _lattice_dual_candidates
    out = Path('exhibition_tracking_v15.json')
    if '--out' in sys.argv:
        try:
            out = Path(sys.argv[sys.argv.index('--out') + 1])
        except Exception:
            pass
    code = 0
    try:
        v13.main()
    except SystemExit as exc:
        code = int(exc.code or 0)
    finally:
        _patch_output(out)
    if code:
        raise SystemExit(code)


if __name__ == '__main__':
    main()
