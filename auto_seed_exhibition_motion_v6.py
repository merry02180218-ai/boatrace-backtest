#!/usr/bin/env python3
"""Saturated extreme-motion correction for exhibition SES auto seeding.

Starts from v3's permissive six-row LK detector. Only rows whose horizontal
motion magnitude is an extreme outlier versus the six-row fleet are corrected.
Unlike v5's proportional lag correction, v6 uses a deterministic bounded shift
to the configured maximum in the detected motion direction. This removes the
fragile near-cap behavior observed during result-blind technical calibration.

Result-blind: no race-result endpoint or outcome data is read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

import auto_seed_exhibition_motion_v3 as v3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--entry-order', required=True)
    ap.add_argument('--nominal-sec', type=float, default=29.0)
    ap.add_argument('--scan-radius', type=float, default=4.0)
    ap.add_argument('--scan-step', type=float, default=.25)
    ap.add_argument('--extreme-ratio', type=float, default=1.5,
                    help='abs(dx) / median(abs(dx)) threshold for correction')
    ap.add_argument('--max-shift', type=float, default=120.0)
    ap.add_argument('--out', type=Path, default=Path('auto_seed_meta_v6.json'))
    ap.add_argument('--seed-out', type=Path, default=Path('auto_seeds_v6.json'))
    args = ap.parse_args()

    entry = [int(x) for x in args.entry_order.split(',')]
    if sorted(entry) != [1,2,3,4,5,6]:
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
            r['selection_score'] = r['score'] - 2.0 * abs(t - args.nominal_sec)
            cand.append(r)
        t += args.scan_step
    cap.release()

    if not cand:
        raise SystemExit('FAIL_CLOSED: no stable six-row hybrid hull detection')

    best = max(cand, key=lambda x: x['selection_score'])
    abs_dx = np.array([abs(float(r['dominant_dx'])) for r in best['rows']], dtype=float)
    med_abs_dx = float(np.median(abs_dx))
    threshold = args.extreme_ratio * med_abs_dx

    seeds = {}
    details = {}
    corrected = 0
    for boat, row in zip(entry, best['rows']):
        cx, cy = map(float, row['center'])
        dx = float(row['dominant_dx'])
        is_extreme = med_abs_dx > 0 and abs(dx) >= threshold
        shift = 0.0
        if is_extreme:
            shift = float(np.sign(dx) * args.max_shift)
            cx += shift
            corrected += 1
        seeds[str(boat)] = [round(cx, 2), round(cy, 2)]
        details[str(boat)] = {
            'motion_center': [round(float(row['center'][0]), 2), round(float(row['center'][1]), 2)],
            'dominant_dx': round(dx, 3),
            'abs_dx': round(abs(dx), 3),
            'fleet_median_abs_dx': round(med_abs_dx, 3),
            'extreme_threshold': round(threshold, 3),
            'extreme_motion': bool(is_extreme),
            'saturated_shift_x': round(shift, 3),
            'final_seed': [round(cx, 2), round(cy, 2)],
            'direction': row['direction'],
            'coherent_count': int(row['coherent_count']),
            'spread_x': round(float(row['spread_x']), 3),
        }

    payload = {
        'video': str(args.video),
        'result_blind': True,
        'race_results_read': False,
        'method': 'v3 permissive six-row LK + fleet-relative extreme-motion saturated correction',
        'entry_order': entry,
        'nominal_sec': args.nominal_sec,
        'selected_sec': round(float(best['sec']), 3),
        'frame_size': [best['frame_width'], best['frame_height']],
        'fleet_median_abs_dx': round(med_abs_dx, 3),
        'extreme_ratio': args.extreme_ratio,
        'extreme_threshold': round(threshold, 3),
        'max_shift': args.max_shift,
        'corrected_row_count': corrected,
        'seeds': seeds,
        'row_details': details,
        'candidate_count': len(cand),
        'warning': 'EXPERIMENTAL result-blind seed v6; technical calibration only until multi-race validation.',
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
