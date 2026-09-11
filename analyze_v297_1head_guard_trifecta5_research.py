#!/usr/bin/env python3
"""v297: clean 1-head loss-guard + <=5-ticket trifecta research.

Research-only development pass.
- Starts from v296 clean PRE feature families. No meet_st_strength/meet_win/meet_p2.
- Jul/Aug 2026 are never used; Sep outcomes are never read.
- Feb-Jun is expanding walk-forward development, not untouched validation.
- Current-race outcome/order is attached only AFTER all features/history are frozen.
- Head selector = HGB core plus independent LR safety guard, both cut only from train temporal OOF.
- Trifecta model ranks the 20 exact orders 1-a-b. Overall hit rate counts boat1 losses as misses.
"""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

import analyze_v294_1head_verified_prepost_research as v294
import analyze_v293_1head_direct_history_research as v293
import analyze_v296_1head_clean_operational_rebuild as v296

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'analysis_v297_1head_guard_trifecta5'
SUMMARY=ROOT/'summary_v297_1head_guard_trifecta5.md'
TEST_MONTHS=list(v294.TEST_MONTHS)
HEAD_Q=[.95,.975,.985,.99,.995]
GUARD_Q=[.90,.95,.975]
CONF_CUTS=[0.0,.45,.50,.55,.60,.65,.70,.75]
K_LIST=[1,2,3,4,5]

def norm_code(x):
    s=str(x or '').strip()
    if s.endswith('.0') and s[:-2].isdigit():s=s[:-2]
    return s.zfill(12) if s.isdigit() else ''

def parse_combo(x):
    s=str(x or '').strip().replace(' ','')
    try:a=[int(z) for z in s.split('-')]
    except Exception:return ''
    if len(a)!=3 or len(set(a))!=3 or any(z not in range(1,7) for z in a):return ''
    return '-'.join(map(str,a))

def attach_order_after_freeze(d):
    # Settlement-only source. No v108 feature/target field is loaded before freeze.
    use=['date','race_code','actual_combo']
    s=pd.read_csv(v294.V108,encoding='utf-8-sig',dtype={'race_code':str},
                  usecols=lambda c:c in use)
    s['date']=pd.to_datetime(s.date,errors='coerce')
    s=s[(s.date>=pd.Timestamp(v294.START))&(s.date<=pd.Timestamp(v294.END))].copy()
    s['date']=s.date.dt.strftime('%Y-%m-%d')
    s['race_code']=s.race_code.map(norm_code)
    s['actual_combo']=s.actual_combo.map(parse_combo)
    s=s[s.race_code!=''].drop_duplicates(['date','race_code'],keep='last')
    z=d.merge(s,on=['date','race_code'],how='left',validate='one_to_one')
    z['actual_combo']=z.actual_combo.fillna('')
    z['combo_valid']=z.actual_combo.str.match(r'^[1-6]-[1-6]-[1-6]$').astype(int)
    z['order12']=z.actual_combo.where(z.actual_combo.str.startswith('1-'),'')
    cov=float(z.combo_valid.mean()) if len(z) else 0.0
    if cov<.985:raise RuntimeError(f'combo settlement coverage too low {cov:.4f}')
    return z,cov

def combo_pipe(fs):
    pre=ColumnTransformer([
        ('n',SimpleImputer(strategy='median'),fs),
        ('v',OneHotEncoder(categories=[v293.VENUES],handle_unknown='ignore',sparse_output=False),['venue'])
    ],sparse_threshold=0)
    model=HistGradientBoostingClassifier(
        max_iter=180,learning_rate=.045,max_leaf_nodes=19,min_samples_leaf=28,
        l2_regularization=1.5,random_state=297
    )
    return Pipeline([('p',pre),('m',model)])

def combo_predict(fs,tr,te):
    x=tr[(tr.head_hit==1)&(tr.combo_valid==1)&(tr.actual_combo.str.startswith('1-'))].copy()
    if len(x)<1500:raise RuntimeError(f'not enough combo train rows {len(x)}')
    m=combo_pipe(fs);m.fit(x[fs+['venue']],x.actual_combo)
    pro=m.predict_proba(te[fs+['venue']]);classes=np.asarray(m.named_steps['m'].classes_,dtype=object)
    out=[]
    for row in pro:
        ix=np.argsort(-row)
        tickets=[str(classes[j]) for j in ix[:5]]
        top5mass=float(np.sum(row[ix[:5]]))
        out.append((tickets,top5mass))
    return out,len(x),len(classes)

