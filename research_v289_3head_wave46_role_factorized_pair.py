from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUTJ=Path('research_v289_3head_wave46_role_factorized_pair.json')
OUTM=Path('research_v289_3head_wave46_role_factorized_pair.md')
GATE=.365448
OPPS=[1,2,4,5,6]
COMBOS=base.COMBOS

def pipe():
    return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=600,C=.15,solver='lbfgs'))

def fit_head(trainX,y,testX):
    yy=y.str.startswith('3-').astype(int)
    m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto'))
    m.fit(trainX,yy)
    return m.predict_proba(testX)[:,1]

def opponent_features(X, boat):
    # frozen 63-row context plus opponent identity; same pre-race information for each candidate opponent
    z=X.copy()
    for b in OPPS: z[f'opp_is_{b}']=1.0 if b==boat else 0.0
    return z

def fit_role(trainX,train_combo,testX):
    mask=train_combo.str.startswith('3-')
    Xtr=trainX.loc[mask]; yc=train_combo.loc[mask]
    rows=[]; y2=[]; y3=[]
    for idx,c in yc.items():
        p=c.split('-'); second=int(p[1]); third=int(p[2])
        for b in OPPS:
            rows.append(opponent_features(Xtr.loc[[idx]],b).iloc[0])
            y2.append(int(b==second)); y3.append(int(b==third))
    R=pd.DataFrame(rows).reset_index(drop=True)
    m2=pipe(); m3=pipe(); m2.fit(R,np.array(y2)); m3.fit(R,np.array(y3))
    p2=np.zeros((len(testX),len(OPPS))); p3=np.zeros_like(p2)
    for j,b in enumerate(OPPS):
        Z=opponent_features(testX,b)
        p2[:,j]=m2.predict_proba(Z)[:,1]; p3[:,j]=m3.predict_proba(Z)[:,1]
    return p2,p3

def wave36_cond(trainX,train_combo,testX):
    mask=train_combo.str.startswith('3-')
    m=pipe(); m.fit(trainX.loc[mask],train_combo.loc[mask]); pc=m.predict_proba(testX)
    s=np.zeros((len(testX),len(COMBOS)))
    for j,c in enumerate(m.classes_):
        if c in COMBOS:s[:,COMBOS.index(c)]=pc[:,j]
    return s

def pair_score(p2,p3):
    s=np.zeros((len(p2),len(COMBOS)))
    oi={b:i for i,b in enumerate(OPPS)}
    for j,c in enumerate(COMBOS):
        _,a,b=map(int,c.split('-')); s[:,j]=p2[:,oi[a]]*p3[:,oi[b]]
    return s

def top5(score):
    return [';'.join(COMBOS[j] for j in np.argsort(-score[i])[:5]) for i in range(len(score))]

def stats(q,col):
    hit=np.array([str(a) in str(t).split(';') for a,t in zip(q.actual,q[col])])
    return {'races':len(q),'hits':int(hit.sum()),'rate':float(hit.mean()) if len(q) else 0.}

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
    bc=pd.read_csv(BASEC,dtype=str).fillna(''); ex=set(bc.race_code.astype(str))
    if len(ex)!=94:raise RuntimeError('exact v288 94 required')
    d=d[~d.race_code.astype(str).isin(ex)].copy()
    d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    # Hard scope: only Feb train and March OOS. Apr-Jun outcomes are never evaluated/read by this audit.
    fm=d[d.month.isin(['2026-02','2026-03'])].copy().reset_index(drop=True)
    X=base.build_static(fm); y=fm.settle__actual_combo.astype(str)
    tr=fm.month=='2026-02'; te=fm.month=='2026-03'
    ph=fit_head(X.loc[tr],y.loc[tr],X.loc[te]); old=wave36_cond(X.loc[tr],y.loc[tr],X.loc[te]); p2,p3=fit_role(X.loc[tr],y.loc[tr],X.loc[te]); role=pair_score(p2,p3)
    m=fm.loc[te].copy().reset_index(drop=True); m['p3']=ph; m['actual']=m.settle__actual_combo.astype(str).to_numpy(); m['old_top5']=top5(old); m['role_top5']=top5(role)
    # One conservative predeclared blend, normalized row-wise before 50/50 blend.
    on=old/np.maximum(old.sum(axis=1,keepdims=True),1e-12); rn=role/np.maximum(role.sum(axis=1,keepdims=True),1e-12); m['blend_top5']=top5(.5*on+.5*rn)
    q=m[m.p3>=GATE].sort_values(['date','race_code']).reset_index(drop=True); split=len(q)//2
    res={}
    for col in ['old_top5','role_top5','blend_top5']:
        res[col]={'full':stats(q,col),'early':stats(q.iloc[:split],col),'late':stats(q.iloc[split:],col)}
    oldhit=np.array([a in t.split(';') for a,t in zip(q.actual,q.old_top5)])
    bestname=max(['role_top5','blend_top5'],key=lambda c:res[c]['full']['hits']); newhit=np.array([a in t.split(';') for a,t in zip(q.actual,q[bestname])])
    gained=int((~oldhit&newhit).sum()); lost=int((oldhit&~newhit).sum()); delta=int(newhit.sum()-oldhit.sum())
    stable=min(res[bestname]['early']['rate'],res[bestname]['late']['rate'])>=min(res['old_top5']['early']['rate'],res['old_top5']['late']['rate'])-.03
    passed=delta>=1 and lost<=2 and stable
    out={'wave':'46-role-factorized-pair','gate':GATE,'march_only':True,'baseline':res['old_top5'],'variants':res,'best':bestname,'gained_old_misses':gained,'lost_old_hits':lost,'net_top5_delta':delta,'stable_halves':bool(stable),'promotion_pass':bool(passed),'decision':'MARCH_GATE_PASS' if passed else 'NO_ADOPTION','apr_jun_opened':False,'september_outcomes_read':False}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave46 role-factorized opponent audit','',f"- March gated baseline: **{res['old_top5']['full']['races']}R / {res['old_top5']['full']['hits']} hits / {res['old_top5']['full']['rate']:.3%}**",f"- Role Top5: **{res['role_top5']['full']['hits']} hits / {res['role_top5']['full']['rate']:.3%}**",f"- 50/50 Wave36 blend Top5: **{res['blend_top5']['full']['hits']} hits / {res['blend_top5']['full']['rate']:.3%}**",f"- Best: **{bestname}**; gained {gained}, lost {lost}, net {delta:+d}",f"- early/late: {res[bestname]['early']['rate']:.3%} / {res[bestname]['late']['rate']:.3%}",f"- decision: **{out['decision']}**",'- Apr-Jun not opened. September outcomes unread.']
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)
if __name__=='__main__':main()
