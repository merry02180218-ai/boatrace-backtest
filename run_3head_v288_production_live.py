#!/usr/bin/env python3
"""Fail-closed production wrapper around the audited 3-head v288 LIVE scorer.

Adds only operational guards: target/cache date parity, frozen September model
metadata, race bounds, and purchase-deadline date parity. After validation it
delegates unchanged scoring to run_20260911_3head_v288_live.py.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import joblib

JST = timezone(timedelta(hours=9))
EXPECTED_HISTORY_CUTOFF = '2026-08-31'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='YYYYMMDD')
    ap.add_argument('--jcd', type=int, required=True)
    ap.add_argument('--race', type=int, required=True)
    ap.add_argument('--cache', required=True)
    ap.add_argument('--deadline-jst', required=True)
    args = ap.parse_args()

    if not re.fullmatch(r'202609\d{2}', args.date):
        raise RuntimeError('production v288 wrapper is frozen to September 2026')
    if not 1 <= args.jcd <= 24:
        raise RuntimeError(f'invalid JCD: {args.jcd}')
    if not 1 <= args.race <= 12:
        raise RuntimeError(f'invalid race number: {args.race}')

    target = datetime.strptime(args.date, '%Y%m%d').date()
    deadline = datetime.fromisoformat(args.deadline_jst)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=JST)
    deadline = deadline.astimezone(JST)
    if deadline.date() != target:
        raise RuntimeError(f'deadline date mismatch: target={target} deadline={deadline.date()}')

    z = joblib.load(args.cache)
    cache_date = str(z.get('date', '')).replace('-', '')
    if cache_date != args.date:
        raise RuntimeError(f'cache date mismatch: cache={cache_date!r} target={args.date!r}')
    if z.get('history_cutoff') != EXPECTED_HISTORY_CUTOFF:
        raise RuntimeError(
            f'cache history cutoff mismatch: {z.get("history_cutoff")!r} != {EXPECTED_HISTORY_CUTOFF!r}'
        )
    if z.get('target_result_or_payout_used') is not False:
        raise RuntimeError('cache result/payout leakage guard failed')
    if z.get('operational_pre_training_quantile') is not True:
        raise RuntimeError('cache is not the training-quantile production PRE')
    if z.get('operational_pre_percentile_bridge') is not False:
        raise RuntimeError('legacy current-universe percentile bridge is prohibited in production')
    if 'pre_candidates' not in z or 'current_rows' not in z:
        raise RuntimeError('cache missing required production payload')

    cmd = [
        sys.executable,
        'run_20260911_3head_v288_live.py',
        '--date', args.date,
        '--jcd', str(args.jcd),
        '--race', str(args.race),
        '--cache', args.cache,
        '--deadline-jst', deadline.isoformat(),
    ]
    return subprocess.run(cmd, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
