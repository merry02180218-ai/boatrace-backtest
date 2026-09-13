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
OUT=Path('analysis_v289_3head_wave26_exactorder_softmax.csv')
OUTJ=Path('research_v289_3head_wave26_exactorder_softmax.json')
OUTM=Path('research_v289_3head_wave26_exactorder_softmax.md')
TRAIN_TEST_MONTHS=['2026-04','2026-05','2026-06']
SHADOW_MONTHS=['2026-07','2026-08']
THRESHOLDS=[.18,.20,.22,.24,.26,.28,.30,.32,.35,.38,.40]
KS=[3,5,7,10,15,20]
METRICS=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','モーター2連対率','モーター3連対率','ボート2連対率']
COMBOS=[f'3-{a}-{b}' for a in [1,2,4,5,6] for b in [1,2,4,5,6] if b!=a]
CLASSES=['OTHER']+COMBOS


def num(s): return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')

def build_features(df):
    X=pd.DataFrame(index=df.index)
    for met in METRICS:
        vals={}
        for b in range(1,7):
            c=f'card__艇{b}_{met}'
            if c in df: vals[b]=num(df[c])
        if 3 in vals:
            X[f'b3_{met}']=vals[3]
            oth=pd.concat([vals[b] for b in vals if b!=3],axis=1)
            X[f'b3_minus_mean_{met}']=vals[3]-oth.mean(axis=1)
            for b in [1,2,4,5,6]:
                if b in vals:X[f'b3_minus_b{b}_{met}']=vals[3]-vals[b]
    for b in range(1,7):
        sts=[]; fins=[]
        for d in range(1,8):
            for s in range(1,3):
                c=f'card__艇{b}_節D{d}走{s}_ST'; r=f'card__艇{b}_節D{d}走{s}_着順'
                if c in df: sts.append(num(df[c]))
                if r in df: fins.append(num(df[r]))
        if sts:X[f'b{b}_recent_st']=pd.concat(sts,axis=1).mean(axis=1)
        if fins:X[f'b{b}_recent_finish']=pd.concat(fins,axis=1).mean(axis=1)
    for met in ['recent_st','recent_finish']:
        cols=[f'b{b}_{met}' for b in [1,2,4,5,6] if f'b{b}_{met}' in X]
        if f'b3_{met}' in X and cols:X[f'b3_minus_others_{met}']=X[f'b3_{met}']-X[cols].mean(axis=1)
    return X.replace([np.inf,-np.inf],np.nan)

def target_combo(s):
    s=str(s)
    return s if s in COMBOS else 'OTHER'

def fit_model(X,y):
    pipe=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=350,C=0.35,solver='lbfgs'))
    pipe.fit(X,y)
    return pipe

def predict_probs(model,X):
    p=model.predict_proba(X); classes=list(model.classes_)
    out=np.zeros((len(X),len(CLASSES)),dtype=float)
    for j,c in enumerate(classes):
        if c in CLASSES: out[:,CLASSES.index(c)]=p[:,j]
    return out

def dutch_return(row,tickets):
    try:od=json.loads(row['closing_odds__json'])
    except Exception:return 0
    odds=[]
    for c in tickets:
        try:o=float(od[c])
        except Exception:return 0
        if o<=1:return 0
        odds.append(o)
    inv=np.array([1/o for o in odds],dtype=float); raw=100*inv/inv.sum(); units=np.floor(raw).astype(int); rem=int(100-units.sum())
    if rem>0:
        frac=raw-units
        for i in np.argsort(-frac)[:rem]:units[i]+=1
    ac=str(row['settle__actual_combo'])
    if ac not in tickets:return 0
    pay=int(float(row['settle__trifecta_payout_100_yen'] or 0)); return int(units[tickets.index(ac)]*pay)

def block(g):
    n=len(g); stake=n*10000; payout=int(g['variant_return'].sum()) if n else 0; hits=int((g['variant_return']>0).sum()) if n else 0
    return {'races':n,'hits':hits,'hit_rate_pct':100*hits/n if n else None,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else None}

def maxdd(g):
    if g.empty:return 0
    pnl=(g['variant_return'].astype(float)-10000).cumsum(); peak=pnl.cummax(); return float((peak-pnl).max())

def add_predictions(df,X,y):
    P=np.full((len(df),len(CLASSES)),np.nan)
    pos={idx:i for i,idx in enumerate(df.index)}
    for m in TRAIN_TEST_MONTHS:
        tr=df['month']<m; te=df['month']==m
        model=fit_model(X.loc[tr],y.loc[tr]); pp=predict_probs(model,X.loc[te])
        for k,idx in enumerate(df.index[te]):P[pos[idx],:]=pp[k]
    tr=df['month']<='2026-06'; model=fit_model(X.loc[tr],y.loc[tr])
    for m in SHADOW_MONTHS:
        te=df['month']==m; pp=predict_probs(model,X.loc[te])
        for k,idx in enumerate(df.index[te]):P[pos[idx],:]=pp[k]
    return P

