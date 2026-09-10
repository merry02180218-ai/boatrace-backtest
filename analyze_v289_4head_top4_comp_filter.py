#!/usr/bin/env python3
"""v289: use v283 fixed Top4 composite odds as a one-dimensional market filter.

Purpose
-------
v288 suggested that fixed Top4 composite odds may carry information about both
boat-4 head strength and basket value.  v289 keeps everything else fixed and
asks only whether Top4 composite odds can filter BET races profitably.

Discipline
----------
* Base ticket set is ALWAYS v283 Top4. No variable N.
* The only candidate filter is Top4 composite odds from archived odds.
* July/August excluded; September outcomes not read.
* Archived odds are retrospective proxy only; this is development diagnostics.
* Every selected BET race costs exactly 10,000 yen, inverse-odds Dutch / 100-yen
  Hamilton. Miss payout 0.
* Do not promote a threshold directly from this Apr-Jun scan.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import analyze_v285_4head_independent_newroi_topn as v285
import analyze_v288_4head_composite_odds_band_floor as v288

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
BANDS=ROOT/'analysis_v289_4head_top4_comp_bands.csv'
FLOORS=ROOT/'analysis_v289_4head_top4_comp_floor.csv'
FLOORM=ROOT/'analysis_v289_4head_top4_comp_floor_monthly.csv'
LOMO=ROOT/'analysis_v289_4head_top4_comp_lomo.csv'
VERIFY=ROOT/'analysis_v289_4head_top4_comp_verify.csv'
SUM=ROOT/'summary_v289_4head_top4_comp_filter.md'
BANK=10000
FLOOR_GRID=(3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,12.0,15.0)
MONTHS=('2026-04','2026-05','2026-06')
BAND_DEF=(
    (-np.inf,4.0,'<4'),
    (4.0,5.0,'4-5'),
    (5.0,6.0,'5-6'),
    (6.0,8.0,'6-8'),
    (8.0,10.0,'8-10'),
    (10.0,12.0,'10-12'),
    (12.0,15.0,'12-15'),
    (15.0,np.inf,'15+'),
)


def bname(x):
    x=float(x)
    for lo,hi,n in BAND_DEF:
        if x>=lo and x<hi:return n
    return 'NA'


def agg(g):
    cost=len(g)*BANK;ret=float(g.return_yen.sum())
    return {
        'R':len(g),'head4_wins':int(g.head4_win.sum()),'hits':int(g.hit.sum()),
        'head4_rate_pct':100*g.head4_win.mean() if len(g) else np.nan,
        'hit_rate_pct':100*g.hit.mean() if len(g) else np.nan,
        'avg_comp':g.comp_odds.mean() if len(g) else np.nan,
        'return_yen':ret,'profit_yen':ret-cost,
        'roi_pct':100*ret/cost if cost else np.nan,
    }


def load_top4():
    q=pd.read_csv(SRC,dtype={'race_code':str})
    q['race_code']=q.race_code.astype(str).str.zfill(12)
    q=q[q.n==4].copy()
    if q.race_code.nunique()!=100 or len(q)!=100:
        raise RuntimeError(f'expected exactly 100 unique Top4 rows, got {len(q)} / {q.race_code.nunique()}')
    q['comp_band']=q.comp_odds.map(bname)
    return q


def verify(q):
    old=pd.read_csv(v285.OUT)
    r=old[(old.scope=='S+A')&(old.model=='v283')&(old.n==4)].iloc[0]
    ret=float(q.return_yen.sum());roi=100*ret/(len(q)*BANK)
    V=pd.DataFrame([{'R':len(q),'new_return':ret,'v285_return':float(r.return_yen),
                     'return_diff':ret-float(r.return_yen),'new_roi':roi,
                     'v285_roi':float(r.roi_pct),'roi_diff':roi-float(r.roi_pct)}])
    V.to_csv(VERIFY,index=False)
    if abs(float(V.return_diff.iloc[0]))>1e-6:raise RuntimeError('Top4 verification failed')
    return V


def band_table(q):
    rows=[]
    for b,g in q.groupby('comp_band',sort=False):
        rows.append({'comp_band':b,**agg(g)})
    B=pd.DataFrame(rows);B.to_csv(BANDS,index=False);return B


def floor_tables(q):
    rows=[];mr=[]
    for fl in FLOOR_GRID:
        g=q[q.comp_odds>=fl].copy()
        rows.append({'floor':fl,'coverage_pct':100*len(g)/len(q),**agg(g)})
        for m in MONTHS:
            gg=g[g.month==m]
            mr.append({'floor':fl,'month':m,'coverage_pct':100*len(gg)/len(q[q.month==m]),**agg(gg)})
    F=pd.DataFrame(rows);F.to_csv(FLOORS,index=False)
    M=pd.DataFrame(mr);M.to_csv(FLOORM,index=False)
    return F,M


def lomo(q):
    rec=[]
    for hold in MONTHS:
        train=q[q.month!=hold]
        cand=[]
        for fl in FLOOR_GRID:
            g=train[train.comp_odds>=fl]
            # Keep enough support and at least 5 selected races in each training month.
            ok=len(g)>=20 and all(len(g[g.month==m])>=5 for m in MONTHS if m!=hold)
            if not ok:continue
            a=agg(g)
            # Favor profitability but penalize fragile coverage collapse.
            cand.append((a['roi_pct'],a['R'],fl,a))
        if not cand:continue
        cand.sort(key=lambda x:(-x[0],-x[1],x[2]))
        _,_,fl,tr_a=cand[0]
        te=q[(q.month==hold)&(q.comp_odds>=fl)]
        te_a=agg(te)
        rec.append({'holdout_month':hold,'chosen_floor':fl,'train_R':tr_a['R'],'train_roi_pct':tr_a['roi_pct'],
                    'hold_R':te_a['R'],'hold_head4_wins':te_a['head4_wins'],'hold_hits':te_a['hits'],
                    'hold_return_yen':te_a['return_yen'],'hold_profit_yen':te_a['profit_yen'],'hold_roi_pct':te_a['roi_pct']})
    L=pd.DataFrame(rec);L.to_csv(LOMO,index=False);return L


def main():
    q=load_top4();V=verify(q);B=band_table(q);F,M=floor_tables(q);L=lomo(q)
    try:
        auc=max(roc_auc_score(q.head4_win,q.comp_odds),1-roc_auc_score(q.head4_win,q.comp_odds))
    except Exception:auc=np.nan
    try:
        auc_hit=max(roc_auc_score(q.hit,q.comp_odds),1-roc_auc_score(q.hit,q.comp_odds))
    except Exception:auc_hit=np.nan

    f2=F.copy();mins=M.groupby('floor').roi_pct.min().rename('min_month_roi').reset_index();f2=f2.merge(mins,on='floor',how='left')
    viable=f2[f2.R>=20].copy()
    best=viable.sort_values(['roi_pct','R'],ascending=[False,False]).iloc[0]
    stable=viable.sort_values(['min_month_roi','roi_pct'],ascending=[False,False]).iloc[0]

    Ls=['# v289 fixed Top4 composite-odds filter (v283)','',
        '- Base tickets: **v283 Top4 fixed**. No variable N.',
        '- Only filter input: Top4 composite odds.',
        '- Every selected BET race costs 10,000 yen; exact Dutch economics retained.',
        '- Jul/Aug excluded; September outcomes not read.',
        '- Archived odds are retrospective proxy; this is exploratory development evidence, not prospective OOS.','',
        '## Verification','',
        f'- All 100 unfiltered races reproduce v285 Top4 exactly: return **{V.new_return.iloc[0]:.0f} yen**, ROI **{V.new_roi.iloc[0]:.2f}%**.','',
        '## Does Top4 composite odds contain signal?','',
        f'- Oriented AUC for boat-4 head result from composite odds alone: **{auc:.4f}**.',
        f'- Oriented AUC for exact trifecta hit from composite odds alone: **{auc_hit:.4f}**.','',
        '## Absolute composite-odds bands','',
        '|band|R|4-head wins|head rate|hits|hit rate|avg comp|profit|ROI|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    order=[x[2] for x in BAND_DEF]
    for b in order:
        x=B[B.comp_band==b]
        if x.empty:continue
        r=x.iloc[0];Ls.append(f'|{b}|{int(r.R)}|{int(r.head4_wins)}|{r.head4_rate_pct:.1f}%|{int(r.hits)}|{r.hit_rate_pct:.1f}%|{r.avg_comp:.2f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')

    Ls += ['','## Simple floor filter: BET only if Top4 composite odds >= floor','',
           '|floor|R|coverage|head rate|hits|hit rate|profit|ROI|min monthly ROI|',
           '|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in f2.iterrows():
        Ls.append(f'|{r.floor:.1f}|{int(r.R)}|{r.coverage_pct:.1f}%|{r.head4_rate_pct:.1f}%|{int(r.hits)}|{r.hit_rate_pct:.1f}%|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{r.min_month_roi:.2f}%|')

    Ls += ['','## LOMO floor robustness','',
           'For each held-out month, choose the floor using only the other two months (minimum support constraints), then apply it unchanged to the held-out month.','',
           '|holdout|chosen floor|train R|train ROI|hold R|hold hits|hold profit|hold ROI|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in L.iterrows():
        Ls.append(f'|{r.holdout_month}|{r.chosen_floor:.1f}|{int(r.train_R)}|{r.train_roi_pct:.2f}%|{int(r.hold_R)}|{int(r.hold_hits)}|{r.hold_profit_yen:+.0f}|{r.hold_roi_pct:.2f}%|')
    if len(L):
        cost=L.hold_R.sum()*BANK;ret=L.hold_return_yen.sum();roi=100*ret/cost if cost else np.nan
        Ls += ['',f'- Combined LOMO holdouts: **{int(L.hold_R.sum())} bets, return {ret:.0f} yen, ROI {roi:.2f}%**.']

    Ls += ['','## Development read','',
           f'- Best same-sample floor with R>=20: **>= {best.floor:.1f}**, R={int(best.R)}, ROI={best.roi_pct:.2f}%.',
           f'- Best minimum-month floor with R>=20: **>= {stable.floor:.1f}**, R={int(stable.R)}, aggregate ROI={stable.roi_pct:.2f}%, min-month={stable.min_month_roi:.2f}%.',
           '- Same-sample leaders are not production thresholds. The LOMO result is the more useful robustness check.',
           '- If LOMO is not clearly positive/stable, keep unfiltered Top4 as the stronger current baseline rather than forcing an odds filter.']
    SUM.write_text('\n'.join(Ls)+'\n',encoding='utf-8');print('\n'.join(Ls))

if __name__=='__main__':main()
