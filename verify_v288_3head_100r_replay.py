#!/usr/bin/env python3
# Exact replay verifier for the adopted v288 3-head 100R baseline.
from pathlib import Path
import json
import numpy as np
import pandas as pd

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT=Path('verify_v288_3head_100r_replay.json')
KEEP=-0.1999999999999999
RESCUE=0.5672342857142857
WAKU34=0.4999999999999999
ST34=-0.6
MEETST=0.861111111111111
A_ST34=0.6
A_WALL=0.24875
B_MOTOR=0.22388571428571424
B_NST=-0.0714285714285712

def num(q,c): return pd.to_numeric(q[c],errors='coerce')
def target(q):
    b=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    return (b&(num(q,'f__c_b3_minus_b5_st')>=KEEP))|((q.bet==1)&(~b)&(num(q,'f__c_attack3_stretch')<=RESCUE))
def precols(q):
    bad=('pair_','p3','odds','comp','top_n','raw_top','ticket','hit','ret','profit','bet','invalid','result','settle')
    cur=('attack3','wall12','_st','_ex','lap','turn','straight','orig','tilt','exh','tenji','display')
    return [c for c in q if c.startswith('f__') and not any(x in c.lower() for x in bad) and not any(x in c.lower() for x in cur)]
def fit_score(tr,te,cs):
    y=tr._target.astype(int); fs=[]
    for c in cs:
        x=num(tr,c); a=x[y==1].dropna(); b=x[y==0].dropna(); sd=x.std()
        if len(a)>=5 and len(b)>=20 and np.isfinite(sd) and sd>1e-12:
            e=(a.mean()-b.mean())/sd
            if np.isfinite(e): fs.append((abs(e),e,c))
    fs=sorted(fs,reverse=True)[:12]; s=pd.Series(0.,index=te.index)
    for _,e,c in fs:
        a=num(tr,c); x=num(te,c); med=a.median(); sd=a.std()
        if np.isfinite(sd) and sd>1e-12: s+=np.sign(e)*((x.fillna(med)-med)/sd).clip(-4,4)
    return s
def metrics(z):
    n=len(z); hits=int(num(z,'trifecta_hit').fillna(0).sum()); payout=float(num(z,'ret').fillna(0).sum()); stake=n*10000
    return {'races':n,'hits':hits,'hit_rate_pct':100*hits/n if n else None,'stake_yen':stake,'payout_yen':payout,'profit_yen':payout-stake,'roi_pct':100*payout/stake if stake else None}

def main():
    q=pd.read_csv(SRC,dtype={'race_code':str}); q.date=q.date.astype(str); q['month']=q.date.str[:7]; q['_target']=target(q).astype(int)
    ms=sorted(q.month.unique()); pred=[]; cs=precols(q)
    for i,m in enumerate(ms):
        if i<2: continue
        tr=q[q.month.isin(ms[:i])]; te=q[q.month==m].copy(); te['_score']=fit_score(tr,te,cs); pred.append(te[['month','race_code','_score']])
    p=pd.concat(pred,ignore_index=True); p['_pct']=p.groupby('month')['_score'].rank(pct=True,method='first'); p['grade']=np.where(p._pct>=.70,'S',np.where(p._pct>=.20,'A','B'))
    z=q.merge(p[['race_code','grade']],on='race_code'); z=z[(z._target==1)&z.grade.isin(['S','A'])].copy()
    assert (len(z),int(num(z,'trifecta_hit').fillna(0).sum()),round(num(z,'ret').fillna(0).sum()))==(104,39,1200350)
    s=(num(z,'f__c_b3_minus_b4_waku_st')<=WAKU34)&(num(z,'f__c_b3_minus_b4_st')>=ST34)&(num(z,'f__c_b3_meetst')<=MEETST)
    a=(~s)&(num(z,'f__c_b3_minus_b4_st')>=A_ST34)&(num(z,'f__c_wall12_weak')<=A_WALL)
    b=(~s)&(~a)&(num(z,'f__c_b3_minus_b2_motor')>=B_MOTOR)&(num(z,'f__c_b3_inside_nst')<=B_NST)
    z['route']=np.where(s,'S',np.where(a,'A',np.where(b,'B','NO_BET')))
    selected=z[z.route!='NO_BET'].copy()
    out={'source':'frozen v243 artifact run 34383567078','base_purchasable':metrics(z),'routes':{},'combined':metrics(selected),'monthly':{}}
    for r in ['S','A','B']: out['routes'][r]=metrics(z[z.route==r])
    for m,g in selected.groupby('month'): out['monthly'][m]=metrics(g)
    exp={'S':(58,34,1048340),'A':(24,13,398980),'B':(18,9,296490)}
    for r,(n,h,pay) in exp.items():
        x=out['routes'][r]; assert (x['races'],x['hits'],round(x['payout_yen']))==(n,h,pay),(r,x)
    x=out['combined']; assert (x['races'],x['hits'],round(x['payout_yen']))==(100,56,1743810),x
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print('V288_REPLAY_OK')
if __name__=='__main__': main()
