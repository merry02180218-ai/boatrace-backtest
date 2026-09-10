#!/usr/bin/env python3
"""Analyze BOATCAST start-exhibition video for relative slit extension.

This is an experimental, result-blind feature extractor. It intentionally writes
only pre-race video-derived measurements. Race results must be joined later by a
separate step to avoid leakage.

Current v0 workflow:
  1. Read a local MP4 captured from the official exhibition replay.
  2. Sample frames around a user/algorithm supplied slit timestamp.
  3. Write frame images and a CSV template for six-boat x-position tracking.
  4. From tracked x positions, compute relative post-slit gain and SES rank.

Automatic boat detection will be added after representative Japanese-region MP4
samples are available; until then this scaffold keeps the measurement definition
fixed and reproducible.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np

OFFSETS = (0.0, 0.5, 1.0, 1.5)


def sample_frames(video: Path, slit_sec: float, out_dir: Path):
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise SystemExit(f"cannot open video: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    for off in OFFSETS:
        t = max(0.0, slit_sec + off)
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok:
            raise SystemExit(f"cannot read frame at {t:.3f}s")
        p = out_dir / f"slit_{off:+.1f}s.jpg"
        cv2.imwrite(str(p), frame)
        frames[str(off)] = {"time_sec": t, "path": str(p), "width": int(frame.shape[1]), "height": int(frame.shape[0])}
    cap.release()
    return fps, frames


def write_tracking_template(path: Path):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["boat", *[f"x_{off:.1f}" for off in OFFSETS]])
        for boat in range(1, 7):
            w.writerow([boat, "", "", "", ""])


def load_tracking(path: Path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            xs = [float(r[f"x_{off:.1f}"]) for off in OFFSETS]
            rows.append((int(r["boat"]), xs))
    if len(rows) != 6:
        raise ValueError("tracking CSV must contain six boats")
    return rows


def compute(rows):
    # Camera pan affects all boats similarly. Subtract fleet median displacement
    # at each horizon so the feature captures RELATIVE extension, not camera motion.
    x0 = np.array([xs[0] for _, xs in rows], dtype=float)
    result = []
    gains_by_h = {}
    for hi, off in enumerate(OFFSETS[1:], start=1):
        raw = np.array([xs[hi] for _, xs in rows], dtype=float) - x0
        rel = raw - np.median(raw)
        gains_by_h[off] = rel
    final = gains_by_h[1.5]
    # Higher x is assumed to be forward direction. Flip source coordinates before
    # filling the CSV if a venue/camera uses the opposite orientation.
    order = np.argsort(-final)
    ranks = np.empty(6, dtype=int); ranks[order] = np.arange(1, 7)
    # v0 SES: centered final relative gain normalized robustly by fleet MAD.
    med = np.median(final)
    mad = np.median(np.abs(final - med))
    scale = max(1.0, 1.4826 * mad)
    z = (final - med) / scale
    ses = np.clip(np.rint(z), -3, 3).astype(int)
    for i, (boat, xs) in enumerate(rows):
        result.append({
            "boat": boat,
            "x_slit": xs[0],
            "rel_gain_0_5px": round(float(gains_by_h[0.5][i]), 3),
            "rel_gain_1_0px": round(float(gains_by_h[1.0][i]), 3),
            "rel_gain_1_5px": round(float(final[i]), 3),
            "stretch_rank": int(ranks[i]),
            "ses_v0": int(ses[i]),
        })
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--slit-sec", type=float, required=True)
    ap.add_argument("--out-dir", type=Path, default=Path("exhibition_slit_frames"))
    ap.add_argument("--tracking-csv", type=Path, default=Path("exhibition_tracking.csv"))
    ap.add_argument("--result-json", type=Path, default=Path("exhibition_ses.json"))
    ap.add_argument("--compute", action="store_true", help="compute SES from a completed tracking CSV")
    args = ap.parse_args()

    fps, frames = sample_frames(args.video, args.slit_sec, args.out_dir)
    if not args.tracking_csv.exists():
        write_tracking_template(args.tracking_csv)
    payload = {
        "video": str(args.video), "slit_sec": args.slit_sec, "fps": fps,
        "offsets_sec": OFFSETS, "frames": frames,
        "leakage_guard": "PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER",
    }
    if args.compute:
        payload["boats"] = compute(load_tracking(args.tracking_csv))
    args.result_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
