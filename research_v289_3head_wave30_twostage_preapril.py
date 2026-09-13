from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OLD=Path('analysis_v289_3head_wave19_full_universe_payout_enriched.csv')
OUT=Path('analysis_v289_3head_wave30_twostage_preapril.csv')
OUTJ=Path('research_v289_3head_wave30_twostage_preapril.json')
OUTM=Path('research_v289_3head_wave30_twostage_preapril.md')
METRICS=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','モーター2連対率','モーター3連対率','ボート2連対率']
COMBOS=[f'3-{a}-{b}' for a in [1,2,4,5,6] for b in [1,2,4,5,6] if b!=a]
THRESHOLDS=[.18,.20,.22,.24,.26,.28,.30,.32,.35,.38,.40,.45,.50]
KS=[3,5,7,10,15,20]
BASELINE={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}

def num(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')
def build_static(df):
    X=pd.DataFrame(index=df.index)
    for met in METRICS:
        vals={b:num(df[f'card__艇{b}_{met}']) for b in range(1,7) if f'card__艇{b}_{met}' in df}
        if 3 not in vals: continue
        X[f'b3_{met}']=vals[3]
        oth=pd.concat([vals[b] for b in vals if b!=3],axis=1)
        X[f'b3_minus_mean_{met}']=vals[3]-oth.mean(axis=1)
        for b in [1,2,4,5,6]:
            if b in vals:X[f'b3_minus_b{b}_{met}']=vals[3]-vals[b]
    if X.shape[1]!=63:raise RuntimeError(f'expected 63 static features got {X.shape[1]}')
    bad=[c for c in X.columns if any(x in c for x in ['節D','着順','settle','closing','odds','払戻'])]
    if bad:raise RuntimeError(f'forbidden features {bad[:5]}')
    return X.replace([np.inf,-np.inf],np.nan)
def pipe(C=.35):
    return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=400,C=C,solver='lbfgs'))
def dutch_return(r,tickets):
    try:od=json.loads(r['closing_odds__json']);odds=np.array([float(od[c]) for c in tickets])
    except:return 0
    if len(odds)==0 or np.any(odds<=1):return 0
    raw=100*(1/odds)/(1/odds).sum();units=np.floor(raw).astype(int);rem=100-int(units.sum())
    if rem>0:
        frac=raw-units
        for i in np.argsort(-frac)[:rem]:units[i]+=1
    ac=str(r['settle__actual_combo'])
    return int(units[tickets.index(ac)]*int(float(r['settle__trifecta_payout_100_yen'] or 0))) if ac in tickets else 0
def block(g):
    n=len(g);stake=n*10000;payout=int(g['variant_return'].sum()) if n else 0;hits=int((g['variant_return']>0).sum()) if n else 0
    return {'races':n,'hits':hits,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else None}
def maxdd(g):
    if g.empty:return 0
    pnl=(g['variant_return']-10000).cumsum();return float((pnl.cummax()-pnl).max())
def fit_predict(trainX,train_combo,testX):
    yhead=train_combo.str.startswith('3-').astype(int)
    head=pipe(.35);head.fit(trainX,yhead);p3=head.predict_proba(testX)[:,list(head.classes_).index(1)]
    mask=yhead.eq(1)
    cond=pipe(.25);cond.fit(trainX.loc[mask],train_combo.loc[mask])
    pc=cond.predict_proba(testX);score=np.zeros((len(testX),len(COMBOS)))
    for j,c in enumerate(cond.classes_):
        if c in COMBOS: score[:,COMBOS.index(c)]=pc[:,j]
    return p3,score
def score(base,t,k):
    q=base[base['p3']>=t].copy();rets=[];tsall=[]
    for _,r in q.iterrows():
        ts=str(r[f'top{k}']).split(';') if r[f'top{k}'] else [];tsall.append(';'.join(ts));rets.append(dutch_return(r,ts))
    q['tickets']=tsall;q['variant_return']=rets
    m=block(q);mm={mo:block(g) for mo,g in q.groupby('month')};m.update({'threshold':t,'k':k,'monthly':mm,'min_month_roi_pct':min((z['roi_pct'] for z in mm.values()),default=None),'red_months':sum(1 for z in mm.values() if z['roi_pct']<100),'max_drawdown_yen':maxdd(q.sort_values(['date','race_code']))});return q,m

