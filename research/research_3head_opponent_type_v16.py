#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

p='union53/accepted_union_head53_opponents_v15.csv'
d=pd.read_csv(p,dtype={'race_code':str})
d.race_code=d.race_code.str.zfill(12)
# identity artifact only has labels/models; rebuild pre/post/PH feature universe with accepted v14 code,
# then join strictly by race_code. We deliberately evaluate simple leave-one-month-out rules only.
import sys,runpy
sys.path.insert(0,'research');sys.path.insert(0,'.')
src=open('research/run_3head_three_layer_independent_core_v14.py',encoding='utf-8').read()
# persist p (candidate frame) before output
needle='z=pd.DataFrame(rows);z.to_csv(CSV,index=False)'
repl="pd.concat(pred,ignore_index=True).to_csv('opponent_feature_universe_v16.csv',index=False)\n    "+needle
assert needle in src
src=src.replace(needle,repl,1)
open('/tmp/v16_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v16_builder.py',run_name='__main__')
u=pd.read_csv('opponent_feature_universe_v16.csv')
u['race_code']=pd.to_numeric(u.rc,errors='coerce').astype('Int64').astype(str).str.zfill(12)
x=d.merge(u.drop_duplicates('race_code'),on='race_code',how='left',suffixes=('','_u'))
assert len(x)==53 and x.pre_score.notna().all(), 'FEATURE_JOIN_FAIL'

# Add Waku10-like/native pre features already carried by accepted builder + PLAYERHistory/post features.
# Avoid any result/outcome columns and IDs.
features=[c for c in x.columns if (
    c.startswith('b') and '_pl_' in c or
    c.startswith('pl_rel') or c.startswith('post_') or
    c.startswith('sig_') or c.startswith('new_')
)]
features=[c for c in features if pd.api.types.is_numeric_dtype(x[c]) and x[c].notna().sum()>=20]
# include accepted scores
for c in ['pre_score','ph_score']:
    if c in x and c not in features: features.append(c)

# Three practical opponent classes: 2 / 1 / OUTER(4,5,6)
x['opp_class']=x.second.map(lambda v:'2' if int(v)==2 else ('1' if int(v)==1 else 'OUTER'))
print('FEATURE_COUNT',len(features))
print('CLASS_COUNTS',x.opp_class.value_counts().to_dict())

# Leave-one-month-out, no same-month fitting.
preds=[]
for testm in ['jul','aug']:
    tr=x[x.month.ne(testm)].copy(); te=x[x.month.eq(testm)].copy()
    # small sample: L1 logistic with aggressive regularization; feature screening by univariate train-only effect.
    scores=[]
    for c in features:
        z=pd.to_numeric(tr[c],errors='coerce')
        if z.notna().sum()<15 or z.nunique()<2: continue
        # train-only between-class dispersion / within scale
        means=tr.assign(_z=z).groupby('opp_class')['_z'].mean()
        sc=float(means.max()-means.min())/(float(z.std())+1e-9)
        scores.append((sc,c))
    use=[c for _,c in sorted(scores,reverse=True)[:8]]
    model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.08,class_weight='balanced',solver='liblinear',max_iter=2000,random_state=316))
    model.fit(tr[use],tr.opp_class)
    pr=model.predict(te[use])
    q=te[['month','race_code','second','third','opp_class']].copy();q['pred_class']=pr;q['correct']=q.pred_class.eq(q.opp_class);q['features']='|'.join(use);preds.append(q)
    print('LOMO',testm,'N',len(q),'ACC',round(q.correct.mean(),4),'PRED',q.pred_class.value_counts().to_dict(),'USE',use)
o=pd.concat(preds,ignore_index=True);o.to_csv('opponent_type_lomo_v16.csv',index=False)
print('LOMO_ALL',len(o),'ACC',round(o.correct.mean(),4))
# descriptive feature deltas, not selection rules
for c in features:
    z=x.groupby('opp_class')[c].mean()
    if z.notna().sum()==3:
        spread=(z.max()-z.min())/(pd.to_numeric(x[c],errors='coerce').std()+1e-9)
        if np.isfinite(spread) and spread>0.35: print('FEATURE_SPLIT',c,round(float(spread),3),{k:round(float(v),4) for k,v in z.items()})
print('OPPONENT_TYPE_V16_OK')
