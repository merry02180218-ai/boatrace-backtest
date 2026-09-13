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
BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUT=Path('analysis_v289_3head_wave35_logistic_stable_gate.csv')
OUTJ=Path('research_v289_3head_wave35_logistic_stable_gate.json')
OUTM=Path('research_v289_3head_wave35_logistic_stable_gate.md')
BASE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070}
QS=[.70,.75,.80,.85,.90,.93,.95,.97,.98,.99]
KS=[3,5]

def fit_predict(trainX,train_combo,testX):
    y3=train_combo.str.startswith('3-').astype(int).to_numpy()
    head=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15,solver='lbfgs'))
    head.fit(trainX,y3); p3=head.predict_proba(testX)[:,1]
    mask=y3==1
    cond=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15,solver='lbfgs'))
    cond.fit(trainX.iloc[np.flatnonzero(mask)],train_combo.to_numpy()[mask])
    pc=cond.predict_proba(testX); score=np.zeros((len(testX),len(base.COMBOS)))
    for j,c in enumerate(cond.classes_):
        if c in base.COMBOS: score[:,base.COMBOS.index(c)]=pc[:,j]
    return p3,score

def labelstat(q,k):
    n=len(q); h=int(q.actual3.sum()); t=sum(str(a) in str(ts).split(';') for a,ts in zip(q.actual,q[f'top{k}']))
    return {'races':n,'head_hits':h,'head_rate':h/n if n else 0.,'ticket_hits':t,'ticket_rate':t/n if n else 0.}

def money(q,k):
    x=q.copy(); x['variant_return']=[base.dutch_return(r,str(r[f'top{k}']).split(';') if r[f'top{k}'] else []) for _,r in x.iterrows()]
    m=base.block(x); mm={mo:base.block(g) for mo,g in x.groupby('month')}
    m.update({'monthly':mm,'min_month_roi_pct':min((z['roi_pct'] for z in mm.values()),default=None),'red_months':sum(z['roi_pct']<100 for z in mm.values()),'max_drawdown_yen':base.maxdd(x.sort_values(['date','race_code']))})
    return x,m

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('')
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    bc=pd.read_csv(BASEC,dtype=str).fillna(''); ex=set(bc.race_code.astype(str))
    if len(ex)!=94 or bc.race_code.nunique()!=94: raise RuntimeError('exact v288 94 required')
    d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d)
    if X.shape[1]!=63: raise RuntimeError(f'expected 63 static features, got {X.shape[1]}')
    y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3-').astype(int); n=len(d)
    p=np.full(n,np.nan); score=np.full((n,len(base.COMBOS)),np.nan)
    def run(trm,tem):
        tr=np.flatnonzero(trm.to_numpy()); te=np.flatnonzero(tem.to_numpy()); a,b=fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te]); p[te]=a; score[te,:]=b
    run(d.month=='2026-02',d.month=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']: run(d.month<mo,d.month==mo)
    frozen=d.month<='2026-06'
    for mo in ['2026-07','2026-08']: run(frozen,d.month==mo)
    d['p3']=p
    for k in KS:
        vals=[]
        for i in range(n):
            if not np.isfinite(score[i]).any(): vals.append(''); continue
            idx=np.argsort(-np.nan_to_num(score[i],nan=-1))[:k]; vals.append(';'.join(base.COMBOS[j] for j in idx))
        d[f'top{k}']=vals
    march=d[d.month=='2026-03'].sort_values(['date','race_code']).reset_index(drop=True); split=len(march)//2; early=march.iloc[:split]; late=march.iloc[split:]
    baseline_full=labelstat(march,3); cand=[]
    for qv in QS:
        cut=float(march.p3.quantile(qv))
        for k in KS:
            sf=march[march.p3>=cut]; se=early[early.p3>=cut]; sl=late[late.p3>=cut]
            f=labelstat(sf,k); e=labelstat(se,k); l=labelstat(sl,k)
            if f['races']>=30 and e['races']>=10 and l['races']>=10:
                worst=min(e['head_rate'],l['head_rate']); lift=worst-(march.actual3.mean())
                cand.append({'q':qv,'cut':cut,'k':k,'full':f,'early':e,'late':l,'worst_half_head_rate':worst,'worst_half_lift':lift})
    if not cand: raise RuntimeError('no March candidate')
    chosen=max(cand,key=lambda z:(z['worst_half_head_rate'],z['full']['head_rate'],z['full']['ticket_rate'],z['full']['races'],-z['q'],-z['k']))
    hold=d[d.month.isin(['2026-04','2026-05','2026-06'])]; shadow=d[d.month.isin(['2026-07','2026-08'])]
    sh,hm=money(hold[hold.p3>=chosen['cut']],chosen['k']); ss,sm=money(shadow[shadow.p3>=chosen['cut']],chosen['k'])
    overlap=int(pd.concat([sh,ss]).race_code.astype(str).isin(ex).sum())
    if overlap: raise RuntimeError(f'v288 overlap {overlap}')
    pd.concat([sh.assign(period='pristine_holdout'),ss.assign(period='shadow')]).to_csv(OUT,index=False,encoding='utf-8-sig')
    cmb={'races':94+hm['races'],'hits':52+hm['hits'],'stake_yen':940000+hm['stake_yen'],'payout_yen':1622070+hm['payout_yen']}; cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    dec='RESEARCH_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION'
    out={'wave':'35-logistic-stable-gate','scope':'Wave20 full population minus exact v288 94 only','feature_count':63,'march_selection_no_monetary_roi':chosen,'strict_pristine_holdout_apr_jun':hm,'shadow_non_pristine_jul_aug':sm,'legacy_overlap':overlap,'combined_baseline_plus_holdout':cmb,'decision':dec}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    e=chosen['early']; l=chosen['late']; f=chosen['full']
    lines=['# Wave35 corrected-scope logistic stable gate','',f"- March gate: **p3>={chosen['cut']:.6f}, top{chosen['k']}** (q={chosen['q']})",f"- March validation: {f['races']}R / head rate {f['head_rate']:.3%}; early {e['head_rate']:.3%}; late {l['head_rate']:.3%}; worst-half {chosen['worst_half_head_rate']:.3%}",f"- Apr-Jun: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- min month {hm['min_month_roi_pct']:.3f}% / red months {hm['red_months']} / max DD {hm['max_drawdown_yen']:,.0f} yen",f"- Jul-Aug shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + holdout: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",f'- exact v288 overlap: **{overlap}**',f'- decision: **{dec}**','','## Holdout monthly']
    for mo,z in hm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines),flush=True)
if __name__=='__main__': main()
