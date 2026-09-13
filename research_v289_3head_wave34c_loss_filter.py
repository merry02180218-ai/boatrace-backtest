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
import research_v289_3head_wave34b_prototype_stability as w34b

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
BASELINE_CODES=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('analysis_v289_3head_wave34c_loss_filter.csv')
OUTJ=Path('research_v289_3head_wave34c_loss_filter.json')
OUTM=Path('research_v289_3head_wave34c_loss_filter.md')
BASELINE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}
W34B={'races':387,'hits':54,'roi_pct':85.449,'profit_yen':-563130,'apr_roi':94.839,'may_roi':73.993,'jun_roi':87.591}
BASE_SCORE_CUT=0.233221
BASE_AGREE_CUT=0.55
K=3
RISK_QS=[.45,.55,.65,.75,.85,.90,.95,1.0]


def block_eval(q):
    q=q.copy(); rets=[]; tickets=[]
    for _,r in q.iterrows():
        ts=str(r['top3']).split(';') if r['top3'] else []
        tickets.append(';'.join(ts)); rets.append(base.dutch_return(r,ts))
    q['tickets']=tickets; q['variant_return']=rets
    m=base.block(q); mm={mo:base.block(g) for mo,g in q.groupby('month')}
    m.update({'monthly':mm,'min_month_roi_pct':min((z['roi_pct'] for z in mm.values()),default=None),'red_months':sum(1 for z in mm.values() if z['roi_pct']<100),'max_drawdown_yen':base.maxdd(q.sort_values(['date','race_code']))})
    return q,m


