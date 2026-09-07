#!/usr/bin/env python3
"""v191: restore June for the clean 3-head PRE validation.

Uses the same static-only v190 feature/model code, but restores historical waku10 with
historical_data_loader.waku10_rows(): saved BoatraceCSV first, then overlap-validated
BOATCAST direct fallback. No current-race TKZ/STT/original exhibition, result, payout or
odds are PRE features.

Temporal protocol is restored to:
  June train -> July cutoff tuning -> August untouched test.
Production after exhibition remains actual v165 p3head>=.30 -> v166 lambda=1.00 Top10.
"""
from __future__ import annotations
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

import analyze_v190_3head_clean_pre_monitor as v
from historical_data_loader import waku10_rows

OUT=v.ROOT/'analysis_v191_3head_clean_pre_validation.csv'
PRED=v.ROOT/'prediction_v191_20260909_3head_pre_monitor.csv'
SUMMARY=v.ROOT/'summary_v191_3head_clean_pre_restore_june.md'


def fetch_day(d):
    y=d.strftime('%Y/%m/%d')
    cards=v.getcsv(v.BASE+f'data/programs/race_cards/{y}.csv')
    wrows,src=waku10_rows(y)
    return d,cards,v.bycode(wrows),src


def hist_rows():
    labs=v.labels();days=[];d=date(2026,6,1)
    while d<=date(2026,8,31):
        days.append(d);d+=timedelta(days=1)
    out=[];missing=0;cover={'boatracecsv_saved':0,'boatcast_direct':0,'missing':0};missing_dates=[]
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs=[ex.submit(fetch_day,d) for d in days]
        for f in as_completed(fs):
            d,cards,wm,src=f.result();cover[src]=cover.get(src,0)+1
            if not cards:
                missing_dates.append(d.isoformat());continue
            for c in cards:
                code=c.get('レースコード','');lab=labs.get(code);w=wm.get(code)
                if not lab or not w:
                    missing+=1;continue
                q=v.raw_features(c,w);q.update(lab);q['race_code']=code;q['waku_source']=src;out.append(q)
    return out,missing,cover,sorted(missing_dates)


def main():
    h,miss,cover,missing_dates=hist_rows()
    tr=[r for r in h if r['month']=='2026-06']
    tu=[r for r in h if r['month']=='2026-07']
    te=[r for r in h if r['month']=='2026-08']
    pos=[sum(r['label'] for r in z) for z in [tr,tu,te]]
    print('v191 restore rows', [len(tr),len(tu),len(te)], 'positives',pos,'missing',miss,'waku_cover',cover,'missing_dates',missing_dates,flush=True)
    if min(pos)<5:
        raise SystemExit(f'insufficient positives train/tune/test: {pos}')

    m=v.fit(tr)
    pu=v.pred(m,tu);cut=v.choose_cut(tu,pu);mu=v.metric(tu,pu,cut)
    pe=v.pred(m,te);me=v.metric(te,pe,cut)
    passed=me[3]>=.80 and me[5]<=.35
    for r,p in zip(tu,pu):r['pre_prob_eval']=p;r['split']='tune_july'
    for r,p in zip(te,pe):r['pre_prob_eval']=p;r['split']='untouched_aug'
    pd.DataFrame(tu+te).to_csv(OUT,index=False,encoding='utf-8-sig')

    # Runtime behavior remains v190's static-only official-card scan.
    final=v.fit(h);rt,avs,errs=v.runtime(final,cut)
    pd.DataFrame(rt).to_csv(PRED,index=False,encoding='utf-8-sig')
    cand=[z for z in rt if z['pre_watch']]
    now=datetime.now(ZoneInfo('Asia/Tokyo'))
    L=['# v191 clean 3-head PRE — June restored','',
       '**PREは監視候補のみ。正式候補は展示後 actual v165 p3head>=30%。**','',
       '## June restoration','- historical waku10: saved BoatraceCSV -> validated BOATCAST fallback',
       f'- waku source days: {cover}',f'- race-card missing dates: {missing_dates or "none"}',f'- unmatched race rows: {miss}','',
       '## Temporal validation',
       f'- June train: R {len(tr)}, formal {pos[0]}',
       f'- July tune: R {mu[0]}, formal {mu[1]}, watch {mu[2]} ({100*mu[5]:.1f}%), recall {100*mu[3]:.1f}%, precision {100*mu[4]:.1f}%',
       f'- frozen cut: **{cut:.6f}**',
       f'- August untouched: R {me[0]}, formal {me[1]}, watch {me[2]} ({100*me[5]:.1f}%), recall {100*me[3]:.1f}%, precision {100*me[4]:.1f}%',
       f'- gate: **{"PASS" if passed else "FAIL"}** (Aug recall>=80%, watch<=35%)','',
       '## 2026-09-09 PRE monitor',f'- scan JST: **{now:%Y-%m-%d %H:%M:%S}**',f'- active venues: **{len(avs)}**',f'- scored: **{len(rt)}R** / errors {len(errs)}R',f'- PRE watch: **{len(cand)}R**','',
       '|締切|場|R|3号艇|級|PRE p|','|---|---|---:|---|---|---:|']
    for z in cand:L.append(f"|{z['deadline']}|{z['venue_name']}|{z['race']}R|{z['boat3_name']}|{z['boat3_grade']}|{100*z['pre_monitor_prob']:.1f}%|")
    if not cand:L.append('|-|-|-|-|-|-|')
    L += ['','## Canonical operation','PRE watch -> exhibition -> actual v165 p3head>=30% -> v166 lambda=1.00 Top10. PRE score is never p3head and never BUY.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
