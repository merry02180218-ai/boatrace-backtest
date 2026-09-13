from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OLD=Path('analysis_v289_3head_wave19_full_universe_payout_enriched.csv')
OUT=Path('analysis_v289_3head_wave24_neighbor_analog.csv')
OUTJ=Path('research_v289_3head_wave24_neighbor_analog.json')
OUTM=Path('research_v289_3head_wave24_neighbor_analog.md')
TRAIN_TEST_MONTHS=['2026-04','2026-05','2026-06']
SHADOW_MONTHS=['2026-07','2026-08']
THRESHOLDS=[.16,.18,.20,.22,.24,.26,.28,.30,.32,.35,.38,.40,.45,.50]
METRICS=['全国平均ST','全国勝率','全国2連対率','全国3連対率','当地勝率','当地2連対率','モーター2連対率','モーター3連対率','ボート2連対率']


def num(s):
    return pd.to_numeric(s.astype(str).str.replace('%','',regex=False),errors='coerce')


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


def model():
    # Deliberately distinct from Wave23 tree boosting: standardized latent analog space + distance-weighted KNN.
    return make_pipeline(
        SimpleImputer(strategy='median'),
        StandardScaler(),
        PCA(n_components=12,random_state=24),
        KNeighborsClassifier(n_neighbors=200,weights='distance',metric='euclidean',n_jobs=-1),
    )


def dutch_return(row):
    try:od=json.loads(row['closing_odds__json'])
    except Exception:return 0
    boats=[1,2,4,5,6]; combos=[f'3-{a}-{b}' for a in boats for b in boats if b!=a]
    odds=[]
    for c in combos:
        try:o=float(od[c])
        except Exception:return 0
        if o<=1:return 0
        odds.append(o)
    inv=np.array([1/o for o in odds],dtype=float)
    raw=100*inv/inv.sum(); units=np.floor(raw).astype(int); rem=int(100-units.sum())
    if rem>0:
        frac=raw-units
        for i in np.argsort(-frac)[:rem]:units[i]+=1
    ac=str(row['settle__actual_combo'])
    if ac not in combos:return 0
    pay=int(float(row['settle__trifecta_payout_100_yen'] or 0))
    return int(units[combos.index(ac)]*pay)


def block(g):
    n=len(g); stake=n*10000; payout=int(g['dutch_return'].sum()) if n else 0
    hits=int(g['settle__head3_actual'].astype(int).sum()) if n else 0
    return {'races':n,'hits':hits,'hit_rate_pct':100*hits/n if n else None,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else None}


def maxdd(g):
    if g.empty:return 0
    pnl=(g['dutch_return'].astype(float)-10000).cumsum(); peak=pnl.cummax(); return float((peak-pnl).max())


