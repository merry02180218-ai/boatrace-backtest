#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score

# Reuse v16 artifacts directly so this study is exactly on the same 39 covered accepted-head races.
d=pd.read_csv('v16/opponent_type_lomo_v16.csv',dtype={'race_code':str})
# Need feature matrix; rebuild the same covered accepted-head table used in v16 by executing a patched copy.
import sys,runpy
sys.path.insert(0,'research');sys.path.insert(0,'.')
src=open('research/research_3head_opponent_type_v16.py',encoding='utf-8').read()
needle="print('FEATURE_COUNT',len(features))"
repl="x.to_csv('opponent_binary_feature_table_v17.csv',index=False)\n"+needle
assert needle in src
src=src.replace(needle,repl,1)
# prevent nested model section from running
cut="# Leave-one-month-out, no same-month fitting."
src=src.split(cut)[0]+"\nprint('V17_FEATURE_TABLE_OK')\n"
open('/tmp/v17_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v17_builder.py',run_name='__main__')

x=pd.read_csv('opponent_binary_feature_table_v17.csv',dtype={'race_code':str})
assert len(x)==39
features=[c for c in x.columns if (
    (c.startswith('b') and '_pl_' in c) or c.startswith('pl_rel') or c.startswith('post_') or c.startswith('sig_') or c.startswith('new_') or c in ['pre_score','ph_score']
)]
features=[c for c in features if pd.api.types.is_numeric_dtype(x[c]) and x[c].notna().sum()>=20]
print('FEATURE_COUNT',len(features))

def run_binary(target_name, positive_second):
    xx=x.copy()
    xx['target']=xx.second.astype(int).eq(positive_second).astype(int)
    print('TARGET',target_name,'POS',int(xx.target.sum()),'NEG',int((1-xx.target).sum()))
    outs=[]
    for testm in ['jul','aug']:
        tr=xx[xx.month.ne(testm)].copy(); te=xx[xx.month.eq(testm)].copy()
        scores=[]
        for c in features:
            z=pd.to_numeric(tr[c],errors='coerce')
            if z.notna().sum()<15 or z.nunique()<2: continue
            a=tr.loc[tr.target.eq(1),c].astype(float).mean()
            b=tr.loc[tr.target.eq(0),c].astype(float).mean()
            sc=abs(a-b)/(float(z.std())+1e-9)
            scores.append((sc,c))
        use=[c for _,c in sorted(scores,reverse=True)[:6]]
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.06,class_weight='balanced',solver='lbfgs',max_iter=2000,random_state=317))
        model.fit(tr[use],tr.target)
        p=model.predict_proba(te[use])[:,1]
        # evaluate conservative thresholds; selection is based only on training-fitted model
        for th in [.45,.50,.55,.60,.65]:
            pred=(p>=th).astype(int)
            n=int(pred.sum())
            hit=int(((pred==1)&(te.target.values==1)).sum())
            prec=hit/n if n else np.nan
            rec=hit/int(te.target.sum()) if int(te.target.sum()) else np.nan
            print('BIN',target_name,'TEST',testm,'TH',th,'SEL',n,'HIT',hit,'PREC',None if np.isnan(prec) else round(prec,4),'RECALL',None if np.isnan(rec) else round(rec,4),'USE',use)
        q=te[['month','race_code','second','third']].copy();q['target']=te.target.values;q['prob']=p;q['features']='|'.join(use);outs.append(q)
    o=pd.concat(outs,ignore_index=True)
    o.to_csv(f'binary_{target_name}_v17.csv',index=False)
    # Simple single-feature threshold scan, trained on opposite month only; report for interpretability.
    key='b2_pl_frame_p2' if target_name=='3_2' else 'b1_pl_frame_win'
    if key in xx:
        for testm in ['jul','aug']:
            tr=xx[xx.month.ne(testm)].copy();te=xx[xx.month.eq(testm)].copy()
            vals=sorted(pd.to_numeric(tr[key],errors='coerce').dropna().unique())
            cands=[float(np.quantile(vals,q)) for q in [.4,.5,.6,.7]] if vals else []
            for th in sorted(set(round(v,6) for v in cands)):
                pred=pd.to_numeric(te[key],errors='coerce').ge(th)
                n=int(pred.sum());hit=int((pred & te.target.eq(1)).sum())
                print('SINGLE',target_name,key,'TEST',testm,'TH',th,'SEL',n,'HIT',hit,'PREC',round(hit/n,4) if n else None)

run_binary('3_2',2)
run_binary('3_1',1)
print('OPPONENT_BINARY_V17_OK')