def eval_variant(base,t,k):
    q=base[base['p3']>=t].copy()
    if q.empty:return q,block(q)
    rets=[]; tickets=[]
    for _,r in q.iterrows():
        ts=str(r[f'top{k}']).split(';') if r[f'top{k}'] else []
        tickets.append(';'.join(ts)); rets.append(dutch_return(r,ts))
    q['tickets']=tickets; q['variant_return']=rets
    met=block(q); mm={m:block(g) for m,g in q.groupby('month')}; met.update({'threshold':t,'k':k,'monthly':mm,'min_month_roi_pct':min((x['roi_pct'] for x in mm.values()),default=None),'red_months':sum(1 for x in mm.values() if x['roi_pct']<100),'max_drawdown_yen':maxdd(q.sort_values(['date','race_code']))})
    return q,met

def main():
    df=pd.read_csv(SRC,dtype=str).fillna('')
    if df['date'].max()>'2026-08-31':raise RuntimeError('September forbidden')
    for c in ['closing_odds__json','closing_odds__ok','settle__usable','settle__actual_combo']:
        if c not in df:raise RuntimeError(f'missing required {c}')
    old=pd.read_csv(OLD,dtype=str).fillna(''); exclusion=set(old['race_code'].astype(str))
    if len(exclusion)!=678:raise RuntimeError(f'expected exclusion 678 got {len(exclusion)}')
    df=df[~df['race_code'].astype(str).isin(exclusion)].copy(); df=df[(df['settle__usable']=='1')&(df['closing_odds__ok']=='1')].copy(); df['month']=df['date'].str[:7]
    X=build_features(df)
    if X.shape[1]<20:raise RuntimeError(f'insufficient features {X.shape[1]}')
    y=df['settle__actual_combo'].map(target_combo)
    P=add_predictions(df,X,y)
    for j,c in enumerate(CLASSES):df[f'prob__{c}']=P[:,j]
    df['p3']=np.nansum(P[:,1:],axis=1)
    for k in KS:
        vals=[]
        for i in range(len(df)):
            pp=P[i,1:]; order=np.argsort(-pp)[:k]; vals.append(';'.join(COMBOS[j] for j in order))
        df[f'top{k}']=vals
    pristine=df[df['month'].isin(TRAIN_TEST_MONTHS)].copy(); variants=[]
    for k in KS:
        for t in THRESHOLDS:
            q,met=eval_variant(pristine,t,k)
            if met['races']>=100:variants.append(met)
    if not variants:raise RuntimeError('no eligible variants')
    stable=[v for v in variants if v['red_months']==0]
    chosen=max(stable or variants,key=lambda z:z['roi_pct']); t=chosen['threshold']; k=chosen['k']
    sel_pr,chosen2=eval_variant(pristine,t,k)
    shadowbase=df[df['month'].isin(SHADOW_MONTHS)].copy(); sel_sh,sm=eval_variant(shadowbase,t,k)
    selected=pd.concat([sel_pr,sel_sh],ignore_index=True); selected.to_csv(OUT,index=False,encoding='utf-8-sig')
    baseline={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}
    cmb={'races':baseline['races']+chosen2['races'],'hits':baseline['hits']+chosen2['hits'],'stake_yen':baseline['stake_yen']+chosen2['stake_yen'],'payout_yen':baseline['payout_yen']+chosen2['payout_yen']}; cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    decision='SHADOW_CANDIDATE' if chosen2['roi_pct']>=baseline['roi_pct'] and chosen2['red_months']==0 else 'NO_ADOPTION'
    out={'wave':'26-conditional-exactorder-softmax','source_rows_after_conservative_v243678_exclusion':len(df),'feature_count':X.shape[1],'classes':len(CLASSES),'legacy_overlap':0,'chosen_pristine':chosen2,'shadow_non_pristine':sm,'legacy_baseline':baseline,'combined_pristine_plus_baseline':cmb,'decision':decision,'notes':['Distinct family: 21-class multinomial softmax predicts OTHER vs each of 20 exact 3-head trifecta orders from pre-deadline features.','Ticket ranking is model-probability-only; closing odds are used only after selection for JPY10,000 Dutch settlement.','Apr-Jun choose threshold and ticket count; Jul-Aug NON-PRISTINE shadow frozen after Jun.']}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# Wave26 conditional exact-order softmax','',f"- source rows: **{len(df)}**",f"- features: **{X.shape[1]} / classes 21**",'- legacy overlap: **0**',f"- chosen: **p3>={t:.2f}, top{k} tickets**",f"- pristine Apr-Jun: **{chosen2['races']}R / {chosen2['hits']} hits / ROI {chosen2['roi_pct']:.3f}% / profit {chosen2['profit_yen']:+,} yen**",f"- min-month ROI: **{chosen2['min_month_roi_pct']:.3f}%** / red months **{chosen2['red_months']}** / max DD **{chosen2['max_drawdown_yen']:,.0f} yen**",f"- Jul-Aug NON-PRISTINE shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + pristine add-on: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",f"- decision: **{decision}**",'','## Pristine monthly']
    for m,x in chosen2['monthly'].items():L.append(f"- {m}: {x['races']}R / {x['hits']} hits / ROI {x['roi_pct']:.3f}% / profit {x['profit_yen']:+,} yen")
    L+=['','## NON-PRISTINE shadow monthly']
    for m,x in sm['monthly'].items():L.append(f"- {m}: {x['races']}R / {x['hits']} hits / ROI {x['roi_pct']:.3f}% / profit {x['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L),flush=True)

if __name__=='__main__':main()