def head_fold(tr,te,core_fs,guard_fs):
    # Independent model families; both gates are learned only from prior temporal OOF.
    oo_h=v293.oof('hgb',core_fs,tr); ch=v293.calfit(oo_h)
    oop_h=v293.cal(ch,oo_h.p)
    ph=v293.cal(ch,v293.fitpred('hgb',core_fs,tr,te))
    oo_g=v293.oof('lr',guard_fs,tr); cg=v293.calfit(oo_g)
    oop_g=v293.cal(cg,oo_g.p)
    pg=v293.cal(cg,v293.fitpred('lr',guard_fs,tr,te))
    hc={q:float(np.quantile(oop_h,q)) for q in HEAD_Q}
    gc={q:float(np.quantile(oop_g,q)) for q in GUARD_Q}
    return ph,pg,hc,gc,len(oo_h),len(oo_g)

def run(d,fams):
    core0=fams['CLEAN_STATIC6_PLAYER']
    # Independent safety view: boat1/2/3 absolutes plus all relative/attack signals.
    guard0=[c for c in core0 if c.startswith(('b1_','b2_','b3_','rel_','attack23_'))]
    combo0=list(core0)
    pred=[];folds=[]
    for tm in TEST_MONTHS:
        tr=d[d.month<tm].copy();te=d[d.month==tm].copy()
        core=v293.available(tr,core0,.55);guard=v293.available(tr,guard0,.55);cfs=v293.available(tr,combo0,.55)
        ph,pg,hc,gc,noh,nog=head_fold(tr,te,core,guard)
        z=te[['date','month','race_code','venue','race','head_hit','actual_combo','combo_valid']].copy()
        z['test_month']=tm;z['p_head_hgb']=ph;z['p_safe_lr']=pg
        for q,c in hc.items():z[f'hgb_q{q}_cut']=c;z[f'hgb_q{q}_sel']=(ph>=c).astype(int)
        for q,c in gc.items():z[f'lr_q{q}_cut']=c;z[f'lr_q{q}_sel']=(pg>=c).astype(int)
        cp,ncombo,nclasses=combo_predict(cfs,tr,te)
        z['top5']=[';'.join(t) for t,_ in cp]
        z['top5_mass']=[m for _,m in cp]
        actual=z.actual_combo.to_numpy()
        for k in K_LIST:
            z[f'hit{k}']=[int(bool(a) and a in tickets.split(';')[:k]) for a,tickets in zip(actual,z.top5)]
        pred.append(z)
        folds.append({'month':tm,'core_features':len(core),'guard_features':len(guard),
                      'combo_features':len(cfs),'train':len(tr),'test':len(te),
                      'head_oof':noh,'guard_oof':nog,'combo_train_headwins':ncombo,
                      'combo_classes':nclasses})
        print('fold',tm,'test',len(te),'headf',len(core),'combo train',ncombo,flush=True)
    return pd.concat(pred,ignore_index=True),pd.DataFrame(folds)

def selector_specs():
    s=[]
    for h in HEAD_Q:s.append((f'HGB_q{h:.3f}',h,None))
    for h in [.975,.985,.99,.995]:
        for g in GUARD_Q:s.append((f'HGB_q{h:.3f}_AND_LR_q{g:.3f}',h,g))
    return s

def mask_rule(g,hq,gq,conf):
    m=(g[f'hgb_q{hq}_sel']==1)
    if gq is not None:m &= (g[f'lr_q{gq}_sel']==1)
    if conf>0:m &= (g.top5_mass>=conf)
    return m

def wilson(h,n):return v293.wilson(int(h),int(n))

