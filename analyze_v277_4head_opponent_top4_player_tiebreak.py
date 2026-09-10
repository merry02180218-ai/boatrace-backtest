#!/usr/bin/env python3
"""v277: preserve v96 Top4 membership, use player history only as an internal tiebreak.

Rationale
---------
v274-v276 show that player-history is real signal for SECOND, but replacing the
v96 pair ranking damages small-N coverage.  This audit keeps the exact v96 Top4
pair set and only reorders those four pairs with a SECOND-role player-history
score.  Therefore pair Top4/Top6/Top10 coverage is mathematically unchanged;
only Top1/Top2/Top3 ordering can move.

Discipline
----------
* Jul/Aug excluded; September not read.
* Alpha is chosen using Feb-Mar only.
* Apr-Jun is untouched by alpha selection and reported as holdout-like evidence.
* v268/v273 head selectors are unchanged.
* No odds are used in ranking or alpha selection.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v275_4head_opponent_player_blend as v275
import analyze_v270_4head_win_feature_importance as v270
import analyze_v96_4corner_monthly_walkforward_tiebreak as v96

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v277_4head_opponent_top4_player_tiebreak.csv'
MONTH=ROOT/'analysis_v277_4head_opponent_top4_player_tiebreak_monthly.csv'
SUM=ROOT/'summary_v277_4head_opponent_top4_player_tiebreak.md'
BOATS=v274.BOATS
TUNE=('2026-02','2026-03')
HOLD=('2026-04','2026-05','2026-06')
MONTHS=TUNE+HOLD
ALPHAS=(0.0,0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50,0.75,1.00)
TOPK=4


def pair_scores(c2,c3):
    z=[]
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            z.append((float(c2[s])+float(c3[t]),s,t))
    z.sort(key=lambda x:(-x[0],x[1],x[2]))
    return z


def reorder_top4(c2,c3,p2,alpha):
    base=pair_scores(c2,c3)
    top=base[:TOPK]
    rest=base[TOPK:]
    # Only SECOND-role player-history signal is added. Third stays pure v96.
    rescored=[]
    for bs,s,t in top:
        rescored.append((bs+alpha*float(p2[s]),s,t))
    rescored.sort(key=lambda x:(-x[0],x[1],x[2]))
    return [(s,t) for _,s,t in rescored]+[(s,t) for _,s,t in rest]


def prank(order,actual):
    try:return order.index(actual)+1
    except ValueError:return 0


def build_cases():
    d,_,_=v270.prepare();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    specs=v274.feature_specs(d);long=v274.build_long(d,specs)
    fam=v274.families(specs)
    # BASE7_PLAYER produces the strong SECOND player-history score found in v274.
    rs=v96.read();cur=v275.current_role_maps(rs);pl=v275.player_prob_maps(long,fam['BASE7_PLAYER'])
    sel=v274.selected_codes()
    rec=[]
    for code,g in long[long.month.isin(MONTHS)].groupby('race_code'):
        if len(g)!=5:continue
        key=(str(g.date.iloc[0]),str(code).zfill(12))
        if key not in cur or key not in pl:continue
        a2=int(g.loc[g.y2==1,'boat'].iloc[0]);a3=int(g.loc[g.y3==1,'boat'].iloc[0])
        c2,c3=cur[key];p2,_=pl[key]
        rec.append({'date':key[0],'month':key[0][:7],'race_code':key[1],
                    'actual':(a2,a3),'c2':c2,'c3':c3,'p2':p2,
                    'selected_SA':int(key[1] in sel)})
    return rec


def evaluate(cases,alpha,months,selected=False):
    ranks=[]
    for r in cases:
        if r['month'] not in months:continue
        if selected and not r['selected_SA']:continue
        ranks.append(prank(reorder_top4(r['c2'],r['c3'],r['p2'],alpha),r['actual']))
    n=len(ranks);o={'races':n}
    for k in (1,2,3,4,6,10,20):
        o[f'top{k}_pct']=100*sum(1<=x<=k for x in ranks)/n if n else np.nan
    return o


def main():
    cases=build_cases()
    tune=[]
    for a in ALPHAS:
        m=evaluate(cases,a,TUNE)
        # Top4 is invariant by construction. Tune for Top2 first, then Top1/Top3,
        # and prefer the smaller alpha on exact ties.
        obj=0.65*m['top2_pct']+0.25*m['top1_pct']+0.10*m['top3_pct']
        tune.append({'alpha':a,'objective':obj,**m})
    td=pd.DataFrame(tune)
    best=td.sort_values(['objective','top2_pct','top1_pct','top3_pct','alpha'],
                        ascending=[False,False,False,False,True]).iloc[0]
    alpha=float(best.alpha)

    rows=[]
    for scope,mons,selected in [('TUNE_ALL',TUNE,False),('HOLD_ALL',HOLD,False),('HOLD_SA',HOLD,True)]:
        for name,a in [('V96',0.0),('TOP4_PLAYER_TB',alpha)]:
            rows.append({'scope':scope,'model':name,'alpha':a,**evaluate(cases,a,mons,selected)})
    out=pd.DataFrame(rows);out.to_csv(OUT,index=False)

    monthly=[]
    for mon in HOLD:
        for selected in (False,True):
            for name,a in [('V96',0.0),('TOP4_PLAYER_TB',alpha)]:
                monthly.append({'month':mon,'scope':'SA' if selected else 'ALL','model':name,
                                'alpha':a,**evaluate(cases,a,(mon,),selected)})
    mm=pd.DataFrame(monthly);mm.to_csv(MONTH,index=False)

    def rr(scope,name):return out[(out.scope==scope)&(out.model==name)].iloc[0]
    L=['# v277 4-head opponent Top4 player-history tiebreak','',
       '- Exact v96 Top4 pair membership is preserved; only ordering inside Top4 may change.',
       '- Extra signal is SECOND-role BASE7_PLAYER score only; THIRD remains v96.',
       '- Alpha selected on Feb-Mar only; Apr-Jun not used for alpha selection.',
       '- Jul/Aug excluded; September not read; no odds used.',
       '- v268/v273 head selectors unchanged.','',
       '## Feb-Mar alpha choice','',
       f'- chosen alpha: **{alpha:.2f}**',
       '|alpha|R|Top1|Top2|Top3|Top4|objective|',
       '|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in td.iterrows():
        L.append(f'|{r.alpha:.2f}|{int(r.races)}|{r.top1_pct:.1f}%|{r.top2_pct:.1f}%|{r.top3_pct:.1f}%|{r.top4_pct:.1f}%|{r.objective:.2f}|')
    L += ['','## Apr-Jun comparison','',
          '|scope|model|R|Top1|Top2|Top3|Top4|Top6|Top10|',
          '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for scope in ('HOLD_ALL','HOLD_SA'):
        for name in ('V96','TOP4_PLAYER_TB'):
            r=rr(scope,name);L.append(f'|{scope}|{name}|{int(r.races)}|{r.top1_pct:.1f}%|{r.top2_pct:.1f}%|{r.top3_pct:.1f}%|{r.top4_pct:.1f}%|{r.top6_pct:.1f}%|{r.top10_pct:.1f}%|')
    L += ['','## S+A monthly stability','',
          '|month|model|R|Top1|Top2|Top4|Top6|Top10|',
          '|---|---|---:|---:|---:|---:|---:|---:|']
    for _,r in mm[mm.scope=='SA'].iterrows():
        L.append(f'|{r.month}|{r.model}|{int(r.races)}|{r.top1_pct:.1f}%|{r.top2_pct:.1f}%|{r.top4_pct:.1f}%|{r.top6_pct:.1f}%|{r.top10_pct:.1f}%|')
    b=rr('HOLD_SA','V96');n=rr('HOLD_SA','TOP4_PLAYER_TB')
    L += ['','## Decision',
          f'- S+A delta: Top1 {n.top1_pct-b.top1_pct:+.1f}pt, Top2 {n.top2_pct-b.top2_pct:+.1f}pt, Top3 {n.top3_pct-b.top3_pct:+.1f}pt.',
          '- Top4/Top6/Top10 are intentionally preserved by construction.',
          '- Only if Top2 improves without unstable month behavior should this proceed to an exact new-ROI ticket-order test. Otherwise retain pure v96.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
