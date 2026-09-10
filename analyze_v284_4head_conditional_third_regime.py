#!/usr/bin/env python3
"""v284: independent conditional THIRD model with inner/outer second regimes.

Purpose
-------
v282 showed that P(third | candidate second, context) is strong globally, while
v283 showed remaining instability in the frozen S+A head-win slice. v284 keeps
the independent SECOND model fixed and splits the conditional THIRD task by the
candidate second boat's side of boat 4:
  INNER_SECOND: second in {1,2,3}
  OUTER_SECOND: second in {5,6}

No v96 score/rank/order is used in features, fitting, candidate restriction,
blending, fallback, or pair ordering. v96 is loaded only after v284 predictions
and policy are frozen, as a benchmark.

Selection discipline
--------------------
* SECOND fixed to PLAYER_START/L2=10.
* INNER and OUTER conditional-THIRD family/L2 selected independently on Feb-Mar.
* Pair alpha and structural ordering selected on Feb-Mar only.
* Apr-Jun untouched holdout-like evaluation.
* Jul/Aug excluded; September not read; no odds.
* If a regime has fewer than MIN_REGIME_RACES prior training races, the fallback
  is the independent GLOBAL conditional model (COND_BASE/L2=.3), never v96.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.special import logsumexp

import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v282_4head_conditional_third as v282
import analyze_v283_4head_conditional_pair_order as v283
import analyze_v274_4head_opponent_feature_audit as v274

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v284_4head_conditional_third_regime.csv'
GRID=ROOT/'analysis_v284_4head_conditional_third_regime_grid.csv'
PAIRGRID=ROOT/'analysis_v284_4head_conditional_third_regime_pair_grid.csv'
MONTH=ROOT/'analysis_v284_4head_conditional_third_regime_monthly.csv'
COEF=ROOT/'analysis_v284_4head_conditional_third_regime_coefficients.csv'
SUM=ROOT/'summary_v284_4head_conditional_third_regime.md'

SECOND_FAMILY='PLAYER_START'; SECOND_L2=10.0
GLOBAL_FAMILY='COND_BASE'; GLOBAL_L2=0.3
L2S=(0.3,1.0,3.0,10.0)
FAMILIES=('COND_BASE','COND_COMPACT','COND_DIFF')
ALPHAS=(0.50,0.55,0.60,0.65,0.70,0.75)
MODES=('JOINT','TOP2XTOP2','S12_ONE','S1_TWO')
MIN_REGIME_RACES=20


def side(s): return 'INNER' if int(s)<4 else 'OUTER'


def prep():
    z,base=v282.prep(); pairs,fams=v282.make_pairs(z,base); p2=v282.second_probs(z,base)
    return z,base,pairs,fams,p2


def fit_one(tr,fs,l2):
    use=v282.good(tr,fs)
    return v282.ListwiseN(l2).fit(tr,use),use


def regime_predictions(pairs,fams,p2,inner_cfg,outer_cfg,keep_coef=False):
    rec=[]; co=[]
    for mon in v279.MONTHS:
        tr0=pairs[(pairs.month<mon)&(pairs.train_group==1)].copy(); te=pairs[pairs.month==mon].copy()
        if tr0.race_code.nunique()<v279.MIN_TRAIN or te.empty: continue
        global_m,global_use=fit_one(tr0,fams[GLOBAL_FAMILY],GLOBAL_L2)
        models={}; uses={}; fallback={}
        for rg,cfg in [('INNER',inner_cfg),('OUTER',outer_cfg)]:
            fam,l2=cfg
            trg=tr0[tr0.second_boat.map(side)==rg].copy()
            nr=trg.race_code.nunique()
            if nr>=MIN_REGIME_RACES:
                m,use=fit_one(trg,fams[fam],l2); models[rg]=m;uses[rg]=use;fallback[rg]=0
            else:
                models[rg]=global_m;uses[rg]=global_use;fallback[rg]=1
            if keep_coef:
                for f,b in zip(models[rg].features,models[rg].beta):
                    co.append({'month':mon,'regime':rg,'feature':f,'beta':float(b),'fallback_global':fallback[rg],'train_races':nr})
        te=te.copy(); scores=[]
        for _,r in te.iterrows():
            rg=side(r.second_boat); m=models[rg]
            one=pd.DataFrame([r])
            scores.append(float(m.score(one)[0]))
        te['sc']=scores
        for code,g in te.groupby('race_code'):
            if g.actual2.nunique()!=1 or g.actual3.nunique()!=1:continue
            a2=int(g.actual2.iloc[0]);a3=int(g.actual3.iloc[0]);cond={};actual_rank=0
            for s,gs in g.groupby('second_boat'):
                ss=gs.sc.to_numpy(float); pp=np.exp(ss-logsumexp(ss))
                for t,v in zip(gs.third_boat.astype(int),pp):cond[(int(s),int(t))]=float(v)
                if int(s)==a2:
                    order=[int(x) for x in gs.assign(_p=pp).sort_values(['_p','third_boat'],ascending=[False,True]).third_boat]
                    actual_rank=order.index(a3)+1 if a3 in order else 0
            rec.append({'month':mon,'date':str(g.date.iloc[0]),'race_code':str(code).zfill(12),'actual2':a2,'actual3':a3,'cond_rank':actual_rank,
                        'actual_second_regime':side(a2),
                        'cond':'|'.join(f'{s}>{t}:{cond[(s,t)]:.12g}' for s in v279.BOATS for t in v279.BOATS if s!=t)})
    cp=pd.DataFrame(rec)
    return cp.merge(p2,on=['month','date','race_code'],how='inner'),pd.DataFrame(co)


def role_eval(raw):
    g=raw[raw.month.isin(v279.TUNE)]
    out={}
    for rg in ('INNER','OUTER'):
        x=g[g.actual_second_regime==rg]
        out[rg]={'races':len(x),'t1':100*(x.cond_rank<=1).mean() if len(x) else np.nan,'t2':100*(x.cond_rank<=2).mean() if len(x) else np.nan}
    return out


def choose_regime(pairs,fams,p2,rg):
    rows=[]
    # Select each regime separately on its own Feb-Mar conditional-third accuracy.
    for fam in FAMILIES:
        for l2 in L2S:
            cfg=(fam,l2)
            inner=cfg if rg=='INNER' else (GLOBAL_FAMILY,GLOBAL_L2)
            outer=cfg if rg=='OUTER' else (GLOBAL_FAMILY,GLOBAL_L2)
            raw,_=regime_predictions(pairs,fams,p2,inner,outer,False)
            ev=role_eval(raw)[rg];obj=.60*ev['t1']+.40*ev['t2']
            rows.append({'regime':rg,'family':fam,'l2':l2,'races':ev['races'],'top1':ev['t1'],'top2':ev['t2'],'objective':obj})
    q=pd.DataFrame(rows).sort_values(['objective','top1','top2'],ascending=False)
    b=q.iloc[0];return (str(b.family),float(b.l2)),q


def parse_p2(s):return v282.parse_p2(s)
def parse_cond(s):return v282.parse_cond(s)


def joint_order(p2,pc,a):
    z=[]
    for s in v279.BOATS:
        for t in v279.BOATS:
            if s==t:continue
            sc=a*math.log(max(p2[s],1e-12))+(1-a)*math.log(max(pc[(s,t)],1e-12));z.append((sc,s,t))
    z.sort(key=lambda x:(-x[0],x[1],x[2]));return [(s,t) for _,s,t in z]


def order_policy(p2,pc,a,mode):
    base=joint_order(p2,pc,a)
    if mode=='JOINT':return base
    sr=sorted(v279.BOATS,key=lambda s:(-p2[s],s));cr={s:sorted([t for t in v279.BOATS if t!=s],key=lambda t:(-pc[(s,t)],t)) for s in v279.BOATS}
    s1,s2=sr[:2]
    if mode=='TOP2XTOP2':
        pool=[(s,cr[s][k]) for k in (0,1) for s in (s1,s2)];pre=sorted(pool,key=lambda x:base.index(x))
    elif mode=='S12_ONE':pre=[(s1,cr[s1][0]),(s2,cr[s2][0])]
    else:pre=[(s1,cr[s1][0]),(s1,cr[s1][1])]
    out=[];seen=set()
    for x in pre+base:
        if x not in seen:seen.add(x);out.append(x)
    return out


def add_rank(raw,a,mode):
    q=raw.copy();rr=[];r2=[];r3=[]
    for _,r in q.iterrows():
        p2=parse_p2(r.p2);pc=parse_cond(r.cond);actual=(int(r.actual2),int(r.actual3));o=order_policy(p2,pc,a,mode);rr.append(v279.rank_of(o,actual))
        sr=sorted(v279.BOATS,key=lambda s:(-p2[s],s));cr=sorted([t for t in v279.BOATS if t!=actual[0]],key=lambda t:(-pc[(actual[0],t)],t))
        r2.append(sr.index(actual[0])+1);r3.append(cr.index(actual[1])+1)
    q['pair_rank']=rr;q['second_rank']=r2;q['third_rank']=r3;return q


def main():
    z,base,pairs,fams,p2=prep()
    inner_cfg,gi=choose_regime(pairs,fams,p2,'INNER'); outer_cfg,go=choose_regime(pairs,fams,p2,'OUTER')
    G=pd.concat([gi,go],ignore_index=True);G.to_csv(GRID,index=False)
    raw,coef=regime_predictions(pairs,fams,p2,inner_cfg,outer_cfg,True);coef.to_csv(COEF,index=False)
    rows=[]
    for mode in MODES:
        for a in ALPHAS:
            q=add_rank(raw,a,mode);g=q[q.month.isin(v279.TUNE)];m=v279.metric(g);obj=.55*m['top2']+.28*m['top4']+.12*m['top6']+.05*m['top10']
            rows.append({'mode':mode,'alpha2':a,'races':len(g),'top1':m['top1'],'top2':m['top2'],'top4':m['top4'],'top6':m['top6'],'top10':m['top10'],'objective':obj})
    PG=pd.DataFrame(rows).sort_values(['objective','top2','top4'],ascending=False);PG.to_csv(PAIRGRID,index=False);bp=PG.iloc[0];mode=str(bp['mode']);a=float(bp.alpha2)
    q=add_rank(raw,a,mode);q['selected_SA']=q.race_code.astype(str).isin(v274.selected_codes()).astype(int)
    # Benchmark only after all v284 choices/order are frozen.
    q['v96_rank']=v279.baseline_ranks(q);q.to_csv(OUT,index=False)
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
    # Conditional third by actual second regime on holdout.
    reg=[]
    for rg in ('INNER','OUTER'):
        g=h[h.actual_second_regime==rg];reg.append((rg,len(g),100*(g.third_rank<=1).mean() if len(g) else np.nan,100*(g.third_rank<=2).mean() if len(g) else np.nan))
    L=['# v284 independent conditional THIRD regime split','',
       '- No v96 signal in model/features/restriction/fallback/order. v96 benchmark only after freeze.',
       '- SECOND fixed PLAYER_START/L2=10. Conditional THIRD split by candidate SECOND side: INNER 1/2/3 vs OUTER 5/6.',
       '- Regime family/L2 and pair policy selected on Feb-Mar only; Apr-Jun untouched.',
       '- Sparse-regime fallback is independent GLOBAL COND_BASE/L2=.3, never v96.',
       '- Jul/Aug excluded; September not read; no odds.','',
       '## Frozen regime choices','',f'- INNER SECOND -> THIRD: **{inner_cfg[0]}**, L2 **{inner_cfg[1]:g}**',f'- OUTER SECOND -> THIRD: **{outer_cfg[0]}**, L2 **{outer_cfg[1]:g}**','',
       '### Regime grid','', '|regime|family|L2|R|T1|T2|objective|','|---|---|---:|---:|---:|---:|---:|']
    for _,r in G.sort_values(['regime','objective'],ascending=[True,False]).iterrows():L.append(f'|{r.regime}|{r.family}|{r.l2:g}|{int(r.races)}|{r.top1:.1f}%|{r.top2:.1f}%|{r.objective:.2f}|')
    L += ['','## Frozen pair-order policy (Feb-Mar)','',f'- mode: **{mode}**',f'- alpha2: **{a:.2f}**',f'- tune T2/T4/T6/T10: **{bp.top2:.1f}% / {bp.top4:.1f}% / {bp.top6:.1f}% / {bp.top10:.1f}%**','',
          '## Apr-Jun holdout-like result','',
          '|scope|R|2nd T1|T2|cond3 T1|T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in [('ALL 4-head wins',mh),('Frozen S+A head-wins',ms)]:L.append(f'|{name}|{int(m["races"])}|{m["second_top1"]:.1f}%|{m["second_top2"]:.1f}%|{m["third_top1"]:.1f}%|{m["third_top2"]:.1f}%|{m["top1"]:.1f}%|{m["top2"]:.1f}%|{m["top4"]:.1f}%|{m["top6"]:.1f}%|{m["top10"]:.1f}%|{m["v96_top2"]:.1f}%|{m["v96_top4"]:.1f}%|{m["v96_top6"]:.1f}%|{m["v96_top10"]:.1f}%|')
    L += ['','## Apr-Jun conditional THIRD by actual SECOND regime','', '|regime|R|T1|T2|','|---|---:|---:|---:|']
    for rg,n,t1,t2 in reg:L.append(f'|{rg}|{n}|{t1:.1f}%|{t2:.1f}%|')
    L += ['','## S+A monthly','', '|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in M[M.scope=='SA'].iterrows():L.append(f'|{r.month}|{int(r.races)}|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.v96_top2:.1f}%|{r.v96_top4:.1f}%|{r.v96_top6:.1f}%|{r.v96_top10:.1f}%|')
    L += ['','## Decision','- Promote v284 only if S+A small-N coverage improves and monthly deterioration is reduced.',
          '- Otherwise retain v282/v283 as the independent baseline and next add more data or a pre-Apr-frozen attack-strength regime rather than tuning on Apr-Jun outcomes.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
