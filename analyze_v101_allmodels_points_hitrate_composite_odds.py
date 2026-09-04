"""v101: all-model ticket-count hit probability + pre-close composite odds.

Purpose
- For every model, A/S grade and N=1..20 fixed-head tickets, report:
  head win probability, conditional ticket coverage given the head wins,
  overall trifecta hit rate, equal-stake ROI, and average combined odds.
- Current production comparison uses v83 entry gate + BASE score/ticket order.
  Shadow v96/v100 role tiebreaks are deliberately excluded.

No-leak odds policy
- Odds come only from BoatraceCSV data/previews/od3 rows whose acquisition timestamp
  is strictly before the race cutoff timestamp.
- Missing historical pre-close odds stay missing. No final/deadline odds substitution.
- Odds are used only for descriptive combined-odds statistics, never candidate selection.
"""
from __future__ import annotations
import csv
from datetime import datetime, date, timedelta
from statistics import mean, median

from backtest import rows

SRC='analysis_v83_wind_entry_gate.csv'
OUT='analysis_v101_allmodels_points_hitrate_composite_odds.csv'
SUMMARY='summary_v101_allmodels_points_hitrate_composite_odds.md'
START='2025-11-01'; END='2026-08-31'; A=55.0; S=67.0
MODELS=['3まくり','3まくり差し','4カドまくり','5頭展開']


def ff(x,d=None):
    try:
        if x is None or str(x).strip()=='': return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def bycode(rs):return {r.get('レースコード',''):r for r in rs if r.get('レースコード')}

def tickets(r):
    return [x.strip() for x in (r.get('tickets20_display') or '').split(';') if x.strip()][:20]

def preclose_info(r,ds):
    acq=(r.get('取得日時') or '').strip();cut=(r.get('締切時刻') or '').strip()
    if not acq or not cut:return None
    try:
        a=datetime.fromisoformat(acq)
        hh,mm=map(int,cut.split(':')[:2])
        y,m,d=map(int,ds.split('-'))
        c=datetime(y,m,d,hh,mm,tzinfo=a.tzinfo)
        lead=(c-a).total_seconds()/60.0
        return lead if lead>0 else None
    except Exception:return None

def combo_odds(orow,ts):
    vals=[]
    for t in ts:
        v=ff(orow.get('3連単_'+t))
        if v is None or v<=1.0:return None
        vals.append(v)
    den=sum(1.0/v for v in vals)
    return (1.0/den) if den>0 else None

def load_odds_map(candidate_dates):
    om={};leads=[];available_dates=[]
    # Repository policy/tree currently provides od3 in Jul/Aug inside this 10-month window.
    for ds in sorted(d for d in candidate_dates if '2026-07-01'<=d<='2026-08-31'):
        ymd=ds.replace('-','/')
        rr=rows(f'data/previews/od3/{ymd}.csv')
        accepted=0
        for r in rr:
            lead=preclose_info(r,ds)
            code=r.get('レースコード','')
            if code and lead is not None:
                om[code]=r;leads.append(lead);accepted+=1
        if accepted:available_dates.append(ds)
    return om,leads,available_dates

def grade_ok(r,g):
    s=ff(r.get('score'),-999)
    return s >= (S if g=='S' else A)

