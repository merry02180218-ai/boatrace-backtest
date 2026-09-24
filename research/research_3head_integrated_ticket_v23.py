#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np, runpy, sys
from collections import Counter,defaultdict
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

sys.path.insert(0,'research'); sys.path.insert(0,'.')

# Exact same 39-race causal feature table.
src=open('research/research_3head_opponent_type_v16.py',encoding='utf-8').read()
needle="print('FEATURE_COUNT',len(features))"
repl="x.to_csv('integrated_ticket_feature_table_v23.csv',index=False)\n"+needle
assert needle in src
src=src.replace(needle,repl,1)
src=src.split("# Leave-one-month-out, no same-month fitting.")[0]+"\nprint('V23_FEATURE_TABLE_OK')\n"
open('/tmp/v23_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v23_builder.py',run_name='__main__')

x=pd.read_csv('integrated_ticket_feature_table_v23.csv',dtype={'race_code':str})
x.race_code=x.race_code.str.zfill(12)
x['second']=pd.to_numeric(x.second,errors='coerce').astype(int)
x['third']=pd.to_numeric(x.third,errors='coerce').astype(int)
assert len(x)==39

def learn_thresholds(tr):
    return {
      'b2':float(pd.to_numeric(tr.b2_pl_frame_p2,errors='coerce').quantile(.6)),
      'b1':float(pd.to_numeric(tr.b1_pl_frame_win,errors='coerce').quantile(.6)),
      'se':float(pd.to_numeric(tr.post_straight_edge2,errors='coerce').quantile(.5)),
    }

def route(df,th,outer_cut):
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
    base_outer=~(sig32|sig31)
    b4r=pd.to_numeric(df.b4_pl_recent_p2,errors='coerce')
    strong_outer=base_outer & b4r.ge(outer_cut)
    r=np.where(sig32,'2',np.where(sig31,'1',np.where(strong_outer,'OUTER_STRONG','FALLBACK')))
    return pd.Series(r,index=df.index)

def long_outer(df):
    rows=[]
    for _,r in df.iterrows():
        for b in [4,5,6]:
            z={'race_code':r.race_code,'boat':b,'y':int(int(r.second)==b)}
            for suf in ['pl_all_win','pl_all_p2','pl_frame_win','pl_frame_p2','pl_recent_p2']:
                c=f'b{b}_{suf}'; z[suf]=r[c] if c in r.index else np.nan
            for suf in ['win','top2','top3','ewma_rank','ewma_st']:
                c=f'post_motor_b{b}_{suf}'; z['motor_'+suf]=r[c] if c in r.index else np.nan
            rows.append(z)
    return pd.DataFrame(rows)

def third_rank(train,second):
    poss=[b for b in [1,2,4,5,6] if b!=second]
    sub=train[train.second.eq(second)]
    cnt=Counter(sub.third.tolist())
    overall=Counter(train.third.tolist())
    return sorted(poss,key=lambda b:(cnt[b],overall[b]),reverse=True)

def fallback_second_rank(train):
    # only among train races that are not correctly caught by strong 1/2/outer logic
    cnt=Counter(train.second.tolist())
    return [b for b,_ in cnt.most_common() if b in [1,2,4,5,6]]

scenarios={
 'NARROW': {'third_k':2,'outer_second_k':1,'fallback_second_k':2,'fallback_third_k':2},
 'BALANCED':{'third_k':3,'outer_second_k':2,'fallback_second_k':2,'fallback_third_k':3},
 'BROAD':{'third_k':4,'outer_second_k':2,'fallback_second_k':3,'fallback_third_k':3},
}
records=[]

