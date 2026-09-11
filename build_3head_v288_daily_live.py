#!/usr/bin/env python3
"""Generic September-2026 production builder for 3-head v288 PRE + LIVE cache.

The adopted v288 September model/threshold universe is frozen through 2026-08-31.
This wrapper changes only target-day plumbing: runtime date, current input paths,
and output paths.  The audited PRE scanner and cache builder remain the canonical
implementation and share one in-memory augmented frame for operational speed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import joblib
import pandas as pd

import scan_20260911_3head_v288_pre as pre
import build_20260911_3head_v288_live_cache as cache

FROZEN_FIRST = pd.Timestamp('2026-09-01')
FROZEN_NEXT = pd.Timestamp('2026-10-01')
HISTORY_CUTOFF = '2026-08-31'
BIAS_START = date(2026, 8, 1)


def resolve_date(arg: str | None) -> date:
    s = arg or os.environ.get('TARGET_DATE', '').strip()
    if not s:
        s = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d')
    day = datetime.strptime(s, '%Y-%m-%d').date()
    if not (date(2026, 9, 1) <= day <= date(2026, 9, 30)):
        raise RuntimeError('this frozen v288 daily builder is valid only for 2026-09-01..2026-09-30')
    return day


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date')
    args = ap.parse_args()
    day = resolve_date(args.date)
    day8 = day.strftime('%Y%m%d')
    inp = Path('current_input/v288') / day8
    cards_path = inp / 'race_cards.csv'
    waku_path = inp / 'waku10.csv'
    if not cards_path.exists() or not waku_path.exists():
        raise RuntimeError(f'missing current PRE inputs: {inp}')

    outdir = Path('live_outputs/v288') / day8
    outdir.mkdir(parents=True, exist_ok=True)
    pre_csv = outdir / 'pre_scan.csv'
    pre_md = outdir / 'pre_scan.md'
    cache_path = outdir / 'live_cache.joblib'

    # Runtime target-day plumbing.  Frozen September fit boundaries remain exact.
    pre.DAY = day
    pre.FIRST = FROZEN_FIRST
    pre.NEXT = FROZEN_NEXT
    pre.CUR_CARDS = cards_path
    pre.CUR_WAKU = waku_path
    pre.OUT = pre_csv
    pre.SUM = pre_md
    cache.OUT = cache_path

    # Preserve the audited current-base recipe but replace its date-specific literal.
    def make_current_base_for_target():
        cards = pre.bycode(pre.local_csv(pre.CUR_CARDS))
        waku = pre.bycode(pre.local_csv(pre.CUR_WAKU))
        bias = pre.learn_bias()
        out = []
        for code, card in cards.items():
            if code not in waku:
                continue
            z = pre.v108.feature_row(day.isoformat(), card, waku[code], {}, {}, {}, bias)
            if z is None:
                continue
            z.update({'winner': 0, 'valid_result': 0, 'actual_combo': '', 'valid_payout': 0, 'payout100': 0})
            for b in range(1, 7):
                for key in (f'艇{b}_選手名', f'艇{b}_選手登番'):
                    if key in card:
                        z[key] = card.get(key)
            out.append(z)
        if not out:
            raise RuntimeError(f'no current PRE rows built cards={len(cards)} waku={len(waku)}')
        return pd.DataFrame(out)

    original_current_base = pre.make_current_base
    original_bias = pre.learn_bias
    original_build = pre.build_augmented

    def target_bias(end=None, start=None):
        return original_bias(
            end=end or (day - timedelta(days=1)),
            start=start or BIAS_START,
        )

    pre.make_current_base = make_current_base_for_target
    pre.learn_bias = target_bias

    t0 = time.perf_counter()
    try:
        bundle = original_build()
        build_seconds = time.perf_counter() - t0
        pre.build_augmented = lambda: bundle

        t1 = time.perf_counter()
        pre.main()
        pre_seconds = time.perf_counter() - t1

        t2 = time.perf_counter()
        cache.main()
        cache_seconds = time.perf_counter() - t2
    finally:
        pre.make_current_base = original_current_base
        pre.learn_bias = original_bias
        pre.build_augmented = original_build

    # Normalize date-specific metadata written by the audited 2026-09-11 cache builder.
    z = joblib.load(cache_path)
    z['date'] = day8
    z['history_cutoff'] = HISTORY_CUTOFF
    z['production_daily_wrapper'] = True
    z['target_result_or_payout_used'] = False
    joblib.dump(z, cache_path, compress=3)

    q = pd.read_csv(pre_csv, dtype={'race_code': str}) if pre_csv.exists() else pd.DataFrame()
    candidates = [] if q.empty else q.race_code.astype(str).str.zfill(12).tolist()
    total_seconds = time.perf_counter() - t0
    manifest = {
        'policy': '3HEAD_V288_PRODUCTION',
        'target_date': day.isoformat(),
        'target_date_yyyymmdd': day8,
        'history_cutoff': HISTORY_CUTOFF,
        'result_blind_target_day': True,
        'result_or_payout_used': False,
        'operational_pre_training_quantile': True,
        'operational_pre_percentile_bridge': False,
        'pre_candidate_count': len(candidates),
        'pre_candidate_race_codes': candidates,
        'cards_sha256': sha256(cards_path),
        'waku_sha256': sha256(waku_path),
        'cache_sha256': sha256(cache_path),
        'build_augmented_seconds': build_seconds,
        'pre_after_build_seconds': pre_seconds,
        'cache_after_build_seconds': cache_seconds,
        'total_seconds': total_seconds,
        'single_augmented_build': True,
        'scope_guard': 'September 2026 only; next month requires a newly frozen prior-month model/history audit',
    }
    (outdir / 'daily_manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
