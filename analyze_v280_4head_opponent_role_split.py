#!/usr/bin/env python3
"""v280: independent role-split opponent model for 4-head races.

Builds on v279's NEW listwise framework, not on v96.  SECOND and THIRD choose
feature family and regularization independently on Feb-Mar. Pair composition is
also chosen on Feb-Mar, then frozen for Apr-Jun evaluation.

v96 is benchmark-only after new predictions are frozen.
Jul/Aug excluded; September not read; no odds in training or ordering.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.special import logsumexp

import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v270_4head_win_feature_importance as v270

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v280_4head_opponent_role_split.csv'
GRID=ROOT/'analysis_v280_4head_opponent_pairblend_grid.csv'
MONTH=ROOT/'analysis_v280_4head_opponent_role_split_monthly.csv'
SUM=ROOT/'summary_v280_4head_opponent_role_split.md'


def role_obj(r,role):
    # Prefer exact first choice but retain coverage of top2.
    return .60*r[f'{role}_top1']+.40*r[f'{role}_top2']


def choose_roles(grid):
    t=grid[grid.scope=='TUNE'].copy()
    t['second_obj']=t.apply(lambda r:role_obj(r,'second'),axis=1)
    t['third_obj']=t.apply(lambda r:role_obj(r,'third'),axis=1)
    s=t.sort_values(['second_obj','second_top1','second_top2'],ascending=False).iloc[0]
    q=t.sort_values(['third_obj','third_top1','third_top2'],ascending=False).iloc[0]
    return (str(s.family),float(s.l2),float(s.second_obj)),(str(q.family),float(q.l2),float(q.third_obj))


def fit_scores(z,fams,c2,l2_2,c3,l2_3):
    rec=[]
    for mon in v279.MONTHS:
        tr=z[z.month<mon].copy();te=z[z.month==mon].copy()
        if tr.race_code.nunique()<v279.MIN_TRAIN or te.empty:continue
        f2=v279.good_features(tr,fams[c2]);f3=v279.good_features(tr,fams[c3])
        m2=v279.ListwiseSoftmax(l2_2).fit(tr,f2,'y2')
        m3=v279.ListwiseSoftmax(l2_3).fit(tr,f3,'y3')
        te=te.copy();te['s2']=m2.score(te);te['s3']=m3.score(te)
        for code,g in te.groupby('race_code'):
            if len(g)!=5 or g.y2.sum()!=1 or g.y3.sum()!=1:continue
            p2=v279.probs_within_race(g,'s2');p3=v279.probs_within_race(g,'s3')
            a2=int(g.loc[g.y2==1,'boat'].iloc[0]);a3=int(g.loc[g.y3==1,'boat'].iloc[0])
            rec.append({'month':mon,'date':str(g.date.iloc[0]),'race_code':str(code).zfill(12),'actual2':a2,'actual3':a3,
                        'p2':'|'.join(f'{b}:{p2[b]:.12g}' for b in v279.BOATS),'p3':'|'.join(f'{b}:{p3[b]:.12g}' for b in v279.BOATS),
                        'nfeat2':len(f2),'nfeat3':len(f3)})
    return pd.DataFrame(rec)


def parse(s):return {int(x.split(':')[0]):float(x.split(':')[1]) for x in str(s).split('|')}


def order_pair(p2,p3,alpha,conditional):
    a=[]
    for s in v279.BOATS:
        for t in v279.BOATS:
            if s==t:continue
            q3=p3[t]
            if conditional:q3=q3/max(1.0-p3[s],1e-9)
            sc=alpha*math.log(max(p2[s],1e-12))+(1-alpha)*math.log(max(q3,1e-12))
            a.append((sc,s,t))
    a.sort(key=lambda x:(-x[0],x[1],x[2]));return [(s,t) for _,s,t in a]


def add_ranks(df,alpha,conditional):
    q=df.copy();pr=[];r2=[];r3=[]
    for _,r in q.iterrows():
        p2=parse(r.p2);p3=parse(r.p3);actual=(int(r.actual2),int(r.actual3))
        pr.append(v279.rank_of(order_pair(p2,p3,alpha,conditional),actual))
        o2=sorted(v279.BOATS,key=lambda b:(-p2[b],b));o3=sorted(v279.BOATS,key=lambda b:(-p3[b],b))
        r2.append(o2.index(actual[0])+1);r3.append(o3.index(actual[1])+1)
    q['pair_rank']=pr;q['second_rank']=r2;q['third_rank']=r3;return q


def metrics(g):
    return v279.metric(g)


def main():
    grid=pd.read_csv(v279.OUT_GRID)
    c2,c3=choose_roles(grid);fam2,l22,_=c2;fam3,l23,_=c3
    d,z=v279.build_source();base_for_rel=[c for c in list(v279.ABILITY)+list(v279.PLAYER)+list(v279.PRIOR_HINTS)+list(v279.START_HINTS)+list(v279.POSITION)+list(v279.CURRENT) if c in z]
    z=v279.add_relative(z,base_for_rel);fams=v279.family_map(z)
    raw=fit_scores(z,fams,fam2,l22,fam3,l23)

    rows=[]
    for cond in (False,True):
        for alpha in (0.50,0.55,0.60,0.65,0.70,0.75):
            q=add_ranks(raw,alpha,cond);g=q[q.month.isin(v279.TUNE)];m=metrics(g)
            obj=.50*m['top2']+.30*m['top4']+.15*m['top6']+.05*m['top10']
            rows.append({'conditional3':cond,'alpha2':alpha,'races':len(g),'top1':m['top1'],'top2':m['top2'],'top4':m['top4'],'top6':m['top6'],'top10':m['top10'],'objective':obj})
    bg=pd.DataFrame(rows).sort_values(['objective','top2','top4'],ascending=False);bg.to_csv(GRID,index=False)
    best=bg.iloc[0];cond=str(best.conditional3).lower()=='true' if not isinstance(best.conditional3,(bool,np.bool_)) else bool(best.conditional3);alpha=float(best.alpha2)
    q=add_ranks(raw,alpha,cond)
    q['selected_SA']=q.race_code.astype(str).isin(v274.selected_codes()).astype(int)
    # benchmark only after new ranking frozen
    q['v96_rank']=v279.baseline_ranks(q)
    q.to_csv(OUT,index=False)

    mr=[]
    for mon,g in q[q.month.isin(v279.HOLD)].groupby('month'):
        for scope,gg in [('ALL',g),('SA',g[g.selected_SA==1])]:
            if gg.empty:continue
            m=metrics(gg);m.update({'month':mon,'scope':scope})
            for k in (1,2,4,6,10):m[f'v96_top{k}']=100*((gg.v96_rank>0)&(gg.v96_rank<=k)).mean()
            mr.append(m)
    M=pd.DataFrame(mr);M.to_csv(MONTH,index=False)

    def report(g):
        m=metrics(g)
        for k in (1,2,4,6,10):m[f'v96_top{k}']=100*((g.v96_rank>0)&(g.v96_rank<=k)).mean() if len(g) else np.nan
        return m
    h=q[q.month.isin(v279.HOLD)];s=h[h.selected_SA==1];mh=report(h);ms=report(s)
    L=['# v280 independent role-split 4-head opponent model','',
       '- v96 is NOT used in features, model fitting, candidate restriction, or pair ordering.',
       '- SECOND and THIRD feature family/L2 are selected independently using Feb-Mar only.',
       '- Pair alpha and conditional-third formula are also selected on Feb-Mar only; Apr-Jun is untouched holdout-like evaluation.',
       '- Jul/Aug excluded; September not read; no odds.','',
       '## Frozen role choices from Feb-Mar','',
       f'- SECOND: **{fam2}**, L2 **{l22:g}**, role objective **{c2[2]:.2f}**',
       f'- THIRD: **{fam3}**, L2 **{l23:g}**, role objective **{c3[2]:.2f}**','',
       '## Pair-composition choice on Feb-Mar','',
       f'- chosen second weight alpha: **{alpha:.2f}**',f'- conditional third normalization: **{cond}**',
       f'- tune Top2/Top4/Top6/Top10: **{best.top2:.1f}% / {best.top4:.1f}% / {best.top6:.1f}% / {best.top10:.1f}%**','',
       '### Pair grid','', '|cond3|alpha2|R|T1|T2|T4|T6|T10|objective|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in bg.iterrows():L.append(f'|{r.conditional3}|{r.alpha2:.2f}|{int(r.races)}|{r.top1:.1f}%|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.objective:.2f}|')
    L += ['','## Apr-Jun holdout-like result','',
          '|scope|R|2nd T1|T2|3rd T1|T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in [('ALL 4-head wins',mh),('Frozen S+A head-wins',ms)]:
        L.append(f'|{name}|{int(m["races"])}|{m["second_top1"]:.1f}%|{m["second_top2"]:.1f}%|{m["third_top1"]:.1f}%|{m["third_top2"]:.1f}%|{m["top1"]:.1f}%|{m["top2"]:.1f}%|{m["top4"]:.1f}%|{m["top6"]:.1f}%|{m["top10"]:.1f}%|{m["v96_top2"]:.1f}%|{m["v96_top4"]:.1f}%|{m["v96_top6"]:.1f}%|{m["v96_top10"]:.1f}%|')
    L += ['','## S+A monthly','', '|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in M[M.scope=='SA'].iterrows():L.append(f'|{r.month}|{int(r.races)}|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.v96_top2:.1f}%|{r.v96_top4:.1f}%|{r.v96_top6:.1f}%|{r.v96_top10:.1f}%|')
    L += ['','## Decision','- Keep the opponent-model rebuild independent of v96 regardless of result.',
          '- If v280 improves small-N coverage and monthly stability, next test exact 10,000-yen Dutch/composite-odds economics.',
          '- If not, next research should target THIRD-role features and race-scenario interactions, because SECOND is already the stronger independent component.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
