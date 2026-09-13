from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUTJ=Path('research_v289_3head_wave36g_rank_rebuild.json')
OUT=Path('analysis_v289_3head_wave36g_rank_rebuild.csv')
CUT=.365448
BOATS=[1,2,4,5,6]
COMBOS=base.COMBOS

def pairmat(df):
    mats=[]; sec=np.array([int(c.split('-')[1]) for c in COMBOS]); thi=np.array([int(c.split('-')[2]) for c in COMBOS]); n=len(df)
    for q in BOATS:mats.append(np.tile((sec==q).astype(float),n))
    for q in BOATS:mats.append(np.tile((thi==q).astype(float),n))
    for met in base.METRICS:
        V={b:base.num(df[f'card__艇{b}_{met}']).to_numpy() for b in range(1,7)}
        v3=np.repeat(V[3],20); va=np.concatenate([[V[int(c.split('-')[1])][i] for c in COMBOS] for i in range(n)]); vb=np.concatenate([[V[int(c.split('-')[2])][i] for c in COMBOS] for i in range(n)])
        mats += [v3,va,vb,v3-va,v3-vb,va-vb]
    return np.vstack(mats).T

def rankscore(s):
    order=np.argsort(-s,axis=1); out=np.empty_like(s,float)
    for i in range(len(s)):out[i,order[i]]=np.arange(20,0,-1)
    return out

def fit(train,test):
    Xtr=base.build_static(train); Xte=base.build_static(test); yc=train.settle__actual_combo.astype(str); y3=yc.str.startswith('3-').astype(int)
    head=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto')).fit(Xtr,y3)
    p3=head.predict_proba(Xte)[:,1]
    th=train[y3.eq(1)].copy(); Xt=base.build_static(th); yt=th.settle__actual_combo.astype(str)
    old=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=1500,C=.15,solver='lbfgs')).fit(Xt,yt)
    pc=old.predict_proba(Xte); sold=np.zeros((len(test),20))
    for j,c in enumerate(old.classes_):sold[:,COMBOS.index(c)]=pc[:,j]
    A=pairmat(th); B=pairmat(test); yy=np.array([int(c==a) for a in yt for c in COMBOS])
    pm=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=1200,C=.3,solver='lbfgs',class_weight='balanced')).fit(A,yy)
    sp=pm.predict_proba(B)[:,1].reshape(len(test),20)
    # Frozen on March OOS: 75% old ordinal rank + 25% pair-candidate ordinal rank.
    snew=.75*rankscore(sold)+.25*rankscore(sp)
    return p3,sold,snew

def actual_rank(actual,score):
    rr=[]
    for a,s in zip(actual,score):
        order=[COMBOS[j] for j in np.argsort(-s)]; rr.append(order.index(a)+1 if a in COMBOS else np.nan)
    return np.array(rr)

def top5(score):return [';'.join(COMBOS[j] for j in np.argsort(-s)[:5]) for s in score]

def summarize(h,col):
    r=h[col].dropna().astype(float)
    return {'n':len(r),'mean_rank':float(r.mean()),'median_rank':float(r.median()),'mrr':float((1/r).mean()),**{f'top{k}':int((r<=k).sum()) for k in [1,3,5,8,10,15,20]}}

def main():
    d=pd.read_csv(SRC,dtype=str).fillna(''); bc=pd.read_csv(BASEC,dtype=str).fillna(''); ex=set(bc.race_code.astype(str))
    if len(ex)!=94 or d.date.max()>'2026-08-31':raise RuntimeError('guard failed')
    d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].copy(); d['month']=d.date.str[:7]
    outs=[]
    for mo in ['2026-03','2026-04','2026-05','2026-06']:
        tr=d[d.month=='2026-02'] if mo=='2026-03' else d[d.month<mo]; te=d[d.month==mo].sort_values(['date','race_code']).copy(); p,so,sn=fit(tr,te)
        te['p3']=p;te['old_rank']=actual_rank(te.settle__actual_combo,so);te['new_rank']=actual_rank(te.settle__actual_combo,sn);te['old_top5']=top5(so);te['new_top5']=top5(sn);outs.append(te)
    z=pd.concat(outs,ignore_index=True)
    march=z[(z.month=='2026-03')&(z.p3>=CUT)]; mh=march[march.settle__actual_combo.str.startswith('3-')].sort_values(['date','race_code']); m=len(mh)//2
    hold=z[z.month.isin(['2026-04','2026-05','2026-06'])&(z.p3>=CUT)].copy(); hh=hold[hold.settle__actual_combo.str.startswith('3-')].copy()
    if len(march)!=90 or len(mh)!=38 or len(hold)!=391 or len(hh)!=160:raise RuntimeError(f'parity {len(march)}/{len(mh)}/{len(hold)}/{len(hh)}')
    hold['old_return']=[base.dutch_return(r,str(r.old_top5).split(';')) for _,r in hold.iterrows()]; hold['new_return']=[base.dutch_return(r,str(r.new_top5).split(';')) for _,r in hold.iterrows()]
    def money(col):
        p=int(hold[col].sum()); return {'races':391,'hits':int((hold[col]>0).sum()),'payout_yen':p,'profit_yen':p-3910000,'roi_pct':100*p/3910000,'monthly':{mo:{'races':len(g),'hits':int((g[col]>0).sum()),'roi_pct':100*g[col].sum()/(len(g)*10000),'profit_yen':int(g[col].sum()-len(g)*10000)} for mo,g in hold.groupby('month')}}
    out={'wave':'36G-opponent-rank-rebuild','march_selected':90,'march_head':38,'march_old':summarize(mh,'old_rank'),'march_new':summarize(mh,'new_rank'),'march_old_half_top5':[float((mh.iloc[:m].old_rank<=5).mean()),float((mh.iloc[m:].old_rank<=5).mean())],'march_new_half_top5':[float((mh.iloc[:m].new_rank<=5).mean()),float((mh.iloc[m:].new_rank<=5).mean())],'holdout_old':summarize(hh,'old_rank'),'holdout_new':summarize(hh,'new_rank'),'rescued_top5':int(((hh.old_rank>5)&(hh.new_rank<=5)).sum()),'lost_top5':int(((hh.old_rank<=5)&(hh.new_rank>5)).sum()),'old_money':money('old_return'),'new_money':money('new_return'),'v288_overlap':int(hold.race_code.astype(str).isin(ex).sum()),'september_forbidden':True,'decision':'NO_ADOPTION' if money('new_return')['roi_pct']<money('old_return')['roi_pct'] else 'RESEARCH_CANDIDATE'}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); hold.to_csv(OUT,index=False,encoding='utf-8-sig'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
