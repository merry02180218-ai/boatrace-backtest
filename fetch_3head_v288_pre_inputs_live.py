#!/usr/bin/env python3
"""Generic result-blind current PRE input fetcher for 3-head v288.

This keeps the audited 2026-09-11 Kyoteibiyori field semantics, but resolves the
target date at runtime and probes JCD01..24 so active venues are not hard-coded.
Races whose required Waku10-equivalent row is unavailable remain explicitly
excluded and are recorded in the manifest; no unvalidated fallback is invented.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import fetch_kyoteibiyori_v288_pre_inputs as base


def resolve_date(arg: str | None) -> str:
    s = arg or os.environ.get('TARGET_DATE', '').strip()
    if not s:
        s = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d')
    return datetime.strptime(s, '%Y-%m-%d').strftime('%Y%m%d')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date')
    args = ap.parse_args()
    day = resolve_date(args.date)
    day_iso = datetime.strptime(day, '%Y%m%d').strftime('%Y-%m-%d')

    base.DAY = day
    out = Path('current_input/v288') / day
    out.mkdir(parents=True, exist_ok=True)

    s = base.requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; v288-pre-live/1.0)',
        'Accept': 'text/html,application/json',
    })
    cards = []
    waku = []
    failures = []
    active = []
    detail_rows = 0

    for jo in range(1, 25):
        try:
            referer, token, meta = base.get_meta(s, jo)
        except Exception as e:
            failures.append((jo, 'meta', str(e)))
            continue
        got = 0
        for rno in range(1, 13):
            try:
                z = base.detail(s, jo, rno, referer, token, meta)
                if not z:
                    continue
                detail_rows += 1
                players = sorted(z['race_list'], key=lambda x: int(x.get('course') or 99))
                mt = base.meeting(s, jo, rno, referer, meta, players)
                card = base.make_card(jo, rno, z, mt)
                wr = base.make_waku(jo, rno, z)
                # The date-specific audited base has a literal 2026-09-11 display
                # field; race codes already use base.DAY. Normalize display only.
                card['レース日'] = day_iso
                wr['レース日'] = day_iso
                cards.append(card)
                waku.append(wr)
                got += 1
                time.sleep(.03)
            except Exception as e:
                failures.append((jo, rno, str(e)))
        if got:
            active.append(jo)
            print(f'JCD{jo:02d}: {got}/12 complete PRE rows', flush=True)

    if not cards or len(cards) != len(waku):
        raise RuntimeError(f'invalid current universe cards={len(cards)} waku={len(waku)}')
    if len(cards) < 120:
        raise RuntimeError(f'insufficient complete current inputs: {len(cards)} < 120')

    base.write_csv(out / 'race_cards.csv', cards)
    base.write_csv(out / 'waku10.csv', waku)
    manifest = {
        'target_date': day_iso,
        'result_blind': True,
        'current_exhibition_used': False,
        'active_venues_with_complete_rows': [f'{x:02d}' for x in active],
        'detail_rows_seen': detail_rows,
        'complete_race_rows': len(cards),
        'waku_rows': len(waku),
        'excluded_rows': max(0, detail_rows - len(cards)),
        'failures': failures,
        'waku_policy': 'strict audited v288 semantics; missing required Waku10 excludes that race',
    }
    (out / 'input_manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(
        'ACTIVE', ','.join(f'{x:02d}' for x in active),
        'DETAIL', detail_rows,
        'COMPLETE', len(cards),
        'EXCLUDED', max(0, detail_rows - len(cards)),
        flush=True,
    )


if __name__ == '__main__':
    main()
