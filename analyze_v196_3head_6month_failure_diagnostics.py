#!/usr/bin/env python3
"""v196: diagnose where v195 production ROI is lost, without changing production.
Joins v195 frozen selections to canonical v108 features and reports pre-result segment metrics.
This is diagnosis, not a production filter selection. Avoid post-hoc adoption.
"""
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parent
BT=ROOT/'analysis_v195_3head_production_6month_backtest.csv'
SRC=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v196_3head_6month_failure_diagnostics.csv'
SUM=ROOT/'summary_v196_3head_6month_failure_diagnostics.md'

def metric(g):
    if len(g)==0:return None
    h=g[g.y3head==1]; s=g[g.valid_payout==1]
    cost=s.cost_yen.sum(); ret=s.return_yen.sum()
    return [len(g),100*g.y3head.mean(),100*g.hit.mean(),100*h.hit.mean() if len(h) else 0,cost,ret,100*ret/cost if cost else 0]
def line(label,g):
    m=metric(g);return f'|{label}|{m[0]}|{m[1]:.2f}%|{m[2]:.2f}%|{m[3]:.2f}%|{m[4]:.0f}|{m[5]:.0f}|{m[6]:.1f}%|'
def main():
    b=pd.read_csv(BT); s=pd.read_csv(SRC,low_memory=False)
    # v195 race_code/date identify frozen candidate rows
    keep=['date','race_code','venue','race']+[c for c in ['grade3','wr3','local3','motor3','waku_wr3','waku_sr_strength3','nst_strength3','past_win3','meet_st_strength3','threat1','threat2','threat4','threat5','threat6','margin2','margin_all','st_margin23','ex_margin23','turn_margin23','straight_margin23','one_score'] if c in s.columns]
    z=b.merge(s[keep].drop_duplicates(['date','race_code']),on=['date','race_code'],how='left')
    z.to_csv(OUT,index=False)
    L=['# v196 3号艇 6か月 failure diagnostics','', '- source: v195 frozen production candidates; no ticket re-ranking', '- segments use only pre-result/direct features; payout only settlement', '- IMPORTANT: descriptive diagnosis only. Do not adopt a filter from these same six months without forward validation.','','## Month','|segment|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for mon,g in z.groupby('month'):L.append(line(str(mon),g))
    L += ['','## p3head bands','|segment|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    bins=[.30,.325,.35,.375,.40,.45,.50,1.01]
    for a,c in zip(bins[:-1],bins[1:]):
        g=z[(z.p3head>=a)&(z.p3head<c)];
        if len(g):L.append(line(f'{a:.3f}-{c:.3f}',g))
    if 'venue' in z:
        L += ['','## Venue (min 8 candidates)','|segment|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|']
        vals=[]
        for v,g in z.groupby('venue'):
            if len(g)>=8: vals.append((metric(g)[-1],str(v).zfill(2),g))
        for _,v,g in sorted(vals):L.append(line(v,g))
    # Numeric feature quartiles: report bottom/top quartile only to locate structural weaknesses.
    feats=[c for c in ['threat1','threat2','threat4','threat5','threat6','margin2','margin_all','st_margin23','ex_margin23','turn_margin23','straight_margin23','one_score'] if c in z]
    L += ['','## Pre-result feature tails (Q1 / Q4)','|segment|R|3-head|hit|Top10 cov|cost|return|ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for c in feats:
        q=pd.to_numeric(z[c],errors='coerce');lo=q.quantile(.25);hi=q.quantile(.75)
        for lab,g in [(f'{c} Q1 <= {lo:.3f}',z[q<=lo]),(f'{c} Q4 >= {hi:.3f}',z[q>=hi])]:
            if len(g):L.append(line(lab,g))
    # rank of winning combo within Top10 where hit; useful to diagnose ticket count, not outcome-selected filters.
    ranks=[]
    for _,r in z.iterrows():
        ts=str(r.top10).split(';'); act=str(r.actual_combo); ranks.append(ts.index(act)+1 if act in ts else 0)
    z['hit_rank']=ranks
    L += ['','## Winning ticket rank among frozen Top10','|rank|hits|share of all candidates|','|---:|---:|---:|']
    for k in range(1,11):
        n=int((z.hit_rank==k).sum());L.append(f'|{k}|{n}|{100*n/len(z):.2f}%|')
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':main()