def evaluate(p):
    monthly=[];pooled=[]
    for name,hq,gq in selector_specs():
        for conf in CONF_CUTS:
            start=len(monthly)
            for mo,g in p.groupby('test_month'):
                s=g[mask_rule(g,hq,gq,conf)]
                R=len(s);heads=int(s.head_hit.sum());hit5=int(s.hit5.sum())
                loh,_=wilson(heads,R);lot,_=wilson(hit5,R)
                monthly.append({'rule':name,'head_q':hq,'guard_q':gq,'conf_cut':conf,'month':mo,
                                'R':R,'heads':heads,'head_rate':heads/R if R else np.nan,
                                'hit5':hit5,'trifecta5_rate':hit5/R if R else np.nan,
                                'head_wilson_lo':loh,'tri5_wilson_lo':lot,
                                'avg_top5_mass':float(s.top5_mass.mean()) if R else np.nan})
            mg=pd.DataFrame(monthly[start:])
            R=int(mg.R.sum());H=int(mg.heads.sum());T=int(mg.hit5.sum());v=mg[mg.R>0]
            r={'rule':name,'head_q':hq,'guard_q':gq,'conf_cut':conf,'R':R,'heads':H,
               'head_rate':H/R if R else np.nan,'hit5':T,'trifecta5_rate':T/R if R else np.nan,
               'months':len(v),'worst_head_month':float(v.head_rate.min()) if len(v) else np.nan,
               'worst_tri5_month':float(v.trifecta5_rate.min()) if len(v) else np.nan,
               'min_month_R':int(v.R.min()) if len(v) else 0}
            r['head_wilson_lo'],r['head_wilson_hi']=wilson(H,R)
            r['tri5_wilson_lo'],r['tri5_wilson_hi']=wilson(T,R)
            pooled.append(r)
    return pd.DataFrame(monthly),pd.DataFrame(pooled)

def k_metrics(p,pool):
    cand=pool[(pool.months==5)&(pool.R>=100)&(pool.min_month_R>=10)].copy()
    if cand.empty:return pd.DataFrame()
    cand['joint_gap']=np.maximum(0,.90-cand.head_rate)+np.maximum(0,.80-cand.trifecta5_rate)
    best=cand.sort_values(['joint_gap','trifecta5_rate','head_rate','R'],ascending=[True,False,False,False]).iloc[0]
    name=best['rule'];conf=float(best.conf_cut)
    _,hq,gq=next(x for x in selector_specs() if x[0]==name)
    s=p[mask_rule(p,hq,gq,conf)].copy()
    out=[]
    for k in K_LIST:
        H=int(s[f'hit{k}'].sum());R=len(s);lo,hi=wilson(H,R)
        out.append({'rule':name,'conf_cut':conf,'points':k,'R':R,'hits':H,
                    'hit_rate':H/R if R else np.nan,'wilson_lo':lo,'wilson_hi':hi})
    return pd.DataFrame(out)

def pct(x):return '-' if pd.isna(x) else f'{100*float(x):.2f}%'

