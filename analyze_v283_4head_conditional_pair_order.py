#!/usr/bin/env python3
"""v283: convert frozen v282 probabilities into a better small-N pair order.

No model is retrained and no v96 input is used. v282 SECOND and conditional THIRD
probabilities are frozen. This audit selects only a structural ordering policy on
Feb-Mar, then applies it untouched to Apr-Jun.

Policies explicitly test the small-N tradeoff between:
- two THIRD options behind the strongest SECOND;
- one best THIRD behind each of the top two SECOND candidates;
- a 2x2 beam (SECOND top2 x conditional THIRD top2);
- ordinary joint probability.

Jul/Aug excluded upstream; September not read; no odds.
"""
from pathlib import Path
import math
import pandas as pd
import numpy as np

import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v282_4head_conditional_third as v282
import analyze_v274_4head_opponent_feature_audit as v274

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v283_4head_conditional_pair_order.csv'
GRID=ROOT/'analysis_v283_4head_conditional_pair_order_grid.csv'
MONTH=ROOT/'analysis_v283_4head_conditional_pair_order_monthly.csv'
SUM=ROOT/'summary_v283_4head_conditional_pair_order.md'

ALPHAS=(0.50,0.55,0.60,0.65,0.70,0.75)
MODES=('JOINT','S1_TWO','S12_ONE','TOP2XTOP2','CONF_HYBRID')
THRESH=(1.15,1.30,1.50,1.80,2.20)


def joint_order(p2,pc,a):
    z=[]
    for s in v279.BOATS:
        for t in v279.BOATS:
            if s==t:continue
            sc=a*math.log(max(p2[s],1e-12))+(1-a)*math.log(max(pc[(s,t)],1e-12));z.append((sc,s,t))
    z.sort(key=lambda x:(-x[0],x[1],x[2]));return [(s,t) for _,s,t in z]

def cond_rankings(pc):
    return {s:sorted([t for t in v279.BOATS if t!=s],key=lambda t:(-pc[(s,t)],t)) for s in v279.BOATS}

def unique_prefix(prefix,base):
    out=[];seen=set()
    for x in prefix+base:
        if x not in seen:seen.add(x);out.append(x)
    return out

def order_policy(p2,pc,a,mode,thr):
    base=joint_order(p2,pc,a);sr=sorted(v279.BOATS,key=lambda s:(-p2[s],s));cr=cond_rankings(pc);s1,s2=sr[:2]
    if mode=='JOINT':return base
    if mode=='S1_TWO':
        pre=[(s1,cr[s1][0]),(s1,cr[s1][1])];return unique_prefix(pre,base)
    if mode=='S12_ONE':
        pre=[(s1,cr[s1][0]),(s2,cr[s2][0])];return unique_prefix(pre,base)
    if mode=='TOP2XTOP2':
        pool=[(s,cr[s][k]) for k in (0,1) for s in (s1,s2)]
        score={x:base.index(x) for x in pool};pre=sorted(pool,key=lambda x:score[x]);return unique_prefix(pre,base)
    # confidence hybrid: if strongest SECOND dominates, spend first 2 ranks on
    # its two THIRD choices; otherwise hedge one best THIRD behind each top SECOND.
    ratio=p2[s1]/max(p2[s2],1e-12)
    pre=[(s1,cr[s1][0]),(s1,cr[s1][1])] if ratio>=thr else [(s1,cr[s1][0]),(s2,cr[s2][0])]
    return unique_prefix(pre,base)

def apply(df,a,mode,thr):
    q=df.copy();rr=[];r2=[];r3=[]
    for _,r in q.iterrows():
        p2=v282.parse_p2(r.p2);pc=v282.parse_cond(r.cond);actual=(int(r.actual2),int(r.actual3));o=order_policy(p2,pc,a,mode,thr)
        rr.append(v279.rank_of(o,actual));sr=sorted(v279.BOATS,key=lambda s:(-p2[s],s));cr=cond_rankings(pc);r2.append(sr.index(actual[0])+1);r3.append(cr[actual[0]].index(actual[1])+1)
    q['pair_rank']=rr;q['second_rank']=r2;q['third_rank']=r3;return q

