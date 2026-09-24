#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np, runpy, sys
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

sys.path.insert(0,'research'); sys.path.insert(0,'.')

# Rebuild same exact 39-race causal feature table.
src=open('research/research_3head_opponent_type_v16.py',encoding='utf-8').read()
needle="print('FEATURE_COUNT',len(features))"
repl="x.to_csv('outer_true_feature_table_v22.csv',index=False)\n"+needle
assert needle in src
src=src.replace(needle,repl,1)
src=src.split("# Leave-one-month-out, no same-month fitting.")[0]+"\nprint('V22_FEATURE_TABLE_OK')\n"
open('/tmp/v22_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v22_builder.py',run_name='__main__')

x=pd.read_csv('outer_true_feature_table_v22.csv',dtype={'race_code':str})
x.race_code=x.race_code.str.zfill(12)
x['second']=pd.to_numeric(x.second,errors='coerce').astype(int)
x['third']=pd.to_numeric(x.third,errors='coerce').astype(int)
assert len(x)==39

def learn_thresholds(df):
    return {
        'b2':float(pd.to_numeric(df.b2_pl_frame_p2,errors='coerce').quantile(.6)),
        'b1':float(pd.to_numeric(df.b1_pl_frame_win,errors='coerce').quantile(.6)),
        'se':float(pd.to_numeric(df.post_straight_edge2,errors='coerce').quantile(.5)),
    }

def route_outer(df,th):
    b2=pd.to_numeric(df.b2_pl_frame_p2,errors='coerce')
    b1=pd.to_numeric(df.b1_pl_frame_win,errors='coerce')
    se=pd.to_numeric(df.post_straight_edge2,errors='coerce')
    sig32=(b2>=th['b2'])&(se<=th['se'])
    sig31=(b1>=th['b1'])&(se>=th['se'])
    both=sig32&sig31
    if both.any():
        b2z=(b2-th['b2'])/(pd.to_numeric(df.b2_pl_frame_p2,errors='coerce').std()+1e-9)
        b1z=(b1-th['b1'])/(pd.to_numeric(df.b1_pl_frame_win,errors='coerce').std()+1e-9)
        sig32=sig32 & (~both | (b2z>=b1z))
        sig31=sig31 & (~both | (b1z>b2z))
    return ~(sig32|sig31)

# Features intentionally aimed at "1/2 survive vs outer survives".
cand=[
 'b1_pl_all_win','b1_pl_all_p2','b1_pl_frame_win','b1_pl_frame_p2','b1_pl_recent_p2',
 'b2_pl_all_win','b2_pl_all_p2','b2_pl_frame_win','b2_pl_frame_p2','b2_pl_recent_p2',
 'b4_pl_all_win','b4_pl_all_p2','b4_pl_frame_p2','b4_pl_recent_p2',
 'b5_pl_all_win','b5_pl_all_p2','b5_pl_frame_p2','b5_pl_recent_p2',
 'b6_pl_all_win','b6_pl_all_p2','b6_pl_frame_p2','b6_pl_recent_p2',
 'post_motor_b1_ewma_rank','post_motor_b2_ewma_rank',
 'post_motor_rank_edge1','post_motor_rank_edge2',
 'post_motor_gap1_top2','post_motor_gap2_top2','post_motor_inner_top2_gap',
 'post_st_rank3','post_st_field_edge','post_st_edge4',
 'post_straight_edge2','post_straight_edge4',
 'post_ex_edge4','post_turn_edge1','post_turn_edge4',
 'pre_score','ph_score'
]
cand=[c for c in cand if c in x.columns]

# Construct relative outer-vs-inner aggregates.
def add_rel(d):
    d=d.copy()
    outer_p2=[]
    for b in [4,5,6]:
        c=f'b{b}_pl_all_p2'
        if c in d: outer_p2.append(pd.to_numeric(d[c],errors='coerce'))
    if outer_p2:
        d['outer_mean_all_p2']=pd.concat(outer_p2,axis=1).mean(axis=1)
    inner_p2=[]
    for b in [1,2]:
        c=f'b{b}_pl_all_p2'
        if c in d: inner_p2.append(pd.to_numeric(d[c],errors='coerce'))
    if inner_p2:
        d['inner_mean_all_p2']=pd.concat(inner_p2,axis=1).mean(axis=1)
    if 'outer_mean_all_p2' in d and 'inner_mean_all_p2' in d:
        d['outer_minus_inner_all_p2']=d['outer_mean_all_p2']-d['inner_mean_all_p2']

    outer_recent=[]
    for b in [4,5,6]:
        c=f'b{b}_pl_recent_p2'
        if c in d: outer_recent.append(pd.to_numeric(d[c],errors='coerce'))
    if outer_recent:
        d['outer_mean_recent_p2']=pd.concat(outer_recent,axis=1).mean(axis=1)
    inner_recent=[]
    for b in [1,2]:
        c=f'b{b}_pl_recent_p2'
        if c in d: inner_recent.append(pd.to_numeric(d[c],errors='coerce'))
    if inner_recent:
        d['inner_mean_recent_p2']=pd.concat(inner_recent,axis=1).mean(axis=1)
    if 'outer_mean_recent_p2' in d and 'inner_mean_recent_p2' in d:
        d['outer_minus_inner_recent_p2']=d['outer_mean_recent_p2']-d['inner_mean_recent_p2']
    return d