def make_summary(cov,folds,monthly,pool,km):
    stable=pool[(pool.months==5)&(pool.R>=100)&(pool.min_month_R>=10)].copy()
    target=stable[(stable.head_rate>=.90)&(stable.trifecta5_rate>=.80)]
    headok=stable[stable.head_rate>=.90].sort_values(['head_rate','R'],ascending=False)
    best=stable.copy();best['joint_gap']=np.maximum(0,.90-best.head_rate)+np.maximum(0,.80-best.trifecta5_rate)
    best=best.sort_values(['joint_gap','trifecta5_rate','head_rate','R'],ascending=[True,False,False,False]).head(20)
    L=['# v297 clean 1HEAD loss-guard + trifecta <=5 research','',
       '- **Development research only. v296 production state is unchanged.**',
       '- Jul/Aug 2026 excluded. September outcomes unread.',
       '- Feb-Jun expanding walk-forward is reused development evidence, not untouched validation.',
       '- Features are v296-clean PRE only; contaminated `meet_st_strength`, `meet_win`, `meet_p2` are excluded.',
       '- Exact-order settlement (`actual_combo`) is attached only after race-card/history features are frozen.',
       '- Head gate: HGB + optional independent LR safety consensus. Every monthly cut comes from training temporal OOF only.',
       '- Trifecta: one multiclass model ranks all 20 exact orders `1-a-b`; hit rate denominator is every final selected race, so a boat1 loss is a trifecta miss.',
       f'- Exact-order settlement coverage: **{100*cov:.2f}%**.','',
       '## Fold audit','|month|train|test|head features|guard features|combo features|combo train 1-head|classes|',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in folds.iterrows():
        L.append(f"|{r.month}|{int(r.train)}|{int(r.test)}|{int(r.core_features)}|{int(r.guard_features)}|{int(r.combo_features)}|{int(r.combo_train_headwins)}|{int(r.combo_classes)}|")
    L+=['','## Stable development zones with head >=90%','|rule|conf|R|head rate|head Wilson low|5pt hit|5pt Wilson low|worst head month|worst 5pt month|min month R|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    if headok.empty:L.append('|None|-|-|-|-|-|-|-|-|-|')
    else:
        for _,r in headok.head(30).iterrows():
            L.append(f"|{r.rule}|{r.conf_cut:.2f}|{int(r.R)}|{pct(r.head_rate)}|{pct(r.head_wilson_lo)}|{pct(r.trifecta5_rate)}|{pct(r.tri5_wilson_lo)}|{pct(r.worst_head_month)}|{pct(r.worst_tri5_month)}|{int(r.min_month_R)}|")
    L+=['','## Best joint zones (R>=100, all 5 months, min month R>=10)','|rule|conf|R|head rate|5pt hit|worst head|worst 5pt|min month R|',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in best.iterrows():
        L.append(f"|{r.rule}|{r.conf_cut:.2f}|{int(r.R)}|{pct(r.head_rate)}|{pct(r.trifecta5_rate)}|{pct(r.worst_head_month)}|{pct(r.worst_tri5_month)}|{int(r.min_month_R)}|")
    L+=['','## <=5 point ceiling for best joint development rule','|points|R|hits|hit rate|Wilson low|','|---:|---:|---:|---:|---:|']
    if km.empty:L.append('|-|-|-|-|-|')
    else:
        for _,r in km.iterrows():L.append(f"|{int(r.points)}|{int(r.R)}|{int(r.hits)}|{pct(r.hit_rate)}|{pct(r.wilson_lo)}|")
    L+=['','## Target decision']
    if target.empty:
        L.append('- **No stable development rule simultaneously reaches 1-head >=90% and 3連単5点以内 >=80%.**')
        L.append('- Do not weaken the denominator or condition trifecta accuracy on boat1 wins; that would overstate live accuracy.')
    else:
        L.append('- Development zones meeting both numerical targets exist, but they are NOT production-qualified because Feb-Jun has already been used for model development:')
        for _,r in target.sort_values(['tri5_wilson_lo','head_wilson_lo','R'],ascending=False).head(10).iterrows():
            L.append(f"  - {r.rule}, conf>={r.conf_cut:.2f}: R={int(r.R)}, head={pct(r.head_rate)}, 5pt={pct(r.trifecta5_rate)}")
    L+=['- Any candidate chosen from this report must be frozen before prospective September input-snapshot replay; outcomes remain unread until after the freeze.']
    return '\n'.join(L)+'\n'

def main():
    d,a=v294.freeze_true_pre();d=v294.add_prior_history(d);d=v294.add_rel(d)
    fams=v296.clean_manifest(d)
    for n,fs in fams.items():
        bad=[c for c in fs if 'meet_' in c]
        if bad:raise RuntimeError(f'forbidden meeting feature in {n}: {bad[:4]}')
    print('features frozen; attach outcomes now',flush=True)
    d=v294.settle_after_freeze(d);d,cov=attach_order_after_freeze(d)
    d=d[(d.valid_result==1)&(d.combo_valid==1)].copy()
    p,folds=run(d,fams);monthly,pool=evaluate(p);km=k_metrics(p,pool)
    folds.to_csv(str(PREFIX)+'_folds.csv',index=False,encoding='utf-8-sig')
    monthly.to_csv(str(PREFIX)+'_monthly.csv',index=False,encoding='utf-8-sig')
    pool.to_csv(str(PREFIX)+'_pooled.csv',index=False,encoding='utf-8-sig')
    km.to_csv(str(PREFIX)+'_kpoints.csv',index=False,encoding='utf-8-sig')
    p.to_csv(str(PREFIX)+'_predictions.csv',index=False,encoding='utf-8-sig')
    SUMMARY.write_text(make_summary(cov,folds,monthly,pool,km),encoding='utf-8')
    print(SUMMARY.read_text(),flush=True)

if __name__=='__main__':main()
