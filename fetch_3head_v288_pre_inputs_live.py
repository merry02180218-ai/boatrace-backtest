#!/usr/bin/env python3
"""Generic result-blind current PRE input fetcher for 3-head v288.

Primary current-card/Waku10-equivalent source remains Kyoteibiyori. If the
Kyoteibiyori Waku10-equivalent row is missing for an otherwise valid race card,
fall back only to the previously overlap-validated direct BOATCAST Waku10 parser.
No result/payout/current-exhibition inputs are used here.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import fetch_kyoteibiyori_v288_pre_inputs as base
from historical_waku10_fetcher import fetch_race as fetch_boatcast_waku10_race


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
    recovered = []
    sources = Counter()
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
            code = f'{day}{jo:02d}{rno:02d}'
            try:
                z = base.detail(s, jo, rno, referer, token, meta)
                if not z:
                    continue
                detail_rows += 1
                players = sorted(z['race_list'], key=lambda x: int(x.get('course') or 99))
                mt = base.meeting(s, jo, rno, referer, meta, players)
                card = base.make_card(jo, rno, z, mt)

                try:
                    wr = base.make_waku(jo, rno, z)
                    source = 'kyoteibiyori'
                except Exception as primary_error:
                    wr = fetch_boatcast_waku10_race(day_iso, code)
                    if not wr:
                        raise RuntimeError(
                            f'Waku10 unavailable in Kyoteibiyori and validated BOATCAST fallback: '
                            f'{primary_error}'
                        )
                    source = 'boatcast_direct_validated_fallback'
                    recovered.append({
                        'race_code': code,
                        'primary_error': str(primary_error),
                    })

                # The date-specific audited base has a literal 2026-09-11 display
                # field; race codes already use base.DAY. Normalize display only.
                card['レース日'] = day_iso
                wr['レース日'] = day_iso
                cards.append(card)
                waku.append(wr)
                sources[source] += 1
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
        'result_or_payout_used': False,
        'current_exhibition_used': False,
        'active_venues_with_complete_rows': [f'{x:02d}' for x in active],
        'detail_rows_seen': detail_rows,
        'complete_race_rows': len(cards),
        'waku_rows': len(waku),
        'excluded_rows': max(0, detail_rows - len(cards)),
        'waku_source_counts': dict(sources),
        'boatcast_fallback_recovered': recovered,
        'failures': failures,
        'waku_policy': (
            'Kyoteibiyori primary; if its required Waku10-equivalent row is missing, '
            'use only the previously overlap-validated direct BOATCAST Waku10 parser; '
            'otherwise exclude/fail closed'
        ),
    }
    (out / 'input_manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(
        'ACTIVE', ','.join(f'{x:02d}' for x in active),
        'DETAIL', detail_rows,
        'COMPLETE', len(cards),
        'EXCLUDED', max(0, detail_rows - len(cards)),
        'WAKU_SOURCES', dict(sources),
        flush=True,
    )


if __name__ == '__main__':
    main()
