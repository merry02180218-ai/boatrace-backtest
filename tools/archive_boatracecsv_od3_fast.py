#!/usr/bin/env python3
"""Fast archive of BoatraceCSV 3T pre-close odds.

Downloads one daily CSV per date from:
  https://boatracecsv.github.io/data/previews/od3/YYYY/MM/DD.csv

The upstream file is the 3-ren-tan (120-combination) odds snapshot taken 1-10
minutes before close (usually about 5 minutes), not final closing odds.

Usage:
  python tools/archive_boatracecsv_od3_fast.py 2025-10-01 2026-08-31

Writes:
  data/previews/od3/YYYY/MM/DD.csv
  archive_boatracecsv_od3_manifest.csv
"""
from __future__ import annotations

import csv
import io
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = 'https://boatracecsv.github.io/data/previews/od3/{y:04d}/{m:02d}/{d:02d}.csv'
OUT = Path('data/previews/od3')
MANIFEST = Path('archive_boatracecsv_od3_manifest.csv')
WORKERS = 24
RETRIES = 3


def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def validate(raw: bytes):
    # Upstream is UTF-8 CSV. Validate schema enough to prevent saving HTML/error pages.
    text = raw.decode('utf-8-sig')
    rdr = csv.reader(io.StringIO(text))
    header = next(rdr, [])
    odds_cols = [c for c in header if c.startswith('3連単_')]
    if 'レースコード' not in header or len(odds_cols) != 120:
        raise ValueError(f'bad schema: columns={len(header)} odds_cols={len(odds_cols)}')
    rows = sum(1 for _ in rdr)
    if rows <= 0:
        raise ValueError('empty csv')
    return text, rows, len(odds_cols)


def one(d: date):
    p = OUT / f'{d:%Y}' / f'{d:%m}' / f'{d:%d}.csv'
    if p.exists() and p.stat().st_size > 0:
        try:
            text = p.read_text(encoding='utf-8-sig')
            _, rows, odds_cols = validate(text.encode('utf-8-sig'))
            return {'date': d.isoformat(), 'status': 'existing', 'rows': rows,
                    'odds_cols': odds_cols, 'url': BASE.format(y=d.year,m=d.month,d=d.day), 'error': ''}
        except Exception:
            pass

    url = BASE.format(y=d.year, m=d.month, d=d.day)
    err = ''
    for k in range(RETRIES):
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 boatrace-backtest research'})
            with urlopen(req, timeout=20) as r:
                raw = r.read()
            text, rows, odds_cols = validate(raw)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding='utf-8')
            return {'date': d.isoformat(), 'status': 'downloaded', 'rows': rows,
                    'odds_cols': odds_cols, 'url': url, 'error': ''}
        except HTTPError as e:
            err = f'HTTP {e.code}'
            if e.code == 404:
                break
        except (URLError, TimeoutError, ValueError, UnicodeDecodeError) as e:
            err = f'{type(e).__name__}: {e}'
        if k + 1 < RETRIES:
            time.sleep(0.8 * (2 ** k))
    return {'date': d.isoformat(), 'status': 'missing', 'rows': 0,
            'odds_cols': 0, 'url': url, 'error': err}


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: script START_DATE END_DATE')
    start = date.fromisoformat(sys.argv[1])
    end = date.fromisoformat(sys.argv[2])
    days = list(daterange(start, end))
    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, d): d for d in days}
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            results.append(r)
            print(f"[{i}/{len(days)}] {r['date']} {r['status']} rows={r['rows']} {r['error']}", flush=True)

    results.sort(key=lambda x: x['date'])
    with MANIFEST.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['date','status','rows','odds_cols','url','error'])
        w.writeheader(); w.writerows(results)

    ok = [r for r in results if r['status'] in ('downloaded','existing')]
    miss = [r for r in results if r['status'] == 'missing']
    total_rows = sum(r['rows'] for r in ok)
    print(f'SUMMARY days={len(days)} available={len(ok)} missing={len(miss)} race_rows={total_rows}', flush=True)
    if miss:
        print('MISSING_DATES', ','.join(r['date'] for r in miss), flush=True)


if __name__ == '__main__':
    main()
