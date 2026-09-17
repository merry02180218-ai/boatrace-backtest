#!/usr/bin/env python3
"""Renewed 4-head probability research using BoatraceCSV public CSVs.

Research only. Apr-Jun train, Jul-Aug holdout. September outcomes are blocked.
Opponent/ticket semantics stay frozen at v283 + THIRD0.10 for later evaluation.
"""
from __future__ import annotations
from io import StringIO
from pathlib import Path
import math, requests
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

OUT=Path('/tmp/head4_boatracecsv_headprob'); OUT.mkdir(parents=True,exist_ok=True)
BASE='https://boatracecsv.github.io/data'
TRAIN_MONTHS={'2026-04','2026-05','2026-06'}; HOLD_MONTHS={'2026-07','2026-08'}
START=pd.Timestamp('2026-04-01'); END=pd.Timestamp('2026-08-31')
CUTS=[round(x,3) for x in np.arange(.10,.601,.01)]


def get_csv(kind, d):
    if d >= pd.Timestamp('2026-09-01'): raise RuntimeError('September outcome access blocked')
    url=f"{BASE}/{kind}/{d:%Y/%m/%d}.csv"
    r=requests.get(url,timeout=20)
    if r.status_code==404:return pd.DataFrame()
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text))

def pick_col(df, *needles):
    for c in df.columns:
        s=str(c).lower()
        if all(n.lower() in s for n in needles): return c
    return None

def boat_col(df,b,*needles):
    # Supports Japanese upstream names such as 艇4_全国勝率 and variants.
    tags=[f'艇{b}',f'{b}枠',f'{b}号艇']
    for c in df.columns:
        s=str(c)
        if any(t in s for t in tags) and all(n.lower() in s.lower() for n in needles): return c
    return None

def f(v):
    try:
        x=float(v); return x if math.isfinite(x) else np.nan
    except:return np.nan

def build():
    rows=[]
    for d in pd.date_range(START,END,freq='D'):
        cards=get_csv('programs/race_cards',d); res=get_csv('results/realtime',d)
        if cards.empty or res.empty: continue
        rc=pick_col(cards,'レース','コード') or pick_col(cards,'race','code')
        rr=pick_col(res,'レース','コード') or pick_col(res,'race','code')
        win=pick_col(res,'1着','艇') or pick_col(res,'winner')
        if not rc or not rr or not win: continue
        rmap={str(x[rr]).zfill(12):x for _,x in res.iterrows()}
        for _,x in cards.iterrows():
            code=str(x[rc]).zfill(12); y=rmap.get(code)
            if y is None: continue
            row={'date':str(d.date()),'month':d.strftime('%Y-%m'),'race_code':code,'head4':int(f(y[win])==4)}
            # Pre-race BoatraceCSV race-card features only: no preview/result leakage.
            for b in range(1,7):
                specs={
                    'national_win':['全国','勝率'],'national_top2':['全国','2連'],'national_top3':['全国','3連'],
                    'local_win':['当地','勝率'],'local_top2':['当地','2連'],'local_top3':['当地','3連'],
                    'motor_top2':['モーター','2連'],'motor_top3':['モーター','3連'],
                    'boat_top2':['ボート','2連'],'boat_top3':['ボート','3連'],
                    'avg_st':['平均','ST'],'flying':['F'],'late':['L']}
                for name,ns in specs.items():
                    c=boat_col(cards,b,*ns); row[f'b{b}_{name}']=f(x[c]) if c else np.nan
            rows.append(row)
    z=pd.DataFrame(rows)
    if z.empty: raise RuntimeError('NO_BOATRACECSV_ROWS')
    z.to_csv(OUT/'source_rows.csv',index=False)
    return z

def main():
    z=build(); tr=z[z.month.isin(TRAIN_MONTHS)].copy(); ho=z[z.month.isin(HOLD_MONTHS)].copy()
    if tr.empty or ho.empty: raise RuntimeError(f'PERIOD_INCOMPLETE train={len(tr)} hold={len(ho)}')
    feats=[c for c in z.columns if c.startswith('b') and z[c].notna().sum()>=max(50,int(.25*len(z)))]
    if not feats: raise RuntimeError('NO_USABLE_FEATURES')
    pipe=Pipeline([('prep',ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('sc',StandardScaler())]),feats)])),('lr',LogisticRegression(max_iter=2000,class_weight=None,C=.5))])
    pipe.fit(tr[feats],tr.head4)
    tr['head_prob']=pipe.predict_proba(tr[feats])[:,1]; ho['head_prob']=pipe.predict_proba(ho[feats])[:,1]
    rows=[]
    for cut in CUTS:
        for period,q in [('DEV_APR_JUN',tr),('HOLDOUT_JUL_AUG',ho)]:
            s=q[q.head_prob>=cut]
            rows.append({'cut':cut,'period':period,'R':len(s),'head4':int(s.head4.sum()),'head4_rate_pct':100*s.head4.mean() if len(s) else np.nan,'coverage_pct':100*len(s)/len(q)})
    pd.DataFrame(rows).to_csv(OUT/'headprob_threshold_sweep.csv',index=False)
    pd.concat([tr,ho]).to_csv(OUT/'scored_races.csv',index=False)
    pd.DataFrame({'feature':feats}).to_csv(OUT/'features.csv',index=False)
    print('BOATRACECSV_HEAD4_PROB_RESEARCH_OK')
    print('SOURCE',BASE)
    print('TRAIN',len(tr),int(tr.head4.sum()),'HOLDOUT',len(ho),int(ho.head4.sum()))
    print('FEATURES',len(feats))
    print(pd.DataFrame(rows).to_string(index=False))
    print('SEPTEMBER_UNREAD')
    print('PRODUCTION_UNCHANGED')
if __name__=='__main__': main()
