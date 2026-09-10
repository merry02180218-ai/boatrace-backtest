#!/usr/bin/env python3
"""v288: composite-odds band economics and floor-based variable N for v283.

Purpose
-------
v287 showed that choosing N by distance to the inherited target 10.5 mostly
collapsed to the minimum candidate N.  v288 therefore asks a more useful market
question while keeping the independent v283 opponent order fixed:

1) For each fixed Top-N (N=2..20), what is realized ROI inside pre-defined
   composite-odds bands?
2) Does a floor rule work better: choose the LARGEST N whose composite odds stay
   at or above a required floor?  This lets a high-odds race broaden coverage,
   while stopping early when adding tickets makes the Dutch basket too short.

Discipline
----------
* v283 opponent ranking is unchanged and completely independent of v96.
* S/A head selectors are unchanged; S priority, A only outside S.
* July/August excluded; September outcomes are not read.
* N is chosen only from the fixed opponent order + archived odds, never result.
* Every BET race costs exactly 10,000 yen; miss payout=0.
* Inverse-odds Dutch with 100-yen Hamilton rounding.
* Archived odds are retrospective settlement/selection proxy only.  All v288
  floor comparisons are development diagnostics, NOT prospective OOS and NOT a
  newly frozen production rule.
"""
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v285_4head_independent_newroi_topn as v285
import analyze_v286_4head_variable_n_dutch as v286
import analyze_v287_4head_composite_odds_variable_n as v287
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
DETAIL=ROOT/'analysis_v288_4head_composite_odds_alln_detail.csv'
CELLS=ROOT/'analysis_v288_4head_composite_odds_band_cells.csv'
CELLM=ROOT/'analysis_v288_4head_composite_odds_band_monthly.csv'
FLOOR=ROOT/'analysis_v288_4head_composite_floor_policies.csv'
FLOORM=ROOT/'analysis_v288_4head_composite_floor_monthly.csv'
FLOORD=ROOT/'analysis_v288_4head_composite_floor_detail.csv'
VERIFY=ROOT/'analysis_v288_4head_fixed4_verify.csv'
SUM=ROOT/'summary_v288_4head_composite_odds_band_floor.md'
BANK=10000
NS=tuple(range(2,21))
FLOORS=(3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0)
MAXNS=(10,20)

# Pre-defined before looking at v288 cell outcomes.  Fine enough to distinguish
# the 4-8x region seen in v285/v287, while retaining a tail above 10x.
BANDS=(
    (-np.inf,3.0,'<3'),
    (3.0,4.0,'3-4'),
    (4.0,5.0,'4-5'),
    (5.0,6.0,'5-6'),
    (6.0,8.0,'6-8'),
    (8.0,10.0,'8-10'),
    (10.0,12.0,'10-12'),
    (12.0,15.0,'12-15'),
    (15.0,np.inf,'15+'),
)


def band(x):
    x=float(x)
    for lo,hi,name in BANDS:
        if x>=lo and x<hi:return name
    return 'NA'


def odds_row(oi,code):
    if code not in oi.index:return None
    r=oi.loc[code]
    return r.iloc[-1] if isinstance(r,pd.DataFrame) else r


def agg(g):
    cost=len(g)*BANK;ret=float(g.return_yen.sum())
    return {
        'R':len(g),
        'head4_wins':int(g.head4_win.sum()),
        'hits':int(g.hit.sum()),
        'head4_rate_pct':100*g.head4_win.mean() if len(g) else np.nan,
        'hit_rate_pct':100*g.hit.mean() if len(g) else np.nan,
        'avg_comp':g.comp_odds.mean() if len(g) else np.nan,
        'return_yen':ret,
        'profit_yen':ret-cost,
        'roi_pct':100*ret/cost if cost else np.nan,
    }


def build_alln():
    port=v286.hold_portfolio().copy();port['race_code']=port.race_code.astype(str).str.zfill(12)
    orders=v287.infer_orders(port)['v283']
    am=v287.actual_map();od=load_odds();oi=od.set_index('race_code',drop=False)
    rows=[];missing=[]
    for _,r in port.iterrows():
        code=str(r.race_code);a=am.get(code);odr=odds_row(oi,code)
        if not a or a[3]!=1 or odr is None:
            missing.append(code);continue
        order=orders.get(code)
        if order is None:missing.append(code);continue
        for n in NS:
            z=v287.comp_for(order,n,odr)
            if z is None:raise RuntimeError(f'invalid odds {code} N{n}')
            comp,tickets,_=z
            st=v287.settle_tickets(tickets,odr,a)
            if st is None:raise RuntimeError(f'settle failed {code} N{n}')
            hit,ret,_=st
            rows.append({
                'date':r.date,'month':r.month,'race_code':code,'layer':r.layer,
                'n':n,'winner':a[0],'second':a[1],'third':a[2],
                'head4_win':int(a[0]==4),'hit':int(hit),'return_yen':float(ret),
                'profit_yen':float(ret-BANK),'comp_odds':float(comp),'comp_band':band(comp),
                'tickets':'|'.join(tickets)
            })
    if missing:raise RuntimeError(f'missing evaluable portfolio races: {len(missing)}')
    q=pd.DataFrame(rows)
    if q.race_code.nunique()!=len(port):raise RuntimeError('portfolio coverage mismatch')
    q.to_csv(DETAIL,index=False)
    return q


