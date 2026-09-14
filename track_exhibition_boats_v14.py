#!/usr/bin/env python3
"""Result-blind diversified-candidate directional beam tracker for exhibition SES.

v14 keeps v13's multi-hypothesis six-boat beam, unchanged hard geometry gates,
NCC confidence thresholds, fallback caps, immutable anchor/adaptive appearance,
and slit-motion fail-closed corridor.  It addresses a specific v13 failure mode:
all surviving paths can inherit the same bad single-frame prediction because
candidate generation is centered on only one x prediction per boat.

Without relaxing any confidence threshold, v14 searches the same local NCC model
around several bounded horizontal anchors derived from the v13 prediction, then
keeps distinct candidates.  It also asks v13 for a larger transition pool and
reranks that pool with a soft, result-blind preference for motion consistent with
the immutable slit direction.  Hard v13 direction/geometry gates still decide
feasibility; the soft prior only preserves plausible alternatives in the beam.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v13 as v13
import track_exhibition_boats_v9 as v9

_ORIG_DUAL = v9.dual_candidates
_ORIG_FEASIBLE = v13._feasible_combos


def _diverse_dual_candidates(cur_g, adaptive_t, anchor_t, pred, ylo, yhi,
                             search_x, search_y, topk):
    """Generate distinct appearance candidates from bounded x-shifted anchors.

    Each individual search uses the unchanged v9 matching logic and thresholds.
    The extra anchors expand hypothesis coverage; they do not lower NCC gates.
    """
    pred = np.asarray(pred, dtype=np.float32)
    sx = float(search_x)
    shifts = (0.0, -0.50 * sx, 0.50 * sx)
    pool = []
    per_anchor = max(1, int(topk))
    for dx in shifts:
        p = pred.copy()
        p[0] += float(dx)
        for est, ad, an, src in _ORIG_DUAL(
                cur_g, adaptive_t, anchor_t, p, ylo, yhi,
                search_x, search_y, per_anchor):
            est = np.asarray(est, dtype=np.float32)
            identity = max(float(ad), float(an))
            pool.append((identity, est, float(ad), float(an), src))

    pool.sort(key=lambda z: z[0], reverse=True)
    kept = []
    limit = max(3, 2 * int(topk))
    for _identity, est, ad, an, src in pool:
        if any(float(np.linalg.norm(est - k[0])) < 12.0 for k in kept):
            continue
        kept.append((est, ad, an, src))
        if len(kept) >= limit:
            break
    return kept


def _directional_feasible(cand_lists, centers, preds, cells, fleet, advance,
                          min_ncc, dir_sign, initial_x, reverse_cap,
                          step_reverse_cap, step_hist, initial_order,
                          width, height, per_state_keep):
    """Keep v13 hard feasibility, but preserve direction-consistent alternatives."""
    expanded_keep = max(18, int(per_state_keep) * 4)
    ranked = _ORIG_FEASIBLE(
        cand_lists, centers, preds, cells, fleet, advance, min_ncc,
        dir_sign, initial_x, reverse_cap, step_reverse_cap, step_hist,
        initial_order, width, height, expanded_keep)
    if not ranked:
        return ranked

    adv = max(1, int(advance))
    rescored = []
    for row in ranked:
        local_score, idxs, P, step_vecs, frame_id, frame_an, frame_ad, gaps = row
        bonus = 0.0
        for i in range(6):
            sign = float(dir_sign[i])
            if sign == 0.0:
                continue
            cumulative = sign * float(P[i, 0] - initial_x[i])
            step_dir = sign * float(step_vecs[i][0])
            bonus += 0.006 * float(np.clip(cumulative, -reverse_cap, reverse_cap))
            bonus += 0.012 * float(np.clip(
                step_dir, -step_reverse_cap * adv, step_reverse_cap * adv))
        rescored.append((float(local_score) + bonus, row))

    rescored.sort(key=lambda z: z[0], reverse=True)
    out = []
    for new_score, row in rescored[:max(1, int(per_state_keep))]:
        out.append((new_score,) + row[1:])
    return out


def _patch_output(path: Path) -> None:
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return
    obj['method'] = 'v14 result-blind diversified-candidate directional beam tracker'
    obj['tracker_version'] = 'v14'
    obj['v14_changes'] = {
        'candidate_anchors': 'center plus +/-0.50 search_x; unchanged v9 matcher/NCC gates',
        'max_distinct_appearance_candidates_per_boat': 4,
        'transition_pool_before_direction_rerank': 'max(18, per_state_keep*4)',
        'hard_gates': 'unchanged from v13',
        'result_blind': True,
    }
    boats = obj.get('boats') or {}
    for b in boats.values():
        if 'ses_v13' in b and 'ses_v14' not in b:
            b['ses_v14'] = b.pop('ses_v13')
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    v9.dual_candidates = _diverse_dual_candidates
    v13._feasible_combos = _directional_feasible
    out = Path('exhibition_tracking_v14.json')
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
