from __future__ import annotations
import json
import numpy as np
import pandas as pd

from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from run_3head_funsite_broad50_wave16 import (
    build_pre_enhanced, load_canonical, choose_features, pct_ref
)
import run_3head_wave19_motor_exhibition_gate as w19

MONTHS = {
    'oct': ('2025-10-01','2025-10-31'),
    'nov': ('2025-11-01','2025-11-30'),
    'dec': ('2025-12-01','2025-12-31'),
    'jan': ('2026-01-01','2026-01-31'),
    'feb': ('2026-02-01','2026-02-28'),
    'mar': ('2026-03-01','2026-03-31'),
    'apr': ('2026-04-01','2026-04-30'),
}

FROZEN = {
    'A_precision': {
        'band': [1,12], 'bq': 0.925,
        'conds': [
            ['post_motor_rank_edge2','>=',0.20],
            ['post_ex_rank3','<=',1.0],
        ],
    },
    'B_stability': {
        'band': [1,8], 'bq': 0.925,
        'conds': [
            ['post_motor_inner_top2_gap','>=',0.05],
            ['post_ex_rank3','<=',2.0],
        ],
    },
    'Control_PRE': {
        'band': [1,8], 'bq': 0.99, 'conds': [],
    },
}

def cond_mask(df, cond):
    col, op, val = cond
    x = pd.to_numeric(df[col], errors='coerce')
    if op == '>=': return x >= val
    if op == '<=': return x <= val
    raise ValueError(op)

def fixed_mask(df, spec):
    rn = pd.to_numeric(df.race_no, errors='coerce')
    pre = pd.to_numeric(df.pre_score, errors='coerce')
    lo, hi = spec['band']
    m = (rn >= lo) & (rn <= hi) & pre.notna() & (pre >= spec['bq'])
    for cond in spec['conds']:
        m &= cond_mask(df, cond).fillna(False)
    return m

def metrics(df, mask):
    m = np.asarray(mask, dtype=bool)
    n = int(m.sum())
    if not n:
        return {'n':0,'hits':0,'rate':None,'venues':0}
    y = df.y.to_numpy(dtype=int)
    return {'n':n,'hits':int(y[m].sum()),'rate':float(y[m].mean()),
            'venues':int(df.loc[m,'venue'].nunique())}

def split_metrics(df, mask):
    d = pd.to_datetime(df.date).dt.day
    return {
        'total': metrics(df, mask),
        'h1': metrics(df, mask & (d <= 15)),
        'h2': metrics(df, mask & (d > 15)),
    }

def venue_audit(df, mask):
    q = df.loc[np.asarray(mask,bool), ['venue','y']].copy()
    total_n = len(q)
    if not total_n:
        return {'total_n':0,'max_venue_share':None,'top_venues':[],
                'loo_min_rate':None,'loo_max_rate':None,'loo':[]}
    by=[]
    for v,g in q.groupby('venue'):
        by.append({'venue':str(v),'n':int(len(g)),'hits':int(g.y.sum()),
                   'rate':float(g.y.mean()),'share':float(len(g)/total_n)})
    by=sorted(by,key=lambda z:z['n'],reverse=True)
    loo=[]
    for v in sorted(q.venue.astype(str).unique()):
        g=q[q.venue.astype(str)!=v]
        if len(g):
            loo.append({'left_out':str(v),'n':int(len(g)),'hits':int(g.y.sum()),
                        'rate':float(g.y.mean())})
    return {
        'total_n':int(total_n),
        'max_venue_share':float(max(x['share'] for x in by)),
        'top_venues':by[:10],
        'loo_min_rate':float(min(x['rate'] for x in loo)) if loo else None,
        'loo_max_rate':float(max(x['rate'] for x in loo)) if loo else None,
        'loo':loo,
    }

