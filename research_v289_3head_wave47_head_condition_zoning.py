from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUTJ=Path('research_v289_3head_wave47_head_condition_zoning.json')
OUTM=Path('research_v289_3head_wave47_head_condition_zoning.md')
CUT=.365448
COMBOS=base.COMBOS

def num(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')

def col(df,b,met):
    k=f'card__艇{b}_{met}'
    if k not in df: raise RuntimeError(f'missing {k}')
    return num(df[k])

def sparse(df, family):
    x=pd.DataFrame(index=df.index)
    # lower average ST is better; differences are b3 - opponent (negative favors boat3)
    if family in ('st','st_win','st_win_motor','all'):
        for b in [1,2,4]: x[f'st_3m{b}']=col(df,3,'全国平均ST')-col(df,b,'全国平均ST')
    if family in ('win','st_win','st_win_motor','all'):
        for met in ['全国勝率','当地勝率']:
            for b in [1,2,4]: x[f'{met}_3m{b}']=col(df,3,met)-col(df,b,met)
    if family in ('motor','st_win_motor','all'):
        for met in ['モーター2連対率','モーター3連対率']:
            for b in [1,2,4]: x[f'{met}_3m{b}']=col(df,3,met)-col(df,b,met)
    return x.replace([np.inf,-np.inf],np.nan)

def head_pipe():
    return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.08,solver='lbfgs',class_weight='balanced'))

def wave36(trainX,train_combo,testX):
    y3=train_combo.str.startswith('3-').astype(int).to_numpy()
    hm=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto'))
    hm.fit(trainX,y3); p3=hm.predict_proba(testX)[:,1]
    mask=y3==1
    cm=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15,solver='lbfgs'))
    cm.fit(trainX.iloc[np.flatnonzero(mask)],train_combo.to_numpy()[mask]); pc=cm.predict_proba(testX)
    score=np.zeros((len(testX),len(COMBOS)))
    for j,c in enumerate(cm.classes_):
        if c in COMBOS: score[:,COMBOS.index(c)]=pc[:,j]
    tops=[]
    for i in range(len(testX)):
        idx=np.argsort(-score[i])[:5]; tops.append(';'.join(COMBOS[j] for j in idx))
    return p3,tops

def stat(q):
    n=len(q); hh=int(q.head3.sum()); th=int(q.top5_hit.sum())
    return {'races':n,'head_hits':hh,'head_rate':hh/n if n else None,'ticket_hits':th,'ticket_rate':th/n if n else None}

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    bc=pd.read_csv(BASEC,dtype=str).fillna(''); ex=set(bc.race_code.astype(str))
    if len(ex)!=94: raise RuntimeError('exact v288 94 required')
    d=d[~d.race_code.astype(str).isin(ex)].copy()
    d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    fm=d[d.month.isin(['2026-02','2026-03'])].copy().reset_index(drop=True)
    X63=base.build_static(fm); y=fm.settle__actual_combo.astype(str)
    tr=fm.month=='2026-02'; te=fm.month=='2026-03'
    p3,tops=wave36(X63.loc[tr],y.loc[tr],X63.loc[te])
    m=fm.loc[te].copy().reset_index(drop=True); m['p3']=p3; m['actual']=y.loc[te].to_numpy(); m['head3']=m.actual.str.startswith('3-').astype(int); m['top5']=tops; m['top5_hit']=[a in t.split(';') for a,t in zip(m.actual,m.top5)]
    m=m[m.p3>=CUT].sort_values(['date','race_code']).reset_index(drop=True)
    split=len(m)//2; early_idx=set(m.index[:split]); late_idx=set(m.index[split:])
    baseline=stat(m)
    variants=[]
    families=['st','win','motor','st_win','st_win_motor']
    for fam in families:
        X=sparse(fm,fam); mod=head_pipe(); mod.fit(X.loc[tr],y.loc[tr].str.startswith('3-').astype(int)); z=mod.predict_proba(X.loc[te])[:,1]
        mm=fm.loc[te,['race_code']].copy(); mm['zone_score']=z
        q=m.merge(mm,on='race_code',how='left')
        # Fixed retention levels: 50% and 60% of Wave36 March candidate universe by zone score.
        for keep in [.50,.60]:
            cut=float(q.zone_score.quantile(1-keep)); sel=q[q.zone_score>=cut].copy().sort_values(['date','race_code']).reset_index(drop=True)
            # Evaluate halves by original chronological boundary, not re-splitting selected rows.
            boundary=m.iloc[split-1].date + '|' + m.iloc[split-1].race_code
            key=sel.date+'|'+sel.race_code; se=sel[key<=boundary]; sl=sel[key>boundary]
            f=stat(sel); e=stat(se); l=stat(sl)
            lift=f['head_rate']-baseline['head_rate']
            variants.append({'family':fam,'keep':keep,'cut':cut,'full':f,'early':e,'late':l,'head_lift':lift,'worst_half_head_rate':min(e['head_rate'] or 0,l['head_rate'] or 0)})
    valid=[v for v in variants if v['full']['races']>=45 and v['head_lift']>=.05 and v['early']['races']>=15 and v['late']['races']>=15 and min(v['early']['head_rate'],v['late']['head_rate'])>=baseline['head_rate']-.03]
    best=max(variants,key=lambda v:(v['head_lift'],v['worst_half_head_rate'],v['full']['races']))
    out={'wave':'47-head-condition-zoning','march_cut':CUT,'march_baseline':baseline,'march_early_baseline':stat(m.iloc[:split]),'march_late_baseline':stat(m.iloc[split:]),'variants':variants,'best':best,'gate_passers':valid,'decision':'MARCH_GATE_PASS' if valid else 'NO_ADOPTION','apr_jun_opened':False,'september_outcomes_read':False}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave47 head-condition zoning','',f"- March Wave36 baseline: **{baseline['races']}R / {baseline['head_hits']} head hits / {baseline['head_rate']:.3%}; Top5 {baseline['ticket_hits']} / {baseline['ticket_rate']:.3%}**",f"- Best: **{best['family']} keep={best['keep']:.0%}** => {best['full']['races']}R / head {best['full']['head_rate']:.3%} (lift {best['head_lift']:+.3%}) / Top5 {best['full']['ticket_rate']:.3%}",f"- Best early/late head: {best['early']['head_rate']:.3%} / {best['late']['head_rate']:.3%}",f"- gate passers: **{len(valid)}**",f"- decision: **{out['decision']}**",'- Apr-Jun not opened in this script.', '- September outcomes are not read.']
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)
if __name__=='__main__': main()
