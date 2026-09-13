from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesClassifier
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASELINE_CODES=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('analysis_v289_3head_wave32_extratrees_gate.csv')
OUTJ=Path('research_v289_3head_wave32_extratrees_gate.json')
OUTM=Path('research_v289_3head_wave32_extratrees_gate.md')
BASELINE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}


def fit_predict(trainX,train_combo,testX):
    imp=SimpleImputer(strategy='median')
    Xi=imp.fit_transform(trainX); Xt=imp.transform(testX)
    yhead=train_combo.str.startswith('3-').astype(int)
    head=ExtraTreesClassifier(
        n_estimators=400,max_depth=6,min_samples_leaf=25,max_features=.70,
        class_weight='balanced',random_state=32,n_jobs=-1
    )
    head.fit(Xi,yhead)
    p3=head.predict_proba(Xt)[:,list(head.classes_).index(1)]
    mask=yhead.eq(1); cond=base.cond_pipe(); cond.fit(trainX.loc[mask],train_combo.loc[mask])
    pc=cond.predict_proba(testX); score=np.zeros((len(testX),len(base.COMBOS)))
    for j,c in enumerate(cond.classes_):
        if c in base.COMBOS: score[:,base.COMBOS.index(c)]=pc[:,j]
    return p3,score


def main():
    df=pd.read_csv(SRC,dtype=str).fillna('')
    if df['date'].max()>'2026-08-31': raise RuntimeError('September forbidden')
    bdf=pd.read_csv(BASELINE_CODES,dtype=str).fillna('')
    exclusion=set(bdf['race_code'].astype(str))
    if len(exclusion)!=94: raise RuntimeError(f'baseline exclusion must be exact 94, got {len(exclusion)}')
    if bdf['route'].value_counts().to_dict()!={'S':55,'A':21,'B':18}: raise RuntimeError('baseline route counts mismatch')
    source_n=len(df); source_overlap=int(df['race_code'].astype(str).isin(exclusion).sum())
    df=df[~df['race_code'].astype(str).isin(exclusion)].copy()
    df=df[(df['settle__usable']=='1')&(df['closing_odds__ok']=='1')].copy()
    df['month']=df['date'].str[:7]
    X=base.build_static(df); yc=df['settle__actual_combo'].astype(str)
    p3=np.full(len(df),np.nan); cs=np.full((len(df),len(base.COMBOS)),np.nan); pos={idx:i for i,idx in enumerate(df.index)}
    def run(tr,te):
        ph,sc=fit_predict(X.loc[tr],yc.loc[tr],X.loc[te])
        for j,idx in enumerate(df.index[te]): p3[pos[idx]]=ph[j]; cs[pos[idx],:]=sc[j]
    run(df['month']=='2026-02',df['month']=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']: run(df['month']<mo,df['month']==mo)
    frozen=df['month']<='2026-06'
    for mo in ['2026-07','2026-08']: run(frozen,df['month']==mo)
    df['p3']=p3
    for k in base.KS:
        arr=[]
        for i in range(len(df)):
            if not np.isfinite(cs[i]).any(): arr.append(''); continue
            order=np.argsort(-np.nan_to_num(cs[i],nan=-1))[:k]
            arr.append(';'.join(base.COMBOS[j] for j in order))
        df[f'top{k}']=arr
    tune=df[df['month']=='2026-03'].copy(); variants=[]
    for k in base.KS:
        for t in base.THRESHOLDS:
            _,m=base.score(tune,t,k)
            if m['races']>=100: variants.append(m)
    if not variants: raise RuntimeError('no March variant >=100R')
    chosen=max(variants,key=lambda z:z['roi_pct']); t=chosen['threshold']; k=chosen['k']
    sel_h,hm=base.score(df[df['month'].isin(['2026-04','2026-05','2026-06'])].copy(),t,k)
    sel_s,sm=base.score(df[df['month'].isin(['2026-07','2026-08'])].copy(),t,k)
    overlap=int(pd.concat([sel_h,sel_s])['race_code'].astype(str).isin(exclusion).sum())
    if overlap!=0: raise RuntimeError(f'v288 overlap {overlap}')
    pd.concat([sel_h.assign(period='pristine_holdout'),sel_s.assign(period='shadow')],ignore_index=True).to_csv(OUT,index=False,encoding='utf-8-sig')
    cmb={'races':BASELINE['races']+hm['races'],'hits':BASELINE['hits']+hm['hits'],'stake_yen':BASELINE['stake_yen']+hm['stake_yen'],'payout_yen':BASELINE['payout_yen']+hm['payout_yen']}
    cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    decision='SHADOW_CANDIDATE' if hm['races']>=100 and hm['roi_pct']>=BASELINE['roi_pct'] and hm['red_months']==0 else ('RESEARCH_CANDIDATE' if hm['races']>=100 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION')
    out={'wave':'32-extratrees-corrected-94-exclusion','family':'ExtraTrees 3-head gate + conditional exact-order logistic','feature_count':63,'source_rows_before_exclusion':source_n,'exact_v288_exclusion_rows':len(exclusion),'source_v288_overlap_rows':source_overlap,'march_tuning_from_feb_only':chosen,'strict_pristine_holdout_apr_jun':hm,'shadow_non_pristine_jul_aug':sm,'legacy_overlap':overlap,'combined_baseline_plus_holdout':cmb,'decision':decision,'scope_note':'Wave20 full six-boat population; exclude exact v288 operational 94 baseline only. No old v243/PRE/bet/route candidate prefilter.'}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave32 ExtraTrees corrected full-population scope','', '- Scope: Wave20 all six-boat universe; exclude exact v288 operational 94R only (not old 678R).',f"- Source baseline-code overlap before exclusion: **{source_overlap}R** / selected overlap: **{overlap}R**",f"- March tune (train Feb only): **p3>={t:.2f}, top{k}; {chosen['races']}R / ROI {chosen['roi_pct']:.3f}%**",f"- Apr-Jun walk-forward holdout: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- min month: **{hm['min_month_roi_pct']:.3f}%** / red months **{hm['red_months']}** / max DD **{hm['max_drawdown_yen']:,.0f} yen**",f"- Jul-Aug NON-PRISTINE shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + holdout: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",f'- decision: **{decision}**','','## Pristine holdout monthly']
    for mo,z in hm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    lines+=['','## Shadow monthly']
    for mo,z in sm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)

if __name__=='__main__': main()