def main():
    df=pd.read_csv(SRC,dtype=str).fillna('')
    if df['date'].max()>'2026-08-31':raise RuntimeError('September forbidden')
    old=pd.read_csv(OLD,dtype=str).fillna('');exclusion=set(old['race_code'].astype(str))
    if len(exclusion)!=678:raise RuntimeError('bad exclusion')
    df=df[~df['race_code'].astype(str).isin(exclusion)].copy();df=df[(df['settle__usable']=='1')&(df['closing_odds__ok']=='1')].copy();df['month']=df['date'].str[:7]
    X=build_static(df);yc=df['settle__actual_combo'].astype(str)
    p3=np.full(len(df),np.nan);cs=np.full((len(df),len(COMBOS)),np.nan);pos={idx:i for i,idx in enumerate(df.index)}
    def run(train_mask,test_mask):
        ph,sc=fit_predict(X.loc[train_mask],yc.loc[train_mask],X.loc[test_mask])
        for j,idx in enumerate(df.index[test_mask]): p3[pos[idx]]=ph[j];cs[pos[idx],:]=sc[j]
    run(df['month']=='2026-02',df['month']=='2026-03')
    for mo in ['2026-04','2026-05','2026-06']: run(df['month']<mo,df['month']==mo)
    train_shadow=df['month']<='2026-06'
    for mo in ['2026-07','2026-08']: run(train_shadow,df['month']==mo)
    df['p3']=p3
    for k in KS:
        arr=[]
        for i in range(len(df)):
            if not np.isfinite(cs[i]).any(): arr.append('');continue
            order=np.argsort(-np.nan_to_num(cs[i],nan=-1))[:k];arr.append(';'.join(COMBOS[j] for j in order))
        df[f'top{k}']=arr
    tune=df[df['month']=='2026-03'].copy();variants=[]
    for k in KS:
        for t in THRESHOLDS:
            _,m=score(tune,t,k)
            if m['races']>=100:variants.append(m)
    if not variants:raise RuntimeError('no March variant >=100R')
    chosen=max(variants,key=lambda z:z['roi_pct']);t=chosen['threshold'];k=chosen['k']
    sel_h,hm=score(df[df['month'].isin(['2026-04','2026-05','2026-06'])].copy(),t,k)
    sel_s,sm=score(df[df['month'].isin(['2026-07','2026-08'])].copy(),t,k)
    pd.concat([sel_h.assign(period='pristine_holdout'),sel_s.assign(period='shadow')],ignore_index=True).to_csv(OUT,index=False,encoding='utf-8-sig')
    cmb={'races':BASELINE['races']+hm['races'],'hits':BASELINE['hits']+hm['hits'],'stake_yen':BASELINE['stake_yen']+hm['stake_yen'],'payout_yen':BASELINE['payout_yen']+hm['payout_yen']};cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen'];cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    decision='SHADOW_CANDIDATE' if hm['races']>=100 and hm['roi_pct']>=BASELINE['roi_pct'] and hm['red_months']==0 else ('RESEARCH_CANDIDATE' if hm['races']>=100 and hm['roi_pct']>=110 and hm['red_months']<=1 else 'NO_ADOPTION')
    out={'wave':'30-twostage-preapril','family':'binary 3-head gate + conditional exact-order','feature_count':63,'march_tuning_from_feb_only':chosen,'strict_pristine_holdout_apr_jun':hm,'shadow_non_pristine_jul_aug':sm,'legacy_overlap':0,'combined_baseline_plus_holdout':cmb,'decision':decision,'notes':['Distinct two-stage family from Wave29 multinomial model.','No 節D/current-meet result/ST fields.','Threshold and ticket count selected only from March predictions trained on February.','Apr-Jun untouched model-selection holdout. Jul-Aug NON-PRISTINE shadow only. September forbidden. Closing odds staking only.']}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave30 two-stage pre-April validation','',f"- March tune (train Feb only): **p3>={t:.2f}, top{k}; {chosen['races']}R / ROI {chosen['roi_pct']:.3f}%**",f"- Apr-Jun untouched holdout: **{hm['races']}R / {hm['hits']} hits / ROI {hm['roi_pct']:.3f}% / profit {hm['profit_yen']:+,} yen**",f"- min month: **{hm['min_month_roi_pct']:.3f}%** / red months **{hm['red_months']}** / max DD **{hm['max_drawdown_yen']:,.0f} yen**",f"- Jul-Aug NON-PRISTINE shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + holdout: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",'- legacy overlap: **0**',f'- decision: **{decision}**','','## Pristine holdout monthly']
    for mo,z in hm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    lines+=['','## Shadow monthly']
    for mo,z in sm['monthly'].items(): lines.append(f"- {mo}: {z['races']}R / {z['hits']} hits / ROI {z['roi_pct']:.3f}% / profit {z['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines),flush=True)
if __name__=='__main__': main()

# workflow trigger after workflow registration
