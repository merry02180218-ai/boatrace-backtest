#!/usr/bin/env python3
"""Geometry-aware result-blind auto seeding for exhibition SES.

v7 keeps v3's permissive six-row LK detector, but changes two decisions that
proved fragile in v6:
1) candidate time selection explicitly rewards safe vertical lane separation;
2) extreme-motion correction is only applied to isolated extreme rows. Adjacent
   extreme rows are treated as ambiguous and left unshifted rather than forcing
   multiple saturated corrections into uncertain geometry.

No race-result or outcome data is read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

import auto_seed_exhibition_motion_v3 as v3


def spacing_metrics(rows):
    cy = np.array([float(r['center'][1]) for r in rows], dtype=float)
    gaps = np.diff(cy)
    return gaps, float(np.min(gaps)), float(np.median(gaps))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--entry-order', required=True)
    ap.add_argument('--nominal-sec', type=float, default=29.0)
    ap.add_argument('--scan-radius', type=float, default=4.0)
    ap.add_argument('--scan-step', type=float, default=.25)
    ap.add_argument('--extreme-ratio', type=float, default=1.5)
    ap.add_argument('--max-shift', type=float, default=120.0)
    ap.add_argument('--preferred-min-gap', type=float, default=30.0,
                    help='preferred minimum vertical seed gap in native pixels')
    ap.add_argument('--hard-min-gap', type=float, default=22.0,
                    help='reject candidate times below this vertical gap')
    ap.add_argument('--out', type=Path, default=Path('auto_seed_meta_v7.json'))
    ap.add_argument('--seed-out', type=Path, default=Path('auto_seeds_v7.json'))
    args = ap.parse_args()

    entry = [int(x) for x in args.entry_order.split(',')]
    if sorted(entry) != [1, 2, 3, 4, 5, 6]:
        raise SystemExit('--entry-order must contain 1..6 exactly once')

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit('cannot open video')

    cand = []
    t = args.nominal_sec - args.scan_radius
    hi = args.nominal_sec + args.scan_radius
    while t <= hi + 1e-9:
        r = v3.detect_at(cap, t)
        if r:
            gaps, min_gap, med_gap = spacing_metrics(r['rows'])
            # v3 already enforces >=18 px. v7 is stricter because tracker v5
            # later requires distinct lane identities. Prefer >=30 px, reject
            # clearly collapsed six-row geometry below 22 px.
            if min_gap >= args.hard_min_gap:
                spacing_bonus = 2.5 * min(min_gap, 42.0)
                narrow_penalty = 6.0 * max(0.0, args.preferred_min_gap - min_gap)
                time_penalty = 2.0 * abs(t - args.nominal_sec)
                r['selection_score_v7'] = r['score'] + spacing_bonus - narrow_penalty - time_penalty
                r['min_gap'] = min_gap
                r['median_gap'] = med_gap
                r['gaps'] = gaps.tolist()
                cand.append(r)
        t += args.scan_step
    cap.release()

    if not cand:
        raise SystemExit('FAIL_CLOSED: no six-row candidate with safe seed geometry')

    best = max(cand, key=lambda x: x['selection_score_v7'])
    abs_dx = np.array([abs(float(r['dominant_dx'])) for r in best['rows']], dtype=float)
    med_abs_dx = float(np.median(abs_dx))
    threshold = args.extreme_ratio * med_abs_dx
    extreme = [bool(med_abs_dx > 0 and x >= threshold) for x in abs_dx]

    # Adjacent extreme rows are ambiguous under camera pan/perspective. Do not
    # force saturated corrections for either member of an adjacent extreme pair.
    isolated = []
    for i, flag in enumerate(extreme):
        adj = (i > 0 and extreme[i-1]) or (i + 1 < len(extreme) and extreme[i+1])
        isolated.append(bool(flag and not adj))

    seeds = {}
    details = {}
    corrected = 0
    suppressed_ambiguous = 0
    for idx, (boat, row) in enumerate(zip(entry, best['rows'])):
        cx, cy = map(float, row['center'])
        dx = float(row['dominant_dx'])
        shift = 0.0
        if isolated[idx]:
            shift = float(np.sign(dx) * args.max_shift)
            cx += shift
            corrected += 1
        elif extreme[idx]:
            suppressed_ambiguous += 1

        seeds[str(boat)] = [round(cx, 2), round(cy, 2)]
        details[str(boat)] = {
            'motion_center': [round(float(row['center'][0]), 2), round(float(row['center'][1]), 2)],
            'dominant_dx': round(dx, 3),
            'abs_dx': round(abs(dx), 3),
            'fleet_median_abs_dx': round(med_abs_dx, 3),
            'extreme_threshold': round(threshold, 3),
            'extreme_motion': bool(extreme[idx]),
            'isolated_extreme': bool(isolated[idx]),
            'ambiguous_adjacent_extreme': bool(extreme[idx] and not isolated[idx]),
            'applied_shift_x': round(shift, 3),
            'final_seed': [round(cx, 2), round(cy, 2)],
            'direction': row['direction'],
            'coherent_count': int(row['coherent_count']),
            'spread_x': round(float(row['spread_x']), 3),
        }

    payload = {
        'video': str(args.video),
        'result_blind': True,
        'race_results_read': False,
        'method': 'v3 six-row LK + geometry-aware candidate selection + isolated-extreme correction',
        'entry_order': entry,
        'nominal_sec': args.nominal_sec,
        'selected_sec': round(float(best['sec']), 3),
        'frame_size': [best['frame_width'], best['frame_height']],
        'selected_min_gap': round(float(best['min_gap']), 3),
        'selected_median_gap': round(float(best['median_gap']), 3),
        'selected_gaps': [round(float(x), 3) for x in best['gaps']],
        'fleet_median_abs_dx': round(med_abs_dx, 3),
        'extreme_ratio': args.extreme_ratio,
        'extreme_threshold': round(threshold, 3),
        'max_shift': args.max_shift,
        'corrected_row_count': corrected,
        'suppressed_ambiguous_extreme_count': suppressed_ambiguous,
        'seeds': seeds,
        'row_details': details,
        'candidate_count': len(cand),
        'warning': 'EXPERIMENTAL result-blind seed v7; technical validation only until multi-race generalization.',
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
