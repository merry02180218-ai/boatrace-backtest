#!/usr/bin/env python3
"""v279: rebuild 4-head opponent selection from scratch with race-listwise learning.

This model does NOT use v96 score/rank/order as an input, candidate-set constraint,
blend, or tiebreak.  Boat 4 is fixed as winner; the task is to rank the five
remaining boats for SECOND and THIRD directly from pre-result information.

Model design
------------
* One listwise softmax ranker for SECOND and a separate one for THIRD.
* Exactly one target boat per race/role is used in the softmax loss.
* Pair order is produced from P(second=s) * P(third=t), s != t.
* Features are symmetric pre-result boat attributes: ability/course, frozen
  player history, frozen prior exhibition history, prior-only ST, current
  exhibition components, and within-race relative versions of those signals.
* v96 is loaded only AFTER new-model predictions are frozen, solely as a
  reporting benchmark.

Discipline
----------
* 2026-07/08 excluded completely; September not read.
* No odds are used in feature training/ranking.
* Each evaluation month trains only on earlier historical boat-4-win races.
* Hyperparameter/family selection uses Feb-Mar only; Apr-Jun is held out from
  model-choice selection.
* v268/v273 head selectors are unchanged and used only for an S+A report slice.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v278_4head_opponent_current_exhibition_audit as v278
import analyze_v270_4head_win_feature_importance as v270

ROOT=Path(__file__).resolve().parent
OUT_GRID=ROOT/'analysis_v279_4head_opponent_listwise_grid.csv'
OUT_PRED=ROOT/'analysis_v279_4head_opponent_listwise_predictions.csv'
OUT_MONTH=ROOT/'analysis_v279_4head_opponent_listwise_monthly.csv'
SUM=ROOT/'summary_v279_4head_opponent_listwise_rebuild.md'
MONTHS=('2026-02','2026-03','2026-04','2026-05','2026-06')
TUNE=('2026-02','2026-03')
HOLD=('2026-04','2026-05','2026-06')
BOATS=(1,2,3,5,6)
MIN_TRAIN=40
L2_GRID=(0.3,1.0,3.0,10.0)

ABILITY=('v93_grade','v93_national','v93_local','v93_motor','v93_waku','v93_nst')
PLAYER=('pref_pl_all_p2','pref_pl_all_win','pref_pl_frame_p2','pref_pl_recent_p2','pref_pl_frame_win')
PRIOR_HINTS=(
 'pref_vh_delta_overall','pref_vh_delta_turn','pref_vh_delta_display','pref_vh_delta_straight',
 'pref_vh_p1_straight','pref_vh_p2_overall','pref_vh_p12_straight','pref_vh_p12_display',
 'pref_gh_delta_display','pref_gh_delta_turn','pref_gh_delta_overall','pref_gh_p2_turn','pref_gh_p2_overall','pref_gh_p12_display',
)
START_HINTS=('suf_st_raw','suf_st_raw_strength','suf_st_raw_rank','suf_st_corr_strength','suf_st_corr_rank')
POSITION=('pos_boat_number','pos_inside4','pos_outside4','pos_distance4')
CURRENT=tuple(v278.CUR)


def available(cols, names):
    return [x for x in names if x in cols]


def build_source():
    d,_,_=v270.prepare()
    d=d[d._date<pd.Timestamp('2026-07-01')].copy()
    d['date']=d.date.astype(str)
    specs=v274.feature_specs(d)
    # Explicitly exclude v93 direct/score/rank. Only normalized primitive ability
    # components are retained; no v96/v93 opponent ranking is used as a feature.
    keep={}
    for n,s in specs.items():
        if n in ABILITY or n in POSITION or n.startswith('pref_pl_') or n.startswith('pref_vh_') or n.startswith('pref_gh_') or n.startswith('suf_st_'):
            keep[n]=s
    z=v274.build_long(d,keep)
    z=v278.add_current(z)
    return d,z


def add_relative(z, base_features):
    q=z.copy()
    for c in base_features:
        if c not in q:continue
        x=pd.to_numeric(q[c],errors='coerce')
        q[c]=x
        g=q.assign(_x=x).groupby('race_code')['_x']
        med=g.transform('median')
        mean=g.transform('mean')
        std=g.transform('std').replace(0,np.nan)
        mx=g.transform('max')
        # all directions are learned, so no hand-coded sign is imposed.
        q[f'{c}__center']=x-med
        q[f'{c}__z']=(x-mean)/std
        q[f'{c}__gapmax']=x-mx
        q[f'{c}__pct']=q.assign(_x=x).groupby('race_code')['_x'].rank(pct=True,method='average')
    return q


def family_map(z):
    cols=set(z.columns)
    ability=available(cols,ABILITY);player=available(cols,PLAYER)
    prior=available(cols,PRIOR_HINTS);start=available(cols,START_HINTS)
    pos=available(cols,POSITION);cur=available(cols,CURRENT)
    base_core=list(dict.fromkeys(ability+pos+cur))
    base_player=list(dict.fromkeys(base_core+player))
    base_prior=list(dict.fromkeys(base_player+prior))
    base_start=list(dict.fromkeys(base_player+start))
    base_rich=list(dict.fromkeys(base_player+prior+start))
    fam={
      'CORE':base_core,
      'PLAYER':base_player,
      'PLAYER_PRIOR':base_prior,
      'PLAYER_START':base_start,
      'RICH':base_rich,
    }
    # Relative families use only strong, interpretable blocks to control dimension.
    relseed=list(dict.fromkeys(ability+player+cur+pos))
    relcols=[]
    for c in relseed:
        relcols += [f'{c}__center',f'{c}__z',f'{c}__gapmax',f'{c}__pct']
    fam['PLAYER_REL']=list(dict.fromkeys(base_player+[x for x in relcols if x in cols]))
    relseed2=list(dict.fromkeys(ability+player+cur+prior+start+pos))
    relcols2=[]
    for c in relseed2:
        relcols2 += [f'{c}__center',f'{c}__pct']
    fam['RICH_REL']=list(dict.fromkeys(base_rich+[x for x in relcols2 if x in cols]))
    return fam


def good_features(tr,fs,mincov=.55):
    out=[]
    for c in fs:
        if c not in tr:continue
        x=pd.to_numeric(tr[c],errors='coerce')
        if x.notna().mean()>=mincov and x.nunique(dropna=True)>=2:out.append(c)
    return out


class ListwiseSoftmax:
    def __init__(self,l2=1.0):
        self.l2=float(l2);self.imp=None;self.sc=None;self.beta=None;self.features=None
    def fit(self,df,features,ycol):
        self.features=list(features)
        X=df[self.features].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        self.imp=SimpleImputer(strategy='median');X=self.imp.fit_transform(X)
        self.sc=StandardScaler();X=self.sc.fit_transform(X)
        groups=[]
        for _,g in df.reset_index(drop=True).groupby('race_code',sort=False):
            idx=g.index.to_numpy();y=g[ycol].to_numpy(int)
            if len(idx)!=5 or y.sum()!=1:continue
            groups.append((idx,int(np.argmax(y))))
        if not groups:raise RuntimeError('no valid listwise groups')
        p=X.shape[1]
        def fg(b):
            loss=.5*self.l2*np.dot(b,b);grad=self.l2*b.copy()
            for idx,yi in groups:
                Xi=X[idx];s=Xi@b;ls=logsumexp(s);loss += ls-s[yi]
                pr=np.exp(s-ls);grad += Xi.T@pr-Xi[yi]
            return loss,grad
        res=minimize(lambda b:fg(b),np.zeros(p),jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-10})
        self.beta=res.x
        return self
    def score(self,df):
        X=df[self.features].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        X=self.sc.transform(self.imp.transform(X));return X@self.beta


def probs_within_race(g,score_col):
    s=g[score_col].to_numpy(float);p=np.exp(s-logsumexp(s))
    return {int(b):float(v) for b,v in zip(g.boat,p)}


def pair_order(p2,p3):
    a=[]
    for s in BOATS:
        for t in BOATS:
            if s==t:continue
            sc=math.log(max(p2.get(s,1e-12),1e-12))+math.log(max(p3.get(t,1e-12),1e-12))
            a.append((sc,s,t))
    a.sort(key=lambda x:(-x[0],x[1],x[2]));return [(s,t) for _,s,t in a]


def rank_of(order,actual):
    try:return order.index(actual)+1
    except ValueError:return 0


def run_config(z,fs,fam,l2):
    rec=[]
    for mon in MONTHS:
        tr=z[z.month<mon].copy();te=z[z.month==mon].copy()
        if tr.race_code.nunique()<MIN_TRAIN or te.empty:continue
        use=good_features(tr,fs)
        if len(use)<5:continue
        m2=ListwiseSoftmax(l2).fit(tr,use,'y2');m3=ListwiseSoftmax(l2).fit(tr,use,'y3')
        te=te.copy();te['s2']=m2.score(te);te['s3']=m3.score(te)
        for code,g in te.groupby('race_code'):
            if len(g)!=5 or g.y2.sum()!=1 or g.y3.sum()!=1:continue
            p2=probs_within_race(g,'s2');p3=probs_within_race(g,'s3')
            o=pair_order(p2,p3)
            a2=int(g.loc[g.y2==1,'boat'].iloc[0]);a3=int(g.loc[g.y3==1,'boat'].iloc[0]);actual=(a2,a3)
            r2=sorted(BOATS,key=lambda b:(-p2[b],b));r3=sorted(BOATS,key=lambda b:(-p3[b],b))
            rec.append({'family':fam,'l2':l2,'month':mon,'date':str(g.date.iloc[0]),'race_code':str(code).zfill(12),
                        'n_features':len(use),'pair_rank':rank_of(o,actual),
                        'second_rank':r2.index(a2)+1,'third_rank':r3.index(a3)+1})
    return pd.DataFrame(rec)


def metric(g,prefix=''):
    r={'races':len(g)}
    for k in (1,2,3,4,6,10,20):r[f'{prefix}top{k}']=100*((g.pair_rank>0)&(g.pair_rank<=k)).mean() if len(g) else np.nan
    r['second_top1']=100*(g.second_rank<=1).mean() if len(g) else np.nan
    r['second_top2']=100*(g.second_rank<=2).mean() if len(g) else np.nan
    r['third_top1']=100*(g.third_rank<=1).mean() if len(g) else np.nan
    r['third_top2']=100*(g.third_rank<=2).mean() if len(g) else np.nan
    return r


def objective(r):
    return .45*r['top2']+.30*r['top4']+.15*r['top6']+.10*r['top10']


def baseline_ranks(pred):
    # IMPORTANT: v96 imported only here, after all new-model predictions/configs
    # have been generated. It is benchmark-only and never enters training/order.
    import analyze_v251_4head_newroi_bridge as v251
    import analyze_v96_4corner_monthly_walkforward_tiebreak as v96
    base=v251.pair_orders(v96.read())
    d,_,_=v270.prepare();d=d[d._date<pd.Timestamp('2026-07-01')].copy();
    truth={str(r.race_code).zfill(12):(int(r.second),int(r.third)) for _,r in d[(pd.to_numeric(d.valid_result,errors='coerce')==1)&(pd.to_numeric(d.winner,errors='coerce')==4)].iterrows()}
    out=[]
    for _,r in pred.iterrows():
        key=(str(r.date),str(r.race_code).zfill(12));actual=truth.get(key[1]);old=base.get(key,[])
        out.append(rank_of(old,actual) if actual else 0)
    return out


def selected_codes():
    return v274.selected_codes()


def main():
    d,z=build_source()
    # Relative transforms are calculated per race from pre-result candidate values.
    base_for_rel=[c for c in list(ABILITY)+list(PLAYER)+list(PRIOR_HINTS)+list(START_HINTS)+list(POSITION)+list(CURRENT) if c in z]
    z=add_relative(z,base_for_rel)
    fams=family_map(z)
    allpred=[];grid=[]
    for fam,fs in fams.items():
        for l2 in L2_GRID:
            p=run_config(z,fs,fam,l2)
            if p.empty:continue
            allpred.append(p)
            for scope,mons in [('TUNE',TUNE),('HOLD',HOLD)]:
                g=p[p.month.isin(mons)]
                if g.empty:continue
                m=metric(g);m.update({'family':fam,'l2':l2,'scope':scope,'objective':objective(m),'avg_features':g.n_features.mean()});grid.append(m)
    P=pd.concat(allpred,ignore_index=True);G=pd.DataFrame(grid)
    # Choose solely on Feb-Mar.
    tune=G[G.scope=='TUNE'].sort_values(['objective','top2','top4','top6'],ascending=False)
    best=tune.iloc[0];bf=str(best.family);bl=float(best.l2)
    chosen=P[(P.family==bf)&(P.l2==bl)].copy()
    chosen['v96_rank']=baseline_ranks(chosen)
    sel=selected_codes();chosen['selected_SA']=chosen.race_code.astype(str).isin(sel).astype(int)
    chosen.to_csv(OUT_PRED,index=False);G.to_csv(OUT_GRID,index=False)

    monthly=[]
    for mon,g in chosen[chosen.month.isin(HOLD)].groupby('month'):
        m=metric(g);m.update({'month':mon,'scope':'HOLD_ALL'})
        for k in (1,2,4,6,10):m[f'v96_top{k}']=100*((g.v96_rank>0)&(g.v96_rank<=k)).mean()
        monthly.append(m)
        s=g[g.selected_SA==1]
        if len(s):
            m=metric(s);m.update({'month':mon,'scope':'HOLD_SA'})
            for k in (1,2,4,6,10):m[f'v96_top{k}']=100*((s.v96_rank>0)&(s.v96_rank<=k)).mean()
            monthly.append(m)
    M=pd.DataFrame(monthly);M.to_csv(OUT_MONTH,index=False)

    def row_for(g):
        m=metric(g)
        for k in (1,2,4,6,10):m[f'v96_top{k}']=100*((g.v96_rank>0)&(g.v96_rank<=k)).mean() if len(g) else np.nan
        return m
    hold=chosen[chosen.month.isin(HOLD)];sa=hold[hold.selected_SA==1]
    mh=row_for(hold);ms=row_for(sa)
    L=['# v279 independent 4-head opponent listwise rebuild','',
       '- **No v96 score/rank/order is used in training, features, candidate membership, blending, or tiebreaking.**',
       '- Separate SECOND/THIRD listwise-softmax rankers choose among all five opponents.',
       '- Pair ranking is `P(second=s) * P(third=t)` with `s != t`.',
       '- Features: primitive ability/course, frozen player history, frozen prior exhibition/ST, current exhibition components, and race-relative transforms.',
       '- Family/L2 choice uses Feb-Mar only. Apr-Jun is holdout-like model-choice evaluation.',
       '- Jul/Aug excluded; September not read; no odds. v96 appears only as a post-freeze benchmark.','',
       '## Feb-Mar model choice','',
       f'- chosen family: **{bf}**',f'- chosen L2: **{bl:g}**',f'- tune objective: **{best.objective:.2f}**',f'- average features: **{best.avg_features:.0f}**','',
       '### Top tune configurations','',
       '|family|L2|R|T2|T4|T6|T10|objective|', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in tune.head(10).iterrows():L.append(f'|{r.family}|{r.l2:g}|{int(r.races)}|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.objective:.2f}|')
    L += ['','## Apr-Jun holdout-like result','',
          '|scope|R|2nd T1|2nd T2|3rd T1|3rd T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in [('ALL 4-head wins',mh),('Frozen S+A head-wins',ms)]:
        L.append(f'|{name}|{int(m["races"])}|{m["second_top1"]:.1f}%|{m["second_top2"]:.1f}%|{m["third_top1"]:.1f}%|{m["third_top2"]:.1f}%|{m["top1"]:.1f}%|{m["top2"]:.1f}%|{m["top4"]:.1f}%|{m["top6"]:.1f}%|{m["top10"]:.1f}%|{m["v96_top2"]:.1f}%|{m["v96_top4"]:.1f}%|{m["v96_top6"]:.1f}%|{m["v96_top10"]:.1f}%|')
    L += ['','## Apr-Jun monthly stability (S+A)','',
          '|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in M[M.scope=='HOLD_SA'].iterrows():
        L.append(f'|{r.month}|{int(r.races)}|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.v96_top2:.1f}%|{r.v96_top4:.1f}%|{r.v96_top6:.1f}%|{r.v96_top10:.1f}%|')
    L += ['','## Decision rule',
          '- This is the first genuinely independent opponent rebuild. Do not force adoption merely because it is new.',
          '- If Apr-Jun S+A small-N coverage (especially Top2/Top4) is competitive and month-stable, the next step is exact 10,000-yen Dutch/composite-odds economics using this frozen order.',
          '- If it is weak, use v279 diagnostics to refine role-specific features/model class while staying independent of v96; do not fall back to v96 as a feature.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
