#!/usr/bin/env python3
"""Result-blind hypothesis-diverse wrapper around tracker v17.

v17 proved that a state-independent immutable-anchor lattice plus fleet DP can
fail even while every frame has the configured 96 feasible fleet states.  Its
pre-DP pruning keeps only the highest local appearance scores, and its beam
collapse metric averages displacement across all six boats.  Those two choices
can discard a temporally correct alternative when only one outer boat differs.

v18 changes SEARCH DIVERSITY only; it does not relax any visual, geometry,
motion-direction, edge, step-size, NCC, or final confidence gate from v17.
For every frame it keeps the best state from coarse six-boat x-progress buckets
before filling remaining slots by local score.  During beam deduplication it
uses the maximum per-boat displacement instead of the six-boat mean, so a path
that preserves a materially different identity hypothesis for one boat is not
collapsed merely because the other five boats agree.

No race result, future-frame candidate feedback, boat-number special case,
race-specific offset, or quality-threshold relaxation is used.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v17 as v17

_BUCKET_PX = 32.0


def _diverse_frame_fleet_states(cand_lists, initial_order, initial_x, dir_sign,
                                reverse_cap, width, height, keep):
    """v17 safety gates with diversity-preserving pre-DP state retention."""
    best_by_bucket = {}
    all_ranked = []
    for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
        pts = [cand_lists[i][j][0] for i, j in enumerate(idxs)]
        scores = np.asarray([cand_lists[i][j][1] for i, j in enumerate(idxs)], float)
        P = np.asarray(pts, np.float32)
        ys = P[:, 1]
        if not np.array_equal(np.argsort(ys), initial_order):
            continue
        gaps = np.diff(ys[initial_order])
        if np.any(gaps <= 4.0):
            continue
        if (np.any(P[:, 0] < 8) or np.any(P[:, 0] > width - 8) or
                np.any(P[:, 1] < 8) or np.any(P[:, 1] > height - 8)):
            continue
        duplicate = False
        for a in range(6):
            for b in range(a + 1, 6):
                if np.linalg.norm(P[a] - P[b]) < 20.0:
                    duplicate = True
                    break
            if duplicate:
                break
        if duplicate:
            continue

        motion_term = 0.0
        ok = True
        for i in range(6):
            sign = float(dir_sign[i])
            if sign == 0.0:
                continue
            progress = sign * float(P[i, 0] - initial_x[i])
            if progress < -float(reverse_cap):
                ok = False
                break
            if progress < 0.0:
                motion_term -= 0.055 * min(-progress, float(reverse_cap))
        if not ok:
            continue

        appearance = float(np.sum(4.0 * scores))
        weak_penalty = float(np.sum(np.maximum(0.0, 0.62 - scores))) * 1.25
        local_score = appearance + motion_term - weak_penalty
        state = {
            'centers': P,
            'ncc': scores,
            'local_score': local_score,
            'min_sep': float(np.min(gaps)),
        }
        all_ranked.append(state)

        # Bucket on each boat's x progress from the immutable slit seed.  This
        # is result-blind and does not prefer a direction or a boat number; it
        # only prevents many near-identical appearance maxima from consuming
        # the entire pre-DP state budget.
        sig = tuple(int(np.floor(float(P[i, 0] - initial_x[i]) / _BUCKET_PX + 0.5))
                    for i in range(6))
        old = best_by_bucket.get(sig)
        if old is None or local_score > old['local_score']:
            best_by_bucket[sig] = state

    k = max(1, int(keep))
    diverse = sorted(best_by_bucket.values(), key=lambda s: s['local_score'], reverse=True)
    selected = diverse[:k]
    if len(selected) < k:
        all_ranked.sort(key=lambda s: s['local_score'], reverse=True)
        seen_ids = {id(s) for s in selected}
        for s in all_ranked:
            if id(s) in seen_ids:
                continue
            selected.append(s)
            if len(selected) >= k:
                break
    return selected


def _identity_hypothesis_distance(a, b):
    """Keep paths distinct if any boat carries a materially different identity."""
    per_boat = np.linalg.norm(a['centers'] - b['centers'], axis=1)
    return float(np.max(per_boat))


def _rewrite(path: Path):
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return
    obj['tracker_version'] = 'v18'
    method = str(obj.get('method') or '')
    obj['method'] = method.replace('v17', 'v18') + ' + hypothesis-diverse state retention'
    obj['v18_changes'] = {
        'parent': 'v17',
        'state_retention': 'best-per-32px six-boat x-progress bucket, then local-score fill',
        'beam_dedup_distance': 'max per-boat center displacement (not six-boat mean)',
        'quality_thresholds_relaxed': False,
        'geometry_or_motion_gates_relaxed': False,
        'result_blind': True,
    }
    if isinstance(obj.get('boats'), dict):
        for rec in obj['boats'].values():
            if 'ses_v17' in rec:
                rec['ses_v18'] = rec.pop('ses_v17')
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    out = Path('exhibition_tracking_v18.json')
    if '--out' in sys.argv:
        try:
            out = Path(sys.argv[sys.argv.index('--out') + 1])
        except Exception:
            pass
    else:
        sys.argv.extend(['--out', str(out)])

    v17._frame_fleet_states = _diverse_frame_fleet_states
    v17._state_distance = _identity_hypothesis_distance
    code = 0
    try:
        v17.main()
    except SystemExit as exc:
        code = int(exc.code or 0)
    finally:
        _rewrite(out)
    if code:
        raise SystemExit(code)


if __name__ == '__main__':
    main()
