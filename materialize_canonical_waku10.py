from __future__ import annotations
import csv, io, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path
from historical_waku10_fetcher import HEAD, parse_tsv, get as get_text

RAW='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
BOATCAST='https://race.boatcast.jp/hp_txt'
START=date(2025,12,1); END=date(2026,8,31)
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'data/programs/waku10'
COV=ROOT/'canonical_waku10_coverage.csv'
SUMMARY=ROOT/'canonical_waku10_summary.md'
WORKERS=12


def get_bytes(url,timeout=20):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 canonical-waku10'})
        with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
    except Exception:return b''


def dates():
    d=START
    while d<=END:
        yield d
        d+=timedelta(days=1)


def fetch_day(d):
    ymd=d.strftime('%Y/%m/%d'); ds=str(d)
    cards_b=get_bytes(RAW+f'data/programs/race_cards/{ymd}.csv')
    if not cards_b:return d,[],0
    cards=list(csv.DictReader(io.StringIO(cards_b.decode('utf-8-sig'))))
    codes=[]; seen=set()
    for r in cards:
        code=(r.get('レースコード') or '').strip()
        if code and code not in seen:
            seen.add(code);codes.append(code)
    out=[]
    for code in codes:
        jo=code[8:10]; rno=code[10:12]
        body=get_text(f'{BOATCAST}/{jo}/bc_j_waku10_{d:%Y%m%d}_{jo}_{rno}.txt',timeout=15)
        z=parse_tsv(body,code,ds,jo,rno)
        if z:out.append(z)
    return d,out,len(codes)


def write_day(d,rs):
    p=DEST/f'{d:%Y/%m/%d}.csv';p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=HEAD);w.writeheader();w.writerows(sorted(rs,key=lambda r:r['レースコード']))
    return p


def valid_row(r):
    return bool(r.get('レースコード')) and all(k in r for k in HEAD)


def main():
    cov=[]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs={ex.submit(fetch_day,d):d for d in dates()}
        for fut in as_completed(futs):
            d,rs,expected=fut.result()
            if rs:
                codes=[r['レースコード'] for r in rs]
                if len(codes)!=len(set(codes)):raise RuntimeError(f'duplicate race codes {d}')
                if not all(valid_row(r) for r in rs):raise RuntimeError(f'invalid row schema {d}')
                write_day(d,rs)
            cov.append({'date':str(d),'expected_card_races':expected,'restored_rows':len(rs),'coverage_pct':round((len(rs)/expected*100) if expected else 0,3)})
            print(d,'restored',len(rs),'of',expected,flush=True)
    cov.sort(key=lambda r:r['date'])
    with COV.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(cov[0]));w.writeheader();w.writerows(cov)
    months={}
    for r in cov:
        m=r['date'][:7];q=months.setdefault(m,{'days':0,'expected':0,'restored':0});q['days']+=1;q['expected']+=r['expected_card_races'];q['restored']+=r['restored_rows']
    L=['# Canonical Waku10 materialization','','Source: direct historical BOATCAST `bc_j_waku10_*`, parsed by the already validated historical Waku10 parser. No imputation.','', '|month|days|expected races|restored rows|coverage|','|---|---:|---:|---:|---:|']
    for m,q in sorted(months.items()):
        pct=q['restored']/q['expected']*100 if q['expected'] else 0
        L.append(f"|{m}|{q['days']}|{q['expected']}|{q['restored']}|{pct:.2f}%|")
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L),flush=True)

if __name__=='__main__':main()
