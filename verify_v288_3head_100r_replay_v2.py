#!/usr/bin/env python3
# Exact replay verifier for adopted v288, matching the original independent-route semantics.
from pathlib import Path
import json
import numpy as np
import pandas as pd

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT=Path('verify_v288_3head_100r_replay_v2.json')
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
    base=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    return (base&(num(q,'f__c_b3_minus_b5_st')>=KEEP))|((q.bet==1)&(~base)&(num(q,'f__c_attack3_stretch')<=RESCUE))
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
        if np.isfinite(sd) and sd>1e-12:
            s+=np.sign(e)*((x.fillna(med)-med)/sd).clip(-4,4)
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
    p=pd.concat(pred,ignore_index=True); p['_pct']=p.groupby('month')['_score'].rank(pct=True,method='first')
    p['grade']=np.where(p._pct>=.70,'S',np.where(p._pct>=.20,'A','B'))
    u=q.merge(p[['race_code','grade']],on='race_code'); u=u[u.grade.isin(['S','A'])].copy()

    # Canonical v243-final subset retained as an invariant, but only Route S requires it.
    final_mask=u._target==1
    final=u[final_mask]
    assert (len(final),int(num(final,'trifecta_hit').fillna(0).sum()),round(num(final,'ret').fillna(0).sum()))==(104,39,1200350)

    core_cond=(num(u,'f__c_b3_minus_b4_waku_st')<=WAKU34)&(num(u,'f__c_b3_minus_b4_st')>=ST34)&(num(u,'f__c_b3_meetst')<=MEETST)
    s=final_mask & core_cond

    # A/B are independent rescue routes over v249 S+A races that v242 can actually purchase (bet==1),
    # excluding only races already selected by the preceding route(s).
    purch=u.bet==1
    a=purch & (~s) & (num(u,'f__c_b3_minus_b4_st')>=A_ST34) & (num(u,'f__c_wall12_weak')<=A_WALL)
    bcond=(num(u,'f__c_b3_minus_b2_motor')>=B_MOTOR) & (num(u,'f__c_b3_inside_nst')<=B_NST)
    b=purch & (~s) & (~a) & bcond

    u['route']=np.where(s,'S',np.where(a,'A',np.where(b,'B','NO_BET')))
    selected=u[u.route!='NO_BET'].copy()
    out={
      'source':'frozen v243 artifact run 34383567078',
      'semantics':'S requires v243 final; A/B are independent v249 S+A + v242-purchasable rescue routes, precedence S>A>B',
      'v243_final_invariant':metrics(final),
      'v249_sa_candidates':len(u),
      'v249_sa_purchasable':int(purch.sum()),
      'routes':{},'combined':metrics(selected),'monthly':{}
    }
    for r in ['S','A','B']: out['routes'][r]=metrics(u[u.route==r])
    for m,g in selected.groupby('month'): out['monthly'][m]=metrics(g)
    exp={'S':(58,34,1048340),'A':(24,13,398980),'B':(18,9,296490)}
    for r,(n,h,pay) in exp.items():
        x=out['routes'][r]; assert (x['races'],x['hits'],round(x['payout_yen']))==(n,h,pay),(r,x)
    x=out['combined']; assert (x['races'],x['hits'],round(x['payout_yen']))==(100,56,1743810),x
    monthly_expected={
      '2026-02':(8,5,158510),'2026-03':(12,7,210380),'2026-04':(13,9,276730),
      '2026-05':(17,11,337610),'2026-06':(16,9,270960),'2026-07':(14,3,113260),'2026-08':(20,12,376360)}
    for m,(n,h,pay) in monthly_expected.items():
        x=out['monthly'][m]; assert (x['races'],x['hits'],round(x['payout_yen']))==(n,h,pay),(m,x)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    print('V288_REPLAY_V2_OK')
if __name__=='__main__': main()
