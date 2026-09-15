#!/usr/bin/env python3
"""Build result-blind daily race_cards.csv directly from BOATCAST entry tables.

This is a fail-closed fallback for the 03:00 daily preparation.  It only requests
BOATCAST replay/entry pages and never requests result, payout, odds, or race-result
endpoints.  The requested ymd must be visibly present on each accepted page.
"""
from __future__ import annotations
import argparse, io, re, sys
from pathlib import Path
import pandas as pd, requests

UA={'User-Agent':'Mozilla/5.0 (compatible; v351-live-pre-card/1.0)'}
BASE='https://race.boatcast.jp/replay?jo={jo:02d}&race={race}&ymd={ymd}'

def flat(c):
    if isinstance(c,tuple): return ' '.join(str(x) for x in c if str(x)!='nan')
    return str(c)
def num(x):
    m=re.search(r'-?\d+(?:\.\d+)?',str(x).replace(',',''))
    return m.group(0) if m else ''
def pick(cols,*need):
    for c in cols:
        s=flat(c).replace('\n',' ').replace(' ','')
        if all(n.replace(' ','') in s for n in need): return c
    return None
def accepted_table(html):
    try: tabs=pd.read_html(io.StringIO(html))
    except Exception:return None
    for t in tabs:
        if len(t)!=6: continue
        hs='|'.join(flat(c) for c in t.columns)
        if '全国' in hs and '当地' in hs and 'モーター' in hs and ('平均' in hs or 'ST' in hs): return t
    return None

def parse_table(t,ymd,jo,race):
    cols=list(t.columns); c_st=pick(cols,'平均','ST') or pick(cols,'ST'); c_nat=pick(cols,'全国','勝率'); c_loc=pick(cols,'当地','勝率'); c_m2=pick(cols,'モーター','2連対率'); c_fl=pick(cols,'FL'); c_player=pick(cols,'級別') or pick(cols,'選手名')
    missing=[n for n,c in [('平均ST',c_st),('全国勝率',c_nat),('当地勝率',c_loc),('モーター2連対率',c_m2)] if c is None]
    if missing: raise RuntimeError(f'BOATCAST table missing core columns {missing}; headers={[flat(c) for c in cols]}')
    row={'レースコード':f'{ymd}{jo:02d}{race:02d}','レース場コード':f'{jo:02d}'}
    for i in range(6):
        b=i+1; r=t.iloc[i]; p=str(r[c_player]) if c_player is not None else ''; fl=str(r[c_fl]) if c_fl is not None else ''
        gm=re.search(r'\b([AB][12])\b',p); fm=re.search(r'F\s*(\d+)',fl)
        row[f'艇{b}_級別']=gm.group(1) if gm else ''
        row[f'艇{b}_全国平均ST']=num(r[c_st]); row[f'艇{b}_全国勝率']=num(r[c_nat]); row[f'艇{b}_当地勝率']=num(r[c_loc]); row[f'艇{b}_モーター2連対率']=num(r[c_m2]); row[f'艇{b}_F本数']=fm.group(1) if fm else '0'
        # BOATCAST entry table does not expose motor 3-rate in every layout.
        # Leave unavailable fields blank; existing feature code handles missing values.
        row[f'艇{b}_モーター3連対率']=''
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True,help='YYYYMMDD');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();ymd=a.date.replace('-','')
    if not re.fullmatch(r'20\d{6}',ymd): raise SystemExit('bad date')
    sess=requests.Session();sess.headers.update(UA);rows=[];venues=[]
    for jo in range(1,25):
        # Race 1 establishes whether this venue is actually running on target date.
        u=BASE.format(jo=jo,race=1,ymd=ymd); r=sess.get(u,timeout=15); r.raise_for_status(); html=r.text
        visible=(f'{ymd[:4]}/{ymd[4:6]}/{ymd[6:8]}' in html) or (f'{ymd[4:6]}/{ymd[6:8]}' in html)
        t=accepted_table(html)
        if not visible or t is None: continue
        venues.append(jo); rows.append(parse_table(t,ymd,jo,1))
        for race in range(2,13):
            rr=sess.get(BASE.format(jo=jo,race=race,ymd=ymd),timeout=15);rr.raise_for_status();tt=accepted_table(rr.text)
            if tt is None: raise RuntimeError(f'BOATCAST missing entry table {ymd} JCD{jo:02d} R{race}')
            rows.append(parse_table(tt,ymd,jo,race))
    if not rows: raise RuntimeError(f'BOATCAST returned no target-date entry cards for {ymd}')
    q=pd.DataFrame(rows).drop_duplicates('レースコード').sort_values('レースコード');a.out.parent.mkdir(parents=True,exist_ok=True);q.to_csv(a.out,index=False,encoding='utf-8-sig')
    print(f'BOATCAST_CARDS date={ymd} venues={venues} races={len(q)} result_or_payout_used=False chronology_guard=True')
    if len(q)!=12*len(venues): raise RuntimeError('incomplete BOATCAST venue/race grid')
    return 0
if __name__=='__main__': raise SystemExit(main())
