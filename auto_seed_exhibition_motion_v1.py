#!/usr/bin/env python3
"""Automatically find six moving boats in a short start-exhibition clip.

Result-blind/live helper. It does not identify boat colours. Instead it detects six
motion rows and maps top-to-bottom rows to the supplied exhibition entry order,
which should come from pre-race/beforeinfo data.

The selected time is an approximate slit anchor near --nominal-sec. This is a
first live-operability step; exact start-line crossing detection remains separate.
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
    _, labels, centers = cv2.kmeans(ys, k, None, criteria, 8, cv2.KMEANS_PP_CENTERS)
    order = np.argsort(centers[:, 0])
    groups = []
    for idx in order:
        p = points[labels[:, 0] == idx]
        if len(p) < 5:
            return None
        groups.append(p)
    cy = np.array([np.median(g[:, 1]) for g in groups], float)
    if np.min(np.diff(cy)) < 18:
        return None
    return groups


def detect_at(cap, sec: float, dt: float = 0.10):
    a = read_frame(cap, sec)
    b = read_frame(cap, sec + dt)
    if a is None or b is None:
        return None
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    h, w = ga.shape

    mask = np.zeros_like(ga)
    mask[int(h * .12):int(h * .92), int(w * .12):int(w * .94)] = 255
    p0 = cv2.goodFeaturesToTrack(ga, maxCorners=900, qualityLevel=.01,
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
    good = (st[:, 0] == 1) & (stb[:, 0] == 1) & np.isfinite(fb) & (fb < 1.5) & (mag > 0.8) & (mag < 18)
    pts = p0v[good]
    d = d[good]
    if len(pts) < 35:
        return None

    horiz = np.abs(d[:, 0]) >= np.abs(d[:, 1]) * 0.7
    pts = pts[horiz]
    if len(pts) < 30:
        return None

    groups = cluster_rows(pts, 6)
    if groups is None:
        return None

    centers = []
    counts = []
    for g in groups:
        cx = float(np.percentile(g[:, 0], 65))
        cy = float(np.median(g[:, 1]))
        centers.append([cx, cy])
        counts.append(int(len(g)))

    cy = np.array([c[1] for c in centers])
    spacing = np.diff(cy)
    score = float(sum(min(c, 30) for c in counts) + 0.6 * np.min(spacing) + 0.03 * (cy[-1] - cy[0]))
    return {"sec": sec, "centers": centers, "counts": counts, "score": score,
            "frame_width": w, "frame_height": h}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--entry-order", required=True,
                    help="top-to-bottom exhibition order, e.g. 1,2,4,5,6,3")
    ap.add_argument("--nominal-sec", type=float, default=29.0,
                    help="expected slit time within the short clip")
    ap.add_argument("--scan-radius", type=float, default=4.0)
    ap.add_argument("--scan-step", type=float, default=.25)
    ap.add_argument("--out", type=Path, default=Path("auto_seed_meta.json"))
    ap.add_argument("--seed-out", type=Path, default=Path("auto_seeds.json"),
                    help="tracker-ready JSON containing only boat keys 1..6")
    args = ap.parse_args()

    entry = [int(x) for x in args.entry_order.split(',')]
    if sorted(entry) != [1, 2, 3, 4, 5, 6]:
        raise SystemExit("--entry-order must contain boat numbers 1..6 exactly once")

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit("cannot open video")
    candidates = []
    lo = args.nominal_sec - args.scan_radius
    hi = args.nominal_sec + args.scan_radius
    t = lo
    while t <= hi + 1e-9:
        r = detect_at(cap, t)
        if r:
            r["selection_score"] = r["score"] - 2.5 * abs(t - args.nominal_sec)
            candidates.append(r)
        t += args.scan_step
    cap.release()
    if not candidates:
        raise SystemExit("FAIL_CLOSED: no stable six-row motion detection")

    best = max(candidates, key=lambda x: x["selection_score"])
    seeds = {}
    for boat, (cx, cy) in zip(entry, best["centers"]):
        seeds[str(boat)] = [round(cx, 2), round(cy, 2)]

    payload = {
        "video": str(args.video),
        "result_blind": True,
        "race_results_read": False,
        "method": "sparse LK motion rows + supplied pre-race exhibition entry order",
        "entry_order": entry,
        "nominal_sec": args.nominal_sec,
        "selected_sec": round(float(best["sec"]), 3),
        "frame_size": [best["frame_width"], best["frame_height"]],
        "row_feature_counts": best["counts"],
        "seeds": seeds,
        "candidate_count": len(candidates),
        "warning": "selected_sec is an approximate slit anchor; exact start-line detector not yet validated",
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.seed_out.write_text(json.dumps(seeds, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