def main():
    src=pd.read_csv(v282.OUT,dtype={'race_code':str});src['race_code']=src.race_code.astype(str).str.zfill(12)
    rows=[]
    for mode in MODES:
        thrs=THRESH if mode=='CONF_HYBRID' else (1.5,)
        for a in ALPHAS:
            for th in thrs:
                q=apply(src,a,mode,th);g=q[q.month.isin(v279.TUNE)];m=v279.metric(g)
                obj=.55*m['top2']+.28*m['top4']+.12*m['top6']+.05*m['top10']
                rows.append({'mode':mode,'alpha2':a,'threshold':th,'races':len(g),'top1':m['top1'],'top2':m['top2'],'top4':m['top4'],'top6':m['top6'],'top10':m['top10'],'objective':obj})
    G=pd.DataFrame(rows).sort_values(['objective','top2','top4'],ascending=False);G.to_csv(GRID,index=False);b=G.iloc[0]
    mode=str(b['mode']);a=float(b.alpha2);th=float(b.threshold);q=apply(src,a,mode,th)
    # retain benchmark already attached by v282; it never entered policy selection.
    q['selected_SA']=q.race_code.astype(str).isin(v274.selected_codes()).astype(int);q.to_csv(OUT,index=False)
    mr=[]
    for mon,g in q[q.month.isin(v279.HOLD)].groupby('month'):
        for scope,gg in [('ALL',g),('SA',g[g.selected_SA==1])]:
            if gg.empty:continue
            m=v279.metric(gg);m.update({'month':mon,'scope':scope})
            for k in (2,4,6,10):m[f'v96_top{k}']=100*((gg.v96_rank>0)&(gg.v96_rank<=k)).mean()
            mr.append(m)
    M=pd.DataFrame(mr);M.to_csv(MONTH,index=False)
    def rep(g):
        m=v279.metric(g)
        for k in (2,4,6,10):m[f'v96_top{k}']=100*((g.v96_rank>0)&(g.v96_rank<=k)).mean() if len(g) else np.nan
        return m
    h=q[q.month.isin(v279.HOLD)];s=h[h.selected_SA==1];mh=rep(h);ms=rep(s)
    L=['# v283 conditional pair-order audit','',
       '- v282 model probabilities are frozen; no retraining here.',
       '- No v96 signal enters ordering or selection; v96 is benchmark-only.',
       '- Ordering mode/alpha/threshold selected on Feb-Mar only; Apr-Jun untouched.',
       '- Jul/Aug excluded upstream; September not read; no odds.','',
       '## Frozen pair-order policy','',f'- mode: **{mode}**',f'- alpha2: **{a:.2f}**',f'- confidence threshold: **{th:.2f}**',
       f'- tune T2/T4/T6/T10: **{b.top2:.1f}% / {b.top4:.1f}% / {b.top6:.1f}% / {b.top10:.1f}%**','',
       '### Top policy grid','', '|mode|alpha|thr|T1|T2|T4|T6|T10|objective|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in G.head(20).iterrows():L.append(f'|{r["mode"]}|{r.alpha2:.2f}|{r.threshold:.2f}|{r.top1:.1f}%|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.objective:.2f}|')
    L += ['','## Apr-Jun holdout-like result','',
          '|scope|R|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in [('ALL 4-head wins',mh),('Frozen S+A head-wins',ms)]:L.append(f'|{name}|{int(m["races"])}|{m["top1"]:.1f}%|{m["top2"]:.1f}%|{m["top4"]:.1f}%|{m["top6"]:.1f}%|{m["top10"]:.1f}%|{m["v96_top2"]:.1f}%|{m["v96_top4"]:.1f}%|{m["v96_top6"]:.1f}%|{m["v96_top10"]:.1f}%|')
    L += ['','## S+A monthly','', '|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in M[M.scope=='SA'].iterrows():L.append(f'|{r.month}|{int(r.races)}|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.v96_top2:.1f}%|{r.v96_top4:.1f}%|{r.v96_top6:.1f}%|{r.v96_top10:.1f}%|')
    L += ['','## Decision','- Prefer the frozen structural policy only if Apr-Jun small-N coverage improves without a single-month collapse.',
          '- If it fails, the remaining issue is regime-specific opponent behavior rather than generic pair ordering; proceed to pre-Apr-frozen inner-survival/outer-follow regime models.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