for testm in ['jul','aug']:
    tr=x[x.month.ne(testm)].copy(); te=x[x.month.eq(testm)].copy()
    th=learn_thresholds(tr)

    # Outer median must come only from TRAIN races that fall into base OUTER under train thresholds.
    tmp_route=route(tr,th,outer_cut=np.inf)
    base_outer_train=tr[tmp_route.eq('FALLBACK')].copy()
    outer_cut=float(pd.to_numeric(base_outer_train.b4_pl_recent_p2,errors='coerce').quantile(.5))
    tr['route']=route(tr,th,outer_cut)
    te['route']=route(te,th,outer_cut)

    print('ROUTES',testm,te.route.value_counts().to_dict(),'OUTER_CUT',round(outer_cut,6))
    for rr,g in te.groupby('route'):
        ok=((rr=='2')&g.second.eq(2))|((rr=='1')&g.second.eq(1))|((rr=='OUTER_STRONG')&g.second.isin([4,5,6]))
        print('ROUTE_HIT',testm,rr,'N',len(g),'HIT',int(ok.sum()),'RATE',round(ok.mean(),4))

    # Per-race outer 4/5/6 ranking trained only on train OUTER_STRONG.
    tr_os=tr[tr.route.eq('OUTER_STRONG')].copy()
    te_os=te[te.route.eq('OUTER_STRONG')].copy()
    outer_orders={}
    if len(tr_os)>=3 and tr_os.second.isin([4,5,6]).any() and len(te_os):
        ltr=long_outer(tr_os); lte=long_outer(te_os)
        feats=[c for c in ltr.columns if c not in ['race_code','boat','y'] and pd.to_numeric(ltr[c],errors='coerce').notna().sum()>=max(4,len(ltr)//3)]
        if ltr.y.nunique()==2 and feats:
            model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.08,class_weight='balanced',solver='lbfgs',max_iter=2000,random_state=323))
            model.fit(ltr[feats],ltr.y)
            lte['p']=model.predict_proba(lte[feats])[:,1]
            for rc,g in lte.groupby('race_code'):
                outer_orders[rc]=g.sort_values('p',ascending=False).boat.astype(int).tolist()
    # fallback if model unavailable
    train_outer_freq=[b for b,_ in Counter(tr.loc[tr.second.isin([4,5,6]),'second']).most_common()]
    train_outer_freq += [b for b in [4,5,6] if b not in train_outer_freq]

    fallback_rank=fallback_second_rank(tr)

    for scen,cfg in scenarios.items():
        for _,r in te.iterrows():
            route_name=r.route
            seconds=[]
            if route_name=='2': seconds=[2]
            elif route_name=='1': seconds=[1]
            elif route_name=='OUTER_STRONG':
                order=outer_orders.get(r.race_code,train_outer_freq)
                seconds=order[:cfg['outer_second_k']]
            else:
                seconds=fallback_rank[:cfg['fallback_second_k']]

            tickets=[]
            for s in seconds:
                tk=cfg['fallback_third_k'] if route_name=='FALLBACK' else cfg['third_k']
                thirds=third_rank(tr,s)[:tk]
                for t in thirds:
                    if t!=s:
                        tickets.append((3,int(s),int(t)))
            tickets=list(dict.fromkeys(tickets))
            hit=(3,int(r.second),int(r.third)) in tickets
            records.append({'test_month':testm,'scenario':scen,'race_code':r.race_code,'route':route_name,
                            'truth_second':int(r.second),'truth_third':int(r.third),'tickets':len(tickets),'hit':int(hit)})

o=pd.DataFrame(records)
o.to_csv('integrated_ticket_v23.csv',index=False)
for scen,g in o.groupby('scenario'):
    print('SCENARIO',scen,'N',len(g),'HIT',int(g.hit.sum()),'HIT_RATE',round(g.hit.mean(),4),
          'AVG_TICKETS',round(g.tickets.mean(),3),'TOTAL_TICKETS',int(g.tickets.sum()))
    for m,gm in g.groupby('test_month'):
        print('SCENARIO_MONTH',scen,m,'N',len(gm),'HIT',int(gm.hit.sum()),'RATE',round(gm.hit.mean(),4),'AVG_TICKETS',round(gm.tickets.mean(),3))
    strong=g[g.route.ne('FALLBACK')]
    print('STRONG_ONLY',scen,'N',len(strong),'HIT',int(strong.hit.sum()),'RATE',round(strong.hit.mean(),4),'AVG_TICKETS',round(strong.tickets.mean(),3))
    for rr,gr in g.groupby('route'):
        print('ROUTE_TICKET',scen,rr,'N',len(gr),'HIT',int(gr.hit.sum()),'RATE',round(gr.hit.mean(),4),'AVG_TICKETS',round(gr.tickets.mean(),3))
print('INTEGRATED_TICKET_V23_OK')
