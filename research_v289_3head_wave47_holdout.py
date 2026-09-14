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
import research_v289_3head_wave47_head_condition_zoning as z47

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUTJ=Path('research_v289_3head_wave47_holdout.json')
OUTM=Path('research_v289_3head_wave47_holdout.md')
CUT=.365448
COMBOS=base.COMBOS

def wave36_fit(trainX,train_combo,testX):
    y3=train_combo.str.startswith('3-').astype(int).to_numpy()
    hm=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto'))
    hm.fit(trainX,y3); p3=hm.predict_proba(testX)[:,1]
    mask=y3==1
    cm=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15,solver='lbfgs'))
    cm.fit(trainX.iloc[np.flatnonzero(mask)],train_combo.to_numpy()[mask]); pc=cm.predict_proba(testX)
    s=np.zeros((len(testX),len(COMBOS)))
    for j,c in enumerate(cm.classes_):
        if c in COMBOS:s[:,COMBOS.index(c)]=pc[:,j]
    tops=[]
    for i in range(len(testX)):
        idx=np.argsort(-s[i])[:5]; tops.append(';'.join(COMBOS[j] for j in idx))
    return p3,tops

def settle(q):
    x=q.copy(); x['variant_return']=[base.dutch_return(r,str(r.top5).split(';') if r.top5 else []) for _,r in x.iterrows()]
    m=base.block(x); mm={mo:base.block(g) for mo,g in x.groupby('month')}
    m.update({'monthly':mm,'min_month_roi_pct':min((v['roi_pct'] for v in mm.values()),default=None),'red_months':sum(v['roi_pct']<100 for v in mm.values()),'max_drawdown_yen':base.maxdd(x.sort_values(['date','race_code']))})
    return x,m

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31':raise RuntimeError('September forbidden')
    bc=pd.read_csv(BASEC,dtype=str).fillna(''); ex=set(bc.race_code.astype(str))
    if len(ex)!=94:raise RuntimeError('exact v288 94 required')
    d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d); y=d.settle__actual_combo.astype(str)
    p3=np.full(len(d),np.nan); tops=np.array(['']*len(d),dtype=object)
    def run(trm,tem):
        tr=np.flatnonzero(trm.to_numpy()); te=np.flatnonzero(tem.to_numpy()); p,t=wave36_fit(X.iloc[tr],y.iloc[tr],X.iloc[te]); p3[te]=p; tops[te]=t
    run(d.month=='2026-02',d.month=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']:run(d.month<mo,d.month==mo)
    d['p3']=p3; d['top5']=tops

    # Freeze Wave47 zone model from February only. March selects one absolute score threshold (top 60% of Wave36 candidates).
    Z=z47.sparse(d,'motor'); tr=d.month=='2026-02'; zm=z47.head_pipe(); zm.fit(Z.loc[tr],y.loc[tr].str.startswith('3-').astype(int)); zscore=zm.predict_proba(Z)[:,1]; d['zone_score']=zscore
    march=d[(d.month=='2026-03')&(d.p3>=CUT)].copy()
    if len(march)!=90: raise RuntimeError(f'expected March 90, got {len(march)}')
    zone_cut=float(march.zone_score.quantile(.40))

    hold=d[d.month.isin(['2026-04','2026-05','2026-06'])].copy()
    wave=hold[hold.p3>=CUT].copy(); selected=wave[wave.zone_score>=zone_cut].copy()
    _,wm=settle(wave); sx,sm=settle(selected)
    sx.to_csv('analysis_v289_3head_wave47_holdout.csv',index=False,encoding='utf-8-sig')
    decision='RESEARCH_CANDIDATE' if sm['races']>=120 and sm['roi_pct']>=125 and sm['red_months']<=1 and sm['min_month_roi_pct']>=85 else 'NO_ADOPTION'
    out={'wave':'47-head-condition-zoning-holdout','frozen_family':'motor','frozen_keep':'top60pct','march_zone_cut':zone_cut,'wave36_reference_recomputed':wm,'wave47_apr_jun':sm,'decision':decision,'retuned_on_apr_jun':False,'jul_aug_opened':False,'september_outcomes_read':False}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave47 fixed Apr-Jun holdout','',f"- Frozen rule: **motor zone score >= {zone_cut:.6f}** (March top60% threshold)",f"- Wave36 recomputed Apr-Jun: **{wm['races']}R / {wm['hits']} hits / ROI {wm['roi_pct']:.3f}% / profit {wm['profit_yen']:+,} yen**",f"- Wave47 Apr-Jun: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- min month {sm['min_month_roi_pct']:.3f}% / red months {sm['red_months']} / max DD {sm['max_drawdown_yen']:,.0f} yen",f"- decision: **{decision}**",'- No Apr-Jun retuning. Jul-Aug not opened. September unread.','','## Monthly']
    for mo,v in sm['monthly'].items():lines.append(f"- {mo}: {v['races']}R / {v['hits']} hits / ROI {v['roi_pct']:.3f}% / profit {v['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)
if __name__=='__main__':main()