def cell_tables(q):
    rows=[];mr=[]
    for (n,b),g in q.groupby(['n','comp_band'],sort=False):
        rows.append({'n':int(n),'comp_band':b,**agg(g)})
        for mon,gg in g.groupby('month'):
            mr.append({'n':int(n),'comp_band':b,'month':mon,**agg(gg)})
    C=pd.DataFrame(rows);C.to_csv(CELLS,index=False)
    M=pd.DataFrame(mr);M.to_csv(CELLM,index=False)
    return C,M


def choose_floor(g,floor,maxn):
    # largest N that preserves required composite-odds floor; if even N2 is
    # below the floor, N2 is the deterministic fallback (never skip a frozen BET).
    h=g[g.n<=int(maxn)].sort_values('n')
    ok=h[h.comp_odds>=float(floor)]
    return ok.iloc[-1] if len(ok) else h.iloc[0]


def floor_tables(q):
    detail=[]
    for code,g in q.groupby('race_code'):
        for maxn in MAXNS:
            for fl in FLOORS:
                r=choose_floor(g,fl,maxn)
                detail.append({
                    'date':r.date,'month':r.month,'race_code':code,'layer':r.layer,
                    'floor':fl,'max_n':maxn,'n':int(r.n),'comp_odds':float(r.comp_odds),
                    'head4_win':int(r.head4_win),'hit':int(r.hit),'return_yen':float(r.return_yen),
                    'profit_yen':float(r.return_yen-BANK),'comp_band':r.comp_band,
                    'fallback_n2':int(int(r.n)==2 and float(r.comp_odds)<fl)
                })
    D=pd.DataFrame(detail);D.to_csv(FLOORD,index=False)
    rows=[];mr=[]
    for (maxn,fl),g in D.groupby(['max_n','floor']):
        a=agg(g);dist=','.join(f'{int(n)}:{int(c)}' for n,c in g.n.value_counts().sort_index().items())
        rows.append({'scope':'S+A','max_n':int(maxn),'floor':fl,'avg_n':g.n.mean(),'n_dist':dist,
                     'fallback_n2':int(g.fallback_n2.sum()),**a})
        for layer,gg in g.groupby('layer'):
            aa=agg(gg);dd=','.join(f'{int(n)}:{int(c)}' for n,c in gg.n.value_counts().sort_index().items())
            rows.append({'scope':layer,'max_n':int(maxn),'floor':fl,'avg_n':gg.n.mean(),'n_dist':dd,
                         'fallback_n2':int(gg.fallback_n2.sum()),**aa})
        for mon,gg in g.groupby('month'):
            aa=agg(gg);dd=','.join(f'{int(n)}:{int(c)}' for n,c in gg.n.value_counts().sort_index().items())
            mr.append({'month':mon,'max_n':int(maxn),'floor':fl,'avg_n':gg.n.mean(),'n_dist':dd,
                       'fallback_n2':int(gg.fallback_n2.sum()),**aa})
    O=pd.DataFrame(rows);O.to_csv(FLOOR,index=False)
    M=pd.DataFrame(mr);M.to_csv(FLOORM,index=False)
    return O,M,D


def verify_fixed4(q):
    g=q[q.n==4];newret=float(g.return_yen.sum());newroi=100*newret/(len(g)*BANK)
    old=pd.read_csv(v285.OUT)
    r=old[(old.scope=='S+A')&(old.model=='v283')&(old.n==4)].iloc[0]
    V=pd.DataFrame([{'R':len(g),'new_return':newret,'v285_return':float(r.return_yen),
                     'return_diff':newret-float(r.return_yen),'new_roi':newroi,
                     'v285_roi':float(r.roi_pct),'roi_diff':newroi-float(r.roi_pct)}])
    V.to_csv(VERIFY,index=False)
    if abs(float(V.return_diff.iloc[0]))>1e-6:raise RuntimeError('fixed N4 verification failed')
    return V


