from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v289_3head_wave34b_prototype_stability as w34b
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASELINE_CODES=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUTJ=Path('research_v289_3head_wave34g_motor_confirmation.json')
OUTM=Path('research_v289_3head_wave34g_motor_confirmation.md')
OUT=Path('analysis_v289_3head_wave34g_motor_confirmation.csv')
BASELINE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}
PROTO_CUT=0.2332210614000265
AGREE_CUT=.55
QS=[.20,.35,.50,.65,.80]
KS=[3,5]
MOTOR_COLS=['b3_minus_b1_モーター2連対率','b3_minus_mean_モーター2連対率','b3_minus_b1_モーター3連対率','b3_minus_b2_モーター2連対率']

def evaluate(df,mode,cut,k):
    q=df[(df.prototype_mean>=PROTO_CUT)&(df.agreement>=AGREE_CUT)&(df[mode]>=cut)].copy()
    rets=[]
    for _,r in q.iterrows():
        ts=str(r[f'top{k}']).split(';') if r[f'top{k}'] else []
        rets.append(base.dutch_return(r,ts))
    q['variant_return']=rets
    m=base.block(q); mm={mo:base.block(g) for mo,g in q.groupby('month')}
    m.update({'mode':mode,'cut':float(cut),'k':int(k),'monthly':mm,'min_month_roi_pct':min((z['roi_pct'] for z in mm.values()),default=None),'red_months':sum(z['roi_pct']<100 for z in mm.values()),'max_drawdown_yen':base.maxdd(q.sort_values(['date','race_code']))})
    return q,m

def main():
    df=pd.read_csv(SRC,dtype=str).fillna('')
    if df.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    bdf=pd.read_csv(BASELINE_CODES,dtype=str).fillna(''); exclusion=set(bdf.race_code.astype(str))
    if len(exclusion)!=94 or bdf.race_code.nunique()!=94: raise RuntimeError('baseline exact 94 required')
    df=df[~df.race_code.astype(str).isin(exclusion)].copy()
    df=df[(df.settle__usable=='1')&(df.closing_odds__ok=='1')].reset_index(drop=True)
    df['month']=df.date.str[:7]
    X=base.build_static(df)
    if X.shape[1]!=63: raise RuntimeError(f'expected 63 features, got {X.shape[1]}')
    missing=[c for c in MOTOR_COLS if c not in X.columns]
    if missing: raise RuntimeError(f'missing motor features {missing}')
    y=df.settle__actual_combo.astype(str); n=len(df)
    ms=np.full(n,np.nan); sd=np.full(n,np.nan); ag=np.full(n,np.nan); scores=np.full((n,len(base.COMBOS)),np.nan)
    def run(train_mask,test_mask,seed):
        tr=np.flatnonzero(train_mask.to_numpy()); te=np.flatnonzero(test_mask.to_numpy())
        a,b,c,_,e=w34b.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te],seed)
        ms[te]=a; sd[te]=b; ag[te]=c; scores[te,:]=e
    run(df.month=='2026-02',df.month=='2026-03',3403)
    for i,mo in enumerate(['2026-04','2026-05','2026-06'],1): run(df.month<mo,df.month==mo,3403+i)
    frozen=df.month<='2026-06'
    for i,mo in enumerate(['2026-07','2026-08'],4): run(frozen,df.month==mo,3403+i)
    df['prototype_mean']=ms; df['prototype_sd']=sd; df['agreement']=ag
    for c in MOTOR_COLS: df[c]=pd.to_numeric(X[c],errors='coerce')
    # composites use only pre-deadline static features; scaling parameters learned from February only.
    feb=df.month=='2026-02'
    zcols=[]
    for c in MOTOR_COLS:
        med=float(df.loc[feb,c].median()); scale=float((df.loc[feb,c]-med).abs().median())
        if not np.isfinite(scale) or scale<1e-9: scale=float(df.loc[feb,c].std())
        if not np.isfinite(scale) or scale<1e-9: scale=1.0
        z='z_'+c; df[z]=(df[c]-med)/scale; zcols.append(z)
    df['motor_mean_confirm']=df[zcols].mean(axis=1)
    df['motor_min_confirm']=df[zcols].min(axis=1)
    modes=MOTOR_COLS+['motor_mean_confirm','motor_min_confirm']
    for k in KS:
        vals=[]
        for i in range(n):
            if not np.isfinite(scores[i]).any(): vals.append(''); continue
            idx=np.argsort(-np.nan_to_num(scores[i],nan=-1))[:k]
            vals.append(';'.join(base.COMBOS[j] for j in idx))
        df[f'top{k}']=vals
    march=df[df.month=='2026-03'].copy(); cand=[]
    for mode in modes:
        for qv in QS:
            cut=float(march[mode].quantile(qv))
            for k in KS:
                _,m=evaluate(march,mode,cut,k)
                if 30<=m['races']<=250: cand.append(m)
    if not cand: raise RuntimeError('no March candidate')
    # March only; tie favors more support, then simpler single variable.
    chosen=max(cand,key=lambda z:(z['roi_pct'],z['races'],-modes.index(z['mode'])))
    hold=df[df.month.isin(['2026-04','2026-05','2026-06'])]; shadow=df[df.month.isin(['2026-07','2026-08'])]
    sh,hm=evaluate(hold,chosen['mode'],chosen['cut'],chosen['k']); ss,sm=evaluate(shadow,chosen['mode'],chosen['cut'],chosen['k'])
    overlap=int(pd.concat([sh,ss]).race_code.astype(str).isin(exclusion).sum())
    if overlap: raise RuntimeError(f'v288 overlap {overlap}')
    pd.concat([sh.assign(period='pristine_holdout'),ss.assign(period='shadow')]).to_csv(OUT,index=False,encoding='utf-8-sig')
    cmb={'races':BASELINE['races']+hm['races'],'hits':BASELINE['hits']+hm['hits'],'stake_yen':BASELINE['stake_yen']+hm['stake_yen'],'payout_yen':BASELINE['payout_yen']+hm['payout_yen']}
    cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    decision='RESEARCH_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION'
    out={'wave':'34g-motor-confirmation','feature_count':63,'march_tuning_from_feb_only':chosen,'strict_pristine_holdout_apr_jun':hm,'shadow_non_pristine_jul_aug':sm,'legacy_overlap':overlap,'combined_baseline_plus_holdout':cmb,'decision':decision}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave34g relative motor confirmation','',f"- March selected: **{chosen['mode']} >= {chosen['cut']:.4f}, top{chosen['k']}**; {chosen['races']}R / ROI {chosen['roi_pct']:.3f}%",f"- Apr-Jun: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- min month {hm['min_month_roi_pct']:.3f}% / red months {hm['red_months']} / max DD {hm['max_drawdown_yen']:,.0f} yen",f"- Jul-Aug shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + holdout: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",f'- overlap: **{overlap}**',f'- decision: **{decision}**','','## Monthly']
    for mo,z in hm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)
if __name__=='__main__': main()
