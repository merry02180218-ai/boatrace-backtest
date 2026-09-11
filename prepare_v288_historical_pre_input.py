#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from datetime import datetime
from pathlib import Path
from backtest import rows
from historical_waku10_fetcher import fetch_race

def bycode(rs):
    return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def write(path,rs):
    if not rs: raise RuntimeError(f'no rows for {path}')
    fs=[]; seen=set()
    for r in rs:
        for k in r:
            if k not in seen:seen.add(k);fs.append(k)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--date',required=True);a=ap.parse_args()
    day=datetime.strptime(a.date,'%Y-%m-%d').date(); y=day.strftime('%Y/%m/%d'); day8=day.strftime('%Y%m%d')
    cards=rows(f'data/programs/race_cards/{y}.csv'); waku0=rows(f'data/programs/waku10/{y}.csv')
    if not cards: raise RuntimeError(f'no archived race cards {a.date}')
    wm=bycode(waku0); recovered=[]; missing=[]
    for card in cards:
        code=str(card.get('レースコード','')).zfill(12)
        if code in wm: continue
        z=fetch_race(a.date,code)
        if z: wm[code]=z;recovered.append(code)
        else: missing.append(code)
    # Production semantics are fail-closed per race; preserve all complete card+waku rows.
    cc=[];ww=[]
    for card in cards:
        code=str(card.get('レースコード','')).zfill(12)
        if code not in wm:continue
        c=dict(card);w=dict(wm[code]);c['レース日']=a.date;w['レース日']=a.date
        cc.append(c);ww.append(w)
    out=Path('current_input/v288')/day8
    write(out/'race_cards.csv',cc);write(out/'waku10.csv',ww)
    m={'target_date':a.date,'archived_pre_input':True,'result_or_payout_used':False,'current_exhibition_used':False,
       'race_cards_seen':len(cards),'public_waku_rows':len(waku0),'complete_rows':len(cc),
       'boatcast_fallback_recovered':recovered,'excluded_missing_waku':missing}
    (out/'historical_input_manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(m,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
