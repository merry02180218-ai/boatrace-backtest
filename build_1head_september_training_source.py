#!/usr/bin/env python3
"""Build chronology-safe September 1-head training rows.

Features are frozen from BoatraceCSV PRE sources first; only after all target-day
features are frozen are completed historical results joined as labels. This builder
is for LIVE rolling training and does not alter the historical Feb-Aug production
sentinel.
"""
from __future__ import annotations
import argparse,csv,json
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path

import analyze_v108_1head_feasibility as v108
from backtest import rows


def bycode(rs): return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}
def daterange(a,b):
    d=a
    while d<=b:
        yield d; d+=timedelta(days=1)
def write_csv(p,rs):
    if not rs:return
    fs=sorted(set().union(*(r.keys() for r in rs)))
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rs)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--target-date',default='2026-09-15');ap.add_argument('--start-date',default='2026-09-01');ap.add_argument('--out-dir',default='/tmp/onehead_sep_training');a=ap.parse_args()
    target=date.fromisoformat(a.target_date);start=date.fromisoformat(a.start_date);end=target-timedelta(days=1)
    if end<start: raise RuntimeError('no prior-day September range')
    # Reconstruct ST frame bias using only dates before each feature day.
    sums=defaultdict(list);allv=[]
    preload=date(2025,10,1)
    for d in daterange(preload,start-timedelta(days=1)):
        st=rows(f'data/previews/stt/{d:%Y/%m/%d}.csv');v108.update_st(st,sums,allv)
    frozen=[];coverage={}
    for d in daterange(start,end):
        ymd=f'{d:%Y/%m/%d}';cards=rows(f'data/programs/race_cards/{ymd}.csv');waku=bycode(rows(f'data/programs/waku10/{ymd}.csv'));tkz=bycode(rows(f'data/previews/tkz/{ymd}.csv'));stt=bycode(rows(f'data/previews/stt/{ymd}.csv'));orig=bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'));bias=v108.st_bias(sums,allv);n0=len(frozen)
        for c in cards:
            code=str(c.get('レースコード','')).zfill(12)
            if not code or code not in waku: continue
            try:r=v108.feature_row(str(d),c,waku[code],tkz,stt,orig,bias)
            except Exception: continue
            if r is not None:frozen.append(r)
        coverage[str(d)]={'cards':len(cards),'waku':len(waku),'frozen':len(frozen)-n0,'tkz':len(tkz),'stt':len(stt),'orig':len(orig)}
        # Current day ST can affect future days only.
        v108.update_st(list(stt.values()),sums,allv)
    if not frozen: raise RuntimeError('SEPTEMBER_FEATURE_SOURCE_MISSING')
    # Result labels are loaded only after the entire requested feature range is frozen.
    settled=[]
    for r in frozen:
        d=date.fromisoformat(r['date']);ymd=f'{d:%Y/%m/%d}';res=bycode(rows(f'data/results/realtime/{ymd}.csv'));pay=bycode(rows(f'data/results/payouts/{ymd}.csv'));code=r['race_code'];rr=res.get(code,{});pr=pay.get(code,{})
        win=v108.ii(rr.get('1着_艇番'));kim=v108.normkim(rr.get('決まり手'));combo=(pr.get('3連単_組番') or '').strip();payout=v108.ii(pr.get('3連単_払戻金'));tickets=r.get('tickets20_display','').split(';') if r.get('tickets20_display') else []
        q=dict(r);q.update({'valid_result':int(win in range(1,7)),'winner':win,'kimarite':kim,'head_hit':int(win==1),'escape_hit':int(win==1 and kim=='逃げ'),'valid_payout':int(bool(combo) and payout>0),'actual_combo':combo,'payout100':payout,'actual_ticket_rank20':tickets.index(combo)+1 if combo in tickets else 0});settled.append(q)
    valid=[r for r in settled if r['valid_result']]
    if not valid: raise RuntimeError('SEPTEMBER_RESULT_SOURCE_MISSING')
    if max(date.fromisoformat(r['date']) for r in valid)>=target: raise AssertionError('target/future leak')
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);write_csv(out/'september_training_rows.csv',valid)
    meta={'target_date':str(target),'training_start':str(start),'training_max_date':max(r['date'] for r in valid),'feature_rows':len(frozen),'valid_result_rows':len(valid),'head_hits':sum(int(r['head_hit']) for r in valid),'same_day_outcomes_read':False,'target_or_future_rows':0,'chronology_guard':True,'coverage':coverage};(out/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