def main():
    df=pd.read_csv(SRC,dtype=str).fillna('')
    if df['date'].max()>'2026-08-31': raise RuntimeError('September forbidden')
    bdf=pd.read_csv(BASELINE_CODES,dtype=str).fillna(''); exclusion=set(bdf['race_code'].astype(str))
    if len(exclusion)!=94 or bdf['race_code'].nunique()!=94: raise RuntimeError('baseline exclusion must be exact 94')
    if bdf['route'].value_counts().to_dict()!={'S':55,'A':21,'B':18}: raise RuntimeError('baseline route mismatch')
    df=df[~df['race_code'].astype(str).isin(exclusion)].copy()
    df=df[(df['settle__usable']=='1')&(df['closing_odds__ok']=='1')].copy().reset_index(drop=True)
    df['month']=df['date'].str[:7]
    X=base.build_static(df)
    if X.shape[1]!=63: raise RuntimeError(f'expected 63 static features, got {X.shape[1]}')
    y=df['settle__actual_combo'].astype(str)
    n=len(df); ms=np.full(n,np.nan); ag=np.full(n,np.nan); scores=np.full((n,len(base.COMBOS)),np.nan)

    def proto_run(train_mask,test_mask,seed):
        tr=np.flatnonzero(train_mask.to_numpy()); te=np.flatnonzero(test_mask.to_numpy())
        a,_,c,_,e=w34b.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te],seed)
        ms[te]=a; ag[te]=c; scores[te,:]=e

    proto_run(df['month']=='2026-02',df['month']=='2026-03',3403)
    for i,mo in enumerate(['2026-04','2026-05','2026-06'],start=1): proto_run(df['month']<mo,df['month']==mo,3403+i)
    frozen=df['month']<='2026-06'
    for i,mo in enumerate(['2026-07','2026-08'],start=4): proto_run(frozen,df['month']==mo,3403+i)
    df['prototype_mean']=ms; df['agreement']=ag
    vals=[]
    for i in range(n):
        if not np.isfinite(scores[i]).any(): vals.append(''); continue
        idx=np.argsort(-np.nan_to_num(scores[i],nan=-1))[:K]
        vals.append(';'.join(base.COMBOS[j] for j in idx))
    df['top3']=vals

    # Independent false-positive/loss-risk model: fit ONCE on February only, then freeze.
    feb=df['month']=='2026-02'; tr=np.flatnonzero(feb.to_numpy())
    loss_y=(~y.iloc[tr].str.startswith('3-')).astype(int).to_numpy()
    loss_model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.10,solver='lbfgs',class_weight='balanced'))
    loss_model.fit(X.iloc[tr],loss_y)
    df['loss_risk']=loss_model.predict_proba(X)[:,1]

    base_ok=(df['prototype_mean']>=BASE_SCORE_CUT)&(df['agreement']>=BASE_AGREE_CUT)
    march=df[(df['month']=='2026-03')&base_ok].copy()
    if len(march)<30: raise RuntimeError(f'Wave34b March base population unexpectedly small: {len(march)}')
    candidates=[]
    for q in RISK_QS:
        cut=float(march['loss_risk'].quantile(q)) if q<1 else float(march['loss_risk'].max()+1e-12)
        sel=march[march['loss_risk']<=cut].copy(); _,m=block_eval(sel)
        if 25<=m['races']<=len(march):
            m.update({'risk_quantile':float(q),'risk_cut':cut}); candidates.append(m)
    if not candidates: raise RuntimeError('no March risk-filter candidate')
    # March only chooses filter. Prefer ROI, then more races to reduce brittle tiny-sample choice.
    chosen=max(candidates,key=lambda z:(z['roi_pct'],z['races']))
    risk_cut=chosen['risk_cut']

    hold=df[df['month'].isin(['2026-04','2026-05','2026-06']) & base_ok & (df['loss_risk']<=risk_cut)].copy()
    shadow=df[df['month'].isin(['2026-07','2026-08']) & base_ok & (df['loss_risk']<=risk_cut)].copy()
    sel_h,hm=block_eval(hold); sel_s,sm=block_eval(shadow)
    overlap=int(pd.concat([sel_h,sel_s])['race_code'].astype(str).isin(exclusion).sum())
    if overlap!=0: raise RuntimeError(f'v288 overlap {overlap}')
    pd.concat([sel_h.assign(period='pristine_holdout'),sel_s.assign(period='shadow')],ignore_index=True).to_csv(OUT,index=False,encoding='utf-8-sig')

    cmb={'races':BASELINE['races']+hm['races'],'hits':BASELINE['hits']+hm['hits'],'stake_yen':BASELINE['stake_yen']+hm['stake_yen'],'payout_yen':BASELINE['payout_yen']+hm['payout_yen']}
    cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    may=hm['monthly'].get('2026-05',{})
    comparison={'roi_delta_vs_wave34b':hm['roi_pct']-W34B['roi_pct'],'profit_delta_vs_wave34b':hm['profit_yen']-W34B['profit_yen'],'may_roi_delta_vs_wave34b':may.get('roi_pct',0)-W34B['may_roi'] if may else None,'race_delta_vs_wave34b':hm['races']-W34B['races']}
    decision='SHADOW_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=BASELINE['roi_pct'] and hm['red_months']==0 else ('RESEARCH_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION')
    out={'wave':'34c-loss-filter','family':'Wave34b bootstrap prototype stability + frozen Feb-only false-positive logistic filter','feature_count':63,'wave34b_fixed_gate':{'prototype_mean_cut':BASE_SCORE_CUT,'agreement_cut':BASE_AGREE_CUT,'k':K},'march_loss_filter_selection':chosen,'strict_pristine_holdout_apr_jun':hm,'shadow_non_pristine_jul_aug':sm,'legacy_overlap':overlap,'combined_baseline_plus_holdout':cmb,'comparison_to_wave34b':comparison,'decision':decision,'scope_note':'Wave20 full population minus exact v288 94. Loss-risk model fit only on Feb and risk threshold chosen only on March; Apr-Jun not used for tuning.'}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave34c prototype loss-risk filter','',f"- Fixed Wave34b gate: prototype_mean>={BASE_SCORE_CUT:.6f}, agreement>={BASE_AGREE_CUT:.2f}, top3",f"- March loss filter: risk<=**{risk_cut:.6f}** (q={chosen['risk_quantile']:.2f}); {chosen['races']}R / ROI {chosen['roi_pct']:.3f}%",f"- Apr-Jun holdout: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- min month: **{hm['min_month_roi_pct']:.3f}%** / red months **{hm['red_months']}** / max DD **{hm['max_drawdown_yen']:,.0f} yen**",f"- Jul-Aug shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + holdout: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",f"- vs Wave34b: ROI **{comparison['roi_delta_vs_wave34b']:+.3f}pt**, profit **{comparison['profit_delta_vs_wave34b']:+,} yen**, May ROI **{comparison['may_roi_delta_vs_wave34b']:+.3f}pt**",f'- exact v288 overlap: **{overlap}**',f'- decision: **{decision}**','','## Holdout monthly']
    for mo,z in hm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    lines+=['','## Shadow monthly']
    for mo,z in sm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)

if __name__=='__main__': main()
