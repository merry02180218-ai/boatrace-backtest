#!/usr/bin/env python3
"""v188: monthly trifecta diagnostics for v180 head probability + v166 top10 tickets.

Purpose
- v180 itself predicts only boat3-head probability; it does not create trifecta tickets.
- Join frozen v180 style probabilities to v166 direct ordered-pair rankings.
- Report Jun-Aug monthly hit rate and payout-based return diagnostics for fixed top10.

No-leak
- v180 probabilities are strict monthly walk-forward outputs already frozen before current result.
- v166 rankings are strict monthly walk-forward outputs already frozen before settlement.
- payout is used only after selection/ranking is fixed.
- No current/final odds are used. Therefore a true market composite-odds number cannot be reconstructed.
  We report (a) average winning-combination payout odds and (b) payout / total 10-ticket stake on hit,
  as clearly labeled payout-based proxies, not true pre-race composite odds.
"""
from __future__ import annotations
import csv
import numpy as np
import pandas as pd

SRC='analysis_v108_1head_feasibility.csv'
P180='analysis_v180_3head_style_headprob.csv'
V166='analysis_v166_3head_pair_direct.csv'
OUT='analysis_v188_v180_v166_monthly_trifecta.csv'
SUMMARY='summary_v188_v180_v166_monthly_trifecta.md'
MONTHS=['2026-06','2026-07','2026-08']
CUTS=[.20,.25,.30,.35,.40]
NPT=10

def ff(x,d=0.):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    src=read(SRC)
    p180=read(P180)
    v166=read(V166)

    # style-variant v180 probabilities, tied back to immutable source row identity.
    pmap={}
    for r in p180:
        if r.get('variant')!='style': continue
        i=ii(r.get('source_index'),-1)
        if not (0<=i<len(src)): continue
        s=src[i]
        key=(s.get('date',''),s.get('race_code',''))
        pmap[key]=ff(r.get('p3head'))

    rows=[]
    for r in v166:
        mon=r.get('v166_month') or r.get('month','')
        if mon not in MONTHS: continue
        key=(r.get('date',''),r.get('race_code',''))
        if key not in pmap: continue
        z=dict(r)
        z['p180_style']=pmap[key]
        rank=ii(r.get('v166_rank20'))
        z['top10_hit']=int(0<rank<=NPT)
        pay=ff(r.get('payout100'))
        z['winning_combo_odds']=pay/100.0 if ii(r.get('valid_payout'))==1 and pay>0 else np.nan
        z['hit_return_multiple_vs_total_stake']=pay/(NPT*100.0) if z['top10_hit'] and ii(r.get('valid_payout'))==1 and pay>0 else np.nan
        rows.append(z)
    d=pd.DataFrame(rows)
    if d.empty: raise SystemExit('no joined v180/v166 rows')

    summary=[]
    for cut in CUTS:
        for scope in MONTHS+['ALL']:
            q=d[d.p180_style>=cut].copy()
            if scope!='ALL':q=q[q.v166_month==scope]
            settled=q[pd.to_numeric(q.valid_payout,errors='coerce').fillna(0).astype(int)==1].copy()
            if len(q)==0:
                summary.append({'cut':cut,'scope':scope,'R':0,'head_rate':np.nan,'hits':0,'hit_rate':np.nan,'avg_winning_combo_odds':np.nan,'avg_hit_return_multiple':np.nan,'roi':np.nan})
                continue
            combo=q.actual_combo.astype(str)
            head_rate=100*combo.str.startswith('3-').mean()
            hit=((pd.to_numeric(q.v166_rank20,errors='coerce').fillna(0)>0)&(pd.to_numeric(q.v166_rank20,errors='coerce').fillna(0)<=NPT))
            hits=int(hit.sum()); hit_rate=100*hit.mean()
            hitq=q[hit & (pd.to_numeric(q.valid_payout,errors='coerce').fillna(0).astype(int)==1)].copy()
            payouts=pd.to_numeric(hitq.payout100,errors='coerce').dropna()
            avg_combo=float((payouts/100).mean()) if len(payouts) else np.nan
            avg_ret_mult=float((payouts/(NPT*100)).mean()) if len(payouts) else np.nan
            cost=len(settled)*NPT*100
            ret=float(pd.to_numeric(settled.loc[(pd.to_numeric(settled.v166_rank20,errors='coerce').fillna(0)>0)&(pd.to_numeric(settled.v166_rank20,errors='coerce').fillna(0)<=NPT),'payout100'],errors='coerce').fillna(0).sum())
            roi=100*ret/cost if cost else np.nan
            summary.append({'cut':cut,'scope':scope,'R':len(q),'head_rate':head_rate,'hits':hits,'hit_rate':hit_rate,'avg_winning_combo_odds':avg_combo,'avg_hit_return_multiple':avg_ret_mult,'roi':roi})

    od=pd.DataFrame(summary); od.to_csv(OUT,index=False)
    L=['# v188 v180 × v166 月別三連単診断','',
       '- v180/style確率で候補を切り、相手はv166 direct ordered-pairの上位10点。','- Jun-Augは各モデル既存のstrict monthly walk-forward出力を結合。','- 結果・払戻は順位固定後のsettlementのみ。','- **締切前の各10点オッズは保存されていないため、真の市場「合成オッズ」は算出不能。**','- 代わりに `平均的中組オッズ` = 的中した3連単払戻/100円、`平均10点投資回収倍率` = 的中払戻/1000円 を併記。後者は合成オッズの代替診断であり、事前市場合成オッズではない。','',
       '## Top10 monthly diagnostics','|v180 cut|月|R|③頭率|的中数|三連単的中率|平均的中組オッズ|平均10点投資回収倍率|ROI|','|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in od.iterrows():
        def f(x,n=2): return '-' if pd.isna(x) else f'{x:.{n}f}'
        L.append(f"|{r['cut']:.2f}|{r['scope']}|{int(r['R'])}|{f(r['head_rate'])}%|{int(r['hits'])}|{f(r['hit_rate'])}%|{f(r['avg_winning_combo_odds'])}倍|{f(r['avg_hit_return_multiple'])}倍|{f(r['roi'],1)}%|")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
