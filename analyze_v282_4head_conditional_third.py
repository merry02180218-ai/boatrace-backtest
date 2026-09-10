#!/usr/bin/env python3
"""v282: independent conditional THIRD model for boat-4-head races.

Core idea
---------
Keep the strong independent SECOND listwise model, but replace the unconditional
THIRD ranker with P(third=t | second=s, pre-result race context). For each
candidate second boat s, the model ranks only the four remaining boats t.
Final pair order is P2(s)^alpha * P3(t|s)^(1-alpha).

This is NOT the old direct 20-pair binary model: training groups are four-way
conditional THIRD choices using the historical actual second boat only as the
conditioning label in prior training races. At inference all five possible
second boats are evaluated, each with four third candidates.

Discipline
----------
* No v96 score/rank/order in features, training, restriction, blending or order.
* SECOND fixed to PLAYER_START/L2=10 from v280.
* Conditional THIRD family/L2 selected on Feb-Mar only.
* Pair alpha selected on Feb-Mar only; Apr-Jun untouched holdout-like evaluation.
* Jul/Aug excluded; September not read; no odds.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v281_4head_opponent_third_scenario as v281
import analyze_v274_4head_opponent_feature_audit as v274

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v282_4head_conditional_third.csv'
GRID3=ROOT/'analysis_v282_4head_conditional_third_grid.csv'
GRIDPAIR=ROOT/'analysis_v282_4head_conditional_pair_grid.csv'
MONTH=ROOT/'analysis_v282_4head_conditional_monthly.csv'
COEF=ROOT/'analysis_v282_4head_conditional_third_coefficients.csv'
SUM=ROOT/'summary_v282_4head_conditional_third.md'

SECOND_FAMILY='PLAYER_START';SECOND_L2=10.0
L2S=(0.3,1.0,3.0,10.0)
ALPHAS=(0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80)

PAIR_KEYS=(
 'v93_national','v93_local','v93_motor','v93_grade','v93_nst',
 'pref_pl_all_p2','pref_pl_all_win','pref_pl_frame_p2','pref_pl_recent_p2','pref_pl_frame_win',
 'suf_st_raw','suf_st_raw_strength','suf_st_corr_strength',
 'cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg',
)

class ListwiseN:
    def __init__(self,l2=1.0):self.l2=float(l2);self.imp=None;self.sc=None;self.beta=None;self.features=None
    def fit(self,df,features):
        self.features=list(features)
        X=df[self.features].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        self.imp=SimpleImputer(strategy='median');X=self.imp.fit_transform(X)
        self.sc=StandardScaler();X=self.sc.fit_transform(X)
        groups=[]
        dd=df.reset_index(drop=True)
        for _,g in dd.groupby('group_id',sort=False):
            idx=g.index.to_numpy();y=g.ycond.to_numpy(int)
            if len(idx)!=4 or y.sum()!=1:continue
            groups.append((idx,int(np.argmax(y))))
        if not groups:raise RuntimeError('no conditional groups')
        p=X.shape[1]
        def fg(b):
            loss=.5*self.l2*np.dot(b,b);grad=self.l2*b.copy()
            for idx,yi in groups:
                Xi=X[idx];s=Xi@b;ls=logsumexp(s);loss+=ls-s[yi]
                pr=np.exp(s-ls);grad+=Xi.T@pr-Xi[yi]
            return loss,grad
        res=minimize(lambda b:fg(b),np.zeros(p),jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-10})
        self.beta=res.x;return self
    def score(self,df):
        X=df[self.features].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        X=self.sc.transform(self.imp.transform(X));return X@self.beta


def prep():
    _,z0=v279.build_source();z0=v281.add_scenario(z0)
    base_for_rel=[c for c in list(v279.ABILITY)+list(v279.PLAYER)+list(v279.PRIOR_HINTS)+list(v279.START_HINTS)+list(v279.POSITION)+list(v279.CURRENT) if c in z0]
    z=v279.add_relative(z0,base_for_rel);base=v279.family_map(z)
    return z,base


def make_pairs(z,base):
    # Candidate-third features are taken from t. Second-to-third relational
    # features use only pre-result values of s and t.
    tbase=[c for c in base['PLAYER_START'] if c in z]
    scenario=[c for c in z.columns if c.startswith('is_boat') or c in ('is_inner123','is_outer56','is_inner_edge3','is_outer_edge5','h4_attack','h4_turning') or '__vs4' in c or '__abs4' in c or c.startswith('h4_attack_x_')]
    rec=[]
    for code,g in z.groupby('race_code'):
        if len(g)!=5 or g.y2.sum()!=1 or g.y3.sum()!=1:continue
        by={int(r.boat):r for _,r in g.iterrows()};a2=int(g.loc[g.y2==1,'boat'].iloc[0]);a3=int(g.loc[g.y3==1,'boat'].iloc[0])
        date=str(g.date.iloc[0]);mon=str(g.month.iloc[0])
        for s in v279.BOATS:
            sr=by[s]
            for t in v279.BOATS:
                if t==s:continue
                tr=by[t];r={'date':date,'month':mon,'race_code':str(code).zfill(12),'second_boat':s,'third_boat':t,
                              'group_id':f'{str(code).zfill(12)}|{s}','actual2':a2,'actual3':a3,
                              'train_group':int(s==a2),'ycond':int(s==a2 and t==a3)}
                for c in tbase:r[f't_{c}']=tr.get(c,np.nan)
                for c in scenario:r[f't_{c}']=tr.get(c,np.nan)
                # Pair-position structure.
                r['pair_same_side4']=float((s<4 and t<4) or (s>4 and t>4))
                r['pair_second_inner']=float(s<4);r['pair_second_outer']=float(s>4)
                r['pair_third_inner']=float(t<4);r['pair_third_outer']=float(t>4)
                r['pair_adjacent']=float(abs(t-s)==1);r['pair_distance']=float(abs(t-s))
                r['pair_third_minus_second']=float(t-s)
                r['pair_second_is1']=float(s==1);r['pair_second_is2']=float(s==2);r['pair_second_is3']=float(s==3);r['pair_second_is5']=float(s==5);r['pair_second_is6']=float(s==6)
                # Third-vs-second ability/foot differences and interactions.
                for c in PAIR_KEYS:
                    if c in z:
                        tv=pd.to_numeric(pd.Series([tr.get(c,np.nan)]),errors='coerce').iloc[0]
                        sv=pd.to_numeric(pd.Series([sr.get(c,np.nan)]),errors='coerce').iloc[0]
                        r[f'diff_{c}']=tv-sv if pd.notna(tv) and pd.notna(sv) else np.nan
                        r[f'prod_{c}']=tv*sv if pd.notna(tv) and pd.notna(sv) else np.nan
                rec.append(r)
    p=pd.DataFrame(rec)
    tcols=[c for c in p.columns if c.startswith('t_')]
    pos=[c for c in p.columns if c.startswith('pair_')]
    dif=[c for c in p.columns if c.startswith('diff_')]
    prod=[c for c in p.columns if c.startswith('prod_')]
    fam={
      'COND_BASE':list(dict.fromkeys(tcols+pos)),
      'COND_DIFF':list(dict.fromkeys(tcols+pos+dif)),
      'COND_DIFF_PROD':list(dict.fromkeys(tcols+pos+dif+prod)),
      'COND_COMPACT':list(dict.fromkeys([c for c in tcols if any(k in c for k in ('v93_national','v93_local','pl_all_p2','pl_all_win','pl_recent_p2','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_st','h4_attack','is_boat','is_inner','is_outer'))]+pos+dif)),
    }
    return p,fam


def good(tr,fs):
    o=[]
    for c in fs:
        x=pd.to_numeric(tr[c],errors='coerce')
        if x.notna().mean()>=.55 and x.nunique(dropna=True)>=2:o.append(c)
    return o


def second_probs(z,base):
    rec=[];fs=base[SECOND_FAMILY]
    for mon in v279.MONTHS:
        tr=z[z.month<mon].copy();te=z[z.month==mon].copy()
        if tr.race_code.nunique()<v279.MIN_TRAIN or te.empty:continue
        use=v279.good_features(tr,fs);m=v279.ListwiseSoftmax(SECOND_L2).fit(tr,use,'y2');te=te.copy();te['s2']=m.score(te)
        for code,g in te.groupby('race_code'):
            if len(g)!=5:continue
            p2=v279.probs_within_race(g,'s2')
            rec.append({'month':mon,'date':str(g.date.iloc[0]),'race_code':str(code).zfill(12),'p2':'|'.join(f'{b}:{p2[b]:.12g}' for b in v279.BOATS)})
    return pd.DataFrame(rec)


def run_conditional(pairs,fs,l2,keep_coef=False):
    rec=[];co=[]
    for mon in v279.MONTHS:
        tr=pairs[(pairs.month<mon)&(pairs.train_group==1)].copy();te=pairs[pairs.month==mon].copy()
        if tr.race_code.nunique()<v279.MIN_TRAIN or te.empty:continue
        use=good(tr,fs);m=ListwiseN(l2).fit(tr,use);te=te.copy();te['sc']=m.score(te)
        if keep_coef:
            for f,b in zip(m.features,m.beta):co.append({'month':mon,'feature':f,'beta':float(b)})
        for code,g in te.groupby('race_code'):
            a2=int(g.actual2.iloc[0]);a3=int(g.actual3.iloc[0]);cond={};actual_rank=0
            for s,gs in g.groupby('second_boat'):
                ss=gs.sc.to_numpy(float);pp=np.exp(ss-logsumexp(ss))
                for t,v in zip(gs.third_boat.astype(int),pp):cond[(int(s),int(t))]=float(v)
                if int(s)==a2:
                    order=[int(x) for x in gs.assign(_p=pp).sort_values(['_p','third_boat'],ascending=[False,True]).third_boat]
                    actual_rank=order.index(a3)+1 if a3 in order else 0
            rec.append({'month':mon,'date':str(g.date.iloc[0]),'race_code':str(code).zfill(12),'actual2':a2,'actual3':a3,'cond_rank':actual_rank,
                        'cond':'|'.join(f'{s}>{t}:{cond[(s,t)]:.12g}' for s in v279.BOATS for t in v279.BOATS if s!=t),'nfeat3':len(use)})
    return pd.DataFrame(rec),pd.DataFrame(co)


def parse_p2(s):return {int(x.split(':')[0]):float(x.split(':')[1]) for x in str(s).split('|')}
def parse_cond(s):
    o={}
    for x in str(s).split('|'):
        a,v=x.split(':');s1,t1=a.split('>');o[(int(s1),int(t1))]=float(v)
    return o


def pair_order(p2,pc,alpha):
    a=[]
    for s in v279.BOATS:
        for t in v279.BOATS:
            if s==t:continue
            sc=alpha*math.log(max(p2[s],1e-12))+(1-alpha)*math.log(max(pc[(s,t)],1e-12))
            a.append((sc,s,t))
    a.sort(key=lambda x:(-x[0],x[1],x[2]));return [(s,t) for _,s,t in a]


def add_pair_rank(raw,alpha):
    q=raw.copy();rr=[];r2=[]
    for _,r in q.iterrows():
        p2=parse_p2(r.p2);pc=parse_cond(r.cond);actual=(int(r.actual2),int(r.actual3));order=pair_order(p2,pc,alpha);rr.append(v279.rank_of(order,actual))
        o2=sorted(v279.BOATS,key=lambda b:(-p2[b],b));r2.append(o2.index(actual[0])+1)
    q['pair_rank']=rr;q['second_rank']=r2;q['third_rank']=q.cond_rank;return q


def metric(g):return v279.metric(g)


def main():
    z,base=prep();pairs,fams=make_pairs(z,base);p2=second_probs(z,base)
    grows=[];cache={}
    for fam,fs in fams.items():
        for l2 in L2S:
            cp,_=run_conditional(pairs,fs,l2,False);cache[(fam,l2)]=cp
            g=cp[cp.month.isin(v279.TUNE)];t1=100*(g.cond_rank<=1).mean();t2=100*(g.cond_rank<=2).mean();obj=.60*t1+.40*t2
            grows.append({'family':fam,'l2':l2,'races':len(g),'third_top1':t1,'third_top2':t2,'third_objective':obj,'avg_features':cp.nfeat3.mean()})
    G=pd.DataFrame(grows).sort_values(['third_objective','third_top1','third_top2'],ascending=False);G.to_csv(GRID3,index=False)
    b3=G.iloc[0];fam3=str(b3.family);l23=float(b3.l2)
    cp,coef=run_conditional(pairs,fams[fam3],l23,True);coef.to_csv(COEF,index=False)
    raw=cp.merge(p2,on=['month','date','race_code'],how='inner')

    pg=[]
    for a in ALPHAS:
        q=add_pair_rank(raw,a);g=q[q.month.isin(v279.TUNE)];m=metric(g);obj=.50*m['top2']+.30*m['top4']+.15*m['top6']+.05*m['top10']
        pg.append({'alpha2':a,'races':len(g),'top1':m['top1'],'top2':m['top2'],'top4':m['top4'],'top6':m['top6'],'top10':m['top10'],'objective':obj})
    PG=pd.DataFrame(pg).sort_values(['objective','top2','top4'],ascending=False);PG.to_csv(GRIDPAIR,index=False);bp=PG.iloc[0];alpha=float(bp.alpha2)
    q=add_pair_rank(raw,alpha);q['selected_SA']=q.race_code.astype(str).isin(v274.selected_codes()).astype(int)
    q['v96_rank']=v279.baseline_ranks(q);q.to_csv(OUT,index=False)

    mr=[]
    for mon,g in q[q.month.isin(v279.HOLD)].groupby('month'):
        for scope,gg in [('ALL',g),('SA',g[g.selected_SA==1])]:
            if gg.empty:continue
            m=metric(gg);m.update({'month':mon,'scope':scope})
            for k in (2,4,6,10):m[f'v96_top{k}']=100*((gg.v96_rank>0)&(gg.v96_rank<=k)).mean()
            mr.append(m)
    M=pd.DataFrame(mr);M.to_csv(MONTH,index=False)
    def rep(g):
        m=metric(g)
        for k in (2,4,6,10):m[f'v96_top{k}']=100*((g.v96_rank>0)&(g.v96_rank<=k)).mean() if len(g) else np.nan
        return m
    h=q[q.month.isin(v279.HOLD)];s=h[h.selected_SA==1];mh=rep(h);ms=rep(s)

    csum=pd.DataFrame()
    if len(coef):
        cc=coef[coef.month.isin(v279.HOLD)].copy()
        if len(cc):csum=cc.groupby('feature').beta.agg(['mean','std','count']).reset_index().assign(abs_mean=lambda x:x['mean'].abs()).sort_values('abs_mean',ascending=False)

    L=['# v282 independent conditional THIRD model','',
       '- SECOND: independent PLAYER_START/L2=10. THIRD is P(third | candidate second, pre-result context).',
       '- No v96 feature/order/candidate restriction/blending. v96 is benchmark only after freeze.',
       '- THIRD family/L2 and pair alpha selected on Feb-Mar only; Apr-Jun untouched holdout-like evaluation.',
       '- Jul/Aug excluded; September not read; no odds.','',
       '## Conditional THIRD choice (Feb-Mar)','',f'- family: **{fam3}**',f'- L2: **{l23:g}**',f'- conditional THIRD Top1/Top2: **{b3.third_top1:.1f}% / {b3.third_top2:.1f}%**','',
       '|family|L2|R|cond T1|T2|objective|features|','|---|---:|---:|---:|---:|---:|---:|']
    for _,r in G.iterrows():L.append(f'|{r.family}|{r.l2:g}|{int(r.races)}|{r.third_top1:.1f}%|{r.third_top2:.1f}%|{r.third_objective:.2f}|{r.avg_features:.0f}|')
    L += ['','## Pair alpha frozen on Feb-Mar','',f'- alpha2: **{alpha:.2f}**',f'- tune T2/T4/T6/T10: **{bp.top2:.1f}% / {bp.top4:.1f}% / {bp.top6:.1f}% / {bp.top10:.1f}%**','',
          '## Apr-Jun holdout-like result','',
          '|scope|R|2nd T1|T2|cond 3rd T1|T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,m in [('ALL 4-head wins',mh),('Frozen S+A head-wins',ms)]:
        L.append(f'|{name}|{int(m["races"])}|{m["second_top1"]:.1f}%|{m["second_top2"]:.1f}%|{m["third_top1"]:.1f}%|{m["third_top2"]:.1f}%|{m["top1"]:.1f}%|{m["top2"]:.1f}%|{m["top4"]:.1f}%|{m["top6"]:.1f}%|{m["top10"]:.1f}%|{m["v96_top2"]:.1f}%|{m["v96_top4"]:.1f}%|{m["v96_top6"]:.1f}%|{m["v96_top10"]:.1f}%|')
    L += ['','## S+A monthly','', '|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in M[M.scope=='SA'].iterrows():L.append(f'|{r.month}|{int(r.races)}|{r.top2:.1f}%|{r.top4:.1f}%|{r.top6:.1f}%|{r.top10:.1f}%|{r.v96_top2:.1f}%|{r.v96_top4:.1f}%|{r.v96_top6:.1f}%|{r.v96_top10:.1f}%|')
    L += ['','## Strongest conditional THIRD coefficients (Apr-Jun fits)','', '|feature|mean beta|abs mean|months|','|---|---:|---:|---:|']
    for _,r in csum.head(20).iterrows():L.append(f'|{r.feature}|{r["mean"]:+.4f}|{r.abs_mean:.4f}|{int(r["count"])}|')
    L += ['','## Decision','- This remains an independent opponent-model branch; v96 is not a fallback feature.',
          '- If conditional THIRD improves Apr-Jun small-N pair coverage, promote it to the next candidate and then test exact 10,000-yen Dutch economics.',
          '- Otherwise research should focus on regime-splitting the conditional THIRD task (inner-survival vs outer-follow) with all regime choices frozen on pre-Apr data.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
