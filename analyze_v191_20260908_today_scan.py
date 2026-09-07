#!/usr/bin/env python3
from datetime import date, datetime
from zoneinfo import ZoneInfo
import pandas as pd
import analyze_v190_3head_clean_pre_monitor as v
import analyze_v191_3head_clean_pre_restore_june as v191

TARGET=date(2026,9,8)
v.HD=TARGET
v.HD8='20260908'
OUT=v.ROOT/'prediction_v191_20260908_3head_pre_monitor.csv'
SUMMARY=v.ROOT/'summary_v191_20260908_today_scan.md'

def main():
    h,miss,cover,missing_dates=v191.hist_rows()
    tr=[r for r in h if r['month']=='2026-06']
    tu=[r for r in h if r['month']=='2026-07']
    te=[r for r in h if r['month']=='2026-08']
    m=v.fit(tr)
    pu=v.pred(m,tu); cut=v.choose_cut(tu,pu)
    final=v.fit(h)
    rt,avs,errs=v.runtime(final,cut)
    pd.DataFrame(rt).to_csv(OUT,index=False,encoding='utf-8-sig')
    cand=[z for z in rt if z['pre_watch']]
    now=datetime.now(ZoneInfo('Asia/Tokyo'))
    L=['# v191 2026-09-08 PRE monitor','',
       '**PREは監視候補のみ。正式候補は展示後 actual v165 p3head>=30%。**','',
       f'- scan JST: **{now:%Y-%m-%d %H:%M:%S}**',
       f'- active venues: **{len(avs)}**',
       f'- scored: **{len(rt)}R** / errors {len(errs)}R',
       f'- PRE watch: **{len(cand)}R**',
       f'- frozen cut: **{cut:.6f}**','',
       '|締切|場|R|3号艇|級|PRE p|','|---|---|---:|---|---|---:|']
    for z in cand:
        L.append(f"|{z['deadline']}|{z['venue_name']}|{z['race']}R|{z['boat3_name']}|{z['boat3_grade']}|{100*z['pre_monitor_prob']:.1f}%|")
    if not cand:L.append('|-|-|-|-|-|-|')
    L += ['','## Canonical operation','PRE watch -> exhibition -> actual v165 p3head>=30% -> v166 lambda=1.00 Top10. PRE score is never p3head and never BUY.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__': main()
