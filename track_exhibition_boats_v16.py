#!/usr/bin/env python3
"""Result-blind motion-aware full-cell anchor-lattice beam tracker for SES.

v16 keeps v15 candidate generation and v13 hard safety/quality gates unchanged,
but fixes a remaining temporal-ranking weakness: high-NCC wake/background paths
can win early beam slots even when their short-horizon screen-x movement opposes
the immutable slit motion measured by seed v17. v16 re-ranks a broader feasible
transition pool with a soft trajectory likelihood using only result-blind slit
motion direction and immutable-anchor appearance. Hard reverse-direction gates,
NCC thresholds, fallback caps, geometry/order/edge gates and adaptive appearance
rules are not relaxed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import track_exhibition_boats_v13 as v13
import track_exhibition_boats_v15 as v15
import track_exhibition_boats_v9 as v9

_ORIG_FEASIBLE = v13._feasible_combos


def _motion_aware_feasible(cand_lists, centers, preds, cells, fleet, advance,
                           min_ncc, dir_sign, initial_x, reverse_cap,
                           step_reverse_cap, step_hist, initial_order, width,
                           height, per_state_keep):
    """Re-rank a broader unchanged-gate transition pool by trajectory evidence.

    The base v13 feasibility function still owns every hard gate. We simply ask
    it for a wider bounded pool, then add two result-blind soft likelihood terms:
    (1) signed step/cumulative progress relative to immutable slit direction and
    (2) immutable-anchor NCC support. This lets physically consistent hypotheses
    survive the beam before a wrong high-NCC wake path reaches a hard corridor.
    """
    pool_keep = max(32, int(per_state_keep) * 4)
    ranked = _ORIG_FEASIBLE(
        cand_lists, centers, preds, cells, fleet, advance, min_ncc,
        dir_sign, initial_x, reverse_cap, step_reverse_cap, step_hist,
        initial_order, width, height, pool_keep)

    rescored = []
    for item in ranked:
        local_score, idxs, P, step_vecs, frame_id, frame_an, frame_ad, gaps = item
        score = float(local_score)

        # Immutable slit-motion likelihood. Near-zero slit rows (dir_sign==0)
        # remain unconstrained. Forward motion receives a mild reward; reverse
        # motion is penalized earlier than, but does not replace, the hard gate.
        for i in range(6):
            sign = float(dir_sign[i])
            if sign == 0.0:
                continue
            signed_step = sign * float(step_vecs[i][0])
            signed_progress = sign * float(P[i, 0] - initial_x[i])
            if signed_step >= 0.0:
                score += 0.025 * min(signed_step, 36.0 * max(1, int(advance)))
            else:
                score -= 0.070 * min(-signed_step, 36.0 * max(1, int(advance)))
            if signed_progress < 0.0:
                score -= 0.020 * min(-signed_progress, float(reverse_cap))

        # Immutable appearance is independent of adaptive-template drift. Keep
        # all existing min-NCC gates unchanged, but prefer paths whose anchor
        # evidence remains healthy over time. Fallbacks are already penalized by
        # v13 and are not granted synthetic appearance credit here.
        for an in frame_an:
            if an is None:
                continue
            an = float(an)
            score += 0.60 * an
            if an < 0.62:
                score -= 1.50 * (0.62 - an)

        rescored.append((score, idxs, P, step_vecs, frame_id, frame_an, frame_ad, gaps))

    rescored.sort(key=lambda z: z[0], reverse=True)
    return rescored[:max(1, int(per_state_keep))]


def _patch_output(path: Path) -> None:
    if not path.exists():
        return
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return
    obj['method'] = 'v16 result-blind motion-aware full-cell anchor-lattice beam tracker'
    obj['tracker_version'] = 'v16'
    obj['v16_changes'] = {
        'candidate_lattice': 'unchanged v15 local + full-cell immutable-anchor peaks',
        'temporal_core': 'v13 multi-hypothesis six-boat beam',
        'transition_pool': 'unchanged hard gates, widened bounded pre-rerank pool only',
        'soft_motion_likelihood': 'signed step and cumulative progress vs immutable v17 slit direction',
        'soft_appearance_likelihood': 'immutable seed-anchor NCC support',
        'hard_gates': 'unchanged from v13',
        'ncc_and_fallback_thresholds': 'unchanged from v13',
        'result_blind': True,
    }
    boats = obj.get('boats') or {}
    for b in boats.values():
        if 'ses_v13' in b and 'ses_v16' not in b:
            b['ses_v16'] = b.pop('ses_v13')
        if 'ses_v15' in b and 'ses_v16' not in b:
            b['ses_v16'] = b.pop('ses_v15')
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    # v15 state-independent full-cell anchor lattice.
    v9.dual_candidates = v15._lattice_dual_candidates
    # v16 changes only transition ranking; base hard feasibility remains inside
    # _ORIG_FEASIBLE and is never bypassed.
    v13._feasible_combos = _motion_aware_feasible

    out = Path('exhibition_tracking_v16.json')
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
