#!/usr/bin/env python3
"""Archive historical BOAT RACE official closing 3T odds.

Source page:
https://www.boatrace.jp/owpc/pc/race/odds3t?hd=YYYYMMDD&jcd=JJ&rno=R

The official page labels these values 締切時オッズ. This script intentionally
keeps them separate from BoatraceCSV pre-close od3 snapshots.

IMPORTANT: the official 3T table is rendered row-major across six first-boat
columns. Its HTML value order is NOT itertools.permutations() order.
"""
from __future__ import annotations
import csv, re, sys, time
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE='https://www.boatrace.jp/owpc/pc/race/odds3t?hd={hd}&jcd={jcd:02d}&rno={rno}'
OUT=Path('data/official_closing_odds3t')
MAPPING_VERSION='official_table_v2'

def official_display_combos():
    """Return the 120 combinations in the exact order displayed in official HTML.

    The table has six first-boat columns. For each ordinal second-boat choice
    (ascending among the other five), each of four third-boat choices is shown
    as a row, with first boats 1..6 traversed across that row.
    """
    out=[]
    for second_idx in range(5):
        for third_idx in range(4):
            for first in range(1,7):
                seconds=[x for x in range(1,7) if x!=first]
                second=seconds[second_idx]
                thirds=[x for x in range(1,7) if x not in (first,second)]
                third=thirds[third_idx]
                out.append(f'{first}-{second}-{third}')
    assert len(out)==120 and len(set(out))==120
    return out

COMBOS=official_display_combos()

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
        rows=[]; hd=d.strftime('%Y%m%d')
        for jcd in range(1,25):
            for rno in range(1,13):
                url=BASE.format(hd=hd,jcd=jcd,rno=rno)
                odds=parse(fetch(url))
                if odds:
                    row={'date':d.isoformat(),'jcd':f'{jcd:02d}','rno':rno,'source_url':url,'source_type':'official_closing','odds_mapping_version':MAPPING_VERSION}
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
