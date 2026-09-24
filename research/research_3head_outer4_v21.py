#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np, runpy, sys
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

sys.path.insert(0,'research'); sys.path.insert(0,'.')

# Rebuild the same 39-race causal feature table used in v19/v20.
src=open('research/research_3head_opponent_type_v16.py',encoding='utf-8').read()
needle="print('FEATURE_COUNT',len(features))"
repl="x.to_csv('outer4_feature_table_v21.csv',index=False)\n"+needle
assert needle in src
src=src.replace(needle,repl,1)
src=src.split("# Leave-one-month-out, no same-month fitting.")[0]+"\nprint('V21_FEATURE_TABLE_OK')\n"
open('/tmp/v21_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v21_builder.py',run_name='__main__')

x=pd.read_csv('outer4_feature_table_v21.csv',dtype={'race_code':str})
x.race_code=x.race_code.str.zfill(12)
x['second']=pd.to_numeric(x.second,errors='coerce').astype(int)
x['third']=pd.to_numeric(x.third,errors='coerce').astype(int)
assert len(x)==39

def thresholds(df):
    return {
        'b2':float(pd.to_numeric(df.b2_pl_frame_p2,errors='coerce').quantile(.6)),
        'b1':float(pd.to_numeric(df.b1_pl_frame_win,errors='coerce').quantile(.6)),
        'se':float(pd.to_numeric(df.post_straight_edge2,errors='coerce').quantile(.5)),
    }

def route_with(th,df):
    b2=pd.to_numeric(df.b2_pl_frame_p2,errors='coerce')
    b1=pd.to_numeric(df.b1_pl_frame_win,errors='coerce')
    se=pd.to_numeric(df.post_straight_edge2,errors='coerce')
    sig32=(b2>=th['b2'])&(se<=th['se'])
    sig31=(b1>=th['b1'])&(se>=th['se'])
    both=sig32&sig31
    if both.any():
        # resolve overlap using anchor distance from the SAME threshold set only
        b2sd=float(b2.std())+1e-9; b1sd=float(b1.std())+1e-9
        b2z=(b2-th['b2'])/b2sd; b1z=(b1-th['b1'])/b1sd
        sig32=sig32 & (~both | (b2z>=b1z))
        sig31=sig31 & (~both | (b1z>b2z))
    return ~(sig32|sig31)

# Candidate 4-vs-(5,6) relative features; all causal.
def add_rel(df):
    d=df.copy()
    pairs=[
      ('pl_all_win','b4_pl_all_win','b5_pl_all_win','b6_pl_all_win'),
      ('pl_all_p2','b4_pl_all_p2','b5_pl_all_p2','b6_pl_all_p2'),
      ('pl_frame_win','b4_pl_frame_win','b5_pl_frame_win','b6_pl_frame_win'),
      ('pl_frame_p2','b4_pl_frame_p2','b5_pl_frame_p2','b6_pl_frame_p2'),
      ('pl_recent_p2','b4_pl_recent_p2','b5_pl_recent_p2','b6_pl_recent_p2'),
      ('motor_win','post_motor_b4_win','post_motor_b5_win','post_motor_b6_win'),
      ('motor_top2','post_motor_b4_top2','post_motor_b5_top2','post_motor_b6_top2'),
      ('motor_top3','post_motor_b4_top3','post_motor_b5_top3','post_motor_b6_top3'),
      ('motor_ewma_rank','post_motor_b4_ewma_rank','post_motor_b5_ewma_rank','post_motor_b6_ewma_rank'),
      ('motor_ewma_st','post_motor_b4_ewma_st','post_motor_b5_ewma_st','post_motor_b6_ewma_st'),
    ]
    for name,c4,c5,c6 in pairs:
        if all(c in d.columns for c in [c4,c5,c6]):
            v4=pd.to_numeric(d[c4],errors='coerce')
            v5=pd.to_numeric(d[c5],errors='coerce')
            v6=pd.to_numeric(d[c6],errors='coerce')
            # positive means 4 stronger, except rank/ST where lower is better.
            if name in {'motor_ewma_rank','motor_ewma_st'}:
                d['rel4_'+name]=pd.concat([v5,v6],axis=1).mean(axis=1)-v4
            else:
                d['rel4_'+name]=v4-pd.concat([v5,v6],axis=1).mean(axis=1)
    for c in ['post_st_edge4','post_ex_edge4','post_turn_edge4','post_straight_edge4','post_motor_rank_edge4','post_motor_st_edge4']:
        if c in d.columns:
            d['g_'+c]=pd.to_numeric(d[c],errors='coerce')
    return d

