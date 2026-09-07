#!/usr/bin/env python3
"""v188: monthly trifecta diagnostics for v180 head probability + v166 top10 tickets.

Uses exact stored official PRE-CLOSE 3T odds from BoatraceCSV `data/previews/od3`.
For each selected race, computes equal-return composite odds for the ten v166 tickets:
    composite_odds = 1 / sum(1 / ticket_odds)
This is the standard dutching composite price of the whole ten-ticket set.

No-leak
- v180 probabilities and v166 ranks are monthly walk-forward and frozen before result.
- od3 is pre-close market information and is used only for market-price diagnostics here.
- payout/result are settlement-only for actual hit rate and ROI.
"""
from __future__ import annotations
import csv, io, urllib.request
import numpy as np
import pandas as pd

RAW='https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/'
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

def fetch_csv(path):
    try:
        req=urllib.request.Request(RAW+path,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=30) as r:s=r.read().decode('utf-8-sig')
        return list(csv.DictReader(io.StringIO(s)))
    except Exception as e:
        print('od3 fetch fail',path,e,flush=True);return []

def parse_tickets(s):
    return [x.strip() for x in str(s or '').split(';') if x.strip()][:NPT]

def build_odds_map(dates):
    out={}; n=0
    for k,ds in enumerate(sorted(set(dates)),1):
        ymd=ds.replace('-','/')
        for r in fetch_csv(f'data/previews/od3/{ymd}.csv'):
            code=(r.get('レースコード') or '').strip()
            if code:
                out[(ds,code)]=r;n+=1
        if k%30==0:print('od3 days',k,'rows',n,flush=True)
    return out

def composite_for(row,tickets):
    odds=[]
    for t in tickets:
        o=ff(row.get('3連単_'+t),0)
        if o<=1e-9:return np.nan,0
        odds.append(o)
    if not odds:return np.nan,0
    return 1.0/sum(1.0/o for o in odds),len(odds)

def main():
    src=read(SRC);p180=read(P180);v166=read(V166)
    pmap={}
    for r in p180:
        if r.get('variant')!='style':continue
        i=ii(r.get('source_index'),-1)
        if 0<=i<len(src):
            s=src[i];pmap[(s.get('date',''),s.get('race_code',''))]=ff(r.get('p3head'))
    dates=[r.get('date','') for r in v166 if (r.get('v166_month') or r.get('month','')) in MONTHS]
    omap=build_odds_map(dates)
    rows=[];miss=0;full=0
    for r in v166:
        mon=r.get('v166_month') or r.get('month','')
        if mon not in MONTHS:continue
        key=(r.get('date',''),r.get('race_code',''))
        if key not in pmap:continue
        od=omap.get(key)
        if not od:miss+=1;continue
        tickets=parse_tickets(r.get('v166_20'))
        comp,nod=composite_for(od,tickets)
        if nod==NPT:full+=1
        z=dict(r);z['p180_style']=pmap[key];z['odds_coverage_n']=nod;z['composite_odds_top10']=comp
        z['odds_acquired']=od.get('取得日時','');z['odds_deadline']=od.get('締切時刻','')
        rank=ii(r.get('v166_rank20'));z['top10_hit']=int(0<rank<=NPT)
        rows.append(z)
    print('joined',len(rows),'odds_miss',miss,'full_top10_odds',full,flush=True)
    d=pd.DataFrame(rows)
    if d.empty:raise SystemExit('no joined v180/v166/od3 rows')
    summary=[]
    for cut in CUTS:
        for scope in MONTHS+['ALL']:
            q=d[d.p180_style>=cut].copy()
            if scope!='ALL':q=q[q.v166_month==scope]
            if len(q)==0:
                summary.append({'cut':cut,'scope':scope,'R':0,'odds_R':0,'head_rate':np.nan,'hits':0,'hit_rate':np.nan,'avg_composite_odds':np.nan,'median_composite_odds':np.nan,'roi':np.nan});continue
            rank=pd.to_numeric(q.v166_rank20,errors='coerce').fillna(0)
            hit=(rank>0)&(rank<=NPT);hits=int(hit.sum());hit_rate=100*hit.mean()
            head_rate=100*q.actual_combo.astype(str).str.startswith('3-').mean()
            oq=q[pd.to_numeric(q.odds_coverage_n,errors='coerce').fillna(0).astype(int)==NPT]
            co=pd.to_numeric(oq.composite_odds_top10,errors='coerce').dropna()
            settled=q[pd.to_numeric(q.valid_payout,errors='coerce').fillna(0).astype(int)==1].copy()
            sr=pd.to_numeric(settled.v166_rank20,errors='coerce').fillna(0)
            ret=float(pd.to_numeric(settled.loc[(sr>0)&(sr<=NPT),'payout100'],errors='coerce').fillna(0).sum())
            cost=len(settled)*NPT*100;roi=100*ret/cost if cost else np.nan
            summary.append({'cut':cut,'scope':scope,'R':len(q),'odds_R':len(co),'head_rate':head_rate,'hits':hits,'hit_rate':hit_rate,
                            'avg_composite_odds':float(co.mean()) if len(co) else np.nan,
                            'median_composite_odds':float(co.median()) if len(co) else np.nan,'roi':roi})
    odf=pd.DataFrame(summary);odf.to_csv(OUT,index=False)
    L=['# v188 v180 × v166 月別三連単 + 締切前合成オッズ','',
       '- v180/style確率で候補を切り、v166 direct ordered-pair上位10点を購入。',
       '- オッズは保存済み公式 `data/previews/od3` の締切前3連単オッズを使用。',
       '- 10点の合成オッズ = `1 / Σ(1 / 各買い目オッズ)`（均等払戻になるよう資金配分した場合のセット価格）。',
       '- 三連単的中率とROIは実結果/払戻でsettlement。','',
       '## Top10 monthly diagnostics','|v180 cut|月|R|odds R|③頭率|的中数|三連単的中率|平均合成オッズ|中央値|ROI|',
       '|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in odf.iterrows():
        def f(x,n=2):return '-' if pd.isna(x) else f'{x:.{n}f}'
        L.append(f"|{r['cut']:.2f}|{r['scope']}|{int(r['R'])}|{int(r['odds_R'])}|{f(r['head_rate'])}%|{int(r['hits'])}|{f(r['hit_rate'])}%|{f(r['avg_composite_odds'])}倍|{f(r['median_composite_odds'])}倍|{f(r['roi'],1)}%|")
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))

if __name__=='__main__':main()
