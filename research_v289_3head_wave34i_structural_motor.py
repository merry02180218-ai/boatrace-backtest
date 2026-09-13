from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import research_v289_3head_wave34b_prototype_stability as w34b
import research_v289_3head_wave31_nonlinear_gate as base

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv')
OUTJ=Path('research_v289_3head_wave34i_structural_motor.json'); OUTM=Path('research_v289_3head_wave34i_structural_motor.md'); OUT=Path('analysis_v289_3head_wave34i_structural_motor.csv')
BASE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070}; PC=.2332210614000265; AC=.55
COLS=['b3_minus_b1_モーター2連対率','b3_minus_mean_モーター2連対率','b3_minus_b1_モーター3連対率','b3_minus_b2_モーター2連対率']
QS=[.20,.35,.50,.65,.80]; KS=[3,5]
def metrics(q,k):
    x=q.copy(); x['variant_return']=[base.dutch_return(r,str(r[f'top{k}']).split(';') if r[f'top{k}'] else []) for _,r in x.iterrows()]
    m=base.block(x); mm={mo:base.block(g) for mo,g in x.groupby('month')}; m.update(monthly=mm,min_month_roi_pct=min((z['roi_pct'] for z in mm.values()),default=None),red_months=sum(z['roi_pct']<100 for z in mm.values()),max_drawdown_yen=base.maxdd(x.sort_values(['date','race_code']))); return x,m
def valstat(q,k):
    n=len(q); heads=int(q.actual3.sum()); ticket=sum(str(a) in str(t).split(';') for a,t in zip(q.actual,q[f'top{k}']))
    return {'races':n,'head_hits':heads,'head_rate':heads/n if n else 0.,'ticket_hits':ticket,'ticket_rate':ticket/n if n else 0.}
def main():
    d=pd.read_csv(SRC,dtype=str).fillna('');
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    bc=pd.read_csv(BASEC,dtype=str).fillna(''); ex=set(bc.race_code.astype(str));
    if len(ex)!=94: raise RuntimeError('exact 94 required')
    d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]
    X=base.build_static(d); 
    if X.shape[1]!=63: raise RuntimeError(f'feature count {X.shape[1]}')
    y=d.settle__actual_combo.astype(str); d['actual']=y; d['actual3']=y.str.startswith('3').astype(int); n=len(d)
    pm=np.full(n,np.nan); ag=np.full(n,np.nan); sc=np.full((n,len(base.COMBOS)),np.nan)
    def run(trm,tem,seed):
        tr=np.flatnonzero(trm.to_numpy()); te=np.flatnonzero(tem.to_numpy()); a,_,c,_,e=w34b.fit_predict(X.iloc[tr],y.iloc[tr],X.iloc[te],seed); pm[te]=a; ag[te]=c; sc[te]=e
    run(d.month=='2026-02',d.month=='2026-03',3403)
    for i,mo in enumerate(['2026-04','2026-05','2026-06'],1): run(d.month<mo,d.month==mo,3403+i)
    frozen=d.month<='2026-06'
    for i,mo in enumerate(['2026-07','2026-08'],4): run(frozen,d.month==mo,3403+i)
    d['prototype_mean']=pm; d['agreement']=ag
    feb=d.month=='2026-02'; z=[]
    for c in COLS:
        d[c]=pd.to_numeric(X[c],errors='coerce'); med=float(d.loc[feb,c].median()); mad=float((d.loc[feb,c]-med).abs().median()); mad=mad if np.isfinite(mad) and mad>1e-9 else 1.; name='z_'+c; d[name]=(d[c]-med)/mad; z.append(name)
    # orientation comes only from February labels, no odds/payouts.
    signs=[]
    for name in z:
        a=d.loc[feb & (d.actual3==1),name].mean(); b=d.loc[feb & (d.actual3==0),name].mean(); signs.append(1. if a>=b else -1.)
    d['motor_struct']=sum(s*d[name] for s,name in zip(signs,z))/len(z)
    for k in KS:
        vals=[]
        for i in range(n):
            if not np.isfinite(sc[i]).any(): vals.append(''); continue
            idx=np.argsort(-np.nan_to_num(sc[i],nan=-1))[:k]; vals.append(';'.join(base.COMBOS[j] for j in idx))
        d[f'top{k}']=vals
    febvals=d.loc[feb,'motor_struct']; march=d[d.month=='2026-03'].sort_values(['date','race_code']).copy(); half=len(march)//2; early=march.iloc[:half]; late=march.iloc[half:]
    candidates=[]
    for qv in QS:
        cut=float(febvals.quantile(qv))
        for k in KS:
            def sel(x): return x[(x.prototype_mean>=PC)&(x.agreement>=AC)&(x.motor_struct>=cut)]
            f=valstat(sel(march),k); e=valstat(sel(early),k); l=valstat(sel(late),k)
            if f['races']>=30 and e['races']>=10 and l['races']>=10:
                # label stability only; no monetary outcome in selection.
                score=min(e['head_rate'],l['head_rate']); candidates.append({'q':qv,'cut':cut,'k':k,'full':f,'early':e,'late':l,'score':score})
    if not candidates: raise RuntimeError('no March stable candidate')
    chosen=max(candidates,key=lambda c:(c['score'],c['full']['head_rate'],c['full']['ticket_rate'],c['full']['races'],-c['q']))
    def select(x): return x[(x.prototype_mean>=PC)&(x.agreement>=AC)&(x.motor_struct>=chosen['cut'])]
    sh,hm=metrics(select(d[d.month.isin(['2026-04','2026-05','2026-06'])]),chosen['k']); ss,sm=metrics(select(d[d.month.isin(['2026-07','2026-08'])]),chosen['k'])
    ov=int(pd.concat([sh,ss]).race_code.astype(str).isin(ex).sum());
    if ov: raise RuntimeError('overlap')
    pd.concat([sh.assign(period='pristine'),ss.assign(period='shadow')]).to_csv(OUT,index=False,encoding='utf-8-sig')
    cmb={'races':94+hm['races'],'hits':52+hm['hits'],'stake_yen':940000+hm['stake_yen'],'payout_yen':1622070+hm['payout_yen']}; cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    dec='RESEARCH_CANDIDATE' if hm['races']>=30 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION'
    out={'wave':'34i-structural-motor','feature_count':63,'feb_orientation_signs':dict(zip(COLS,signs)),'march_validation':chosen,'strict_pristine_holdout_apr_jun':hm,'shadow_non_pristine_jul_aug':sm,'legacy_overlap':ov,'combined_baseline_plus_holdout':cmb,'decision':dec}; OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    lines=['# Wave34i structural motor confirmation','',f"- March validation: q={chosen['q']}, cut={chosen['cut']:.4f}, top{chosen['k']}; {chosen['full']['races']}R / head rate {chosen['full']['head_rate']:.3%}; early {chosen['early']['head_rate']:.3%}; late {chosen['late']['head_rate']:.3%}",f"- Apr-Jun: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- min month {hm['min_month_roi_pct']:.3f}% / red months {hm['red_months']} / max DD {hm['max_drawdown_yen']:,.0f} yen",f"- Jul-Aug shadow: {sm['races']}R / ROI {sm['roi_pct']:.3f}%",f"- combined: {cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen",f'- overlap {ov}; decision **{dec}**','','## Monthly']+[f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen" for mo,z in hm['monthly'].items()]
    OUTM.write_text('\n'.join(lines)+'\n'); print('\n'.join(lines),flush=True)
if __name__=='__main__': main()
