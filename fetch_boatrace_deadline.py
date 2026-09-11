#!/usr/bin/env python3
"""Fetch one race's scheduled purchase deadline from BOAT RACE official racelist.

Result-blind operational helper.  It requests only /race/racelist, validates the
12 scheduled deadline times, emits the selected deadline as an ISO-8601 JST value,
and optionally freezes request metadata/hash for audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
BASE = 'https://www.boatrace.jp/owpc/pc/race/racelist'
UA = 'Mozilla/5.0 (compatible; boatrace-backtest/1.0; +https://github.com/)'
FORBIDDEN = ('/result', '/pay', 'result?', 'pay?')


def safe_get(date: str, jcd: int, rno: int) -> requests.Response:
    if any(x in BASE.lower() for x in FORBIDDEN):
        raise RuntimeError('forbidden endpoint configured')
    r = requests.get(
        BASE,
        params={'rno': rno, 'jcd': f'{jcd:02d}', 'hd': date},
        headers={'User-Agent': UA},
        timeout=15,
    )
    r.raise_for_status()
    if '/race/racelist' not in r.url.lower():
        raise RuntimeError(f'unexpected redirect away from racelist: {r.url}')
    return r


def parse_deadlines(html: str) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    candidates: list[list[str]] = []
    for tr in soup.find_all('tr'):
        text = ' '.join(x.get_text(' ', strip=True) for x in tr.find_all(['th', 'td']))
        if '締切予定時刻' not in text:
            continue
        vals = re.findall(r'(?<!\d)([0-2]?\d:[0-5]\d)(?!\d)', text)
        if len(vals) >= 12:
            candidates.append(vals[:12])
    if not candidates:
        # Defensive text fallback for minor DOM changes.  Limit the search to a
        # short window after the unique schedule label and still require 12 times.
        text = soup.get_text(' ', strip=True)
        pos = text.find('締切予定時刻')
        if pos >= 0:
            vals = re.findall(r'(?<!\d)([0-2]?\d:[0-5]\d)(?!\d)', text[pos:pos + 800])
            if len(vals) >= 12:
                candidates.append(vals[:12])
    if not candidates:
        raise RuntimeError('could not parse 12 scheduled deadlines from official racelist')
    first = candidates[0]
    if any(x != first for x in candidates[1:]):
        raise RuntimeError('conflicting official deadline rows')
    return first


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='YYYYMMDD')
    ap.add_argument('--jcd', type=int, required=True)
    ap.add_argument('--race', type=int, choices=range(1, 13), required=True)
    ap.add_argument('--meta', type=Path)
    args = ap.parse_args()
    if not re.fullmatch(r'20\d{6}', args.date):
        raise SystemExit('--date must be YYYYMMDD')

    requested_at = datetime.now(JST)
    r = safe_get(args.date, args.jcd, args.race)
    fetched_at = datetime.now(JST)
    html = r.text
    times = parse_deadlines(html)
    hm = times[args.race - 1]
    day = datetime.strptime(args.date, '%Y%m%d').date()
    hh, mm = map(int, hm.split(':'))
    deadline = datetime(day.year, day.month, day.day, hh, mm, tzinfo=JST)

    meta = {
        'source': 'BOAT RACE official racelist only',
        'requested_at_jst': requested_at.isoformat(),
        'fetched_at_jst': fetched_at.isoformat(),
        'resolved_url': r.url,
        'html_sha256': hashlib.sha256(html.encode('utf-8', errors='replace')).hexdigest(),
        'date': args.date,
        'jcd': args.jcd,
        'race': args.race,
        'all_deadlines_jst_hm': times,
        'deadline_jst': deadline.isoformat(),
        'result_endpoint_requested': False,
        'payout_endpoint_requested': False,
    }
    if args.meta:
        args.meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(deadline.isoformat())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
