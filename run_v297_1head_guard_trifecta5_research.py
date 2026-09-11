#!/usr/bin/env python3
"""Execution wrapper for v297 with fail-closed multi-source settlement audit.

Prediction-time features are frozen first. Settlement is then reconstructed from:
  1) historical realtime result CSV,
  2) historical payout CSV (`単勝_艇番`, `3連単_組番`) as an independent fallback,
  3) archived v108 `actual_combo` only as a final settlement-only fallback.
No settlement field participates in feature construction or model selection inputs.
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
    s=str(x or '').strip().replace(' ','').replace('‐','-').replace('－','-')
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

def _maps(day):
    ymd=day.strftime('%Y/%m/%d')
    rt=rows(f'data/results/realtime/{ymd}.csv')
    po=rows(f'data/results/payouts/{ymd}.csv')
    rtm={norm_code(r.get('レースコード','')):r for r in rt if norm_code(r.get('レースコード',''))}
    pom={norm_code(r.get('レースコード','')):r for r in po if norm_code(r.get('レースコード',''))}
    return rt,po,rtm,pom

def settle_union_after_freeze(d):
    days=sorted({date.fromisoformat(str(x)) for x in d.date})
    expected={day:set(d.loc[d.date.astype(str)==day.isoformat(),'race_code'].map(norm_code)) for day in days}
    fetched={};raw_rt={};raw_po={};retries={}
    def one(day):
        rt,po,rtm,pom=_maps(day);return day,rt,po,rtm,pom
    with ThreadPoolExecutor(max_workers=10) as ex:
        fs=[ex.submit(one,day) for day in days]
        for j,f in enumerate(as_completed(fs),1):
            day,rt,po,rtm,pom=f.result();fetched[day]=(rtm,pom);raw_rt[day]=len(rt);raw_po[day]=len(po);retries[day]=0
            if j%40==0:print('settlement fetch',j,'/',len(days),flush=True)
    # Retry incomplete dates because backtest.rows() converts transport errors to [].
    for day in days:
        exp=expected[day];rtm,pom=fetched.get(day,({},{}));best=set(rtm)|set(pom);best_match=len(exp & best)
        if len(exp) and best_match/len(exp)<.99:
            for a in range(1,4):
                time.sleep(.15*a);rt,po,nrt,npo=_maps(day);m=len(exp & (set(nrt)|set(npo)))
                if m>best_match:
                    rtm,pom=nrt,npo;best_match=m;raw_rt[day]=len(rt);raw_po[day]=len(po)
                retries[day]=a
                if best_match/len(exp)>=.99:break
            fetched[day]=(rtm,pom)
    day_rows=[]
    for day in days:
        exp=expected[day];rtm,pom=fetched.get(day,({},{}));matched=len(exp & (set(rtm)|set(pom)));n=len(exp)
        day_rows.append({'date':day.isoformat(),'expected':n,'realtime_rows':raw_rt.get(day,0),'payout_rows':raw_po.get(day,0),
                         'matched_union':matched,'coverage_union':matched/n if n else 1.0,'retries':retries.get(day,0)})
    daydf=pd.DataFrame(day_rows).sort_values(['coverage_union','date'])
    daydf.to_csv(DAY_AUDIT,index=False,encoding='utf-8-sig')
    print('worst settlement-source dates after payout fallback:',flush=True);print(daydf.head(20).to_string(index=False),flush=True)

    arc=archived_combo_map();winners=[];combos=[];winner_valids=[];combo_valids=[]
    row_n=winner_n=rt_combo_n=payout_combo_n=archive_combo_n=0
    for _,r in d.iterrows():
        day=date.fromisoformat(str(r.date));code=norm_code(r.race_code);rtm,pom=fetched.get(day,({},{}));rr=rtm.get(code,{});pr=pom.get(code,{})
        if rr or pr:row_n+=1
        a=ii(rr.get('1着_艇番'),0);b=ii(rr.get('2着_艇番'),0);c=ii(rr.get('3着_艇番'),0)
        combo=''
        if a in range(1,7) and b in range(1,7) and c in range(1,7) and len({a,b,c})==3:
            combo=f'{a}-{b}-{c}';rt_combo_n+=1
        else:
            pc=parse_combo(pr.get('3連単_組番',''))
            if pc:
                combo=pc;payout_combo_n+=1
                pa=int(pc.split('-')[0])
                if a not in range(1,7):a=pa
            elif a not in range(1,7):
                a=ii(pr.get('単勝_艇番'),0)
        winner_ok=a in range(1,7)
        if not combo:
            fallback=arc.get((str(r.date),code),'')
            if fallback:
                combo=fallback;archive_combo_n+=1
                if not winner_ok:
                    a=int(combo.split('-')[0]);winner_ok=True
        if winner_ok:winner_n+=1
        combo_ok=bool(combo)
        winners.append(a if winner_ok else 0);combos.append(combo);winner_valids.append(int(winner_ok));combo_valids.append(int(combo_ok))
    z=d.copy();z['winner']=winners;z['valid_result']=winner_valids;z['combo_valid']=combo_valids;z['actual_combo']=combos;z['head_hit']=(z.winner==1).astype(int)
    n=len(z);row_cov=row_n/n if n else 0.0;winner_cov=sum(winner_valids)/n if n else 0.0;combo_cov=sum(combo_valids)/n if n else 0.0
    combo_given_winner=sum(combo_valids)/sum(winner_valids) if sum(winner_valids) else 0.0
    AUDIT.update({'row_cov':row_cov,'winner_cov':winner_cov,'combo_cov_all':combo_cov,'combo_given_winner':combo_given_winner,
                  'rt_combo_n':rt_combo_n,'payout_combo_n':payout_combo_n,'archive_combo_n':archive_combo_n,'n':n})
    print(f"settlement audit rows={row_cov:.6f} winner={winner_cov:.6f} exact_all={combo_cov:.6f} exact_given_winner={combo_given_winner:.6f} realtime_combo={rt_combo_n} payout_fallback={payout_combo_n} archive_fallback={archive_combo_n}",flush=True)
    if row_cov<.99:raise RuntimeError(f'result-row union coverage too low {row_cov:.4f}; inspect {DAY_AUDIT.name}')
    if winner_cov<.99:raise RuntimeError(f'winner settlement coverage too low {winner_cov:.4f}')
    if combo_given_winner<.99:raise RuntimeError(f'exact-order validity among winner-known results too low {combo_given_winner:.4f}')
    return z,combo_given_winner

_orig_summary=base.make_summary
def make_summary(cov,folds,monthly,pool,km):
    s=_orig_summary(cov,folds,monthly,pool,km)
    s=s.replace('Exact-order settlement is fetched directly from historical realtime result CSV only after race-card/history features are frozen.',
                'Settlement is attached only after feature freeze: realtime results first, payout CSV second, archived v108 `actual_combo` last; none are prediction features.')
    s=s.replace('Direct exact-order settlement coverage:', 'Exact-order validity among winner-known results:')
    marker=(f"- Settlement audit: source-row union={100*AUDIT.get('row_cov',0):.2f}%, winner={100*AUDIT.get('winner_cov',0):.2f}%, exact/all={100*AUDIT.get('combo_cov_all',0):.2f}%; "
            f"exact combos realtime={int(AUDIT.get('rt_combo_n',0))}, payout fallback={int(AUDIT.get('payout_combo_n',0))}, archive fallback={int(AUDIT.get('archive_combo_n',0))}.")
    s=s.replace('- Exact-order validity among winner-known results:',marker+'\n- Exact-order validity among winner-known results:')
    return s

base.settle_full_after_freeze=settle_union_after_freeze
base.make_summary=make_summary

if __name__=='__main__':base.main()
