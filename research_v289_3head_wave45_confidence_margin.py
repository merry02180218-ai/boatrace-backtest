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
OUTJ=Path('research_v289_3head_wave45_confidence_margin.json')
OUTM=Path('research_v289_3head_wave45_confidence_margin.md')
CUT=.365448


def fit_predict(trainX,train_combo,testX):
    y3=train_combo.str.startswith('3-').astype(int).to_numpy()
    head=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto'))
    head.fit(trainX,y3); p3=head.predict_proba(testX)[:,1]
    mask=y3==1
    cond=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15,solver='lbfgs'))
    cond.fit(trainX.iloc[np.flatnonzero(mask)],train_combo.to_numpy()[mask])
    pc=cond.predict_proba(testX); score=np.zeros((len(testX),len(base.COMBOS)))
    for j,c in enumerate(cond.classes_):
        if c in base.COMBOS: score[:,base.COMBOS.index(c)]=pc[:,j]
    return p3,score


def topo(v):
    s=np.nan_to_num(np.asarray(v,float),nan=0.0)
    if s.sum()<=0: return dict(top1=0,top3=0,top5=0,margin56=0,entropy=0,concentration=0)
    s=s/s.sum(); q=np.sort(s)[::-1]
    ent=float(-(s[s>0]*np.log(s[s>0])).sum()/np.log(len(s)))
    return dict(top1=float(q[0]),top3=float(q[:3].sum()),top5=float(q[:5].sum()),margin56=float(q[4]-q[5]),entropy=ent,concentration=float(1-ent))


def stat(q):
    n=len(q); h=int(q.top5_hit.sum())
    return {'races':n,'hits':h,'hit_rate':h/n if n else None}


def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    bc=pd.read_csv(BASEC,dtype=str).fillna(''); ex=set(bc.race_code.astype(str))
    d=d[~d.race_code.astype(str).isin(ex)].copy()
    d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d)
    y=d.settle__actual_combo.astype(str)
    tr=np.flatnonzero((d.month=='2026-02').to_numpy()); te=np.flatnonzero((d.month=='2026-03').to_numpy())
    p3,score=fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te])
    m=d.iloc[te].copy().reset_index(drop=True); m['actual']=y.iloc[te].to_numpy(); m['p3']=p3
    tops=[]; feats=[]
    for i,row in enumerate(score):
        idx=np.argsort(-row)[:5]; tops.append([base.COMBOS[j] for j in idx]); feats.append(topo(row))
    tf=pd.DataFrame(feats); m=pd.concat([m.reset_index(drop=True),tf],axis=1)
    m['top5_hit']=[a in t for a,t in zip(m.actual,tops)]
    m=m[m.p3>=CUT].sort_values(['date','race_code']).reset_index(drop=True)
    if len(m)<30: raise RuntimeError('too few March Wave36 candidates')
    split=len(m)//2; early=m.iloc[:split]; late=m.iloc[split:]
    baseline=stat(m)

    rules=[]
    # Predeclared quantile thresholds over topology; no outcome-driven threshold search beyond these fixed bins.
    specs=[('margin56','high',[.50,.60,.70,.75]),('top5','high',[.50,.60,.70,.75]),('concentration','high',[.50,.60,.70,.75]),('entropy','low',[.25,.30,.40,.50])]
    for col,direction,qs in specs:
        for q in qs:
            cut=float(m[col].quantile(q))
            if direction=='high': sel=m[col]>=cut; se=early[col]>=cut; sl=late[col]>=cut
            else: sel=m[col]<=cut; se=early[col]<=cut; sl=late[col]<=cut
            f=stat(m[sel]); e=stat(early[se]); l=stat(late[sl])
            if f['races']>=20 and e['races']>=8 and l['races']>=8:
                lift=(f['hit_rate'] or 0)-(baseline['hit_rate'] or 0)
                rules.append({'feature':col,'direction':direction,'q':q,'cut':cut,'full':f,'early':e,'late':l,'lift':lift,'worst_half':min(e['hit_rate'],l['hit_rate'])})
    # fixed conjunctions using median boundaries only
    meds={c:float(m[c].median()) for c in ['margin56','top5','concentration']}
    combos=[('margin_top5',(m.margin56>=meds['margin56'])&(m.top5>=meds['top5'])),('margin_conc',(m.margin56>=meds['margin56'])&(m.concentration>=meds['concentration'])),('top5_conc',(m.top5>=meds['top5'])&(m.concentration>=meds['concentration']))]
    for name,sel in combos:
        def mk(z):
            ss=(z.margin56>=meds['margin56'])&(z.top5>=meds['top5']) if name=='margin_top5' else ((z.margin56>=meds['margin56'])&(z.concentration>=meds['concentration']) if name=='margin_conc' else (z.top5>=meds['top5'])&(z.concentration>=meds['concentration']))
            return stat(z[ss])
        f=stat(m[sel]); e=mk(early); l=mk(late)
        if f['races']>=20 and e['races']>=8 and l['races']>=8:
            rules.append({'feature':name,'direction':'conjunction','q':'median','cut':meds,'full':f,'early':e,'late':l,'lift':f['hit_rate']-baseline['hit_rate'],'worst_half':min(e['hit_rate'],l['hit_rate'])})
    if not rules: raise RuntimeError('no valid rules')
    # structural gate: >=5 percentage-point full lift, no half below baseline-2pp, >=20 races.
    gate=[r for r in rules if r['lift']>=.05 and r['worst_half']>=baseline['hit_rate']-.02]
    best=max(rules,key=lambda r:(r['worst_half'],r['lift'],r['full']['races']))
    decision='MARCH_GATE_PASS' if gate else 'NO_ADOPTION'
    out={'wave':'45-confidence-margin','march_cut':CUT,'march_baseline':baseline,'march_early_baseline':stat(early),'march_late_baseline':stat(late),'rules':rules,'best_rule':best,'gate_rules':gate,'decision':decision,'open_apr_jun':bool(gate),'september_outcomes_read':False}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave45 confidence/margin topology audit','',f"- March Wave36 candidates: **{baseline['races']}R / {baseline['hits']} hits / {baseline['hit_rate']:.3%}**",f"- Early baseline: {stat(early)['hit_rate']:.3%} / late: {stat(late)['hit_rate']:.3%}",f"- Best rule: **{best['feature']} {best['direction']} q={best['q']}** => {best['full']['races']}R / {best['full']['hit_rate']:.3%}, lift {best['lift']:+.3%}, early {best['early']['hit_rate']:.3%}, late {best['late']['hit_rate']:.3%}",f"- gate rules: **{len(gate)}**",f"- decision: **{decision}**",'- Apr-Jun not opened in this script.', '- September outcomes are not read.']
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)

if __name__=='__main__': main()
