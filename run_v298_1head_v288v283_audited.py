#!/usr/bin/env python3
"""Run v298 with audited v288/v283 structure and vectorized listwise loss.

Semantics are unchanged from the frozen v283-style design: SECOND uses a five-way
listwise softmax with L2=10, THIRD uses a four-way conditional listwise softmax with
L2=0.3, and pair order remains TOP2XTOP2 with alpha2=.60.  The optimizer objective is
vectorized across race groups because the 1-head training universe is much larger
than the original 4-head-win research universe.

Only PRE/prior fields are used. Jul/Aug stay excluded upstream, September outcomes
are unread, meet_* is forbidden, and boat-1 losses stay in the exact denominator.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v297_1head_guard_trifecta5_research as settlement

SAFE=('grade','wr','local','motor','nst_strength','f_safety')
BOATS=v298.BOATS


class FastListwise:
    """Exact vectorized equivalent of v279/v282 grouped softmax loss."""
    group_col='race_code'; target_col='y2'; group_n=5
    def __init__(self,l2=1.0):
        self.l2=float(l2);self.imp=None;self.sc=None;self.beta=None;self.features=None
    def fit(self,df,features,ycol=None):
        self.features=list(features); ycol=ycol or self.target_col
        dd=df.reset_index(drop=True)
        X=dd[self.features].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        self.imp=SimpleImputer(strategy='median');X=self.imp.fit_transform(X)
        self.sc=StandardScaler();X=self.sc.fit_transform(X)
        idx=[];yi=[]
        for _,g in dd.groupby(self.group_col,sort=False):
            ix=g.index.to_numpy();y=g[ycol].to_numpy(int)
            if len(ix)!=self.group_n or y.sum()!=1:continue
            idx.append(ix);yi.append(int(np.argmax(y)))
        if not idx:raise RuntimeError('no valid listwise groups')
        idx=np.vstack(idx);yi=np.asarray(yi,dtype=int);Xg=X[idx];gg=np.arange(len(idx))
        p=X.shape[1]
        def fg(b):
            s=np.einsum('gkp,p->gk',Xg,b);ls=logsumexp(s,axis=1)
            loss=.5*self.l2*np.dot(b,b)+float(np.sum(ls-s[gg,yi]))
            pr=np.exp(s-ls[:,None])
            grad=self.l2*b+np.einsum('gk,gkp->p',pr,Xg)-Xg[gg,yi].sum(axis=0)
            return loss,grad
        res=minimize(lambda b:fg(b),np.zeros(p),jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-10})
        if not res.success and not np.all(np.isfinite(res.x)):
            raise RuntimeError(f'listwise optimizer failed: {res.message}')
        self.beta=res.x;return self
    def score(self,df):
        X=df[self.features].apply(pd.to_numeric,errors='coerce').to_numpy(float)
        X=self.sc.transform(self.imp.transform(X));return X@self.beta


class FastSecond(FastListwise):
    group_col='race_code';target_col='y2';group_n=5


class FastConditional(FastListwise):
    group_col='group_id';target_col='ycond';group_n=4
    def fit(self,df,features):return super().fit(df,features,'ycond')


def _scalar(x):
    return pd.to_numeric(pd.Series([x]),errors='coerce').iloc[0]


def curated_suffixes(d):
    """PRE-only PLAYER_START-like symmetric fields; fail closed on meet_* leakage."""
    out=[]
    for k in SAFE:
        if all(f'b{b}_{k}' in d for b in range(1,7)):out.append(k)
    for c in d.columns:
        if not c.startswith('b1_'):continue
        k=c[3:]
        if 'meet_' in k:continue
        if '_pl_' in k and all(f'b{b}_{k}' in d for b in range(1,7)):out.append(k)
    out=sorted(set(out))
    if any('meet_' in x for x in out):raise RuntimeError('forbidden meet_* opponent feature')
    return out


def add_threat(d):
    q,made=v298.add_threat_original(d)
    for k in SAFE:
        cols=[f'b{b}_{k}' for b in range(1,5)]
        if not all(c in q for c in cols):continue
        b1,b2,b3,b4=[pd.to_numeric(q[c],errors='coerce') for c in cols]
        feats={
            f'v298_role_b3_minus_b2_{k}':b3-b2,
            f'v298_role_b4_minus_b3_{k}':b4-b3,
            f'v298_role_b4_minus_b2_{k}':b4-b2,
            f'v298_role_attack34_minus_wall12_{k}':pd.concat([b3,b4],axis=1).max(axis=1)-pd.concat([b1,b2],axis=1).max(axis=1),
            f'v298_role_inside12_minus_attack34_{k}':pd.concat([b1,b2],axis=1).max(axis=1)-pd.concat([b3,b4],axis=1).max(axis=1),
        }
        for name,val in feats.items():q[name]=val;made.append(name)
    if all(f'b{b}_nst_strength' in q for b in range(1,5)):
        b1,b2,b3,b4=[pd.to_numeric(q[f'b{b}_nst_strength'],errors='coerce') for b in range(1,5)]
        wall=pd.concat([b1,b2],axis=1).max(axis=1);attack=pd.concat([b3,b4],axis=1).max(axis=1)
        q['v298_role_wall12_x_attack34_nst']=(wall-attack)*(attack-b1);made.append('v298_role_wall12_x_attack34_nst')
    return q,list(dict.fromkeys(made))


def cand_record(r,b,sufs,prefix=''):
    z={}
    if prefix:
        z[f'{prefix}pos_boat']=float(b);z[f'{prefix}pos_inner23']=float(b in (2,3));z[f'{prefix}pos_outer456']=float(b in (4,5,6))
        z[f'{prefix}pos_edge3']=float(b==3);z[f'{prefix}pos_edge4']=float(b==4);z[f'{prefix}pos_distance1']=float(b-1)
    else:
        z.update({'boat':int(b),'pos_boat':float(b),'pos_inner23':float(b in (2,3)),'pos_outer456':float(b in (4,5,6)),
                  'pos_edge3':float(b==3),'pos_edge4':float(b==4),'pos_distance1':float(b-1)})
    for k in sufs:
        cv=_scalar(r.get(f'b{b}_{k}',np.nan));h=_scalar(r.get(f'b1_{k}',np.nan))
        z[f'{prefix}cand_{k}']=cv;z[f'{prefix}diff1_{k}']=cv-h if pd.notna(cv) and pd.notna(h) else np.nan
        inner=[]
        for j in BOATS:
            if j>=b:break
            vv=_scalar(r.get(f'b{j}_{k}',np.nan))
            if pd.notna(vv):inner.append(float(vv))
        z[f'{prefix}innermax_{k}_minus_cand']=(max(inner)-cv) if inner and pd.notna(cv) else (0.0 if b==2 and pd.notna(cv) else np.nan)
    return z


def _add_race_relative(z,sufs):
    q=z.copy()
    for k in sufs:
        c=f'cand_{k}'
        if c not in q:continue
        x=pd.to_numeric(q[c],errors='coerce');q[c]=x;g=q.assign(_x=x).groupby('race_code')['_x'];med=g.transform('median')
        q[f'{c}__center']=x-med;q[f'{c}__pct']=q.assign(_x=x).groupby('race_code')['_x'].rank(pct=True,method='average')
    return q


def second_long(d,sufs):
    rec=[]
    for _,r in d.iterrows():
        a2,a3=v298.actual23(r.actual_combo)
        if int(r.head_hit)!=1 or a2 not in BOATS or a3 not in BOATS:continue
        for b in BOATS:
            z={'date':r.date,'month':r.month,'race_code':str(r.race_code).zfill(12),'y2':int(b==a2),'actual2':a2,'actual3':a3}
            z.update(cand_record(r,b,sufs));rec.append(z)
    return _add_race_relative(pd.DataFrame(rec),sufs)


def conditional_long(d,sufs):
    rec=[]
    for _,r in d.iterrows():
        a2,a3=v298.actual23(r.actual_combo)
        if int(r.head_hit)!=1 or a2 not in BOATS or a3 not in BOATS:continue
        for s in BOATS:
            sr=cand_record(r,s,sufs,'s_')
            for t in BOATS:
                if t==s:continue
                tr=cand_record(r,t,sufs,'t_')
                z={'date':r.date,'month':r.month,'race_code':str(r.race_code).zfill(12),'group_id':f'{str(r.race_code).zfill(12)}|{s}',
                   'second_boat':s,'third_boat':t,'train_group':int(s==a2),'ycond':int(s==a2 and t==a3),'actual2':a2,'actual3':a3,
                   'pair_same_side1':float((s<=3 and t<=3) or (s>=4 and t>=4)),'pair_second_inner23':float(s in (2,3)),
                   'pair_second_outer456':float(s in (4,5,6)),'pair_third_inner23':float(t in (2,3)),'pair_third_outer456':float(t in (4,5,6)),
                   'pair_adjacent':float(abs(s-t)==1),'pair_distance':float(abs(s-t)),'pair_third_minus_second':float(t-s),
                   'pair_second_is2':float(s==2),'pair_second_is3':float(s==3),'pair_second_is4':float(s==4),
                   'pair_second_is5':float(s==5),'pair_second_is6':float(s==6)}
                z.update(sr);z.update(tr)
                for k in sufs:
                    tv=z.get(f't_cand_{k}',np.nan);sv=z.get(f's_cand_{k}',np.nan)
                    z[f'diff_{k}']=tv-sv if pd.notna(tv) and pd.notna(sv) else np.nan
                    z[f'prod_{k}']=tv*sv if pd.notna(tv) and pd.notna(sv) else np.nan
                rec.append(z)
    return pd.DataFrame(rec)


if __name__=='__main__':
    v298.add_threat_original=v298.add_threat
    v298.add_threat=add_threat;v298.suffixes=curated_suffixes;v298.cand_record=cand_record
    v298.second_long=second_long;v298.conditional_long=conditional_long
    # Same objective/regularization as frozen v283 lineage, only vectorized.
    v298.v279.ListwiseSoftmax=FastSecond;v298.v282.ListwiseN=FastConditional
    settlement.AUDIT.clear();v298.v297.settle_full_after_freeze=settlement.settle_union_after_freeze
    print('v298 upgrade: curated PLAYER_START + v288 PRE roles + v282 conditional pairs + vectorized exact listwise loss',flush=True)
    v298.main()
