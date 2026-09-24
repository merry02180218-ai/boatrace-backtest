#!/usr/bin/env python3
from __future__ import annotations
import pandas as pd, numpy as np, runpy, sys
from collections import defaultdict

# Rebuild the exact 39-race causal feature table used in v17.
sys.path.insert(0,'research'); sys.path.insert(0,'.')
src=open('research/research_3head_opponent_type_v16.py',encoding='utf-8').read()
needle="print('FEATURE_COUNT',len(features))"
repl="x.to_csv('opponent_regime_feature_table_v18.csv',index=False)\n"+needle
assert needle in src
src=src.replace(needle,repl,1)
cut="# Leave-one-month-out, no same-month fitting."
src=src.split(cut)[0]+"\nprint('V18_FEATURE_TABLE_OK')\n"
open('/tmp/v18_builder.py','w',encoding='utf-8').write(src)
runpy.run_path('/tmp/v18_builder.py',run_name='__main__')

x=pd.read_csv('opponent_regime_feature_table_v18.csv',dtype={'race_code':str})
x.race_code=x.race_code.str.zfill(12)
assert len(x)==39
x['second']=pd.to_numeric(x.second,errors='coerce').astype(int)
x['is32']=x.second.eq(2)
x['is31']=x.second.eq(1)
# race_code structure: YYYYMMDD + place(2) + race(2)
x['venue_code']=x.race_code.str[8:10]
x['race_no']=pd.to_numeric(x.race_code.str[10:12],errors='coerce')

# Candidate causal regime fields.
cand=[
 'b2_pl_frame_p2','b1_pl_frame_win','b2_pl_all_p2','b2_pl_recent_p2',
 'post_st_rank3','post_st_edge4','post_st_field_edge','post_straight_edge2',
 'post_motor_b1_ewma_rank','post_motor_b2_ewma_rank','post_motor_rank_edge1',
 'post_motor_rank_edge2','post_motor_gap1_top2','post_motor_gap2_top2',
 'post_motor_inner_top2_gap','post_ex_edge4','post_turn_edge1','post_turn_edge4'
]
cand=[c for c in cand if c in x.columns]
print('ROWS',len(x),'CAND',cand)
print('VENUES',x.venue_code.value_counts().to_dict())

# Descriptive month shift for each candidate.
for c in cand:
    a=pd.to_numeric(x.loc[x.month.eq('jul'),c],errors='coerce')
    b=pd.to_numeric(x.loc[x.month.eq('aug'),c],errors='coerce')
    if a.notna().sum()>=5 and b.notna().sum()>=5:
        sd=pd.to_numeric(x[c],errors='coerce').std()+1e-9
        print('MONTH_SHIFT',c,'JUL',round(a.mean(),4),'AUG',round(b.mean(),4),'STD_DELTA',round((b.mean()-a.mean())/sd,3))

# Train-threshold on opposite month for anchor PLAYERHistory features, then test simple causal interactions.
def eval_rule(testm,target,base_col,base_q,gate_col=None,gate_dir='ge',gate_q=.5):
    tr=x[x.month.ne(testm)].copy(); te=x[x.month.eq(testm)].copy()
    ycol='is32' if target=='3_2' else 'is31'
    bt=pd.to_numeric(tr[base_col],errors='coerce').quantile(base_q)
    mask=pd.to_numeric(te[base_col],errors='coerce').ge(bt)
    desc=f'{base_col}>={bt:.6f}'
    if gate_col:
        gt=pd.to_numeric(tr[gate_col],errors='coerce').quantile(gate_q)
        z=pd.to_numeric(te[gate_col],errors='coerce')
        mask &= z.ge(gt) if gate_dir=='ge' else z.le(gt)
        desc+=f' & {gate_col}{">=" if gate_dir=="ge" else "<="}{gt:.6f}'
    n=int(mask.sum()); hit=int((mask & te[ycol]).sum())
    prec=hit/n if n else np.nan
    rec=hit/int(te[ycol].sum()) if int(te[ycol].sum()) else np.nan
    return n,hit,prec,rec,desc

rows=[]
for target,base in [('3_2','b2_pl_frame_p2'),('3_1','b1_pl_frame_win')]:
    for testm in ['jul','aug']:
        # anchor only
        for bq in [.5,.6,.7]:
            n,h,p,r,d=eval_rule(testm,target,base,bq)
            rows.append((target,testm,'BASE',n,h,p,r,d))
        # interactions: thresholds fit on opposite month only
        for gate in [c for c in cand if c not in {base,'b2_pl_all_p2','b2_pl_recent_p2','b1_pl_frame_win','b2_pl_frame_p2'}]:
            for direc in ['ge','le']:
                n,h,p,r,d=eval_rule(testm,target,base,.6,gate,direc,.5)
                # Keep only practical rules.
                if n>=2:
                    rows.append((target,testm,gate+'_'+direc,n,h,p,r,d))

out=pd.DataFrame(rows,columns=['target','test_month','rule','sel','hit','precision','recall','desc'])
out.to_csv('opponent_regime_rules_v18.csv',index=False)

# Rank rules by cross-month robustness: same named gate/direction must work in both months.
for target in ['3_2','3_1']:
    z=out[(out.target.eq(target)) & ~out.rule.eq('BASE')].copy()
    agg=[]
    for rule,g in z.groupby('rule'):
        if set(g.test_month)!={'jul','aug'}: continue
        sel=int(g.sel.sum()); hit=int(g.hit.sum())
        # harmonic-ish emphasis: minimum monthly precision + total support
        monthly=g.set_index('test_month').precision.to_dict()
        if any(pd.isna(v) for v in monthly.values()): continue
        agg.append((min(monthly.values()),hit/sel if sel else 0,sel,hit,rule,monthly,g.desc.tolist()))
    for a in sorted(agg,reverse=True)[:15]:
        print('ROBUST',target,'MINPREC',round(a[0],4),'ALLPREC',round(a[1],4),'SEL',a[2],'HIT',a[3],'RULE',a[4],'MONTHLY',a[5],'DESC',a[6])

# Venue concentration check; descriptive only due small n.
for target,ycol in [('3_2','is32'),('3_1','is31')]:
    for v,g in x.groupby('venue_code'):
        if len(g)>=2:
            print('VENUE',target,v,'N',len(g),'HIT',int(g[ycol].sum()),'RATE',round(g[ycol].mean(),4),'MONTHS',g.month.value_counts().to_dict())

print('OPPONENT_REGIME_V18_OK')
