from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score

SRC=Path('analysis_v289_3head_wave21_allrace_feature_settled.csv')
OLD=Path('analysis_v289_3head_wave19_full_universe_payout_enriched.csv')
OUT=Path('analysis_v289_3head_wave23_fullpop_walkforward.csv')
OUTJ=Path('research_v289_3head_wave23_fullpop_walkforward.json')
OUTM=Path('research_v289_3head_wave23_fullpop_walkforward.md')
THRESHOLDS=[.16,.18,.20,.22,.24,.26,.28,.30,.32,.35,.38,.40]
TRAIN_TEST_MONTHS=['2026-04','2026-05','2026-06']
SHADOW_MONTHS=['2026-07','2026-08']
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
    return make_pipeline(SimpleImputer(strategy='median'),HistGradientBoostingClassifier(max_iter=120,max_depth=3,learning_rate=.05,l2_regularization=1.0,random_state=1))

def dutch_return(row):
    try: od=json.loads(row['closing_odds__json'])
    except Exception:return 0
    boats=[1,2,4,5,6]
    combos=[f'3-{a}-{b}' for a in boats for b in boats if b!=a]
    odds=[]
    for c in combos:
        try:o=float(od[c])
        except Exception:return 0
        if o<=1:return 0
        odds.append(o)
    inv=np.array([1/o for o in odds],dtype=float)
    raw=100*inv/inv.sum() # 100 units of JPY100 = JPY10,000
    units=np.floor(raw).astype(int)
    rem=int(100-units.sum())
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
    conservative_exclusion=set(old['race_code'].astype(str))
    df=df[~df['race_code'].astype(str).isin(conservative_exclusion)].copy()
    # This excludes all old v243 678R, therefore legacy v288 94R overlap is guaranteed zero.
    df=df[(df['settle__usable']=='1')&(df['closing_odds__ok']=='1')].copy()
    df['month']=df['date'].str[:7]
    y=df['settle__head3_actual'].astype(int)
    X=build_features(df)
    pred=pd.Series(np.nan,index=df.index,dtype=float)
    auc={}
    for m in TRAIN_TEST_MONTHS:
        tr=df['month']<m; te=df['month']==m
        clf=model();clf.fit(X.loc[tr],y.loc[tr]); pred.loc[te]=clf.predict_proba(X.loc[te])[:,1]
        auc[m]=float(roc_auc_score(y.loc[te],pred.loc[te]))
    # Jul/Aug are non-pristine shadow only: one model frozen after Jun; never used for threshold selection.
    tr=df['month']<='2026-06'; clf=model();clf.fit(X.loc[tr],y.loc[tr])
    shadow_auc={}
    for m in SHADOW_MONTHS:
        te=df['month']==m;pred.loc[te]=clf.predict_proba(X.loc[te])[:,1]
        shadow_auc[m]=float(roc_auc_score(y.loc[te],pred.loc[te]))
    df['p3_wave23']=pred
    df['dutch_return']=df.apply(dutch_return,axis=1)
    variants=[]
    pristine=df[df['month'].isin(TRAIN_TEST_MONTHS)].copy()
    for t in THRESHOLDS:
        q=pristine[pristine['p3_wave23']>=t].copy()
        if len(q)<20:continue
        mm={m:block(g) for m,g in q.groupby('month')}
        met=block(q); met.update({'threshold':t,'monthly':mm,'min_month_roi_pct':min((x['roi_pct'] for x in mm.values()),default=None),'red_months':sum(1 for x in mm.values() if x['roi_pct']<100),'max_drawdown_yen':maxdd(q.sort_values(['date','race_code']))})
        variants.append(met)
    # Select using Feb-Jun only. Require >=100 pristine races, then maximize ROI; this is frozen before Jul/Aug.
    eligible=[v for v in variants if v['races']>=100]
    if not eligible:raise RuntimeError('no eligible variants')
    chosen=max(eligible,key=lambda z:z['roi_pct'])
    t=chosen['threshold']
    shadow=df[df['month'].isin(SHADOW_MONTHS)&(df['p3_wave23']>=t)].copy()
    shadow_monthly={m:block(g) for m,g in shadow.groupby('month')}
    shadow_metrics=block(shadow);shadow_metrics.update({'monthly':shadow_monthly,'min_month_roi_pct':min((x['roi_pct'] for x in shadow_monthly.values()),default=None),'red_months':sum(1 for x in shadow_monthly.values() if x['roi_pct']<100),'max_drawdown_yen':maxdd(shadow.sort_values(['date','race_code']))})
    selected=df[(df['month'].isin(TRAIN_TEST_MONTHS+SHADOW_MONTHS))&(df['p3_wave23']>=t)].copy()
    selected.to_csv(OUT,index=False,encoding='utf-8-sig')
    baseline={'races':94,'hits':52,'stake_yen':940000,'payout_yen':1622070,'profit_yen':682070,'roi_pct':172.560638}
    combined={'races':baseline['races']+chosen['races'],'hits':baseline['hits']+chosen['hits'],'stake_yen':baseline['stake_yen']+chosen['stake_yen'],'payout_yen':baseline['payout_yen']+chosen['payout_yen']}
    combined['profit_yen']=combined['payout_yen']-combined['stake_yen'];combined['roi_pct']=100*combined['payout_yen']/combined['stake_yen']
    decision='NO_ADOPTION'
    if chosen['roi_pct']>=baseline['roi_pct'] and chosen['red_months']==0:decision='SHADOW_CANDIDATE'
    out={'wave':'23-fullpop-head3-walkforward-all20-dutch','source_rows_after_conservative_v243678_exclusion':len(df),'feature_count':X.shape[1],'legacy_overlap':0,'overlap_method':'exclude every race_code in old v243 678R source, a conservative superset of legacy v288 94R','pristine_auc':auc,'shadow_auc_non_pristine':shadow_auc,'variants':variants,'chosen_pristine':chosen,'shadow_non_pristine':shadow_metrics,'legacy_baseline':baseline,'combined_pristine_plus_baseline':combined,'decision':decision,'notes':['Apr-Jun only used for threshold selection/evaluation; Jul-Aug reported shadow only and never select threshold.','closing odds and settlement are never model features; they are staking/evaluation only.','JPY10,000/race; 20 exact 3-head combinations Dutch allocated in JPY100 units.']}
    OUTJ.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Wave23 full-population walk-forward 3-head research','',f"- source rows after conservative old-v243 exclusion: **{len(df)}**",f"- features: **{X.shape[1]}**",f"- legacy overlap: **0** (all old v243 678R excluded)",f"- chosen threshold: **{t:.2f}**",f"- pristine Apr-Jun: **{chosen['races']}R / {chosen['hits']} hits / ROI {chosen['roi_pct']:.3f}% / profit {chosen['profit_yen']:+,} yen**",f"- pristine min-month ROI: **{chosen['min_month_roi_pct']:.3f}%** / red months **{chosen['red_months']}** / max DD **{chosen['max_drawdown_yen']:,.0f} yen**",f"- Jul-Aug NON-PRISTINE shadow: **{shadow_metrics['races']}R / {shadow_metrics['hits']} hits / ROI {shadow_metrics['roi_pct']:.3f}% / profit {shadow_metrics['profit_yen']:+,} yen**",f"- baseline + pristine add-on: **{combined['races']}R / ROI {combined['roi_pct']:.3f}% / profit {combined['profit_yen']:+,} yen**",f"- decision: **{decision}**",'', '## Pristine monthly']
    for m,x in chosen['monthly'].items():lines.append(f"- {m}: {x['races']}R / {x['hits']} hits / ROI {x['roi_pct']:.3f}% / profit {x['profit_yen']:+,} yen")
    lines+=['','## NON-PRISTINE shadow monthly']
    for m,x in shadow_monthly.items():lines.append(f"- {m}: {x['races']}R / {x['hits']} hits / ROI {x['roi_pct']:.3f}% / profit {x['profit_yen']:+,} yen")
    OUTM.write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines))
if __name__=='__main__':main()
