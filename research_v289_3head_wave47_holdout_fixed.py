from pathlib import Path
import json, numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
import research_v289_3head_wave31_nonlinear_gate as base
SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv'); BASEC=Path('v288_operational_pre_replay_94_baseline_codes.csv'); CUT=.365448; COMBOS=base.COMBOS

def num(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')
def zfeat(d):
    x=pd.DataFrame(index=d.index)
    for m in ['モーター2連対率','モーター3連対率']:
        for b in [1,2,4]: x[f'{m}_{b}']=num(d[f'card__艇3_{m}'])-num(d[f'card__艇{b}_{m}'])
    return x
def w36(tx,ty,vx):
    yh=ty.str.startswith('3-').astype(int).to_numpy(); h=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto')); h.fit(tx,yh); p=h.predict_proba(vx)[:,1]
    m=yh==1; c=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.15)); c.fit(tx.iloc[np.flatnonzero(m)],ty.to_numpy()[m]); pc=c.predict_proba(vx); s=np.zeros((len(vx),len(COMBOS)))
    for j,k in enumerate(c.classes_):
        if k in COMBOS:s[:,COMBOS.index(k)]=pc[:,j]
    t=[';'.join(COMBOS[j] for j in np.argsort(-s[i])[:5]) for i in range(len(vx))]; return p,t
def money(q):
    x=q.copy(); x['variant_return']=[base.dutch_return(r,str(r.top5).split(';')) for _,r in x.iterrows()]; m=base.block(x); mm={k:base.block(g) for k,g in x.groupby('month')}; m.update(monthly=mm,min_month_roi_pct=min(v['roi_pct'] for v in mm.values()),red_months=sum(v['roi_pct']<100 for v in mm.values()),max_drawdown_yen=base.maxdd(x.sort_values(['date','race_code']))); return m

def main():
    d=pd.read_csv(SRC,dtype=str).fillna('');
    if d.date.max()>'2026-08-31': raise RuntimeError('September forbidden')
    ex=set(pd.read_csv(BASEC,dtype=str).race_code.astype(str)); d=d[~d.race_code.astype(str).isin(ex)].copy(); d=d[(d.settle__usable=='1')&(d.closing_odds__ok=='1')].reset_index(drop=True); d['month']=d.date.str[:7]; X=base.build_static(d); y=d.settle__actual_combo.astype(str); p=np.full(len(d),np.nan); tops=np.array(['']*len(d),object)
    def run(a,b):
        tr=np.flatnonzero(a.to_numpy()); te=np.flatnonzero(b.to_numpy()); pp,tt=w36(X.iloc[tr],y.iloc[tr],X.iloc[te]); p[te]=pp; tops[te]=tt
    run(d.month=='2026-02',d.month=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']: run(d.month<mo,d.month==mo)
    d['p3']=p; d['top5']=tops; Z=zfeat(d); tr=d.month=='2026-02'; zm=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=800,C=.08,class_weight='balanced')); zm.fit(Z.loc[tr],y.loc[tr].str.startswith('3-').astype(int)); d['zone']=zm.predict_proba(Z)[:,1]
    march=d[(d.month=='2026-03')&(d.p3>=CUT)]; zcut=float(march.zone.quantile(.40)); hold=d[d.month.isin(['2026-04','2026-05','2026-06'])]; wave=hold[hold.p3>=CUT]; sel=wave[wave.zone>=zcut]; wm=money(wave); sm=money(sel); dec='RESEARCH_CANDIDATE' if sm['races']>=120 and sm['roi_pct']>=125 and sm['red_months']<=1 and sm['min_month_roi_pct']>=85 else 'NO_ADOPTION'
    print(f'Wave36 {wm["races"]}R {wm["hits"]} hits ROI {wm["roi_pct"]:.3f}% profit {wm["profit_yen"]:+,}')
    print(f'Wave47 {sm["races"]}R {sm["hits"]} hits ROI {sm["roi_pct"]:.3f}% profit {sm["profit_yen"]:+,} minmonth {sm["min_month_roi_pct"]:.3f}% red {sm["red_months"]} maxDD {sm["max_drawdown_yen"]:,.0f}')
    for mo,v in sm['monthly'].items(): print(f'{mo} {v["races"]}R {v["hits"]} hits ROI {v["roi_pct"]:.3f}% profit {v["profit_yen"]:+,}')
    print('decision',dec); print('September unread')
if __name__=='__main__': main()
