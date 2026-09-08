#!/usr/bin/env python3
"""v212: variable 3-head ticket count using BOTH head confidence and opponent concentration.

Input is v211 fixed-strategy rows, which already contain exact monthly prior-only v166
rankings and new 10k Dutch settlements for Top4/6/8/10/12/15.

Protocol:
- July only: standardize p3head and effN, search a tiny blend weight grid and monotone
  score cut quantiles mapping high confidence -> fewer points (4/6/8/10).
- Objective: maximize July ROI subject to preserving >=85% of July Top10 hit rate and
  average points <10.
- August: freeze July mean/sd, blend weight and cuts; no retuning.
- p3head and effN are prediction-time features; outcomes/odds are used only for July
  strategy tuning and August settlement.
"""
from pathlib import Path
import itertools
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'analysis_v211_3head_variable_points_newroi.csv'
OUT=ROOT/'analysis_v212_3head_joint_confidence_points.csv'
SUM=ROOT/'summary_v212_3head_joint_confidence_points.md'
WEIGHTS=(0.25,0.50,0.75)
QGRID=(0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80)


def metrics(df):
    if df.empty:return dict(R=0,hit=0,avg_points=0,comp=0,cost=0,ret=0,roi=0,profit=0)
    cost=float(df.cost.sum());ret=float(df.return_yen.sum())
    return dict(R=len(df),hit=100*df.hit.mean(),avg_points=float(df.rule_points.mean()),
                comp=float(df.composite_odds.mean()),cost=cost,ret=ret,
                roi=100*ret/cost if cost else 0,profit=ret-cost)


def choose_points(score,cuts):
    a,b,c=cuts
    if score>=a:return 4
    if score>=b:return 6
    if score>=c:return 8
    return 10


def build_selected(fixed,score_map,cuts):
    rows=[]
    for code,sc in score_map.items():
        n=choose_points(sc,cuts)
        q=fixed[(fixed.race_code==code)&(fixed.points==n)]
        if len(q):
            x=q.iloc[0].copy();x['joint_score']=sc;x['rule_points']=n;rows.append(x)
    return pd.DataFrame(rows)


def main():
    z=pd.read_csv(SRC,dtype={'race_code':str})
    z=z[z.strategy=='fixed'].copy()
    jul=z[z.month=='2026-07'].copy();aug=z[z.month=='2026-08'].copy()
    jb=jul.drop_duplicates('race_code').copy();ab=aug.drop_duplicates('race_code').copy()
    p_mu=float(jb.p3head.mean());p_sd=float(jb.p3head.std(ddof=0) or 1)
    e_mu=float(jb.effn.mean());e_sd=float(jb.effn.std(ddof=0) or 1)
    b10=jul[jul.points==10].copy();base_hit=100*b10.hit.mean()
    candidates=[]
    for w in WEIGHTS:
        js=w*((jb.p3head-p_mu)/p_sd)+(1-w)*(-(jb.effn-e_mu)/e_sd)
        smap=dict(zip(jb.race_code,js))
        vals=np.asarray(list(smap.values()),float)
        qs=sorted(set(float(np.quantile(vals,q)) for q in QGRID),reverse=True)
        # Need descending a>b>c because larger joint score => fewer points.
        for a,b,c in itertools.combinations(qs,3):
            if not (a>b>c):continue
            g=build_selected(jul,smap,(a,b,c))
            if g.empty:continue
            m=metrics(g)
            if m['avg_points']>=10:continue
            if base_hit>0 and m['hit']<0.85*base_hit:continue
            candidates.append((m['roi'],-m['avg_points'],m['hit'],w,(a,b,c),m))
    if candidates:
        candidates.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
        _,_,_,w,cuts,tunem=candidates[0]
    else:
        w=0.5;cuts=(float('inf'),float('inf'),float('inf'));tunem=metrics(b10.assign(rule_points=10))

    def score_frame(base):
        return w*((base.p3head-p_mu)/p_sd)+(1-w)*(-(base.effn-e_mu)/e_sd)
    jscore=score_frame(jb);ascore=score_frame(ab)
    jsel=build_selected(jul,dict(zip(jb.race_code,jscore)),cuts)
    asel=build_selected(aug,dict(zip(ab.race_code,ascore)),cuts)
    out=pd.concat([jsel.assign(split='july_tune'),asel.assign(split='aug_untouched')],ignore_index=True)
    out.to_csv(OUT,index=False)

    L=['# v212 3-head joint-confidence variable points','',
       '- input: v211 exact v166 monthly prior-only rankings + new 10k Dutch settlements',
       '- variable signal = frozen July-standardized blend of p3head and opponent concentration (-effN)',
       f'- selected head/concentration blend weight on p3head: **{w:.2f}** (remaining {1-w:.2f} on concentration)',
       f'- frozen joint-score cuts: **{cuts[0]:.4f} / {cuts[1]:.4f} / {cuts[2]:.4f}**',
       '- mapping: highest confidence => 4pt, then 6pt, then 8pt, else 10pt',
       '- July constraint: hit >=85% of fixed Top10 and avg points <10',
       '- August untouched: July mean/sd, weight, cuts all frozen','']
    L += ['## Comparison','|month|strategy|R|hit|avg points|avg comp|cost|return|ROI|profit|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for mon,gfix,gvar in [('2026-07',jul,jsel),('2026-08',aug,asel)]:
        for name,n in [('Top6 fixed',6),('Top10 fixed',10)]:
            g=gfix[gfix.points==n].copy();g['rule_points']=n;m=metrics(g)
            L.append(f"|{mon}|{name}|{m['R']}|{m['hit']:.2f}%|{m['avg_points']:.2f}|{m['comp']:.3f}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
        m=metrics(gvar)
        L.append(f"|{mon}|joint variable|{m['R']}|{m['hit']:.2f}%|{m['avg_points']:.2f}|{m['comp']:.3f}|{m['cost']:.0f}|{m['ret']:.0f}|{m['roi']:.1f}%|{m['profit']:+.0f}|")
    L += ['','## August variable distribution','|points|R|share|','|---:|---:|---:|']
    for n in (4,6,8,10):
        c=int((asel.rule_points==n).sum()) if len(asel) else 0
        L.append(f'|{n}|{c}|{100*c/len(asel) if len(asel) else 0:.1f}%|')
    L += ['','## Interpretation','- SHADOW only. July is tune; August is the only untouched test for this joint rule.',
          '- Compare primarily against fixed Top6 and Top10 under the same 10k Dutch definition.',
          '- If joint variable does not beat fixed Top6 in August, the evidence currently favors simple Top6 over complexity.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8')
    print('\n'.join(L))

if __name__=='__main__':main()
