#!/usr/bin/env python3
"""Detect the BOATCAST start-exhibition photo/grid from an exhibition MP4.

This helper is intentionally result-blind.  It scans the exhibition replay for the
broadcast's "スタート展示写真" scene, detects the regularly spaced yellow timing
grid, and writes a calibration image/JSON.  The grid is useful as an ST/perspective
anchor before estimating post-slit extension from moving frames.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def _merge_nearby(xs: list[float], tol: float = 5.0) -> list[float]:
    if not xs:
        return []
    out: list[list[float]] = [[xs[0]]]
    for x in xs[1:]:
        if x - out[-1][-1] <= tol:
            out[-1].append(x)
        else:
            out.append([x])
    return [sum(g) / len(g) for g in out]


def detect_grid(frame):
    h, _ = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    yellow = cv2.inRange(hsv, np.array([18, 100, 100]), np.array([42, 255, 255]))
    roi = yellow[int(h * 0.05): int(h * 0.92)]
    col = (roi > 0).sum(axis=0)
    raw = np.where(col > h * 0.18)[0]

    groups: list[list[int]] = []
    for x in raw:
        x = int(x)
        if not groups or x > groups[-1][-1] + 1:
            groups.append([x])
        else:
            groups[-1].append(x)
    centers = [sum(g) / len(g) for g in groups]
    centers = _merge_nearby(centers)

    if len(centers) < 6:
        return 0, []
    diffs = np.diff(centers)
    med = float(np.median(diffs))
    mad = float(np.median(np.abs(diffs - med)))
    regular = 20 < med < 300 and mad < max(4.0, med * 0.08)
    return (len(centers) if regular else 0), [round(x, 2) for x in centers]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("start_exhibition_calibration"))
    ap.add_argument("--scan-step", type=float, default=1.0)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit(f"cannot open video: {args.video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps

    best = (-1, None, None, [])
    t = 0.0
    while t < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok:
            break
        score, lines = detect_grid(frame)
        if score > best[0]:
            best = (score, t, frame.copy(), lines)
        t += args.scan_step
    cap.release()

    score, photo_sec, frame, lines = best
    if frame is None or score < 6:
        raise SystemExit("start exhibition grid photo not detected")

    diffs = np.diff(lines)
    spacing = float(np.median(diffs)) if len(diffs) else None
    photo_path = args.out_dir / "start_exhibition_photo.jpg"
    cv2.imwrite(str(photo_path), frame)
    payload = {
        "video": str(args.video),
        "fps": fps,
        "duration_sec": duration,
        "detected_photo_sec": photo_sec,
        "grid_line_count": score,
        "grid_x_px": lines,
        "median_grid_spacing_px": spacing,
        "leakage_guard": "PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER",
        "note": "Grid-photo anchor only. Use it to calibrate exhibition-ST/perspective before post-slit stretch.",
    }
    (args.out_dir / "calibration.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
