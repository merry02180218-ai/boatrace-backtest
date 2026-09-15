#!/usr/bin/env python3
"""Run the exhibition SES pipeline directly on the Japan Windows host.

This deliberately avoids GitHub Actions queue/checkout latency. Intended to be
called by a local watcher/Task Scheduler process once a target race and its
pre-race exhibition entry order are known.

Pipeline:
1) fetch only the short BOATCAST start-exhibition clip
2) auto-detect six boat motion rows with seed v17
3) track 1.5 s with tracker v33 and compute SES
4) write one combined live result JSON

No race-result endpoint is accessed. The wrapper fails closed if v33 does not
accept the six-boat measurement.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def run(cmd, env=None):
    t0 = time.perf_counter()
    p = subprocess.run(cmd, env=env, text=True, capture_output=True)
    sec = time.perf_counter() - t0
    if p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(map(str, cmd))}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return sec, p.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='YYYYMMDD')
    ap.add_argument('--stadium', required=True, help='e.g. 01kiryu')
    ap.add_argument('--race', required=True, type=int)
    ap.add_argument('--entry-order', required=True, help='e.g. 1,2,4,5,6,3')
    ap.add_argument('--clip-start-sec', type=float, default=82.0)
    ap.add_argument('--clip-duration-sec', type=float, default=52.0)
    ap.add_argument('--nominal-slit-sec', type=float, default=29.0,
                    help='slit anchor within the short clip')
    ap.add_argument('--out-dir', type=Path, default=Path('live_exhibition_ses'))
    args = ap.parse_args()

    entry = [int(x) for x in args.entry_order.split(',')]
    if sorted(entry) != [1,2,3,4,5,6]:
        raise SystemExit('--entry-order must contain 1..6 exactly once')

    root = Path(__file__).resolve().parent
    outdir = args.out_dir / f"{args.date}_{args.stadium}_{args.race:02d}"
    outdir.mkdir(parents=True, exist_ok=True)
    video = outdir / f"boatcast_{args.date}_{args.stadium}_{args.race:02d}_startclip.mp4"
    clip_meta = video.with_suffix('.json')
    seed_meta = outdir / 'auto_seed_meta_v17.json'
    seed_json = outdir / 'auto_seeds_v17.json'
    track_json = outdir / 'exhibition_tracking_v33.json'
    final_json = outdir / 'live_exhibition_ses.json'

    env = os.environ.copy()
    env.update({
        'RACE_DATE': args.date,
        'STADIUM': args.stadium,
        'RACE': str(args.race),
        'CLIP_START_SEC': str(args.clip_start_sec),
        'CLIP_DURATION_SEC': str(args.clip_duration_sec),
        'VIDEO_OUT': str(video),
        'META_OUT': str(clip_meta),
    })

    t_all = time.perf_counter()
    fetch_sec, _ = run([sys.executable, str(root / 'download_boatcast_exhibition_fastclip.py')], env=env)

    seed_sec, _ = run([
        sys.executable, str(root / 'auto_seed_exhibition_motion_v17.py'), str(video),
        '--entry-order', args.entry_order,
        '--nominal-sec', str(args.nominal_slit_sec),
        '--out', str(seed_meta), '--seed-out', str(seed_json)
    ])
    sm = json.loads(seed_meta.read_text(encoding='utf-8'))
    slit = float(sm['selected_sec'])

    track_sec, _ = run([
        sys.executable, str(root / 'track_exhibition_boats_v33.py'), str(video),
        '--slit-sec', str(slit),
        '--seed-json', str(seed_json),
        '--seed-meta', str(seed_meta),
        '--out', str(track_json),
        '--stride', '2', '--topk', '6', '--per-boat-keep', '5',
        '--per-path-keep', '12', '--beam-width', '24', '--bank-cap', '5'
    ])
    tr = json.loads(track_json.read_text(encoding='utf-8'))
    if not tr.get('accepted'):
        raise SystemExit('FAIL_CLOSED: tracker v33 did not accept measurement')

    total = time.perf_counter() - t_all
    cm = json.loads(clip_meta.read_text(encoding='utf-8'))
    payload = {
        'race_date': args.date,
        'stadium': args.stadium,
        'race': args.race,
        'entry_order': entry,
        'result_blind': True,
        'race_results_read': False,
        'pipeline': {'seed': 'v17', 'tracker': 'v33'},
        'clip_start_sec': args.clip_start_sec,
        'selected_slit_sec_in_clip': slit,
        'timing_sec': {
            'fastclip_process': round(fetch_sec, 3),
            'auto_seed_process': round(seed_sec, 3),
            'ses_track_process': round(track_sec, 3),
            'pipeline_total': round(total, 3),
            'fastclip_internal': cm.get('timing_sec', {}),
        },
        'boats': tr.get('boats', {}),
        'accepted': True,
        'source_files': {
            'clip_meta': str(clip_meta),
            'seed_meta': str(seed_meta),
            'tracking': str(track_json),
        },
        'warning': 'LIVE research pipeline. v17+v33 passed the four-sample Kiryu technical matrix; broader September/venue validation is still required.',
    }
    final_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
