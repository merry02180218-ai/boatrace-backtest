#!/usr/bin/env python3
"""Execution wrapper for v297 with fail-closed settlement audit.

Features are frozen first. Settlement then uses realtime historical result CSV as
primary source and archived v108 actual_combo only as a settlement-only fallback.
Result-source completeness is audited per day with bounded retries before any
missing race can be excluded from model development.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import date
import time
import pandas as pd

import analyze_v297_1head_guard_trifecta5_research as base
import analyze_v294_1head_verified_prepost_research as v294
from backtest import rows
from backtest_v51_lane_corrected_tickets import ii

AUDIT={}
DAY_AUDIT=base.ROOT/'analysis_v297_1head_guard_trifecta5_settlement_days.csv'

def norm_code(x):return base.norm_code(x)

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
    s['date']=s.date.dt.strftime('%Y-%m-%d');s['race_code']=s.race_code.map(norm_code);s['actual_combo']=s.actual_combo.map(parse_combo)
    s=s[(s.race_code!='')&(s.actual_combo!='')].drop_duplicates(['date','race_code'],keep='last')
    return {(r.date,r.race_code):r.actual_combo for r in s.itertuples(index=False)}

def _fetch_result_map(day):
    rs=rows(f"data/results/realtime/{day.strftime('%Y/%m/%d')}.csv")
    mp={norm_code(r.get('レースコード','')):r for r in rs if norm_code(r.get('レースコード',''))}
    return rs,mp

def settle_union_after_freeze(d):
    days=sorted({date.fromisoformat(str(x)) for x in d.date})
    expected={day:set(d.loc[d.date.astype(str)==day.isoformat(),'race_code'].map(norm_code)) for day in days}
    fetched={}; raw_counts={}; retries={}
    def one(day):
        rs,mp=_fetch_result_map(day)
        return day,rs,mp
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(one,day) for day in days]
        for j,f in enumerate(as_completed(fs),1):
            day,rs,mp=f.result();fetched[day]=mp;raw_counts[day]=len(rs);retries[day]=0
            if j%40==0:print('exact-result fetch',j,'/',len(days),flush=True)
    # Retry only incomplete dates and keep the best response. backtest.rows() has no cache
    # and swallows network errors, so a one-shot empty/partial fetch must not silently bias evaluation.
    for day in days:
        exp=expected[day]
        best=fetched.get(day,{})
        best_match=len(exp & set(best))
        if len(exp) and best_match/len(exp)<.99:
            for a in range(1,4):
                time.sleep(.15*a)
                rs,mp=_fetch_result_map(day)
                m=len(exp & set(mp))
                if m>best_match:
                    best,best_match=mp,m;raw_counts[day]=len(rs)
                retries[day]=a
                if best_match/len(exp)>=.99:break
            fetched[day]=best
    day_rows=[]
    for day in days:
        exp=expected[day];mp=fetched.get(day,{})
        matched=len(exp & set(mp));n=len(exp)
        day_rows.append({'date':day.isoformat(),'expected':n,'raw_result_rows':raw_counts.get(day,0),
                         'matched':matched,'coverage':matched/n if n else 1.0,'retries':retries.get(day,0)})
    daydf=pd.DataFrame(day_rows).sort_values(['coverage','date'])
    daydf.to_csv(DAY_AUDIT,index=False,encoding='utf-8-sig')
    print('worst settlement-source dates:',flush=True)
    print(daydf.head(20).to_string(index=False),flush=True)

    arc=archived_combo_map();winners=[];combos=[];winner_valids=[];combo_valids=[]
    row_n=winner_n=direct_combo_n=fallback_n=0
    for _,r in d.iterrows():
        rr=fetched.get(date.fromisoformat(str(r.date)),{}).get(norm_code(r.race_code),{})
        if rr:row_n+=1
        a=ii(rr.get('1着_艇番'),0);b=ii(rr.get('2着_艇番'),0);c=ii(rr.get('3着_艇番'),0)
        winner_ok=a in range(1,7)
        if winner_ok:winner_n+=1
        direct=(winner_ok and b in range(1,7) and c in range(1,7) and len({a,b,c})==3)
        combo=f'{a}-{b}-{c}' if direct else ''
        if direct:direct_combo_n+=1
        else:
            fallback=arc.get((str(r.date),norm_code(r.race_code)),'')
            if fallback:
                combo=fallback;fallback_n+=1
                if not winner_ok:
                    a=int(combo.split('-')[0]);winner_ok=True;winner_n+=1
        combo_ok=bool(combo)
        winners.append(a if winner_ok else 0);combos.append(combo);winner_valids.append(int(winner_ok));combo_valids.append(int(combo_ok))
    z=d.copy();z['winner']=winners;z['valid_result']=winner_valids;z['combo_valid']=combo_valids;z['actual_combo']=combos;z['head_hit']=(z.winner==1).astype(int)
    n=len(z);row_cov=row_n/n if n else 0.0;winner_cov=sum(winner_valids)/n if n else 0.0;combo_cov=sum(combo_valids)/n if n else 0.0
    combo_given_winner=sum(combo_valids)/sum(winner_valids) if sum(winner_valids) else 0.0
    AUDIT.update({'row_cov':row_cov,'winner_cov':winner_cov,'combo_cov_all':combo_cov,'combo_given_winner':combo_given_winner,'fallback_n':fallback_n,'n':n})
    print(f"settlement audit rows={row_cov:.6f} winner={winner_cov:.6f} exact_all={combo_cov:.6f} exact_given_winner={combo_given_winner:.6f} fallback_n={fallback_n}",flush=True)
    if row_cov<.99:raise RuntimeError(f'result-row source coverage too low {row_cov:.4f}; inspect {DAY_AUDIT.name}')
    if winner_cov<.99:raise RuntimeError(f'winner settlement coverage too low {winner_cov:.4f}')
    if combo_given_winner<.99:raise RuntimeError(f'exact-order validity among winner-known results too low {combo_given_winner:.4f}')
    return z,combo_given_winner

_orig_summary=base.make_summary
def make_summary(cov,folds,monthly,pool,km):
    s=_orig_summary(cov,folds,monthly,pool,km)
    s=s.replace('Exact-order settlement is fetched directly from historical realtime result CSV only after race-card/history features are frozen.',
                'Settlement is attached only after feature freeze; realtime historical result CSV is primary and archived v108 `actual_combo` is settlement-only fallback.')
    s=s.replace('Direct exact-order settlement coverage:', 'Exact-order validity among winner-known results:')
    marker=f"- Settlement audit: source-row={100*AUDIT.get('row_cov',0):.2f}%, winner={100*AUDIT.get('winner_cov',0):.2f}%, exact/all={100*AUDIT.get('combo_cov_all',0):.2f}%, fallback={int(AUDIT.get('fallback_n',0))}."
    s=s.replace('- Exact-order validity among winner-known results:', marker+'\n- Exact-order validity among winner-known results:')
    return s

base.settle_full_after_freeze=settle_union_after_freeze
base.make_summary=make_summary

if __name__=='__main__':base.main()
