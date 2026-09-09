#!/usr/bin/env python3
"""v233: audit Waku10 availability and attempt historical backfill from original Boatcast source.
No model tuning. Saves provenance/coverage. Never imputes missing values.
"""
from __future__ import annotations
import csv, io, urllib.request
from datetime import date,timedelta
from pathlib import Path

PUB='https://boatracecsv.github.io/data/programs/waku10/'
BOAT='https://race.boatcast.jp/hp_txt/'
START=date(2025,12,1); END=date(2026,8,31)
OUT=Path('data/audit/v233_waku10'); OUT.mkdir(parents=True,exist_ok=True)

def get(url):
 try:
  with urllib.request.urlopen(url,timeout=15) as r:return r.read()
 except Exception:return b''

def scheduled_venues(d):
 # B-file lists scheduled races/venues and is the same historical scheduling source used elsewhere in repo.
 ymd=d.strftime('%y%m%d'); candidates=[f'https://www1.mbrace.or.jp/od2/B/{ymd}.lzh',f'https://www1.mbrace.or.jp/od2/B/{ymd}.txt']
 # Avoid binary parsing here: infer venues from existing race_cards public CSV when available.
 u=f'https://boatracecsv.github.io/data/programs/race_cards/{d:%Y/%m/%d}.csv'; b=get(u)
 if not b:return []
 try:
  rs=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig')))); return sorted({str(r.get('レース場コード','')).zfill(2) for r in rs if r.get('レース場コード')})
 except Exception:return []

def main():
 rows=[]; d=START
 while d<=END:
  rel=f'{d:%Y/%m/%d}.csv'; pub=get(PUB+rel)
  venues=scheduled_venues(d); direct_ok=0; direct_bytes=0
  # If published daily Waku10 is missing, probe the documented original per-race Boatcast endpoints.
  if not pub and venues:
   ymd=d.strftime('%Y%m%d')
   for jo in venues:
    for rr in range(1,13):
     url=f'{BOAT}{jo}/bc_j_waku10_{ymd}_{jo}_{rr}.txt'; b=get(url)
     if b: direct_ok+=1; direct_bytes+=len(b)
  rows.append({'date':str(d),'published_waku10':int(bool(pub)),'published_bytes':len(pub),'scheduled_venues':len(venues),'direct_boatcast_files_found':direct_ok,'direct_boatcast_bytes':direct_bytes})
  if d.day==1: print(d,rows[-1],flush=True)
  d+=timedelta(days=1)
 with open(OUT/'coverage.csv','w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
 months={}
 for r in rows:
  m=r['date'][:7]; q=months.setdefault(m,{'days':0,'published':0,'direct_recovered_days':0});q['days']+=1;q['published']+=r['published_waku10'];q['direct_recovered_days']+=int(r['direct_boatcast_files_found']>0)
 lines=['# v233 Waku10 coverage/backfill audit','', 'No imputation. Missing published days are probed against the documented original Boatcast bc_j_waku10 endpoint.','', '|month|days|published Waku10 days|direct-source recoverable missing days|','|---|---:|---:|---:|']
 for m,q in sorted(months.items()):lines.append(f"|{m}|{q['days']}|{q['published']}|{q['direct_recovered_days']}|")
 (OUT/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))
if __name__=='__main__':main()
