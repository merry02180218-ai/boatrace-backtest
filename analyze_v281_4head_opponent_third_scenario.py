#!/usr/bin/env python3
"""v281: independent THIRD-role scenario research for the 4-head opponent model.

No v96 score/rank/order is used in training, feature construction, candidate
restriction, blending, or pair ordering. v96 is benchmark-only after the new
order is frozen.

SECOND stays on the strong v280 PLAYER_START listwise route (L2=10). THIRD is
rebuilt with scenario features describing inside survival / outside follow,
boat-4 current attack context, opponent-vs-4 current-foot gaps, and race-relative
signals. Pair ordering can additionally use a smoothed P(third=t | second=s)
transition prior learned ONLY from races before each evaluation month.

Selection discipline:
- THIRD family/L2: Feb-Mar only.
- pair alpha / transition gamma: Feb-Mar only.
- Apr-Jun: untouched holdout-like evaluation.
- Jul/Aug excluded; September not read; no odds.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd

import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v280_4head_opponent_role_split as v280
import analyze_v278_4head_opponent_current_exhibition_audit as v278
import analyze_v274_4head_opponent_feature_audit as v274

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v281_4head_opponent_third_scenario.csv'
GRID3=ROOT/'analysis_v281_4head_opponent_third_grid.csv'
GRIDPAIR=ROOT/'analysis_v281_4head_opponent_pair_grid.csv'
MONTH=ROOT/'analysis_v281_4head_opponent_monthly.csv'
COEF=ROOT/'analysis_v281_4head_opponent_third_coefficients.csv'
SUM=ROOT/'summary_v281_4head_opponent_third_scenario.md'

SECOND_FAMILY='PLAYER_START'
SECOND_L2=10.0
L2S=(0.3,1.0,3.0,10.0)
ALPHAS=(0.55,0.60,0.65,0.70,0.75,0.80)
GAMMAS=(0.0,0.15,0.30,0.50,0.75)


def add_head4_current(z):
    q=z.copy()
    h=q[['date','race_code','month']].drop_duplicates().copy();h['boat']=4
    h=v278.add_current(h)
    ren={c:f'h4_{c}' for c in v279.CURRENT if c in h.columns}
    h=h[['race_code']+list(ren)].rename(columns=ren)
    return q.merge(h,on='race_code',how='left')


def add_scenario(z):
    q=add_head4_current(z)
    # Non-linear positional identity. These are known pre-race and let the model
    # learn inner-survival vs outer-follow patterns without assuming monotonicity.
    for b in v279.BOATS:q[f'is_boat{b}']=(q.boat.astype(int)==b).astype(float)
    q['is_inner123']=(q.boat.astype(int)<4).astype(float)
    q['is_outer56']=(q.boat.astype(int)>4).astype(float)
    q['is_inner_edge3']=(q.boat.astype(int)==3).astype(float)
    q['is_outer_edge5']=(q.boat.astype(int)==5).astype(float)

    # Boat-4 current attack context. corrected_direct components are all scaled
    # so larger is better after rank conversion.
    hs=[f'h4_{c}' for c in ('cur_ex','cur_st','cur_orig_straight','cur_orig_avg') if f'h4_{c}' in q]
    q['h4_attack']=q[hs].apply(pd.to_numeric,errors='coerce').mean(axis=1) if hs else np.nan
    ht=[f'h4_{c}' for c in ('cur_orig_lap','cur_orig_turn') if f'h4_{c}' in q]
    q['h4_turning']=q[ht].apply(pd.to_numeric,errors='coerce').mean(axis=1) if ht else np.nan

    # Opponent-vs-head foot gaps and interactions. Positive gap means opponent
    # has the stronger current component.
    for c in v279.CURRENT:
        hc=f'h4_{c}'
        if c in q and hc in q:
            x=pd.to_numeric(q[c],errors='coerce');h=pd.to_numeric(q[hc],errors='coerce')
            q[f'{c}__vs4']=x-h
            q[f'{c}__abs4']=(x-h).abs()
    for side in ('is_inner123','is_outer56','is_inner_edge3','is_outer_edge5'):
        q[f'h4_attack_x_{side}']=pd.to_numeric(q['h4_attack'],errors='coerce')*q[side]
    for c in ('cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_st'):
        if c in q:
            q[f'h4_attack_x_{c}']=pd.to_numeric(q['h4_attack'],errors='coerce')*pd.to_numeric(q[c],errors='coerce')
    return q


def scenario_families(z):
    base_for_rel=[c for c in list(v279.ABILITY)+list(v279.PLAYER)+list(v279.PRIOR_HINTS)+list(v279.START_HINTS)+list(v279.POSITION)+list(v279.CURRENT) if c in z]
    q=v279.add_relative(z,base_for_rel)
    base=v279.family_map(q)
    sc=[c for c in q.columns if c.startswith('is_boat') or c in ('is_inner123','is_outer56','is_inner_edge3','is_outer_edge5','h4_attack','h4_turning') or '__vs4' in c or '__abs4' in c or c.startswith('h4_attack_x_')]
    current=list(v279.available(set(q.columns),v279.CURRENT))
    light=[c for c in sc if c in ('is_inner123','is_outer56','is_inner_edge3','is_outer_edge5','h4_attack','h4_turning') or c.endswith('__vs4') or c.startswith('h4_attack_x_is_')]
    fam={
      'THIRD_PLAYER_START':list(base['PLAYER_START']),
      'THIRD_SCENARIO_LIGHT':list(dict.fromkeys(base['PLAYER_START']+light)),
      'THIRD_SCENARIO_CURRENT':list(dict.fromkeys(base['PLAYER_START']+current+sc)),
      'THIRD_RICH_SCENARIO':list(dict.fromkeys(base['RICH']+sc)),
    }
    return q,fam,base


def transition_prior(tr,laplace=1.0):
    counts={(s,t):laplace for s in v279.BOATS for t in v279.BOATS if s!=t}
    for _,g in tr.groupby('race_code'):
        if len(g)!=5 or g.y2.sum()!=1 or g.y3.sum()!=1:continue
        s=int(g.loc[g.y2==1,'boat'].iloc[0]);t=int(g.loc[g.y3==1,'boat'].iloc[0])
        if s!=t:counts[(s,t)]+=1.0
    out={}
    for s in v279.BOATS:
        den=sum(counts[(s,t)] for t in v279.BOATS if t!=s)
        for t in v279.BOATS:
            if t!=s:out[(s,t)]=counts[(s,t)]/den
    return out


def role_predictions(z,f2,l22,f3,l23,keep_coef=False):
    rec=[];co=[]
    for mon in v279.MONTHS:
        tr=z[z.month<mon].copy();te=z[z.month==mon].copy()
        if tr.race_code.nunique()<v279.MIN_TRAIN or te.empty:continue
        use2=v279.good_features(tr,f2);use3=v279.good_features(tr,f3)
        if len(use2)<5 or len(use3)<5:continue
        m2=v279.ListwiseSoftmax(l22).fit(tr,use2,'y2');m3=v279.ListwiseSoftmax(l23).fit(tr,use3,'y3')
        te=te.copy();te['s2']=m2.score(te);te['s3']=m3.score(te);prior=transition_prior(tr)
        if keep_coef:
            for f,b in zip(m3.features,m3.beta):co.append({'month':mon,'feature':f,'beta':float(b)})
        for code,g in te.groupby('race_code'):
            if len(g)!=5 or g.y2.sum()!=1 or g.y3.sum()!=1:continue
            p2=v279.probs_within_race(g,'s2');p3=v279.probs_within_race(g,'s3')
            a2=int(g.loc[g.y2==1,'boat'].iloc[0]);a3=int(g.loc[g.y3==1,'boat'].iloc[0])
            o2=sorted(v279.BOATS,key=lambda b:(-p2[b],b));o3=sorted(v279.BOATS,key=lambda b:(-p3[b],b))
            rec.append({'month':mon,'date':str(g.date.iloc[0]),'race_code':str(code).zfill(12),'actual2':a2,'actual3':a3,
                        'p2':'|'.join(f'{b}:{p2[b]:.12g}' for b in v279.BOATS),
                        'p3':'|'.join(f'{b}:{p3[b]:.12g}' for b in v279.BOATS),
                        'prior':'|'.join(f'{s}>{t}:{prior[(s,t)]:.12g}' for s in v279.BOATS for t in v279.BOATS if s!=t),
                        'second_rank':o2.index(a2)+1,'third_rank':o3.index(a3)+1,
                        'nfeat2':len(use2),'nfeat3':len(use3)})
    return pd.DataFrame(rec),pd.DataFrame(co)


def parse_probs(s):return {int(x.split(':')[0]):float(x.split(':')[1]) for x in str(s).split('|')}
def parse_prior(s):
    o={}
    for x in str(s).split('|'):
        a,v=x.split(':');s1,t1=a.split('>');o[(int(s1),int(t1))]=float(v)
    return o


def pair_order(p2,p3,prior,alpha,gamma):
    a=[]
    for s in v279.BOATS:
        for t in v279.BOATS:
            if s==t:continue
            sc=alpha*math.log(max(p2[s],1e-12))+(1-alpha)*math.log(max(p3[t],1e-12))
            if gamma>0:sc += gamma*math.log(max(prior.get((s,t),1e-12),1e-12))
            a.append((sc,s,t))
    a.sort(key=lambda x:(-x[0],x[1],x[2]));return [(s,t) for _,s,t in a]


def add_pair_rank(raw,alpha,gamma):
    q=raw.copy();rr=[]
    for _,r in q.iterrows():
        p2=parse_probs(r.p2);p3=parse_probs(r.p3);pr=parse_prior(r.prior);actual=(int(r.actual2),int(r.actual3))
        rr.append(v279.rank_of(pair_order(p2,p3,pr,alpha,gamma),actual))
    q['pair_rank']=rr;return q


def role_stat(g):
    return {'races':len(g),'second_top1':100*(g.second_rank<=1).mean(),'second_top2':100*(g.second_rank<=2).mean(),
            'third_top1':100*(g.third_rank<=1).mean(),'third_top2':100*(g.third_rank<=2).mean()}


def main():
    _,z0=v279.build_source();z0=add_scenario(z0);z,fams,base=scenario_families(z0)
    f2=base[SECOND_FAMILY]

    # Choose THIRD independently on Feb-Mar only.
    grows=[];cache={}
    for fam,f3 in fams.items():
        for l2 in L2S:
            raw,_=role_predictions(z,f2,SECOND_L2,f3,l2,False);cache[(fam,l2)]=raw
            g=raw[raw.month.isin(v279.TUNE)];m=role_stat(g)
            obj=.60*m['third_top1']+.40*m['third_top2']
            grows.append({'family':fam,'l2':l2,**m,'third_objective':obj,'avg_features':raw.nfeat3.mean() if len(raw) else np.nan})
    G=pd.DataFrame(grows).sort_values(['third_objective','third_top1','third_top2'],ascending=False);G.to_csv(GRID3,index=False)
    best3=G.iloc[0];fam3=str(best3.family);l23=float(best3.l2)

    # Refit frozen roles and save THIRD coefficients for interpretability.
    raw,coef=role_predictions(z,f2,SECOND_L2,fams[fam3],l23,True)
    coef.to_csv(COEF,index=False)

    # Pair composition selected on Feb-Mar only.
    rows=[]
    for a in ALPHAS:
        for gm in GAMMAS:
            q=add_pair_rank(raw,a,gm);g=q[q.month.isin(v279.TUNE)];m=v279.metric(g)
            obj=.50*m['top2']+.30*m['top4']+.15*m['top6']+.05*m['top10']
            rows.append({'alpha2':a,'transition_gamma':gm,'races':len(g),'top1':m['top1'],'top2':m['top2'],'top4':m['top4'],'top6':m['top6'],'top10':m['top10'],'objective':obj})
    PG=pd.DataFrame(rows).sort_values(['objective','top2','top4'],ascending=False);PG.to_csv(GRIDPAIR,index=False)
    bp=PG.iloc[0];alpha=float(bp.alpha2);gamma=float(bp.transition_gamma)
    q=add_pair_rank(raw,alpha,gamma);q['selected_SA']=q.race_code.astype(str).isin(v274.selected_codes()).astype(int)
    # Benchmark only AFTER v281 config/order is frozen.
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

    # Average standardized THIRD coefficients across Apr-Jun training fits.
    csum=pd.DataFrame()
    if len(coef):
        cc=coef[coef.month.isin(v279.HOLD)].copy()
        if len(cc):
            csum=cc.groupby('feature').beta.agg(['mean','std','count']).reset_index();csum['abs_mean']=csum['mean'].abs();csum=csum.sort_values('abs_mean',ascending=False)

    L=['# v281 independent THIRD scenario model','',
       '- v96 is not used in features, training, candidate restriction, blending, or ordering; benchmark only after freeze.',
       '- SECOND fixed to PLAYER_START / L2=10 from v280. THIRD family/L2 selected on Feb-Mar only.',
       '- Scenario features include inside/outer identity, boat-4 current attack context, opponent-vs-4 foot gaps, and interactions.',
       '- Optional P(third|second) transition prior is learned only from races before each evaluation month.',
       '- Jul/Aug excluded; September not read; no odds.','',
       '## Frozen THIRD choice from Feb-Mar','',
       f'- THIRD: **{fam3}**, L2 **{l23:g}**, objective **{best3.third_objective:.2f}**',
       f'- SECOND: **{SECOND_FAMILY}**, L2 **{SECOND_L2:g}**','',
       '### THIRD grid','', '|family|L2|R|T1|T2|objective|features|','|---|---:|---:|---:|---:|---:|---:|']
    for _,r in G.iterrows():L.append(f'|{r.family}|{r.l2:g}|{int(r.races)}|{r.third_top1:.1f}%|{r.third_top2:.1f}%|{r.third_objective:.2f}|{r.avg_features:.0f}|')
    L += ['','## Pair composition frozen on Feb-Mar','',f'- second weight alpha: **{alpha:.2f}**',f'- transition gamma: **{gamma:.2f}**',
          f'- tune T2/T4/T6/T10: **{bp.top2:.1f}% / {bp.top4:.1f}% / {bp.top6:.1f}% / {bp.top10:.1f}%**','',
          '## Apr-Jun holdout-like result','',
          '|scope|R|2nd T1|T2|3rd T1|T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in [('ALL 4-head wins',mh),('Frozen S+A head-wins',ms)]:
        L.append(f'|{name}|{int(m["races"])}|{m["second_top1"]:.1f}%|{m["second_top2"]:.1f}%|{m["third_top1"]:.1f}%|{m["third_top2"]:.1f}%|{m["top1"]:.1f}%|{m["top2"]:.1f}%|{m["top4"]:.1f}%|{m["top6"]:.1f}%|{m["top10"]:.1f}%|{m["v96_top2"]:.1f}%|{m["v96_top4"]:.1f}%|{m["v96_top6"]:.1f}%|{m["v96_top10"]:.1f}%|')
    L += ['','## S+A monthly','', '|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in M[M.scope=='SA'].iterrows():L.append(f'|{r.month}|{int(r.races)}|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.v96_top2:.1f}%|{r.v96_top4:.1f}%|{r.v96_top6:.1f}%|{r.v96_top10:.1f}%|')
    L += ['','## Strongest THIRD coefficients (Apr-Jun fits, standardized)','', '|feature|mean beta|abs mean|months|','|---|---:|---:|---:|']
    for _,r in csum.head(18).iterrows():L.append(f'|{r.feature}|{r["mean"]:+.4f}|{r.abs_mean:.4f}|{int(r["count"])}|')
    L += ['','## Decision','- Continue independent opponent-model development; do not use v96 as a feature.',
          '- If scenario/transition features improve THIRD and small-N pair coverage, use v281 as the next independent baseline.',
          '- If not, next step is a dedicated conditional THIRD model P(third | predicted-second, race context), not a return to v96.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
