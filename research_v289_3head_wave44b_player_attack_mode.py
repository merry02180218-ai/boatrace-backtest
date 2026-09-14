from __future__ import annotations
import csv, io, urllib.request, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
import numpy as np
import pandas as pd

BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
START=date(2025,2,1); END=date(2026,3,31)

def fetch_rows(path, attempts=3):
    for i in range(attempts):
        try:
            with urllib.request.urlopen(BASE+path,timeout=30) as r:
                return list(csv.DictReader(io.StringIO(r.read().decode('utf-8-sig'))))
        except Exception:
            time.sleep(.4*(i+1))
    return []

def norm_code(x):
    s=''.join(ch for ch in str(x or '') if ch.isdigit())
    return s.zfill(12) if s else ''

def pick(row, keys):
    for k in keys:
        v=str(row.get(k,'')).strip()
        if v: return v
    return ''

def norm_mode(x):
    s=str(x).replace(' ','').replace('　','')
    if 'まくり差し' in s: return 'MAKURI_SASHI'
    if 'まくり' in s: return 'MAKURI'
    return 'OTHER'

def day_bundle(d):
    ymd=d.strftime('%Y/%m/%d')
    cards=fetch_rows(f'data/programs/race_cards/{ymd}.csv')
    results=fetch_rows(f'data/results/realtime/{ymd}.csv')
    cmap={norm_code(r.get('レースコード','')):r for r in cards if norm_code(r.get('レースコード',''))}
    return d.isoformat(),cmap,results

if __name__=='__main__':
    from research_v289_3head_wave45_confidence_margin import main
    main()
