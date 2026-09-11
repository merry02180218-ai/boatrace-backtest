#!/usr/bin/env python3
"""Result-blind calibration helper for start-exhibition slit-anchor timing.

Runs auto-seed v3 and tracker v5 over a small set of candidate slit times within
an already downloaded short exhibition clip, then ranks candidates only by
tracking quality. It never reads race results.

This is for exposed/historical calibration races, not for changing a locked blind
sample after the result is known.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--entry-order', required=True)
    ap.add_argument('--times', default='28.0,28.25,28.5,28.75,29.0,29.25,29.5')
    ap.add_argument('--out', type=Path, default=Path('ses_anchor_sweep_v1.json'))
    args = ap.parse_args()

    root = Path(__file__).resolve().parent
    times = [float(x) for x in args.times.split(',') if x.strip()]
    rows = []

    for t in times:
        tag = str(t).replace('.', '_')
        sm = Path(f'_sweep_seed_meta_{tag}.json')
        sj = Path(f'_sweep_seeds_{tag}.json')
        tj = Path(f'_sweep_track_{tag}.json')

        rc, so, se = run([
            sys.executable, str(root / 'auto_seed_exhibition_motion_v3.py'), str(args.video),
            '--entry-order', args.entry_order,
            '--nominal-sec', str(t), '--scan-radius', '0', '--scan-step', '0.25',
            '--out', str(sm), '--seed-out', str(sj),
        ])
        rec = {'candidate_sec': t, 'seed_ok': rc == 0, 'result_blind': True, 'race_results_read': False}
        if rc != 0:
            rec['seed_error'] = (se or so).strip()[-500:]
            rows.append(rec)
            continue

        seed_meta = json.loads(sm.read_text(encoding='utf-8'))
        rec['selected_sec'] = seed_meta.get('selected_sec')
        rec['seeds'] = seed_meta.get('seeds')

        rc2, so2, se2 = run([
            sys.executable, str(root / 'track_exhibition_boats_v5.py'), str(args.video),
            '--slit-sec', str(seed_meta['selected_sec']), '--seed-json', str(sj),
            '--out', str(tj), '--stride', '2',
        ])
        rec['track_process_ok'] = rc2 == 0
        if not tj.exists():
            rec['track_error'] = (se2 or so2).strip()[-500:]
            rows.append(rec)
            continue

        tr = json.loads(tj.read_text(encoding='utf-8'))
        rec['accepted'] = bool(tr.get('accepted'))
        rec['quality_tier'] = tr.get('quality_tier', {})
        rec['fallback_fraction'] = tr.get('fallback_fraction', {})
        rec['median_template_ncc'] = tr.get('median_template_ncc', {})
        rec['low_count'] = sum(1 for q in tr.get('quality_tier', {}).values() if q == 'LOW')
        rec['fallback_sum'] = round(sum(float(v) for v in tr.get('fallback_fraction', {}).values()), 3)
        rows.append(rec)

    viable = [r for r in rows if r.get('track_process_ok')]
    best = None
    if viable:
        best = min(viable, key=lambda r: (
            r.get('low_count', 99),
            r.get('fallback_sum', 999.0),
            abs(float(r.get('selected_sec', r['candidate_sec'])) - 29.0),
        ))

    payload = {
        'result_blind': True,
        'race_results_read': False,
        'method': 'fixed-time v3 auto-seed + v5 tracker quality sweep',
        'video': str(args.video),
        'entry_order': [int(x) for x in args.entry_order.split(',')],
        'candidates': rows,
        'best_tracking_quality_candidate': best,
        'warning': 'Calibration helper only; do not tune a blind-locked race after reading its result.',
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
