from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASELINE_CODES=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('analysis_v289_3head_wave34_prototype_distance.csv')
OUTJ=Path('research_v289_3head_wave34_prototype_distance.json')
OUTM=Path('research_v289_3head_wave34_prototype_distance.md')
BASELINE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}
QS=[.90,.93,.95,.97,.98,.99]
KS=[3,5,7]


def fit_predict(trainX,train_combo,testX):
    imp=SimpleImputer(strategy='median')
    A=imp.fit_transform(trainX); B=imp.transform(testX)
    scaler=StandardScaler().fit(A)
    A=scaler.transform(A); B=scaler.transform(B)
    y=train_combo.str.startswith('3-').astype(int).to_numpy()
    if y.sum()<20 or (y==0).sum()<20: raise RuntimeError('insufficient classes')
    pos=A[y==1].mean(axis=0); neg=A[y==0].mean(axis=0)
    dpos=np.sqrt(((B-pos)**2).mean(axis=1)); dneg=np.sqrt(((B-neg)**2).mean(axis=1))
    head_score=dneg-dpos
    mask=y==1
    cond=make_pipeline(StandardScaler(),LogisticRegression(max_iter=500,C=.20,solver='lbfgs'))
    cond.fit(A[mask],train_combo.to_numpy()[mask])
    pc=cond.predict_proba(B)
    score=np.zeros((len(testX),len(base.COMBOS)))
    for j,c in enumerate(cond.classes_):
        if c in base.COMBOS: score[:,base.COMBOS.index(c)]=pc[:,j]
    return head_score,score


def evaluate(df,cut,k):
    q=df[df['head_score']>=cut].copy(); rets=[]; tickets=[]
    for _,r in q.iterrows():
        ts=str(r[f'top{k}']).split(';') if r[f'top{k}'] else []
        tickets.append(';'.join(ts)); rets.append(base.dutch_return(r,ts))
    q['tickets']=tickets; q['variant_return']=rets
    m=base.block(q); mm={mo:base.block(g) for mo,g in q.groupby('month')}
    m.update({'score_cut':float(cut),'k':int(k),'monthly':mm,'min_month_roi_pct':min((z['roi_pct'] for z in mm.values()),default=None),'red_months':sum(1 for z in mm.values() if z['roi_pct']<100),'max_drawdown_yen':base.maxdd(q.sort_values(['date','race_code']))})
    return q,m


def main():
    df=pd.read_csv(SRC,dtype=str).fillna('')
    if df['date'].max()>'2026-08-31': raise RuntimeError('September forbidden')
    bdf=pd.read_csv(BASELINE_CODES,dtype=str).fillna(''); exclusion=set(bdf['race_code'].astype(str))
    if len(exclusion)!=94: raise RuntimeError('baseline exclusion must be exact 94')
    if bdf['route'].value_counts().to_dict()!={'S':55,'A':21,'B':18}: raise RuntimeError('baseline route mismatch')
    df=df[~df['race_code'].astype(str).isin(exclusion)].copy()
    df=df[(df['settle__usable']=='1')&(df['closing_odds__ok']=='1')].copy().reset_index(drop=True)
    df['month']=df['date'].str[:7]
    X=base.build_static(df); y=df['settle__actual_combo'].astype(str)
    n=len(df); hs=np.full(n,np.nan); scores=np.full((n,len(base.COMBOS)),np.nan)
    def run(train_mask,test_mask):
        tr=np.flatnonzero(train_mask.to_numpy()); te=np.flatnonzero(test_mask.to_numpy())
        h,sc=fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]); hs[te]=h; scores[te,:]=sc
    run(df['month']=='2026-02',df['month']=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']: run(df['month']<mo,df['month']==mo)
    frozen=df['month']<='2026-06'
    for mo in ['2026-07','2026-08']: run(frozen,df['month']==mo)
    df['head_score']=hs
    for k in KS:
        vals=[]
        for i in range(n):
            if not np.isfinite(scores[i]).any(): vals.append(''); continue
            idx=np.argsort(-np.nan_to_num(scores[i],nan=-1))[:k]
            vals.append(';'.join(base.COMBOS[j] for j in idx))
        df[f'top{k}']=vals
    march=df[df['month']=='2026-03'].copy(); candidates=[]
    cuts=sorted(set(float(march['head_score'].quantile(q)) for q in QS))
    for k in KS:
        for cut in cuts:
            _,m=evaluate(march,cut,k)
            if 30<=m['races']<=300: candidates.append(m)
    if not candidates: raise RuntimeError('no March candidate')
    chosen=max(candidates,key=lambda z:(z['roi_pct'],-z['races']))
    cut,k=chosen['score_cut'],chosen['k']
    hold=df[df['month'].isin(['2026-04','2026-05','2026-06'])].copy(); shadow=df[df['month'].isin(['2026-07','2026-08'])].copy()
    sel_h,hm=evaluate(hold,cut,k); sel_s,sm=evaluate(shadow,cut,k)
    overlap=int(pd.concat([sel_h,sel_s])['race_code'].astype(str).isin(exclusion).sum())
    if overlap!=0: raise RuntimeError(f'v288 overlap {overlap}')
    pd.concat([sel_h.assign(period='pristine_holdout'),sel_s.assign(period='shadow')],ignore_index=True).to_csv(OUT,index=False,encoding='utf-8-sig')
    cmb={'races':BASELINE['races']+hm['races'],'hits':BASELINE['hits']+hm['hits'],'stake_yen':BASELINE['stake_yen']+hm['stake_yen'],'payout_yen':BASELINE['payout_yen']+hm['payout_yen']}
    cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    decision='SHADOW_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=BASELINE['roi_pct'] and hm['red_months']==0 else ('RESEARCH_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION')
    out={'wave':'34-prototype-distance','family':'standardized positive-vs-negative prototype distance head score + conditional multinomial logistic order','feature_count':63,'march_tuning_from_feb_only':chosen,'strict_pristine_holdout_apr_jun':hm,'shadow_non_pristine_jul_aug':sm,'legacy_overlap':overlap,'combined_baseline_plus_holdout':cmb,'decision':decision,'scope_note':'Wave20 full six-boat population minus exact v288 operational 94R only.'}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave34 prototype-distance corrected scope','',f"- March gate: **score>={cut:.6f}, top{k}; {chosen['races']}R / ROI {chosen['roi_pct']:.3f}%**",f"- Apr-Jun holdout: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- min month: **{hm['min_month_roi_pct']:.3f}%** / red months **{hm['red_months']}** / max DD **{hm['max_drawdown_yen']:,.0f} yen**",f"- Jul-Aug shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + holdout: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",f'- overlap: **{overlap}**',f'- decision: **{decision}**','','## Holdout monthly']
    for mo,z in hm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    lines+=['','## Shadow monthly']
    for mo,z in sm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)

if __name__=='__main__': main()
