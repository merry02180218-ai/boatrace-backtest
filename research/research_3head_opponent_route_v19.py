#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np, runpy, sys
from collections import Counter

# Rebuild exact 39-race causal feature table used in v18.
sys.path.insert(0,'research'); sys.path.insert(0,'.')
src=open('research/research_3head_opponent_type_v16.py',encoding='utf-8').read()
needle="print('FEATURE_COUNT',len(features))"
repl="x.to_csv('opponent_route_feature_table_v19.csv',index=False)\n"+needle
assert needle in src
src=src.replace(needle,repl,1)
src=src.split("# Leave-one-month-out, no same-month fitting.")[0]+"\nprint('V19_FEATURE_TABLE_OK')\n"
open('/tmp/v19_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v19_builder.py',run_name='__main__')

x=pd.read_csv('opponent_route_feature_table_v19.csv',dtype={'race_code':str})
x.race_code=x.race_code.str.zfill(12)
x['second']=pd.to_numeric(x.second,errors='coerce').astype(int)
x['third']=pd.to_numeric(x.third,errors='coerce').astype(int)
assert len(x)==39

# Route rules: thresholds must be fit on the opposite month only.
# 3-2: b2 frame-p2 high + straight-edge2 low
# 3-1: b1 frame-win high + straight-edge2 high
# Quantiles reflect v18 robust rule construction; no current-month target outcomes used.
def month_route(testm):
    tr=x[x.month.ne(testm)].copy()
    te=x[x.month.eq(testm)].copy()

    t_b2=float(pd.to_numeric(tr.b2_pl_frame_p2,errors='coerce').quantile(.6))
    t_b1=float(pd.to_numeric(tr.b1_pl_frame_win,errors='coerce').quantile(.6))
    t_se=float(pd.to_numeric(tr.post_straight_edge2,errors='coerce').quantile(.5))

    b2=pd.to_numeric(te.b2_pl_frame_p2,errors='coerce')
    b1=pd.to_numeric(te.b1_pl_frame_win,errors='coerce')
    se=pd.to_numeric(te.post_straight_edge2,errors='coerce')

    sig32=(b2>=t_b2)&(se<=t_se)
    sig31=(b1>=t_b1)&(se>=t_se)

    # If both fire exactly at the median boundary, resolve by normalized anchor strength.
    both=sig32&sig31
    if both.any():
        b2z=(b2-t_b2)/(pd.to_numeric(tr.b2_pl_frame_p2,errors='coerce').std()+1e-9)
        b1z=(b1-t_b1)/(pd.to_numeric(tr.b1_pl_frame_win,errors='coerce').std()+1e-9)
        sig32= sig32 & (~both | (b2z>=b1z))
        sig31= sig31 & (~both | (b1z>b2z))

    route=np.where(sig32,'2',np.where(sig31,'1','OUTER'))
    out=te[['month','race_code','second','third']].copy()
    out['route']=route
    out['sig32']=sig32.values
    out['sig31']=sig31.values
    out['t_b2']=t_b2; out['t_b1']=t_b1; out['t_se']=t_se
    return out

o=pd.concat([month_route('jul'),month_route('aug')],ignore_index=True)
o.to_csv('opponent_route_v19.csv',index=False)

for m,g in list(o.groupby('month'))+[('all',o)]:
    print('ROUTE_COUNTS',m,g.route.value_counts().to_dict())
    for r,gg in g.groupby('route'):
        correct=((gg.route.eq('2')&gg.second.eq(2)) | (gg.route.eq('1')&gg.second.eq(1)) | (gg.route.eq('OUTER')&gg.second.isin([4,5,6])))
        print('ROUTE_ACC',m,r,'N',len(gg),'HIT',int(correct.sum()),'RATE',round(correct.mean(),4),
              'SECOND',gg.second.value_counts().to_dict())

# Practical ticket recall if route dictates second-place coverage.
# 2-route: second=2 only; 1-route: second=1 only; OUTER-route: second in 4/5/6.
hit2=((o.route.eq('2')&o.second.eq(2))|(o.route.eq('1')&o.second.eq(1))|(o.route.eq('OUTER')&o.second.isin([4,5,6])))
print('SECOND_ROUTE_ALL',len(o),'HIT',int(hit2.sum()),'RATE',round(hit2.mean(),4))

# Third-place tendencies conditional on a CORRECT second-route, to make compact 3rd templates.
z=o[hit2].copy()
for r,gg in z.groupby('route'):
    c=Counter(gg.third)
    print('THIRD_DIST_CORRECT_ROUTE',r,'N',len(gg),dict(sorted(c.items())))
    # top2 third candidates by training-opposite-month only
for testm in ['jul','aug']:
    tr=o[o.month.ne(testm)].copy()
    te=o[o.month.eq(testm)].copy()
    # derive top2 third boats per route only from opposite month correctly-routed races
    train_hit=((tr.route.eq('2')&tr.second.eq(2))|(tr.route.eq('1')&tr.second.eq(1))|(tr.route.eq('OUTER')&tr.second.isin([4,5,6])))
    tops={}
    for r,gg in tr[train_hit].groupby('route'):
        tops[r]=[b for b,_ in Counter(gg.third).most_common(2)]
    sel=te.copy()
    secok=((sel.route.eq('2')&sel.second.eq(2))|(sel.route.eq('1')&sel.second.eq(1))|(sel.route.eq('OUTER')&sel.second.isin([4,5,6])))
    thirdok=[int(row.third) in tops.get(row.route,[]) for row in sel.itertuples()]
    ticket=secok.values & np.array(thirdok)
    print('TOP2_THIRD_TEST',testm,'N',len(sel),'TICKET_HIT',int(ticket.sum()),'RATE',round(ticket.mean(),4),'TOPS',tops)

print('OPPONENT_ROUTE_V19_OK')