def make_frozen_pre_scores(frames):
    # Feature names remain frozen from Oct-Feb, exactly as Wave22.
    frozen = pd.concat([frames[m] for m in ['oct','nov','dec','jan','feb']],
                       ignore_index=True,sort=False)
    _, enh, _ = choose_features(frozen)

    target = frames['apr'].sort_values(['date','rc']).copy()
    hist = pd.concat([frames[m] for m in ['oct','nov','dec','jan','feb','mar','apr']],
                     ignore_index=True,sort=False)
    rows=[]
    for dayv in sorted(target.date.dt.normalize().unique()):
        day=pd.Timestamp(dayv)
        today=target[target.date.dt.normalize()==day].copy()
        tr=hist[(hist.date<day)&(hist.date>=day-pd.Timedelta(days=42))].copy()
        if len(tr)<500 or tr.y.nunique()<2 or len(today)==0:
            continue
        model=make_pipeline(
            SimpleImputer(strategy='median'),
            StandardScaler(),
            LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',
                               max_iter=1800,random_state=161)
        )
        model.fit(tr[enh],tr.y)
        ptr=model.predict_proba(tr[enh])[:,1]
        p=model.predict_proba(today[enh])[:,1]
        z=today[['rc','date','venue','race_no','y']].copy()
        z['pre_score']=pct_ref(ptr,p)
        rows.append(z)
    if not rows:
        raise RuntimeError('no PRE predictions for April')
    return pd.concat(rows,ignore_index=True).drop_duplicates('rc'), len(enh)

def main():
    raw={}
    for m,(a,b) in MONTHS.items():
        x,r,audit=build_pre_enhanced(a,b,True)
        raw[m]=(x,r,audit)
    frames={m:w19.prep_month(x,r) for m,(x,r,_) in raw.items()}

    canon=load_canonical()
    ca=canon[(canon.date>='2026-04-01')&(canon.date<'2026-05-01')][
        ['rc','date','settle__winner']
    ].copy()
    if len(ca) < 3500:
        raise RuntimeError(f'canonical April too small: {len(ca)}')
    base_apr=raw['apr'][0].drop(columns=['date'])
    apr=ca.merge(base_apr,on='rc',how='inner')
    apr['date']=pd.to_datetime(apr['date'])
    apr['y']=(pd.to_numeric(apr.settle__winner,errors='coerce')==3).astype(int)
    frames['apr']=apr

    fc=ca.merge(raw['apr'][1][['rc','result_winner']],on='rc',how='inner')
    agree=float(
        (pd.to_numeric(fc.settle__winner,errors='coerce') ==
         pd.to_numeric(fc.result_winner,errors='coerce')).mean()
    ) if len(fc) else 0.0
    if len(fc) < 3500 or agree < .999:
        raise RuntimeError(f'april cross-check failed n={len(fc)} agreement={agree}')

    pre_apr, enh_count=make_frozen_pre_scores(frames)

    w19.END='2026-04-30'
    days,cache=w19.prefetch_sources()
    post,post_audit=w19.build_motor_exhibition(days,cache)
    apr_scored=pre_apr.merge(post,on=['rc','date'],how='left',validate='one_to_one')

    results={}
    for name,spec in FROZEN.items():
        m=fixed_mask(apr_scored,spec)
        results[name]={
            'definition':spec,
            'april':split_metrics(apr_scored,m),
            'venue_audit':venue_audit(apr_scored,m),
        }

    out={
        'policy':{
            'one_shot_april_confirmation':True,
            'candidate_count':3,
            'threshold_search_performed':False,
            'april_based_retuning_allowed':False,
            'pre_feature_list_frozen_oct_feb':True,
            'motor_strict_prior_day':True,
            'same_day_motor_results_used':False,
            'september_2026_outcomes_read':False,
            'production_v288_changed':False,
        },
        'april_cross_source_winner_check':{'n':int(len(fc)),'agreement':agree},
        'source_audit':{m:raw[m][2] for m in raw},
        'post_source_audit':post_audit,
        'enhanced_pre_feature_count':int(enh_count),
        'april_pre_rows':int(len(pre_apr)),
        'april_scored_rows':int(len(apr_scored)),
        'results':results,
    }
    with open('research_3head_wave23_april_frozen_result.json','w') as f:
        json.dump(out,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))

if __name__=='__main__':
    main()
