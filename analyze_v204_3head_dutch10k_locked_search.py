#!/usr/bin/env python3
"""v204: search 3-head filters using audited 10,000-yen Dutch ROI.
Discovery 2025-12..2026-02; locked test 2026-03..2026-06.
Uses v202 audited per-race Dutch settlements; odds never select races/tickets.
"""
from pathlib import Path
from itertools import product
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parent
DUTCH=ROOT/'analysis_v202_3head_dutch10k_roi.csv'
BASE=ROOT/'analysis_v198_3head_long_history_base.csv'
FEAT=ROOT/'analysis_v108_1head_feasibility.csv'
OUT=ROOT/'analysis_v204_3head_dutch10k_locked_search.csv'
SUM=ROOT/'summary_v204_3head_dutch10k_locked_search.md'
P3=[.30,.325,.35,.375,.40,.425,.45]
TURN=[None,-.4,-.2,0.0,.2]
ST=[None,-.2,0.0,.2]
STRAIGHT=[None,-.2,0.0,.2]
EX=[None,-.2,0.0,.2]
MIN_DISC=15; TOPK=15

def stat(g):
    if g.empty:return dict(R=0,hit=0,comp=0,cost=0,ret=0,roi=0)
    cost=float(g.cost.sum()); ret=float(g['return'].sum())
    return dict(R=len(g),hit=100*g.hit.mean(),comp=g.composite_odds.mean(),cost=cost,ret=ret,roi=100*ret/cost if cost else 0)

def active(v):
    return v is not None and not pd.isna(v)

def apply(d,r):
    q=d[d.p3head>=r['p3']]
    for col,key in [('turn_margin23','turn'),('st_margin23','st'),('straight_margin23','straight'),('ex_margin23','ex')]:
        if active(r[key]):q=q[pd.to_numeric(q[col],errors='coerce')>=float(r[key])]
    return q

def text(r):
    a=[f"p3>={r['p3']:.3f}"]
    for k,label in [('turn','turn'),('st','ST'),('straight','straight'),('ex','EX')]:
        if active(r[k]):a.append(f"{label}>={float(r[k]):.1f}")
    return ' & '.join(a)

def main():
    z=pd.read_csv(DUTCH,dtype={'race_code':str})
    b=pd.read_csv(BASE,dtype={'race_code':str},usecols=['race_code','p3head'])
    f=pd.read_csv(FEAT,dtype={'race_code':str},usecols=['race_code','ex_margin23','st_margin23','straight_margin23','turn_margin23']).drop_duplicates('race_code',keep='last')
    d=z.merge(b.drop_duplicates('race_code'),on='race_code',how='left').merge(f,on='race_code',how='left',suffixes=('','_feat'))
    if 'turn_margin23_feat' in d.columns:d['turn_margin23']=d['turn_margin23_feat'].combine_first(d['turn_margin23'])
    disc=d[(d.month>='2025-12')&(d.month<='2026-02')].copy(); test=d[(d.month>='2026-03')&(d.month<='2026-06')].copy()
    rows=[]
    for p3,turn,st,straight,ex in product(P3,TURN,ST,STRAIGHT,EX):
        r=dict(p3=p3,turn=turn,st=st,straight=straight,ex=ex); g=apply(disc,r)
        if len(g)<MIN_DISC:continue
        m=stat(g)
        score=m['roi'] + .08*min(m['R'],100) + .05*m['hit']
        rows.append({**r,'rule':text(r),'disc_R':m['R'],'disc_hit':m['hit'],'disc_comp':m['comp'],'disc_roi':m['roi'],'score':score})
    grid=pd.DataFrame(rows).sort_values(['score','disc_roi','disc_R'],ascending=False)
    selected=[]; seen=set()
    for _,rr in grid.iterrows():
        r=rr.to_dict(); key=tuple(sorted(apply(disc,r).race_code.tolist()))
        if key in seen:continue
        seen.add(key); selected.append(r)
        if len(selected)>=TOPK:break
    out=[]
    for rank,r in enumerate(selected,1):
        md=stat(apply(disc,r)); mt=stat(apply(test,r))
        out.append(dict(rank=rank,rule=r['rule'],disc_R=md['R'],disc_hit=md['hit'],disc_comp=md['comp'],disc_roi=md['roi'],test_R=mt['R'],test_hit=mt['hit'],test_comp=mt['comp'],test_roi=mt['roi']))
    od=pd.DataFrame(out); od.to_csv(OUT,index=False)
    bd=stat(disc); bt=stat(test)
    L=['# v204 3-head audited Dutch10k discovery -> locked test','',
       '- ROI definition: exactly 10,000 yen/race, equal-gross Dutch, 100-yen rounding','- source settlement: corrected official closing odds from v202/v203 audit',
       '- discovery: 2025-12..2026-02 only','- locked test: 2026-03..2026-06 only','- test is never used for rule ranking','- exploratory/SHADOW only; production unchanged','',
       '## Baseline','|segment|R|hit|avg composite odds|ROI|','|---|---:|---:|---:|---:|',
       f"|DISCOVERY BASE|{bd['R']}|{bd['hit']:.2f}%|{bd['comp']:.3f}|{bd['roi']:.1f}%|",f"|LOCKED TEST BASE|{bt['R']}|{bt['hit']:.2f}%|{bt['comp']:.3f}|{bt['roi']:.1f}%|",'',
       '## Top discovery rules, frozen on locked test','|rank|rule|Disc R|Disc hit|Disc comp|Disc ROI|Test R|Test hit|Test comp|Test ROI|','|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in out:L.append(f"|{x['rank']}|{x['rule']}|{x['disc_R']}|{x['disc_hit']:.2f}%|{x['disc_comp']:.3f}|{x['disc_roi']:.1f}%|{x['test_R']}|{x['test_hit']:.2f}%|{x['test_comp']:.3f}|{x['test_roi']:.1f}%|")
    good=[x for x in out if x['test_R']>=20 and x['test_roi']>=100]
    L+=['','## Interpretation']
    if good:
        L.append(f"- {len(good)} rule(s) cleared provisional locked-test screen: Test R>=20 and audited Dutch ROI>=100%.")
        L.append('- Treat only as SHADOW candidates because this feature family has prior historical inspection; do not production-adopt from v204 alone.')
    else:
        L.append('- No rule cleared Test R>=20 and audited Dutch ROI>=100%. Keep v165/v166 production unchanged.')
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__':main()