def main():
    raw=[r for r in read_csv(SRC) if START<=r.get('date','')<=END and r.get('model') in MODELS]
    # Current operational validity: confirmed entry changes excluded; missing course remains kept.
    base=[r for r in raw if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_payout'))==1]
    odds_map,leads,odates=load_odds_map({r.get('date','') for r in base})

    out=[]
    for g in ('A','S'):
        for m in MODELS:
            q=[r for r in base if r.get('model')==m and grade_ok(r,g) and len(tickets(r))>=20]
            head_hits=sum(ii(r.get('head_hit'))==1 for r in q)
            for n in range(1,21):
                hits=[r for r in q if 1<=ii(r.get('actual_rank20'))<=n]
                hit=len(hits)
                ret=sum(ii(r.get('payout100')) for r in hits)
                inv=len(q)*n*100
                codds=[];oleads=[]
                for r in q:
                    orow=odds_map.get(r.get('race_code',''))
                    if not orow:continue
                    lead=preclose_info(orow,r.get('date',''))
                    if lead is None:continue
                    co=combo_odds(orow,tickets(r)[:n])
                    if co is not None:
                        codds.append(co);oleads.append(lead)
                rec={
                    'grade':g,'model':m,'tickets_n':n,'candidate_races':len(q),'head_hits':head_hits,
                    'head_rate_pct':pct(head_hits,len(q)),
                    'ticket_hits':hit,'overall_hit_rate_pct':pct(hit,len(q)),
                    'coverage_given_head_pct':pct(hit,head_hits),
                    'equal_stake_roi_pct':pct(ret,inv),
                    'avg_hit_payout_yen':(mean([ii(r.get('payout100')) for r in hits]) if hits else 0),
                    'odds_races':len(codds),'odds_coverage_pct':pct(len(codds),len(q)),
                    'avg_composite_odds':(mean(codds) if codds else 0),
                    'median_composite_odds':(median(codds) if codds else 0),
                    'avg_odds_lead_min':(mean(oleads) if oleads else 0),
                }
                out.append(rec)

    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(out[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    L=['# v101 全モデル 点数別 頭率・総合的中率・平均合成オッズ','',
       f'- 的中率期間: **{START}〜{END}**（現行BASE score + 現行v51 20通り順位 + v83進入変更除外）。',
       '- 「総合的中率」= 予測頭が1着かつ実3連単が上位N点以内 ÷ 対象レース数。',
       '- 「頭内カバー」= 実3連単が上位N点以内 ÷ 頭的中数。したがって概ね 頭率 × 頭内カバー = 総合的中率。',
       '- 合成オッズ = **1 / Σ(1/各買い目オッズ)**。全N点のod3が正値で、取得日時が締切より前のレースだけ集計。',
       '- v96/v100はshadow候補なので本表には混ぜず、全モデルを現行相手順位で横並び比較。','']
    if odates:
        L += [f'- pre-close od3利用日: **{odates[0]}〜{odates[-1]}** / {len(odates)}日。',
              f'- od3取得リードタイム: 平均 **{mean(leads):.2f}分前** / 中央 **{median(leads):.2f}分前** / 最短 **{min(leads):.2f}分前** / 最長 **{max(leads):.2f}分前**。','']
    else:
        L += ['- pre-close od3利用可能データなし。合成オッズは欠損。','']

    # Full 1..20 tables for every model/grade.
    for g in ('A','S'):
        L += [f'## {g}以上','']
        for m in MODELS:
            rr=[x for x in out if x['grade']==g and x['model']==m]
            if not rr:continue
            h=rr[0]
            L += [f'### {m} — {h["candidate_races"]}R / 頭率 {h["head_rate_pct"]:.1f}%',
                  '|点数|総合的中率|頭内カバー|平均合成オッズ|odds R|oddsカバー|等額ROI|',
                  '|---:|---:|---:|---:|---:|---:|---:|']
            for x in rr:
                co=f'{x["avg_composite_odds"]:.2f}倍' if x['odds_races'] else '-'
                L.append(f'|{x["tickets_n"]}|{x["overall_hit_rate_pct"]:.1f}%|{x["coverage_given_head_pct"]:.1f}%|{co}|{x["odds_races"]}|{x["odds_coverage_pct"]:.1f}%|{x["equal_stake_roi_pct"]:.1f}%|')
            L.append('')

    L += ['## 注意',
          '- 頭率・総合的中率・ROIは10か月全体。平均合成オッズはpre-close od3が存在する期間だけなので、期間が異なる。',
          '- 合成オッズは複数買い目を均等払戻になるようダッチングしたときの理論倍率で、各100円均等買いのROIとは別概念。',
          '- 合成オッズを候補抽出や買い目選別には使用していないため、今回の集計で選択リークは発生しない。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
