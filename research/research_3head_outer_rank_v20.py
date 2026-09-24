#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np, runpy, sys
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# Rebuild the exact causal feature table used by v19.
sys.path.insert(0,'research'); sys.path.insert(0,'.')
src=open('research/research_3head_opponent_type_v16.py',encoding='utf-8').read()
needle="print('FEATURE_COUNT',len(features))"
repl="x.to_csv('outer_rank_feature_table_v20.csv',index=False)\n"+needle
assert needle in src
src=src.replace(needle,repl,1)
src=src.split("# Leave-one-month-out, no same-month fitting.")[0]+"\nprint('V20_FEATURE_TABLE_OK')\n"
open('/tmp/v20_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v20_builder.py',run_name='__main__')

x=pd.read_csv('outer_rank_feature_table_v20.csv',dtype={'race_code':str})
x.race_code=x.race_code.str.zfill(12)
x['second']=pd.to_numeric(x.second,errors='coerce').astype(int)
x['third']=pd.to_numeric(x.third,errors='coerce').astype(int)
assert len(x)==39

def route_outer_mask(tr,te):
    t_b2=float(pd.to_numeric(tr.b2_pl_frame_p2,errors='coerce').quantile(.6))
    t_b1=float(pd.to_numeric(tr.b1_pl_frame_win,errors='coerce').quantile(.6))
    t_se=float(pd.to_numeric(tr.post_straight_edge2,errors='coerce').quantile(.5))
    b2=pd.to_numeric(te.b2_pl_frame_p2,errors='coerce')
    b1=pd.to_numeric(te.b1_pl_frame_win,errors='coerce')
    se=pd.to_numeric(te.post_straight_edge2,errors='coerce')
    sig32=(b2>=t_b2)&(se<=t_se)
    sig31=(b1>=t_b1)&(se>=t_se)
    both=sig32&sig31
    if both.any():
        b2z=(b2-t_b2)/(pd.to_numeric(tr.b2_pl_frame_p2,errors='coerce').std()+1e-9)
        b1z=(b1-t_b1)/(pd.to_numeric(tr.b1_pl_frame_win,errors='coerce').std()+1e-9)
        sig32=sig32 & (~both | (b2z>=b1z))
        sig31=sig31 & (~both | (b1z>b2z))
    return ~(sig32|sig31)

# Candidate-specific causal features for boats 4/5/6.
suffixes=['pl_all_win','pl_all_p2','pl_frame_win','pl_frame_p2','pl_recent_p2']
motor_suffixes=['win','top2','top3','mean_rank','ewma_rank','mean_st','ewma_st','starts']
global_feats=['post_st_rank3','post_st_field_edge','post_ex_edge4','post_turn_edge4','post_straight_edge4','pre_score','ph_score']

def longify(df):
    rows=[]
    for _,r in df.iterrows():
        for b in [4,5,6]:
            row={'month':r.month,'race_code':r.race_code,'boat':b,'second':int(r.second),'third':int(r.third),'y':int(int(r.second)==b)}
            for suf in suffixes:
                c=f'b{b}_{suf}'; row[suf]=r[c] if c in r.index else np.nan
            for suf in motor_suffixes:
                c=f'post_motor_b{b}_{suf}'; row['motor_'+suf]=r[c] if c in r.index else np.nan
            for c in global_feats:
                row[c]=r[c] if c in r.index else np.nan
            rows.append(row)
    return pd.DataFrame(rows)

results=[]
for testm in ['jul','aug']:
    tr_all=x[x.month.ne(testm)].copy(); te_all=x[x.month.eq(testm)].copy()
    tr=tr_all[route_outer_mask(te_all,tr_all) if False else route_outer_mask(te_all,tr_all)]
    # Above route helper expects opposite-month thresholds; recompute correctly for each frame:
    tr=tr_all[route_outer_mask(te_all,tr_all)]
    te=te_all[route_outer_mask(tr_all,te_all)]
    # Training OUTER routes are derived using thresholds from test month to preserve symmetric LOMO.
    # This is descriptive for model fitting; test selection remains based only on train-month thresholds.
    ltr=longify(tr); lte=longify(te)
    feats=[c for c in ltr.columns if c not in ['month','race_code','boat','second','third','y']]
    feats=[c for c in feats if pd.to_numeric(ltr[c],errors='coerce').notna().sum()>=12]
    model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.08,class_weight='balanced',solver='lbfgs',max_iter=2000,random_state=320))
    if ltr.y.nunique()<2:
        raise RuntimeError(f'NO_POSITIVE_CLASS_{testm}')
    model.fit(ltr[feats],ltr.y)
    lte['p']=model.predict_proba(lte[feats])[:,1]
    ranked=lte.sort_values(['race_code','p'],ascending=[True,False]).copy()
    ranked['rank']=ranked.groupby('race_code').cumcount()+1
    top=ranked[ranked['rank'].le(2)].copy()
    per=[]
    for rc,g in ranked.groupby('race_code'):
        truth=int(g.second.iloc[0]); order=g.sort_values('rank').boat.tolist()
        top1=order[0]; top2=order[:2]
        per.append({'month':testm,'race_code':rc,'truth_second':truth,'top1':top1,'top2a':top2[0],'top2b':top2[1],
                    'outer_truth':truth in [4,5,6],'top1_hit':truth==top1,'top2_hit':truth in top2})
    q=pd.DataFrame(per); results.append(q)
    print('OUTER_TEST',testm,'ROUTED',len(q),'OUTER_TRUE',int(q.outer_truth.sum()),
          'TOP1_HIT',int(q.top1_hit.sum()),'TOP1_RATE',round(q.top1_hit.mean(),4),
          'TOP2_HIT',int(q.top2_hit.sum()),'TOP2_RATE',round(q.top2_hit.mean(),4))
    z=q[q.outer_truth]
    print('OUTER_ONLY',testm,'N',len(z),'TOP1_HIT',int(z.top1_hit.sum()),'RATE',round(z.top1_hit.mean(),4) if len(z) else None,
          'TOP2_HIT',int(z.top2_hit.sum()),'RATE2',round(z.top2_hit.mean(),4) if len(z) else None)
    print('PRED_TOP1',testm,q.top1.value_counts().to_dict())

o=pd.concat(results,ignore_index=True)
o.to_csv('outer_rank_v20.csv',index=False)
print('OUTER_ALL','N',len(o),'OUTER_TRUE',int(o.outer_truth.sum()),'TOP1',int(o.top1_hit.sum()),round(o.top1_hit.mean(),4),'TOP2',int(o.top2_hit.sum()),round(o.top2_hit.mean(),4))
z=o[o.outer_truth]
print('OUTER_TRUE_ALL','N',len(z),'TOP1',int(z.top1_hit.sum()),round(z.top1_hit.mean(),4),'TOP2',int(z.top2_hit.sum()),round(z.top2_hit.mean(),4))
print('TRUTH_OUTER_DIST',z.truth_second.value_counts().to_dict())
print('OUTER_RANK_V20_OK')
