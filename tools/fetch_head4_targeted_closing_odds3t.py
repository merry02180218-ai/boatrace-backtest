#!/usr/bin/env python3
"""Recover official closing 3T odds only for fixed HEAD4 candidate races.

Default scope is Apr-Aug 2026; September is explicitly forbidden.  Candidate
selection is delegated to the independent HEAD4 audit.  Only uncovered races
are fetched, so this avoids the full date x 24 venues x 12 races crawl.
"""
from pathlib import Path
import csv
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

import audit_4head_86r_independent as cand
from tools.fetch_official_closing_odds3t import BASE, COMBOS, MAPPING_VERSION, fetch, parse

OUT=ROOT/'data'/'official_closing_odds3t'
START='2026-04-01'; END='2026-08-31'


def parse_code(code):
    s=str(code).zfill(12)
    return s[:8], int(s[8:10]), int(s[10:12])


def existing(ds,jcd,rno):
    p=OUT/ds[:4]/ds[4:6]/f'{ds[6:8]}.csv'
    if not p.is_file(): return False
    q=pd.read_csv(p,dtype=str)
    if 'jcd' not in q or 'rno' not in q: return False
    return bool(((q.jcd.str.zfill(2)==f'{jcd:02d}') & (q.rno.astype(int)==rno)).any())


def merge_row(ds,row):
    p=OUT/ds[:4]/ds[4:6]/f'{ds[6:8]}.csv'; p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_file():
        q=pd.read_csv(p,dtype={'jcd':str})
        q['jcd']=q.jcd.astype(str).str.zfill(2)
        q=q[~((q.jcd==row['jcd']) & (pd.to_numeric(q.rno,errors='coerce')==row['rno']))]
        old=q.to_dict('records')
    else: old=[]
    rows=old+[row]
    fields=['date','jcd','rno','source_type','snapshot_type','source_url','odds_mapping_version']+COMBOS
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)


def main():
    cx=cand.rebuild().copy()
    cx['date']=cx.date.astype(str)
    cx=cx[(cx.date>=START)&(cx.date<=END)].copy()
    if len(cx)!=164 or int(cx.head4.sum())!=70: raise RuntimeError('HEAD4_CANDIDATE_CONTRACT_MISMATCH')
    if any(cx.date>'2026-08-31'): raise RuntimeError('SEPTEMBER_FORBIDDEN')
    targets=[]
    for code in cx.race_code.astype(str):
        ds,jcd,rno=parse_code(code)
        if not existing(ds,jcd,rno): targets.append((ds,jcd,rno))
    print('TARGETS',len(targets),flush=True)
    ok=0; fail=[]
    for ds,jcd,rno in targets:
        url=BASE.format(hd=ds,jcd=jcd,rno=rno)
        odds=parse(fetch(url))
        if not odds:
            fail.append(f'{ds}{jcd:02d}{rno:02d}'); print('MISS',fail[-1],flush=True); continue
        row={'date':f'{ds[:4]}-{ds[4:6]}-{ds[6:8]}','jcd':f'{jcd:02d}','rno':rno,'source_type':'official_closing','snapshot_type':'closing_displayed','source_url':url,'odds_mapping_version':MAPPING_VERSION}
        row.update(odds); merge_row(ds,row); ok+=1; print('OK',f'{ds}{jcd:02d}{rno:02d}',flush=True)
    print('RECOVERED',ok,'FAILED',len(fail),flush=True)
    if fail: print('FAILED_CODES',','.join(fail),flush=True)

if __name__=='__main__': main()