def main():
    q=build_alln();C,CM=cell_tables(q);O,M,D=floor_tables(q);V=verify_fixed4(q)
    sa=O[O.scope=='S+A'].copy()
    monthly_floor=M.groupby(['max_n','floor']).roi_pct.min().rename('min_month_roi').reset_index()
    sa=sa.merge(monthly_floor,on=['max_n','floor'],how='left')
    best_roi=sa.sort_values(['roi_pct','min_month_roi'],ascending=False).iloc[0]
    best_floor=sa.sort_values(['min_month_roi','roi_pct'],ascending=False).iloc[0]

    # Cells with enough support to be interpretable; this is descriptive only.
    stable=C[C.R>=10].sort_values(['roi_pct','R'],ascending=[False,False])

    L=['# v288 composite-odds bands + floor-based variable N (v283)','',
       '- v283 opponent order and S/A head selectors are unchanged.',
       '- Every BET race is exactly 10,000 yen; inverse-odds Dutch / 100-yen Hamilton; miss payout 0.',
       '- N selection uses only fixed opponent order + archived odds, never result/payout.',
       '- Jul/Aug excluded; September outcomes not read.',
       '- Archived odds are retrospective proxy. The floor grid is development diagnostics only and is **not** a frozen prospective rule.','',
       '## Verification','',
       f'- Fixed v283 Top4 reproduced v285 exactly: return **{V.new_return.iloc[0]:.0f} yen**, ROI **{V.new_roi.iloc[0]:.2f}%**, diff **{V.return_diff.iloc[0]:+.0f} yen**.','',
       '## Composite-odds band diagnostics (cells with R>=10)','',
       '|N|comp band|R|4-head wins|hits|hit rate|avg comp|profit|ROI|',
       '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in stable.head(40).iterrows():
        L.append(f'|{int(r.n)}|{r.comp_band}|{int(r.R)}|{int(r.head4_wins)}|{int(r.hits)}|{r.hit_rate_pct:.1f}%|{r.avg_comp:.2f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')

    L += ['','## Floor-rule S+A grid','',
          'Rule: choose the **largest N** up to maxN whose composite odds stay >= floor; if even N2 is below floor, use N2.','',
          '|maxN|floor|R|avg N|N distribution|hits|avg comp|profit|ROI|min monthly ROI|',
          '|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|']
    for _,r in sa.sort_values(['max_n','floor']).iterrows():
        L.append(f'|{int(r.max_n)}|{r.floor:.1f}|{int(r.R)}|{r.avg_n:.2f}|{r.n_dist}|{int(r.hits)}|{r.avg_comp:.2f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|{r.min_month_roi:.2f}%|')

    L += ['','## S / A split for the aggregate-ROI leader','',
          f'- Exploratory leader: maxN={int(best_roi.max_n)}, floor={best_roi.floor:.1f}, S+A ROI **{best_roi.roi_pct:.2f}%**, monthly floor **{best_roi.min_month_roi:.2f}%**.','',
          '|scope|R|avg N|hits|profit|ROI|','|---|---:|---:|---:|---:|---:|']
    for _,r in O[(O.max_n==best_roi.max_n)&(O.floor==best_roi.floor)].sort_values('scope').iterrows():
        L.append(f'|{r.scope}|{int(r.R)}|{r.avg_n:.2f}|{int(r.hits)}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')

    L += ['','## Monthly S+A for aggregate-ROI leader','',
          '|month|R|avg N|hits|avg comp|profit|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for _,r in M[(M.max_n==best_roi.max_n)&(M.floor==best_roi.floor)].sort_values('month').iterrows():
        L.append(f'|{r.month}|{int(r.R)}|{r.avg_n:.2f}|{int(r.hits)}|{r.avg_comp:.2f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')

    L += ['','## Development read','',
          f'- Highest aggregate ROI in the exploratory floor grid: **maxN={int(best_roi.max_n)}, floor={best_roi.floor:.1f}, ROI={best_roi.roi_pct:.2f}%**.',
          f'- Highest minimum-month ROI in the same exploratory grid: **maxN={int(best_floor.max_n)}, floor={best_floor.floor:.1f}, min-month={best_floor.min_month_roi:.2f}%, aggregate={best_floor.roi_pct:.2f}%**.',
          '- Do not promote either cell directly from this Apr-Jun scan. Use the band/floor evidence to define one simple v289 candidate, then freeze it before any prospective/live evaluation.',
          '- For live use, the floor must be applied to one immutable pre-deadline odds snapshot; closing/archive odds are not equivalent to formal OOS.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
