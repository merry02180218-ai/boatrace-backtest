#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

import run_v329_1head_multistage_exhibition as v329
import run_v330_1head_extended_v329_reference as v330

OUT = Path('/tmp/v332')
OUT.mkdir(parents=True, exist_ok=True)
MONTHS_DEV = ['2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']
AUG = '2026-08'
Q_GRID = [0.45,0.50,0.55,0.60,0.65]
ENV_W = [-0.20,-0.10,0.10,0.20]
LOGIT_C = [0.1,1.0,10.0]
LOGIT_Q = [0.45,0.55,0.65]
ATTACK_FEATURES = ['one_ex','one_st','one_straight','one_orig_avg']


def pct(n,d): return 100.0*n/d if d else float('nan')
def metrics(df):
    n=len(df); h=int(df.hit.sum()) if n else 0; hh=int(df.head_hit.sum()) if n else 0
    return {'R':n,'exact3':h,'exact3_rate':pct(h,n),'head':hh,'head_rate':pct(hh,n)}

def load_all():
    old=v329.build_dataset().copy()
    ext=v330.build_reference_features(v330.load_reference()).copy()
    y=pd.concat([old,ext],ignore_index=True,sort=False)
    y['race_code']=y.race_code.astype(str).str.zfill(12)
    y['month']=y.month.astype(str)
    y['hit']=pd.to_numeric(y.hit,errors='coerce').fillna(0).astype(int)
    y['head_hit']=pd.to_numeric(y.head_hit,errors='coerce').fillna(0).astype(int)
    if len(y)!=400 or int(y.head_hit.sum())!=335 or int(y.hit.sum())!=160:
        raise AssertionError(f'identity drift R={len(y)} head={int(y.head_hit.sum())} exact3={int(y.hit.sum())}')
    if set(y.month) != set(MONTHS_DEV+[AUG]):
        raise AssertionError(f'unexpected months {sorted(set(y.month))}')
    return y

def safe_std(s):
    x=pd.to_numeric(s,errors='coerce')
    sd=float(x.std(ddof=0))
    return sd if math.isfinite(sd) and sd>1e-9 else 1.0

def fit_apply(train, test, cfg):
    fam=cfg['family']; out=test.copy(); out['v332_score']=np.nan
    if fam=='ATTACK_ONLY':
        tr=train[train.attack_ready].copy(); te=out[out.attack_ready].copy()
        if len(tr)<20: return out.iloc[0:0].copy(), {}
        th=float(tr.attack_core.quantile(cfg['q']))
        out.loc[te.index,'v332_score']=te.attack_core
        sel=out.attack_ready & out.attack_core.ge(th)
        return out[sel].copy(), {'threshold':th}
    if fam=='ATTACK_ENV_SOFT':
        tr=train[train.attack_ready].copy(); te=out[out.attack_ready].copy()
        if len(tr)<20: return out.iloc[0:0].copy(), {}
        am=float(tr.attack_core.mean()); asd=safe_std(tr.attack_core)
        er=tr.loc[tr.env_ready & tr.env_pair.notna(),'env_pair']
        em=float(er.mean()) if len(er) else 0.0; esd=safe_std(er) if len(er) else 1.0
        atr=(tr.attack_core-am)/asd
        etr=pd.Series(0.0,index=tr.index)
        mm=tr.env_ready & tr.env_pair.notna(); etr.loc[mm]=(tr.loc[mm,'env_pair']-em)/esd
        score_tr=atr + cfg['env_w']*etr
        th=float(score_tr.quantile(cfg['q']))
        ate=(te.attack_core-am)/asd
        ete=pd.Series(0.0,index=te.index)
        mm2=te.env_ready & te.env_pair.notna(); ete.loc[mm2]=(te.loc[mm2,'env_pair']-em)/esd
        score_te=ate + cfg['env_w']*ete
        out.loc[te.index,'v332_score']=score_te
        sel=out.attack_ready & out.v332_score.ge(th)
        return out[sel].copy(), {'attack_mean':am,'attack_sd':asd,'env_mean':em,'env_sd':esd,'threshold':th}
    if fam=='ATTACK_COMPONENT_LOGIT':
        tr=train[train.attack_ready].copy(); te=out[out.attack_ready].copy()
        tr=tr.dropna(subset=ATTACK_FEATURES)
        te=te.dropna(subset=ATTACK_FEATURES)
        if len(tr)<30 or tr.head_hit.nunique()<2: return out.iloc[0:0].copy(), {}
        X=tr[ATTACK_FEATURES].astype(float).to_numpy(); yy=tr.head_hit.astype(int).to_numpy()
        mu=X.mean(axis=0); sd=X.std(axis=0); sd=np.where(sd>1e-9,sd,1.0)
        Xz=(X-mu)/sd
        model=LogisticRegression(C=cfg['C'],solver='liblinear',max_iter=2000,class_weight=None)
        model.fit(Xz,yy)
        ptrain=model.predict_proba(Xz)[:,1]
        th=float(np.quantile(ptrain,cfg['q']))
        if len(te):
            Xt=(te[ATTACK_FEATURES].astype(float).to_numpy()-mu)/sd
            pt=model.predict_proba(Xt)[:,1]
            out.loc[te.index,'v332_score']=pt
        sel=out.attack_ready & out.v332_score.ge(th)
        pars={'threshold':th,'coef':model.coef_[0].tolist(),'intercept':float(model.intercept_[0]),'mean':mu.tolist(),'sd':sd.tolist(),'features':ATTACK_FEATURES}
        return out[sel].copy(), pars
    raise ValueError(fam)

