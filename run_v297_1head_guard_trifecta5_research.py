#!/usr/bin/env python3
"""Execution wrapper for v297.

Uses direct realtime-result top3 as the primary settlement source, and only if
that exact result is missing uses archived v108 actual_combo as a settlement-only
fallback. Neither source participates in feature construction.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date
import pandas as pd

import analyze_v297_1head_guard_trifecta5_research as base
import analyze_v294_1head_verified_prepost_research as v294
from backtest import rows
from backtest_v51_lane_corrected_tickets import ii


def norm_code(x):
    return base.norm_code(x)


def parse_combo(x):
    s=str(x or '').strip().replace(' ','')
    try:a=[int(z) for z in s.split('-')]
    except Exception:return ''
    if len(a)!=3 or len(set(a))!=3 or any(z not in range(1,7) for z in a):return ''
    return '-'.join(map(str,a))


def archived_combo_map():
    use=['date','race_code','actual_combo']
    s=pd.read_csv(v294.V108,encoding='utf-8-sig',dtype={'race_code':str},usecols=lambda c:c in use)
    s['date']=pd.to_datetime(s.date,errors='coerce')
    s=s[(s.date>=pd.Timestamp(v294.START))&(s.date<=pd.Timestamp(v294.END))].copy()
    s['date']=s.date.dt.strftime('%Y-%m-%d');s['race_code']=s.race_code.map(norm_code)
    s['actual_combo']=s.actual_combo.map(parse_combo)
    s=s[(s.race_code!='')&(s.actual_combo!='')].drop_duplicates(['date','race_code'],keep='last')
    return {(r.date,r.race_code):r.actual_combo for r in s.itertuples(index=False)}


def settle_union_after_freeze(d):
    days=sorted({date.fromisoformat(str(x)) for x in d.date});fetched={}
    def one(day):
        rs=rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv")
        return day,{norm_code(r.get('レースコード','')):r for r in rs if norm_code(r.get('レースコード',''))}
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(one,day) for day in days]
        for j,f in enumerate(as_completed(fs),1):
            day,z=f.result();fetched[day]=z
            if j%40==0:print('exact-result fetch',j,'/',len(days),flush=True)
    arc=archived_combo_map();winners=[];combos=[];valid=[];direct_n=0;fallback_n=0
    for _,r in d.iterrows():
        rr=fetched.get(date.fromisoformat(str(r.date)),{}).get(norm_code(r.race_code),{})
        a=ii(rr.get('1着_艇番'),0);b=ii(rr.get('2着_艇番'),0);c=ii(rr.get('3着_艇番'),0)
        direct=(a in range(1,7) and b in range(1,7) and c in range(1,7) and len({a,b,c})==3)
        combo=f'{a}-{b}-{c}' if direct else ''
        if direct:
            direct_n+=1
        else:
            combo=arc.get((str(r.date),norm_code(r.race_code)),'')
            if combo:
                fallback_n+=1
                a=int(combo.split('-')[0])
        ok=bool(combo)
        winners.append(a if ok else 0);combos.append(combo);valid.append(int(ok))
    z=d.copy();z['winner']=winners;z['valid_result']=valid;z['combo_valid']=valid;z['actual_combo']=combos
    z['head_hit']=(z.winner==1).astype(int)
    direct_cov=direct_n/len(z) if len(z) else 0.0;cov=float(z.combo_valid.mean()) if len(z) else 0.0
    print(f'settlement audit direct={direct_cov:.6f} fallback_n={fallback_n} union={cov:.6f}',flush=True)
    if direct_cov<.98:raise RuntimeError(f'direct settlement coverage unexpectedly low {direct_cov:.4f}')
    if cov<.99:raise RuntimeError(f'union exact-order settlement coverage too low {cov:.4f}')
    return z,cov

_orig_summary=base.make_summary
def make_summary(cov,folds,monthly,pool,km):
    s=_orig_summary(cov,folds,monthly,pool,km)
    s=s.replace('Exact-order settlement is fetched directly from historical realtime result CSV only after race-card/history features are frozen.',
                'Exact-order settlement uses historical realtime result CSV first, with archived v108 `actual_combo` only as a settlement-only fallback after features are frozen.')
    s=s.replace('Direct exact-order settlement coverage:','Union exact-order settlement coverage:')
    return s

base.settle_full_after_freeze=settle_union_after_freeze
base.make_summary=make_summary

if __name__=='__main__':
    base.main()
