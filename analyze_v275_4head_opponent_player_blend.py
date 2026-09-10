#!/usr/bin/env python3
"""v275: role-asymmetric opponent blend after v274 feature audit.

v274 found player-history features are especially strong for SECOND, while THIRD
is better anchored by the current v96 context.  This script tests only a small
blend into the frozen v96 role scores.

Selection discipline
--------------------
* Jul/Aug excluded; September not read.
* Blend lambdas are chosen using Feb-Mar 2026 boat-4-win races only.
* Apr-Jun are then reported as untouched opponent-blend holdout months.
* v268/v273 head selectors are never changed.
* No odds are used in ranking or lambda selection.
* This remains development/model-selection evidence because the frozen A-rank
  selector itself was researched on Apr-Jun.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v270_4head_win_feature_importance as v270
import analyze_v96_4corner_monthly_walkforward_tiebreak as v96
import analyze_v251_4head_newroi_bridge as v251

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v275_4head_opponent_player_blend.csv'
MONTH=ROOT/'analysis_v275_4head_opponent_player_blend_monthly.csv'
SUM=ROOT/'summary_v275_4head_opponent_player_blend.md'
BOATS=v274.BOATS
MONTHS=('2026-02','2026-03','2026-04','2026-05','2026-06')
TUNE=('2026-02','2026-03')
HOLD=('2026-04','2026-05','2026-06')
LAMS=(0.0,0.05,0.10,0.15,0.20,0.30,0.40)
MIN_TRAIN=40


def model():
    return Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler()),
                     ('lr',LogisticRegression(C=.16,max_iter=2500))])

def zmap(vals):
    a=np.asarray(list(vals.values()),float);m=float(a.mean());s=float(a.std())
    if not np.isfinite(s) or s<1e-10:return {b:0. for b in vals}
    return {b:(float(v)-m)/s for b,v in vals.items()}

def pair_order(s2,s3):
    z=[]
    for a in BOATS:
        for b in BOATS:
            if a!=b:z.append((float(s2[a])+float(s3[b]),a,b))
    z.sort(key=lambda x:(-x[0],x[1],x[2]));return [(a,b) for _,a,b in z]

def rank(order,actual):
    try:return order.index(actual)+1
    except ValueError:return 0

def current_role_maps(rs):
    out={}
    for mon in MONTHS:
        tr=v96.headrows_before(rs,mon)
        if len(tr)<MIN_TRAIN:continue
        mu,sd=v96.scalers(tr);w2=v96.fit(tr,'second',mu,sd);w3=v96.fit(tr,'third',mu,sd)
        for r in rs:
            if str(r.get('date',''))[:7]!=mon:continue
            key=(str(r.get('date','')),str(r.get('race_code','')).zfill(12))
            s2,s3=v96.role_scores(r,w2,w3,mu,sd);out[key]=(zmap(s2),zmap(s3))
    return out

def player_prob_maps(long,fs):
    out={}
    for mon in MONTHS:
        tr=long[long.month<mon].copy();te=long[long.month==mon].copy()
        if tr.race_code.nunique()<MIN_TRAIN or te.empty:continue
        use=v274.good_features(tr,fs,.55)
        Xtr=tr[use].apply(pd.to_numeric,errors='coerce');Xte=te[use].apply(pd.to_numeric,errors='coerce')
        m2=model();m3=model();m2.fit(Xtr,tr.y2);m3.fit(Xtr,tr.y3)
        te=te.copy();te['p2']=m2.predict_proba(Xte)[:,1];te['p3']=m3.predict_proba(Xte)[:,1]
        for code,g in te.groupby('race_code'):
            key=(str(g.date.iloc[0]),str(code).zfill(12))
            p2={int(b):math.log(max(float(p),1e-9)) for b,p in zip(g.boat,g.p2)}
            p3={int(b):math.log(max(float(p),1e-9)) for b,p in zip(g.boat,g.p3)}
            out[key]=(zmap(p2),zmap(p3))
    return out

def build_cases(long,current,player,selcodes):
    rec=[]
    for code,g in long[long.month.isin(MONTHS)].groupby('race_code'):
        if len(g)!=5:continue
        key=(str(g.date.iloc[0]),str(code).zfill(12))
        if key not in current or key not in player:continue
        a2=int(g.loc[g.y2==1,'boat'].iloc[0]);a3=int(g.loc[g.y3==1,'boat'].iloc[0])
        c2,c3=current[key];p2,p3=player[key]
        rec.append({'date':key[0],'month':key[0][:7],'race_code':key[1],'actual':(a2,a3),
                    'c2':c2,'c3':c3,'p2':p2,'p3':p3,'selected_SA':int(key[1] in selcodes)})
    return rec

def eval_lam(cases,l2,l3,months,selected=False):
    ranks=[]
    for r in cases:
        if r['month'] not in months or (selected and not r['selected_SA']):continue
        s2={b:(1-l2)*r['c2'][b]+l2*r['p2'][b] for b in BOATS}
        s3={b:(1-l3)*r['c3'][b]+l3*r['p3'][b] for b in BOATS}
        ranks.append(rank(pair_order(s2,s3),r['actual']))
    n=len(ranks)
    out={'races':n}
    for k in (1,2,4,6,10,20):out[f'top{k}_pct']=100*sum(1<=x<=k for x in ranks)/n if n else np.nan
    return out

def objective(m):
    # Current live ticket counts are often small, so protect Top2/Top4 first.
    return .45*m['top2_pct']+.30*m['top4_pct']+.15*m['top6_pct']+.10*m['top10_pct']

def main():
    d,_,_=v270.prepare();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    specs=v274.feature_specs(d);long=v274.build_long(d,specs)
    fam=v274.families(specs);fs=fam['BASE7_PLAYER']
    rs=v96.read();cur=current_role_maps(rs);pl=player_prob_maps(long,fs);sel=v274.selected_codes();cases=build_cases(long,cur,pl,sel)
    grid=[]
    base=eval_lam(cases,0,0,TUNE)
    for l2 in LAMS:
        for l3 in LAMS:
            m=eval_lam(cases,l2,l3,TUNE);m.update({'lambda2':l2,'lambda3':l3,'objective':objective(m)})
            # Guardrail: do not choose a tune-period blend that loses either Top2 or Top4 versus current v96.
            m['guardrail']=int(m['top2_pct']>=base['top2_pct'] and m['top4_pct']>=base['top4_pct'])
            grid.append(m)
    gd=pd.DataFrame(grid)
    ok=gd[gd.guardrail==1].copy()
    if ok.empty:ok=gd.copy()
    best=ok.sort_values(['objective','top2_pct','top4_pct','lambda2','lambda3'],ascending=[False,False,False,True,True]).iloc[0]
    l2=float(best.lambda2);l3=float(best.lambda3)

    rows=[]
    for scope,months,selected in [('TUNE_ALL',TUNE,False),('HOLD_ALL',HOLD,False),('HOLD_SA',HOLD,True)]:
        for label,a,b in [('V96',0.,0.),('PLAYER_BLEND',l2,l3)]:
            m=eval_lam(cases,a,b,months,selected);rows.append({'scope':scope,'model':label,'lambda2':a,'lambda3':b,**m})
    o=pd.DataFrame(rows);o.to_csv(OUT,index=False)
    monthly=[]
    for mon in HOLD:
        for selected in (False,True):
            for label,a,b in [('V96',0.,0.),('PLAYER_BLEND',l2,l3)]:
                m=eval_lam(cases,a,b,(mon,),selected)
                monthly.append({'month':mon,'scope':'SA' if selected else 'ALL','model':label,**m})
    pd.DataFrame(monthly).to_csv(MONTH,index=False)

    def row(scope,modelname):return o[(o.scope==scope)&(o.model==modelname)].iloc[0]
    L=['# v275 4-head opponent PLAYER blend','',
       '- v274 finding used: player history is strongest for 2nd; 3rd remains anchored to v96 unless Feb-Mar evidence supports a small player blend.',
       '- Lambda chosen only on Feb-Mar 2026; Apr-Jun then held out from opponent-blend selection.',
       '- Jul/Aug excluded; September not read; head selectors v268/v273 unchanged.',
       '- No odds used in ranking or lambda selection.','',
       '## Feb-Mar lambda search','',
       f'- v96 tune baseline: Top2 {base["top2_pct"]:.1f}%, Top4 {base["top4_pct"]:.1f}%, Top6 {base["top6_pct"]:.1f}%, Top10 {base["top10_pct"]:.1f}%.',
       f'- selected lambda2 (SECOND player blend): **{l2:.2f}**',
       f'- selected lambda3 (THIRD player blend): **{l3:.2f}**',
       '- Selection objective weights Top2/Top4 most heavily and requires tune Top2 and Top4 not below v96.','',
       '## Holdout comparison','',
       '|scope|model|R|Top1|Top2|Top4|Top6|Top10|Top20|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for scope in ('TUNE_ALL','HOLD_ALL','HOLD_SA'):
        for modelname in ('V96','PLAYER_BLEND'):
            r=row(scope,modelname);L.append(f'|{scope}|{modelname}|{int(r.races)}|{r.top1_pct:.1f}%|{r.top2_pct:.1f}%|{r.top4_pct:.1f}%|{r.top6_pct:.1f}%|{r.top10_pct:.1f}%|{r.top20_pct:.1f}%|')
    L += ['','## Apr-Jun month stability (S+A selected 4-head wins)','',
          '|month|model|R|Top2|Top4|Top6|Top10|','|---|---|---:|---:|---:|---:|---:|']
    mm=pd.DataFrame(monthly);q=mm[mm.scope=='SA']
    for _,r in q.iterrows():L.append(f'|{r.month}|{r.model}|{int(r.races)}|{r.top2_pct:.1f}%|{r.top4_pct:.1f}%|{r.top6_pct:.1f}%|{r.top10_pct:.1f}%|')
    vb=row('HOLD_SA','V96');pb=row('HOLD_SA','PLAYER_BLEND')
    L += ['','## Decision',
          f'- S+A holdout delta: Top2 {pb.top2_pct-vb.top2_pct:+.1f}pt, Top4 {pb.top4_pct-vb.top4_pct:+.1f}pt, Top6 {pb.top6_pct-vb.top6_pct:+.1f}pt, Top10 {pb.top10_pct-vb.top10_pct:+.1f}pt.',
          '- If small-N coverage improves or is preserved, next stage may test exact 10,000-yen Dutch ROI with this frozen blend candidate.',
          '- If Top2/Top4 deteriorate, keep v96 and treat player-history features as informative diagnostics rather than a ranking replacement.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