def candidates():
    out=[]
    for q in Q_GRID: out.append({'family':'ATTACK_ONLY','q':q})
    for w in ENV_W:
        for q in Q_GRID: out.append({'family':'ATTACK_ENV_SOFT','env_w':w,'q':q})
    for c in LOGIT_C:
        for q in LOGIT_Q: out.append({'family':'ATTACK_COMPONENT_LOGIT','C':c,'q':q})
    return out

def key(cfg):
    return json.dumps(cfg,sort_keys=True,separators=(',',':'))

def oof_eval(y,cfg):
    preds=[]; monthly=[]
    for m in MONTHS_DEV:
        tr=y[y.month.isin([x for x in MONTHS_DEV if x!=m])].copy()
        va=y[y.month.eq(m)].copy()
        p,_=fit_apply(tr,va,cfg)
        preds.append(p)
        b=metrics(va); pm=metrics(p)
        monthly.append({'month':m,**pm,'base_exact3_rate':b['exact3_rate'],'base_head_rate':b['head_rate'],
                        'exact3_lift_pp':pm['exact3_rate']-b['exact3_rate'] if pm['R'] else -999.0,
                        'head_lift_pp':pm['head_rate']-b['head_rate'] if pm['R'] else -999.0})
    pp=pd.concat(preds,ignore_index=True) if preds else y.iloc[0:0].copy()
    dev=y[y.month.isin(MONTHS_DEV)].copy(); b=metrics(dev); pm=metrics(pp)
    pass_frac=pct(pm['R'],len(dev))
    valid_months=[r for r in monthly if r['R']>=3]
    nonneg_exact=sum(r['exact3_lift_pp']>=0 for r in valid_months)
    med_exact=float(np.median([r['exact3_lift_pp'] for r in valid_months])) if valid_months else -999.0
    med_head=float(np.median([r['head_lift_pp'] for r in valid_months])) if valid_months else -999.0
    exact_lift=pm['exact3_rate']-b['exact3_rate'] if pm['R'] else -999.0
    head_lift=pm['head_rate']-b['head_rate'] if pm['R'] else -999.0
    qualifies=(pm['R']>=0.20*len(dev) and pm['exact3_rate']>=b['exact3_rate'] and pm['head_rate']>=b['head_rate']-2.0 and nonneg_exact>=3)
    score=2.0*exact_lift + 0.8*head_lift + 0.5*med_exact + 0.2*med_head + 0.03*pass_frac
    return {'cfg':cfg,'oof':pm,'baseline':b,'pass_fraction_pct':pass_frac,'nonneg_exact_months':nonneg_exact,
            'median_exact3_lift_pp':med_exact,'median_head_lift_pp':med_head,'exact3_lift_pp':exact_lift,'head_lift_pp':head_lift,
            'qualifies':bool(qualifies),'score':float(score),'monthly':monthly}

