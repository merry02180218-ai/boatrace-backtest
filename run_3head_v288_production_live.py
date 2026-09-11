#!/usr/bin/env python3
"""Fail-closed production wrapper around the audited 3-head v288 LIVE scorer.

Adds only operational guards: target/cache date parity, September-2026 scope, and
purchase-deadline date parity.  After validation it delegates unchanged scoring to
run_20260911_3head_v288_live.py.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import joblib

JST = timezone(timedelta(hours=9))


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
    if z.get('target_result_or_payout_used') is not False:
        raise RuntimeError('cache result/payout leakage guard failed')

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
