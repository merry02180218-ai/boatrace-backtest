#!/usr/bin/env python3
"""Archive historical BOAT RACE official closing 3T odds.

Source page:
https://www.boatrace.jp/owpc/pc/race/odds3t?hd=YYYYMMDD&jcd=JJ&rno=R

The official page labels these values 締切時オッズ. This script intentionally
keeps them separate from BoatraceCSV pre-close od3 snapshots.

Usage:
  python tools/fetch_official_closing_odds3t.py 2025-10-01 2026-08-31

Writes one CSV per day under data/official_closing_odds3t/YYYY/MM/DD.csv.
"""
from __future__ import annotations
import csv, itertools, re, sys, time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE='https://www.boatrace.jp/owpc/pc/race/odds3t?hd={hd}&jcd={jcd:02d}&rno={rno}'
OUT=Path('data/official_closing_odds3t')
COMBOS=[f'{a}-{b}-{c}' for a,b,c in itertools.permutations(range(1,7),3)]

# BOAT RACE odds3t HTML contains 120 odds values in race table cells.
# Parse only the 3T table area and require exactly the complete 120-combination set.
def fetch(url, retries=3):
    req=Request(url, headers={'User-Agent':'Mozilla/5.0 boatrace-backtest historical-research'})
    for k in range(retries):
        try:
            with urlopen(req, timeout=20) as r:
                return r.read().decode('utf-8','ignore')
        except (HTTPError, URLError, TimeoutError):
            if k+1==retries: return None
            time.sleep(1.5*(k+1))

def parse(html):
    if not html or '締切時オッズ' not in html or '3連単オッズ' not in html:
        return None
    # Official markup exposes each combination via data attributes/classes; first try
    # generic sequence extraction from the 3T table. Keep strict validation to avoid
    # silently saving malformed pages if markup changes.
    m=re.search(r'3連単オッズ(.*?)(?:2連単オッズ|3連複オッズ|オッズ情報)', html, re.S)
    area=m.group(1) if m else html
    vals=re.findall(r'(?:odds|ratio)[^>]*>\s*([0-9]+(?:\.[0-9]+)?)\s*<', area, re.I)
    if len(vals)<120:
        vals=re.findall(r'<td[^>]*class="[^"]*(?:odds|ratio)[^"]*"[^>]*>\s*([0-9]+(?:\.[0-9]+)?)\s*</td>', area, re.I)
    if len(vals)!=120:
        return None
    return dict(zip(COMBOS, map(float, vals)))

def daterange(a,b):
    d=a
    while d<=b:
        yield d; d+=timedelta(days=1)

def main():
    if len(sys.argv)!=3:
        raise SystemExit('usage: script START_DATE END_DATE')
    start=date.fromisoformat(sys.argv[1]); end=date.fromisoformat(sys.argv[2])
    total=0
    for d in daterange(start,end):
        rows=[]
        hd=d.strftime('%Y%m%d')
        for jcd in range(1,25):
            for rno in range(1,13):
                url=BASE.format(hd=hd,jcd=jcd,rno=rno)
                odds=parse(fetch(url))
                if odds:
                    row={'date':d.isoformat(),'jcd':f'{jcd:02d}','rno':rno,'source_url':url,'source_type':'official_closing'}
                    row.update(odds); rows.append(row)
                time.sleep(0.08)
        if rows:
            p=OUT/f'{d:%Y}'/f'{d:%m}'/f'{d:%d}.csv'; p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
            total+=len(rows); print(d, len(rows), 'total', total, flush=True)
        else:
            print(d, 0, flush=True)
if __name__=='__main__': main()