def main():
    df=pd.read_csv(SRC,dtype=str).fillna('')
    if df['date'].max()>'2026-08-31':raise RuntimeError('September forbidden')
    if 'closing_odds__json' not in df:raise RuntimeError('closing odds missing')
    old=pd.read_csv(OLD,dtype=str).fillna('')
    exclusion=set(old['race_code'].astype(str))
    if len(exclusion)!=678:raise RuntimeError(f'expected conservative exclusion 678, got {len(exclusion)}')
    df=df[~df['race_code'].astype(str).isin(exclusion)].copy()
    df=df[(df['settle__usable']=='1')&(df['closing_odds__ok']=='1')].copy()
    df['month']=df['date'].str[:7]
    y=df['settle__head3_actual'].astype(int); X=build_features(df)
    if X.shape[1]<20:raise RuntimeError(f'insufficient features {X.shape[1]}')
    pred=pd.Series(np.nan,index=df.index,dtype=float); auc={}
    for m in TRAIN_TEST_MONTHS:
        tr=df['month']<m; te=df['month']==m
        clf=model(); clf.fit(X.loc[tr],y.loc[tr]); pred.loc[te]=clf.predict_proba(X.loc[te])[:,1]
        auc[m]=float(roc_auc_score(y.loc[te],pred.loc[te]))
    # Freeze after June for NON-PRISTINE Jul/Aug shadow.
    tr=df['month']<='2026-06'; clf=model(); clf.fit(X.loc[tr],y.loc[tr]); shadow_auc={}
    for m in SHADOW_MONTHS:
        te=df['month']==m; pred.loc[te]=clf.predict_proba(X.loc[te])[:,1]
        shadow_auc[m]=float(roc_auc_score(y.loc[te],pred.loc[te]))
    df['p3_wave24_neighbor']=pred; df['dutch_return']=df.apply(dutch_return,axis=1)
    pristine=df[df['month'].isin(TRAIN_TEST_MONTHS)].copy(); variants=[]
    for t in THRESHOLDS:
        q=pristine[pristine['p3_wave24_neighbor']>=t].copy()
        if len(q)<20:continue
        mm={m:block(g) for m,g in q.groupby('month')}; met=block(q)
        met.update({'threshold':t,'monthly':mm,'min_month_roi_pct':min((x['roi_pct'] for x in mm.values()),default=None),'red_months':sum(1 for x in mm.values() if x['roi_pct']<100),'max_drawdown_yen':maxdd(q.sort_values(['date','race_code']))})
        variants.append(met)
    eligible=[v for v in variants if v['races']>=100]
    if not eligible:raise RuntimeError('no eligible variants')
    # Prefer no-red-month variants; otherwise best ROI. Still selected only on Apr-Jun.
    stable=[v for v in eligible if v['red_months']==0]
    chosen=max(stable or eligible,key=lambda z:z['roi_pct']); t=chosen['threshold']
    shadow=df[df['month'].isin(SHADOW_MONTHS)&(df['p3_wave24_neighbor']>=t)].copy()
    smm={m:block(g) for m,g in shadow.groupby('month')}; sm=block(shadow)
    sm.update({'monthly':smm,'min_month_roi_pct':min((x['roi_pct'] for x in smm.values()),default=None),'red_months':sum(1 for x in smm.values() if x['roi_pct']<100),'max_drawdown_yen':maxdd(shadow.sort_values(['date','race_code']))})
    selected=df[(df['month'].isin(TRAIN_TEST_MONTHS+SHADOW_MONTHS))&(df['p3_wave24_neighbor']>=t)].copy(); selected.to_csv(OUT,index=False,encoding='utf-8-sig')
    baseline={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}
    cmb={'races':baseline['races']+chosen['races'],'hits':baseline['hits']+chosen['hits'],'stake_yen':baseline['stake_yen']+chosen['stake_yen'],'payout_yen':baseline['payout_yen']+chosen['payout_yen']}
    cmb['profit_yen']=cmb['payout_yen']-cmb['stake_yen']; cmb['roi_pct']=100*cmb['payout_yen']/cmb['stake_yen']
    decision='SHADOW_CANDIDATE' if chosen['roi_pct']>=baseline['roi_pct'] and chosen['red_months']==0 else 'NO_ADOPTION'
    out={'wave':'24-latent-nearest-neighbor-analog','source_rows_after_conservative_v243678_exclusion':len(df),'feature_count':X.shape[1],'latent_components':12,'neighbors':200,'legacy_overlap':0,'pristine_auc':auc,'shadow_auc_non_pristine':shadow_auc,'variants':variants,'chosen_pristine':chosen,'shadow_non_pristine':sm,'legacy_baseline':baseline,'combined_pristine_plus_baseline':cmb,'decision':decision,'notes':['Distinct family from Wave23: standardized PCA latent space + distance-weighted KNN analogs.','Apr-Jun only select threshold; Jul-Aug NON-PRISTINE shadow cannot tune.','Closing odds and settlement are post-selection only; JPY10,000 all-20 Dutch.']}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    L=['# Wave24 latent nearest-neighbor analog','',f"- source rows: **{len(df)}**",f"- features: **{X.shape[1]} -> PCA 12**",'- neighbors: **200 distance-weighted**','- legacy overlap: **0**',f"- chosen threshold: **{t:.2f}**",f"- pristine Apr-Jun: **{chosen['races']}R / {chosen['hits']} hits / ROI {chosen['roi_pct']:.3f}% / profit {chosen['profit_yen']:+,} yen**",f"- min-month ROI: **{chosen['min_month_roi_pct']:.3f}%** / red months **{chosen['red_months']}** / max DD **{chosen['max_drawdown_yen']:,.0f} yen**",f"- Jul-Aug NON-PRISTINE shadow: **{sm['races']}R / {sm['hits']} hits / ROI {sm['roi_pct']:.3f}% / profit {sm['profit_yen']:+,} yen**",f"- baseline + pristine add-on: **{cmb['races']}R / ROI {cmb['roi_pct']:.3f}% / profit {cmb['profit_yen']:+,} yen**",f"- decision: **{decision}**",'','## Pristine monthly']
    for m,x in chosen['monthly'].items():L.append(f"- {m}: {x['races']}R / {x['hits']} hits / ROI {x['roi_pct']:.3f}% / profit {x['profit_yen']:+,} yen")
    L+=['','## NON-PRISTINE shadow monthly']
    for m,x in smm.items():L.append(f"- {m}: {x['races']}R / {x['hits']} hits / ROI {x['roi_pct']:.3f}% / profit {x['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L),flush=True)

if __name__=='__main__':main()
