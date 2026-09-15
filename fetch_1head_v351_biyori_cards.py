#!/usr/bin/env python3
"""Build result-blind daily race_cards.csv from BoatRace Biyori race-list pages.

Only race-list/entry information is requested. Result, payout and odds endpoints are
never requested. Accepted pages must visibly identify the requested date.
"""
from __future__ import annotations
import argparse, io, re
from pathlib import Path
import pandas as pd, requests

UA={'User-Agent':'Mozilla/5.0 (compatible; v351-live-pre-card/1.0)'}
BASE='https://kyoteibiyori.com/race_ichiran.php?hiduke={ymd}&place_no={jo}&race_no=1'

def num(x):
    m=re.search(r'-?\d+(?:\.\d+)?',str(x).replace(',',''))
    return m.group(0) if m else ''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--date',required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    ymd=a.date.replace('-','')
    if not re.fullmatch(r'20\d{6}',ymd): raise SystemExit('bad date')
    sess=requests.Session(); sess.headers.update(UA); out=[]; venues=[]
    for jo in range(1,25):
        r=sess.get(BASE.format(ymd=ymd,jo=jo),timeout=20); r.raise_for_status(); html=r.text
        visible=(f'{ymd[:4]}/{ymd[4:6]}/{ymd[6:8]}' in html) or (f'{ymd[4:6]}/{ymd[6:8]}' in html)
        if not visible: continue
        try: tabs=pd.read_html(io.StringIO(html))
        except Exception: continue
        race_tables=[]
        for t in tabs:
            if t.shape[1] != 6: continue
            text=' '.join(map(str,t.astype(str).values.ravel()))
            regs=re.findall(r'(?<!\d)([3-5]\d{3})(?!\d)',text)
            grades=re.findall(r'(?<![A-Z])([AB][12])(?!\w)',text)
            if len(set(regs))>=6 and len(grades)>=6: race_tables.append(t)
        if len(race_tables)<12: continue
        venues.append(jo)
        for race,t in enumerate(race_tables[:12],1):
            row={'レースコード':f'{ymd}{jo:02d}{race:02d}','レース場コード':f'{jo:02d}'}
            for i in range(6):
                b=i+1; cell=' '.join(str(x) for x in t.iloc[:,i].tolist())
                gm=re.search(r'(?<![A-Z])([AB][12])(?!\w)',cell); stm=re.search(r'(?:平均ST|ST)\s*[:：]?\s*(0?\.\d+)',cell)
                wrs=re.findall(r'(?<!\d)(\d\.\d{1,2})(?!\d)',cell)
                row[f'艇{b}_級別']=gm.group(1) if gm else ''
                row[f'艇{b}_全国平均ST']=stm.group(1) if stm else ''
                row[f'艇{b}_全国勝率']=wrs[0] if len(wrs)>0 else ''
                row[f'艇{b}_当地勝率']=wrs[1] if len(wrs)>1 else ''
                row[f'艇{b}_モーター2連対率']=''; row[f'艇{b}_モーター3連対率']=''; row[f'艇{b}_F本数']='0'
            out.append(row)
    if not out: raise RuntimeError(f'BIYORI returned no target-date entry cards for {ymd}')
    q=pd.DataFrame(out).drop_duplicates('レースコード').sort_values('レースコード')
    if len(q)!=12*len(venues): raise RuntimeError(f'incomplete BIYORI venue/race grid venues={venues} R={len(q)}')
    a.out.parent.mkdir(parents=True,exist_ok=True); q.to_csv(a.out,index=False,encoding='utf-8-sig')
    print(f'BIYORI_CARDS date={ymd} venues={venues} races={len(q)} result_or_payout_used=False chronology_guard=True')
    return 0
if __name__=='__main__': raise SystemExit(main())