x=add_rel(x)
cand += [c for c in ['outer_mean_all_p2','inner_mean_all_p2','outer_minus_inner_all_p2',
                     'outer_mean_recent_p2','inner_mean_recent_p2','outer_minus_inner_recent_p2'] if c in x.columns]
cand=list(dict.fromkeys(cand))

rows=[]
for testm in ['jul','aug']:
    tr_all=x[x.month.ne(testm)].copy()
    te_all=x[x.month.eq(testm)].copy()
    th=learn_thresholds(tr_all)

    tr=tr_all[route_outer(tr_all,th)].copy()
    te=te_all[route_outer(te_all,th)].copy()
    tr['y_outer']=tr.second.isin([4,5,6]).astype(int)
    te['y_outer']=te.second.isin([4,5,6]).astype(int)

    feats=[c for c in cand if pd.to_numeric(tr[c],errors='coerce').notna().sum()>=max(6,len(tr)//2)]
    print('SPLIT',testm,'TRAIN',len(tr),'TRAIN_OUTER_TRUE',int(tr.y_outer.sum()),'TEST',len(te),'TEST_OUTER_TRUE',int(te.y_outer.sum()),'FEATS',len(feats))

    # single-feature rules
    for c in feats:
        ztr=pd.to_numeric(tr[c],errors='coerce')
        zte=pd.to_numeric(te[c],errors='coerce')
        for q in [.35,.5,.65]:
            cut=float(ztr.quantile(q))
            for direc in ['ge','le']:
                pred=zte.ge(cut) if direc=='ge' else zte.le(cut)
                n=int(pred.sum()); hit=int((pred & te.y_outer.eq(1)).sum())
                if n>=2:
                    rows.append({'test_month':testm,'kind':'single','feature':c,'dir':direc,'q':q,'cut':cut,'sel':n,'hit':hit,'precision':hit/n})

    # compact model
    if tr.y_outer.nunique()==2:
        scored=[]
        for c in feats:
            z=pd.to_numeric(tr[c],errors='coerce')
            a=z[tr.y_outer.eq(1)].mean(); b=z[tr.y_outer.eq(0)].mean()
            sc=abs(a-b)/(z.std()+1e-9)
            if np.isfinite(sc): scored.append((sc,c))
        use=[c for _,c in sorted(scored,reverse=True)[:6]]
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
            LogisticRegression(C=.06,class_weight='balanced',solver='lbfgs',max_iter=2000,random_state=322))
        model.fit(tr[use],tr.y_outer)
        p=model.predict_proba(te[use])[:,1]
        for cut in [.45,.5,.55,.6,.65]:
            pred=p>=cut
            n=int(pred.sum()); hit=int((pred & te.y_outer.values.astype(bool)).sum())
            prec=hit/n if n else np.nan
            rec=hit/int(te.y_outer.sum()) if int(te.y_outer.sum()) else np.nan
            print('MODEL',testm,'TH',cut,'SEL',n,'HIT',hit,'PREC',None if np.isnan(prec) else round(prec,4),'RECALL',None if np.isnan(rec) else round(rec,4),'USE',use)
            rows.append({'test_month':testm,'kind':'model','feature':'|'.join(use),'dir':'ge','q':cut,'cut':cut,'sel':n,'hit':hit,'precision':prec})

out=pd.DataFrame(rows)
out.to_csv('outer_true_rules_v22.csv',index=False)

# cross-month robust single rules
z=out[out.kind.eq('single')]
agg=[]
for (feat,direc,q),g in z.groupby(['feature','dir','q']):
    if set(g.test_month)!={'jul','aug'}: continue
    mp=g.set_index('test_month').precision.to_dict()
    sel=int(g.sel.sum());hit=int(g.hit.sum())
    if sel:
        agg.append((min(mp.values()),hit/sel,sel,hit,feat,direc,q,mp))
for a in sorted(agg,reverse=True)[:25]:
    print('ROBUST_OUTER','MINPREC',round(a[0],4),'ALLPREC',round(a[1],4),'SEL',a[2],'HIT',a[3],'RULE',a[4],a[5],'Q',a[6],'MONTHLY',a[7])

print('OUTER_TRUE_V22_OK')
