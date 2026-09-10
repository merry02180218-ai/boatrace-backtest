#!/usr/bin/env python3
"""v290: risk/stability audit for v289 Top4 composite-odds floors 6/7/8.

No new model fitting and no threshold search. The only candidates are the three
floors already requested after v289: 6.0, 7.0, 8.0. Base tickets remain v283
Top4 fixed. July/August are excluded because v288 detail is Apr-Jun only;
September outcomes are not read.

Audit dimensions:
- S/A split
- month split
- venue split
- boat-4 head rate and exact trifecta hit rate
- max drawdown from a zero starting equity curve
- max consecutive misses
- max consecutive losing bets (profit < 0)
- worst 5-bet and 10-bet rolling P&L

Archived odds remain retrospective proxy. This is development evidence, not
prospective OOS and not an automatic production freeze.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
OUT=ROOT/'analysis_v290_4head_top4_comp_risk_summary.csv'
MONTH=ROOT/'analysis_v290_4head_top4_comp_monthly.csv'
LAYER=ROOT/'analysis_v290_4head_top4_comp_layer.csv'
VENUE=ROOT/'analysis_v290_4head_top4_comp_venue.csv'
DETAIL=ROOT/'analysis_v290_4head_top4_comp_selected_detail.csv'
SUM=ROOT/'summary_v290_4head_top4_comp_risk_audit.md'
BANK=10000
FLOORS=(6.0,7.0,8.0)

VENUES={
'01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖',
'07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江',
'13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山',
'19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村'}


def max_streak(mask):
    best=cur=0
    for x in mask:
        if bool(x):
            cur+=1;best=max(best,cur)
        else:cur=0
    return int(best)


def risk_stats(g):
    g=g.sort_values(['date','race_code']).copy()
    pnl=g.profit_yen.astype(float).to_numpy()
    eq=np.cumsum(pnl)
    peaks=np.maximum.accumulate(np.r_[0.0,eq])
    dd=peaks[1:]-eq
    worst5=pd.Series(pnl).rolling(5).sum().min() if len(g)>=5 else np.nan
    worst10=pd.Series(pnl).rolling(10).sum().min() if len(g)>=10 else np.nan
    return {
        'R':len(g),'head4_wins':int(g.head4_win.sum()),'hits':int(g.hit.sum()),
        'head4_rate_pct':100*g.head4_win.mean() if len(g) else np.nan,
        'hit_rate_pct':100*g.hit.mean() if len(g) else np.nan,
        'avg_comp':g.comp_odds.mean() if len(g) else np.nan,
        'return_yen':float(g.return_yen.sum()),
        'profit_yen':float(g.profit_yen.sum()),
        'roi_pct':100*float(g.return_yen.sum())/(len(g)*BANK) if len(g) else np.nan,
        'max_drawdown_yen':float(dd.max()) if len(dd) else 0.0,
        'max_consecutive_misses':max_streak(g.hit.astype(int).eq(0).tolist()),
        'max_consecutive_losing_bets':max_streak(g.profit_yen.lt(0).tolist()),
        'worst_5bet_pnl_yen':float(worst5) if pd.notna(worst5) else np.nan,
        'worst_10bet_pnl_yen':float(worst10) if pd.notna(worst10) else np.nan,
    }


def load_top4():
    q=pd.read_csv(SRC,dtype={'race_code':str})
    q=q[q.n==4].copy()
    if q.race_code.nunique()!=100 or len(q)!=100:
        raise RuntimeError(f'expected 100 Top4 rows, got {len(q)} / {q.race_code.nunique()}')
    q['race_code']=q.race_code.str.zfill(12)
    q['venue_code']=q.race_code.str.slice(8,10)
    q['venue']=q.venue_code.map(VENUES).fillna(q.venue_code)
    q['date']=pd.to_datetime(q.date)
    return q


def main():
    q=load_top4(); details=[]; summary=[]; months=[]; layers=[]; venues=[]
    for fl in FLOORS:
        g=q[q.comp_odds>=fl].sort_values(['date','race_code']).copy()
        g['floor']=fl;details.append(g)
        s=risk_stats(g);summary.append({'floor':fl,'coverage_pct':100*len(g)/len(q),**s})
        for mon,gg in g.groupby('month'):
            months.append({'floor':fl,'month':mon,**risk_stats(gg)})
        for layer,gg in g.groupby('layer'):
            layers.append({'floor':fl,'layer':layer,**risk_stats(gg)})
        for (vc,vn),gg in g.groupby(['venue_code','venue']):
            venues.append({'floor':fl,'venue_code':vc,'venue':vn,**risk_stats(gg)})
    D=pd.concat(details,ignore_index=True);D.to_csv(DETAIL,index=False)
    S=pd.DataFrame(summary);S.to_csv(OUT,index=False)
    M=pd.DataFrame(months);M.to_csv(MONTH,index=False)
    L=pd.DataFrame(layers);L.to_csv(LAYER,index=False)
    V=pd.DataFrame(venues);V.to_csv(VENUE,index=False)

    # A conservative descriptive ranking: require all 3 calendar months ROI>100,
    # then prefer lower max DD, then more bets, then higher ROI. This does NOT
    # freeze a threshold; it simply makes the risk tradeoff explicit.
    month_floor=M.groupby('floor').roi_pct.min().rename('min_month_roi').reset_index()
    T=S.merge(month_floor,on='floor',how='left')
    T['all_months_positive']=T.min_month_roi.gt(100)
    candidates=T[T.all_months_positive].copy()
    rec=(candidates.sort_values(['max_drawdown_yen','R','roi_pct'],ascending=[True,False,False]).iloc[0]
         if len(candidates) else T.sort_values(['max_drawdown_yen','R'],ascending=[True,False]).iloc[0])

    lines=['# v290 Top4 composite-odds floor risk audit','',
           '- Base: v283 fixed Top4, 10,000 yen exact inverse-odds Dutch.',
           '- Audited floors only: **6.0 / 7.0 / 8.0**. No threshold search beyond these three.',
           '- Apr-Jun only; Jul/Aug excluded; September outcomes not read.',
           '- Archived odds are retrospective proxy; this remains development evidence.','',
           '## Overall risk / return','',
           '|floor|R|coverage|4-head rate|hit rate|profit|ROI|max DD|max miss streak|max losing-bet streak|worst 5 bets|worst 10 bets|min month ROI|',
           '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in T.sort_values('floor').iterrows():
        lines.append(f'|{r.floor:.1f}|{int(r.R)}|{r.coverage_pct:.1f}%|{r.head4_rate_pct:.1f}%|{r.hit_rate_pct:.1f}%|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{r.max_drawdown_yen:.0f}|{int(r.max_consecutive_misses)}|{int(r.max_consecutive_losing_bets)}|{r.worst_5bet_pnl_yen:+.0f}|{r.worst_10bet_pnl_yen:+.0f}|{r.min_month_roi:.2f}%|')

    lines += ['','## Monthly','',
              '|floor|month|R|4-head rate|hits|profit|ROI|max DD|max miss streak|',
              '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in M.sort_values(['floor','month']).iterrows():
        lines.append(f'|{r.floor:.1f}|{r.month}|{int(r.R)}|{r.head4_rate_pct:.1f}%|{int(r.hits)}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{r.max_drawdown_yen:.0f}|{int(r.max_consecutive_misses)}|')

    lines += ['','## S / A split','',
              '|floor|layer|R|4-head rate|hits|profit|ROI|max DD|max miss streak|',
              '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in L.sort_values(['floor','layer']).iterrows():
        lines.append(f'|{r.floor:.1f}|{r.layer}|{int(r.R)}|{r.head4_rate_pct:.1f}%|{int(r.hits)}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{r.max_drawdown_yen:.0f}|{int(r.max_consecutive_misses)}|')

    lines += ['','## Venue split','',
              'Small venue cells are descriptive only. R>=3 cells shown first; do not create venue filters from this table.','',
              '|floor|venue|R|4-head wins|hits|profit|ROI|',
              '|---:|---|---:|---:|---:|---:|---:|']
    for fl in FLOORS:
        vv=V[(V.floor==fl)&(V.R>=3)].sort_values(['R','venue'],ascending=[False,True])
        for _,r in vv.iterrows():
            lines.append(f'|{r.floor:.1f}|{r.venue}|{int(r.R)}|{int(r.head4_wins)}|{int(r.hits)}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')

    lines += ['','## Risk read','',
              f'- Descriptive risk-balanced candidate among only 6/7/8: **floor >= {rec.floor:.1f}** (R={int(rec.R)}, ROI={rec.roi_pct:.2f}%, max DD={rec.max_drawdown_yen:.0f} yen, min-month ROI={rec.min_month_roi:.2f}%).',
              '- This is not a formal freeze: all three candidates were already motivated by Apr-Jun diagnostics, so prospective validation still requires an immutable pre-deadline odds snapshot.',
              '- Prefer a threshold that preserves enough bets and survives month/layer/venue concentration rather than simply choosing the highest retrospective ROI.']
    SUM.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))

if __name__=='__main__':main()