def main():
    y=load_all()
    dev=y[y.month.isin(MONTHS_DEV)].copy(); aug=y[y.month.eq(AUG)].copy()
    if len(aug)!=42 or int(aug.hit.sum())!=18 or int(aug.head_hit.sum())!=34:
        raise AssertionError('August identity drift')
    reps=[oof_eval(y,cfg) for cfg in candidates()]
    table=[]
    for r in reps:
        table.append({**r['cfg'],'cfg_key':key(r['cfg']),'qualifies':int(r['qualifies']),'score':r['score'],
                      'oof_R':r['oof']['R'],'oof_exact3_rate':r['oof']['exact3_rate'],'oof_head_rate':r['oof']['head_rate'],
                      'pass_fraction_pct':r['pass_fraction_pct'],'exact3_lift_pp':r['exact3_lift_pp'],'head_lift_pp':r['head_lift_pp'],
                      'median_exact3_lift_pp':r['median_exact3_lift_pp'],'median_head_lift_pp':r['median_head_lift_pp'],
                      'nonneg_exact_months':r['nonneg_exact_months']})
    tab=pd.DataFrame(table).sort_values(['qualifies','score'],ascending=[False,False]).reset_index(drop=True)
    tab.to_csv(OUT/'analysis_v332_candidate_oof.csv',index=False)
    chosen_rep=sorted(reps,key=lambda r:(r['qualifies'],r['score']),reverse=True)[0]
    chosen=chosen_rep['cfg']
    aug_pass,pre_aug_params=fit_apply(dev,aug,chosen)
    aug_base=metrics(aug); aug_m=metrics(aug_pass)
    aug_support=bool(aug_m['R']>=8 and aug_m['head_rate']>=aug_base['head_rate']-5.0 and (
        aug_m['exact3_rate']>=aug_base['exact3_rate'] or
        (aug_m['head_rate']>=aug_base['head_rate']+3.0 and aug_m['exact3_rate']>=aug_base['exact3_rate']-3.0)
    ))
    final_pass,final_params=fit_apply(y,y,chosen)
    monthly=[]
    for m in MONTHS_DEV+[AUG]:
        z=y[y.month.eq(m)].copy(); p,_=fit_apply(y[y.month.ne(m)].copy(),z,chosen)
        monthly.append({'month':m,'baseline':metrics(z),'pass':metrics(p),'pass_fraction_pct':pct(len(p),len(z))})
    pd.DataFrame([{'month':r['month'],
                   **{f'base_{k}':v for k,v in r['baseline'].items()},
                   **{f'pass_{k}':v for k,v in r['pass'].items()},
                   'pass_fraction_pct':r['pass_fraction_pct']} for r in monthly]).to_csv(OUT/'analysis_v332_monthly_leaveoneout.csv',index=False)
    result={
        'identity':{'R':len(y),'head':int(y.head_hit.sum()),'exact3':int(y.hit.sum())},
        'chosen':chosen,
        'chosen_oof':chosen_rep,
        'august_baseline':aug_base,
        'august_pass':aug_m,
        'august_pass_fraction_pct':pct(len(aug_pass),len(aug)),
        'august_support':aug_support,
        'params_fit_feb_jul':pre_aug_params,
        'final_params_fit_feb_aug':final_params,
        'final_training_selection_metrics_descriptive_only':metrics(final_pass),
        'PROMOTE_TO_SEPTEMBER_CANDIDATE':aug_support,
        'SEPTEMBER_OUTCOMES_READ':False,
    }
    (OUT/'result_v332.json').write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    lines=['# v332 attack-first redesign','',
           '- identity: 400 rows / 335 head / 160 exact3','- September outcomes unread.','- env_pair is never a mandatory AND gate.',
           f'- chosen config from Feb-Jul month-OOF: `{json.dumps(chosen,sort_keys=True)}`',
           f"- chosen OOF: {chosen_rep['oof']} pass_fraction={chosen_rep['pass_fraction_pct']:.2f}% exact3_lift={chosen_rep['exact3_lift_pp']:.2f}pp head_lift={chosen_rep['head_lift_pp']:.2f}pp nonneg_exact_months={chosen_rep['nonneg_exact_months']}/6",
           f'- August baseline: {aug_base}',f'- August one-shot PASS: {aug_m}; pass_fraction={pct(len(aug_pass),len(aug)):.2f}%',
           f'- AUGUST_SUPPORTED={aug_support}',f'- PROMOTE_TO_SEPTEMBER_CANDIDATE={aug_support}',
           f'- final Feb-Aug fit params: `{json.dumps(final_params,sort_keys=True)}`']
    (OUT/'summary_v332.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines),flush=True)

if __name__=='__main__': main()
