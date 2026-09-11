#!/usr/bin/env python3
"""Low-latency six-boat auto seeding that targets the moving hull, not the wake.

Result-blind/live helper.

Why v2 exists:
- v1 clustered all moving features by screen row and used the 65th x percentile.
- In BOATCAST start-exhibition footage the boats normally move strongly leftward,
  so that percentile can land in the trailing wake, especially for the upper rows.
- v2 estimates motion direction per row, keeps coherent/fast horizontal features,
  then anchors near the *leading* side of the coherent feature cloud.

The supplied entry order is pre-race information only. No result endpoint is read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def read_frame(cap, sec: float):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000.0)
    ok, fr = cap.read()
    return fr if ok else None


def cluster_rows(points: np.ndarray, k: int = 6):
    ys = points[:, 1].astype(np.float32).reshape(-1, 1)
    if len(ys) < 6 * 5:
        return None
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
    _, labels, centers = cv2.kmeans(ys, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    order = np.argsort(centers[:, 0])
    groups = []
    for idx in order:
        ii = np.flatnonzero(labels[:, 0] == idx)
        if len(ii) < 5:
            return None
        groups.append(ii)
    cy = np.array([np.median(points[ii, 1]) for ii in groups], float)
    if np.min(np.diff(cy)) < 18:
        return None
    return groups


def robust_seed_for_row(points: np.ndarray, motion: np.ndarray, idx: np.ndarray):
    p = points[idx]
    d = motion[idx]
    dx = d[:, 0]
    med_dx = float(np.median(dx))
    direction = -1.0 if med_dx < 0 else 1.0

    # Keep features that move in the row's dominant horizontal direction and are
    # not merely near-static wake/water texture. Use a relative threshold so it
    # remains usable across camera pans and different racecourses.
    same = (dx * direction) > 0
    speed = np.abs(dx)
    speed_ref = float(np.median(speed[same])) if np.any(same) else 0.0
    coherent = same & (speed >= max(0.7, speed_ref * 0.60))
    if np.sum(coherent) < 4:
        coherent = same
    if np.sum(coherent) < 4:
        coherent = np.ones(len(p), dtype=bool)

    q = p[coherent]
    qd = d[coherent]
    # Boat body is at the leading side of the cloud; wake trails behind it.
    # 30th percentile for leftward motion / 70th for rightward motion is less
    # brittle than the absolute extreme while moving well off the wake centroid.
    lead_q = 30.0 if direction < 0 else 70.0
    lead_x = float(np.percentile(q[:, 0], lead_q))

    # Refine around a compact band near the lead anchor. This tends to select the
    # hull/cowling features rather than a single bow pixel or distant spray.
    band = np.abs(q[:, 0] - lead_x) <= 38.0
    if np.sum(band) >= 3:
        qb = q[band]
        qdb = qd[band]
    else:
        qb = q
        qdb = qd

    cx = float(np.median(qb[:, 0]))
    cy = float(np.median(qb[:, 1]))
    med_row_dx = float(np.median(qdb[:, 0]))
    spread_x = float(np.median(np.abs(qb[:, 0] - cx))) if len(qb) else 999.0
    spread_y = float(np.median(np.abs(qb[:, 1] - cy))) if len(qb) else 999.0
    return {
        'center': [cx, cy],
        'dominant_dx': med_dx,
        'refined_dx': med_row_dx,
        'direction': 'left' if direction < 0 else 'right',
        'raw_count': int(len(p)),
        'coherent_count': int(np.sum(coherent)),
        'body_band_count': int(len(qb)),
        'spread_x': spread_x,
        'spread_y': spread_y,
    }


def detect_at(cap, sec: float, dt: float = 0.10):
    a = read_frame(cap, sec)
    b = read_frame(cap, sec + dt)
    if a is None or b is None:
        return None
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    h, w = ga.shape

    mask = np.zeros_like(ga)
    mask[int(h * .12):int(h * .92), int(w * .08):int(w * .96)] = 255
    p0 = cv2.goodFeaturesToTrack(ga, maxCorners=1100, qualityLevel=.008,
                                 minDistance=4, mask=mask, blockSize=5)
    if p0 is None or len(p0) < 40:
        return None
    kw = dict(winSize=(25, 25), maxLevel=3,
              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))
    p1, st, _ = cv2.calcOpticalFlowPyrLK(ga, gb, p0, None, **kw)
    pb, stb, _ = cv2.calcOpticalFlowPyrLK(gb, ga, p1, None, **kw)
    p0v = p0.reshape(-1, 2)
    p1v = p1.reshape(-1, 2)
    fb = np.linalg.norm(pb.reshape(-1, 2) - p0v, axis=1)
    d = p1v - p0v
    mag = np.linalg.norm(d, axis=1)
    good = ((st[:, 0] == 1) & (stb[:, 0] == 1) & np.isfinite(fb) &
            (fb < 1.6) & (mag > 0.8) & (mag < 20))
    pts = p0v[good]
    d = d[good]
    if len(pts) < 35:
        return None

    horiz = np.abs(d[:, 0]) >= np.abs(d[:, 1]) * 0.75
    pts = pts[horiz]
    d = d[horiz]
    if len(pts) < 30:
        return None

    groups = cluster_rows(pts, 6)
    if groups is None:
        return None

    rows = [robust_seed_for_row(pts, d, ii) for ii in groups]
    centers = [r['center'] for r in rows]
    cy = np.array([c[1] for c in centers])
    if np.min(np.diff(cy)) < 18:
        return None

    dirs = [r['direction'] for r in rows]
    majority = max(set(dirs), key=dirs.count)
    direction_agree = sum(x == majority for x in dirs)
    if direction_agree < 5:
        return None

    # Prefer times with six coherent, compact hull candidates close to nominal.
    coherent_sum = sum(min(r['coherent_count'], 30) for r in rows)
    body_sum = sum(min(r['body_band_count'], 14) for r in rows)
    compact_penalty = sum(max(0.0, r['spread_x'] - 20.0) for r in rows)
    spacing_bonus = 0.5 * float(np.min(np.diff(cy)))
    score = float(coherent_sum + 0.8 * body_sum + spacing_bonus - 0.7 * compact_penalty)
    return {
        'sec': sec, 'centers': centers, 'rows': rows, 'score': score,
        'frame_width': w, 'frame_height': h, 'majority_direction': majority,
        'direction_agree': direction_agree,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--entry-order', required=True,
                    help='top-to-bottom exhibition order, e.g. 1,2,4,5,6,3')
    ap.add_argument('--nominal-sec', type=float, default=29.0)
    ap.add_argument('--scan-radius', type=float, default=4.0)
    ap.add_argument('--scan-step', type=float, default=.25)
    ap.add_argument('--out', type=Path, default=Path('auto_seed_meta_v2.json'))
    ap.add_argument('--seed-out', type=Path, default=Path('auto_seeds_v2.json'))
    args = ap.parse_args()

    entry = [int(x) for x in args.entry_order.split(',')]
    if sorted(entry) != [1, 2, 3, 4, 5, 6]:
        raise SystemExit('--entry-order must contain boat numbers 1..6 exactly once')

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit('cannot open video')
    candidates = []
    t = args.nominal_sec - args.scan_radius
    hi = args.nominal_sec + args.scan_radius
    while t <= hi + 1e-9:
        r = detect_at(cap, t)
        if r:
            r['selection_score'] = r['score'] - 2.5 * abs(t - args.nominal_sec)
            candidates.append(r)
        t += args.scan_step
    cap.release()
    if not candidates:
        raise SystemExit('FAIL_CLOSED: no stable six-row hull-oriented detection')

    best = max(candidates, key=lambda x: x['selection_score'])
    seeds = {}
    row_details = {}
    for boat, row in zip(entry, best['rows']):
        cx, cy = row['center']
        seeds[str(boat)] = [round(cx, 2), round(cy, 2)]
        row_details[str(boat)] = {k: (round(v, 3) if isinstance(v, float) else v)
                                  for k, v in row.items() if k != 'center'}

    payload = {
        'video': str(args.video),
        'result_blind': True,
        'race_results_read': False,
        'method': 'LK motion rows + direction-aware coherent leading-hull anchor',
        'entry_order': entry,
        'nominal_sec': args.nominal_sec,
        'selected_sec': round(float(best['sec']), 3),
        'frame_size': [best['frame_width'], best['frame_height']],
        'majority_motion_direction': best['majority_direction'],
        'direction_agree_rows': best['direction_agree'],
        'seeds': seeds,
        'row_details': row_details,
        'candidate_count': len(candidates),
        'warning': 'selected_sec remains an approximate slit anchor; exact start-line detector is separate',
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
