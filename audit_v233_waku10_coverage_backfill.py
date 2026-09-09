#!/usr/bin/env python3
"""v233: audit Waku10 availability and backfill from original Boatcast source.
Audit only; no model tuning. Never imputes missing values.
Recovered source files are saved with provenance.
"""
from __future__ import annotations
import csv, io, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

PUB='https://boatracecsv.github.io/data/programs/waku10/'
RACE='https://boatracecsv.github.io/data/programs/race_cards/'
BOAT='https://race.boatcast.jp/hp_txt/'
START=date(2025,12,1); END=date(2026,8,31)
OUT=Path('data/audit/v233_waku10'); OUT.mkdir(parents=True,exist_ok=True)
BACKFILL=OUT/'recovered_boatcast'; BACKFILL.mkdir(parents=True,exist_ok=True)
TIMEOUT=4
WORKERS=32

def get(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 v233-waku10-audit'})
        with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
            b=r.read()
            return b if b else b''
    except Exception:
        return b''

def daterange():
    d=START
    while d<=END:
        yield d
        d+=timedelta(days=1)

def parse_venues(b):
    if not b:return []
    try:
        rs=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))
        return sorted({str(r.get('レース場コード','')).zfill(2) for r in rs if r.get('レース場コード')})
    except Exception:
        return []

def fetch_pair(item):
    kind,d,url=item
    return kind,d,url,get(url)

def fetch_direct(item):
    d,jo,rr,url=item
    return d,jo,rr,url,get(url)

def main():
    days=list(daterange())
    # Stage 1: bulk-probe published Waku10 and race cards concurrently.
    jobs=[]
    for d in days:
        rel=f'{d:%Y/%m/%d}.csv'
        jobs.append(('waku',d,PUB+rel))
        jobs.append(('race',d,RACE+rel))
    pub={}; race={}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs=[ex.submit(fetch_pair,j) for j in jobs]
        for f in as_completed(futs):
            kind,d,url,b=f.result()
            (pub if kind=='waku' else race)[d]=b

    # Stage 2: only missing published days are probed at documented Boatcast endpoints.
    direct_jobs=[]
    venues_by_day={d:parse_venues(race.get(d,b'')) for d in days}
    for d in days:
        if pub.get(d):
            continue
        ymd=d.strftime('%Y%m%d')
        for jo in venues_by_day[d]:
            for rr in range(1,13):
                url=f'{BOAT}{jo}/bc_j_waku10_{ymd}_{jo}_{rr}.txt'
                direct_jobs.append((d,jo,rr,url))

    recovered={d:[] for d in days}
    if direct_jobs:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs=[ex.submit(fetch_direct,j) for j in direct_jobs]
            for f in as_completed(futs):
                d,jo,rr,url,b=f.result()
                if not b:
                    continue
                sub=BACKFILL/f'{d:%Y/%m/%d}'
                sub.mkdir(parents=True,exist_ok=True)
                p=sub/f'bc_j_waku10_{d:%Y%m%d}_{jo}_{rr}.txt'
                p.write_bytes(b)
                recovered[d].append((jo,rr,url,str(p),len(b)))

    rows=[]
    provenance=[]
    for d in days:
        rec=recovered[d]
        rows.append({
            'date':str(d),
            'published_waku10':int(bool(pub.get(d))),
            'published_bytes':len(pub.get(d,b'')),
            'race_cards_available':int(bool(race.get(d))),
            'scheduled_venues':len(venues_by_day[d]),
            'direct_boatcast_files_found':len(rec),
            'direct_boatcast_bytes':sum(x[4] for x in rec),
        })
        for jo,rr,url,path,n in sorted(rec):
            provenance.append({'date':str(d),'venue':jo,'race':rr,'source_url':url,'saved_path':path,'bytes':n})

    with open(OUT/'coverage.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    with open(OUT/'recovered_provenance.csv','w',newline='',encoding='utf-8') as f:
        fields=['date','venue','race','source_url','saved_path','bytes']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(provenance)

    months={}
    for r in rows:
        m=r['date'][:7]
        q=months.setdefault(m,{'days':0,'published':0,'missing':0,'direct_days':0,'direct_files':0})
        q['days']+=1;q['published']+=r['published_waku10'];q['missing']+=1-r['published_waku10']
        q['direct_days']+=int(r['direct_boatcast_files_found']>0);q['direct_files']+=r['direct_boatcast_files_found']
    lines=['# v233 Waku10 coverage/backfill audit','',
           'No imputation. Published daily Waku10 is checked first. Only missing days are probed against the documented original Boatcast bc_j_waku10 endpoint. Recovered raw files are saved with provenance.','',
           '|month|days|published|missing|direct recovered days|direct files|','|---|---:|---:|---:|---:|---:|']
    for m,q in sorted(months.items()):
        lines.append(f"|{m}|{q['days']}|{q['published']}|{q['missing']}|{q['direct_days']}|{q['direct_files']}|")
    lines += ['',f'Total recovered raw files: {len(provenance)}']
    (OUT/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines),flush=True)

if __name__=='__main__':main()