x=add_rel(x)
feature_cols=[c for c in x.columns if c.startswith('rel4_') or c.startswith('g_')]
print('FEATURES',feature_cols)

rows=[]
for testm in ['jul','aug']:
    tr_all=x[x.month.ne(testm)].copy()
    te_all=x[x.month.eq(testm)].copy()
    th=thresholds(tr_all)

    # Strict: test OUTER route uses thresholds learned on train month only.
    te=te_all[route_with(th,te_all)].copy()
    # Training OUTER subset uses train-month thresholds computed from train only (self-distribution, no test access).
    tr=tr_all[route_with(th,tr_all)].copy()

    tr['y4']=tr.second.eq(4).astype(int)
    te['y4']=te.second.eq(4).astype(int)

    feats=[c for c in feature_cols if pd.to_numeric(tr[c],errors='coerce').notna().sum()>=max(6,len(tr)//2)]
    print('SPLIT',testm,'TRAIN_OUTER',len(tr),'TEST_OUTER',len(te),'TRAIN_4',int(tr.y4.sum()),'TEST_4',int(te.y4.sum()),'FEATS',len(feats))

    # simple relative-feature scans, thresholds fit only on train
    for c in feats:
        ztr=pd.to_numeric(tr[c],errors='coerce')
        zte=pd.to_numeric(te[c],errors='coerce')
        for q in [.4,.5,.6]:
            cut=float(ztr.quantile(q))
            for direc in ['ge','le']:
                pred=zte.ge(cut) if direc=='ge' else zte.le(cut)
                n=int(pred.sum()); hit=int((pred & te.y4.eq(1)).sum())
                if n>=2:
                    rows.append({'test_month':testm,'kind':'single','feature':c,'dir':direc,'q':q,'cut':cut,'sel':n,'hit':hit,'precision':hit/n})

    # compact multivariate model if train has both classes
    if tr.y4.nunique()==2 and len(feats)>=3:
        # feature screen on train only
        scored=[]
        for c in feats:
            z=pd.to_numeric(tr[c],errors='coerce')
            a=z[tr.y4.eq(1)].mean(); b=z[tr.y4.eq(0)].mean()
            sc=abs(a-b)/(z.std()+1e-9)
            if np.isfinite(sc): scored.append((sc,c))
        use=[c for _,c in sorted(scored,reverse=True)[:6]]
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.08,class_weight='balanced',solver='lbfgs',max_iter=2000,random_state=321))
        model.fit(tr[use],tr.y4)
        p=model.predict_proba(te[use])[:,1]
        for cut in [.45,.5,.55,.6]:
            pred=p>=cut; n=int(pred.sum()); hit=int(((pred)&te.y4.values.astype(bool)).sum())
            print('MODEL',testm,'TH',cut,'SEL',n,'HIT',hit,'PREC',round(hit/n,4) if n else None,'USE',use)
            rows.append({'test_month':testm,'kind':'model','feature':'|'.join(use),'dir':'ge','q':cut,'cut':cut,'sel':n,'hit':hit,'precision':hit/n if n else np.nan})

out=pd.DataFrame(rows)
out.to_csv('outer4_rules_v21.csv',index=False)

# Cross-month robust single rules only.
z=out[out.kind.eq('single')]
agg=[]
for (feat,direc,q),g in z.groupby(['feature','dir','q']):
    if set(g.test_month)!={'jul','aug'}: continue
    mp=g.set_index('test_month').precision.to_dict()
    sel=int(g.sel.sum()); hit=int(g.hit.sum())
    agg.append((min(mp.values()),hit/sel if sel else 0,sel,hit,feat,direc,q,mp))
for a in sorted(agg,reverse=True)[:20]:
    print('ROBUST4','MINPREC',round(a[0],4),'ALLPREC',round(a[1],4),'SEL',a[2],'HIT',a[3],'RULE',a[4],a[5],'Q',a[6],'MONTHLY',a[7])

print('OUTER4_V21_OK')
