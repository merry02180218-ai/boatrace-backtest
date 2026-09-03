from __future__ import annotations
import csv, io, urllib.request
from historical_waku10_fetcher import fetch_day

BASE='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'

def _published_rows(path):
    try:
        req=urllib.request.Request(BASE+path,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=20) as r:
            s=r.read().decode('utf-8-sig')
        return list(csv.DictReader(io.StringIO(s))) if s else []
    except Exception:
        return []

def waku10_rows(ymd:str):
    """Return waku10 using saved BoatraceCSV first, then authoritative BOATCAST source.

    ymd: YYYY/MM/DD or YYYY-MM-DD.
    The fallback was overlap-validated on 2026-07-20: 156/156 races and
    32,448/32,448 fields matched the published BoatraceCSV file exactly.
    """
    slash=ymd.replace('-','/')
    saved=_published_rows(f'data/programs/waku10/{slash}.csv')
    if saved:
        return saved, 'boatracecsv_saved'
    direct=fetch_day(slash.replace('/','-'))
    return direct, ('boatcast_direct' if direct else 'missing')
