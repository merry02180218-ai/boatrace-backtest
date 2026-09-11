#!/usr/bin/env python3
from pathlib import Path
import json
import numpy as np
import pandas as pd

SRC=Path('analysis_v243_3head_expand_feature_audit.csv')
OUT=Path('verify_v288_operational_pre_replay.json')
KEEP=-0.1999999999999999; RESCUE=0.5672342857142857
WAKU34=0.4999999999999999; ST34=-0.6; MEETST=0.861111111111111
A_ST34=0.6; A_WALL=0.24875; B_MOTOR=0.22388571428571424; B_NST=-0.0714285714285712
S_Q=.70; A_Q=.20

def num(q,c): return pd.to_numeric(q[c],errors='coerce')
def target(q):
    b=(q.bet==1)&(q.p3>=.45)&q.raw_top_n.between(7,18)&q.comp_odds.between(3.05,4.0)
    return (b&(num(q,'f__c_b3_minus_b5_st')>=KEEP))|((q.bet==1)&(~b)&(num(q,'f__c_attack3_stretch')<=RESCUE))
def precols(q):
    bad=('pair_','p3','odds','comp','top_n','raw_top','ticket','hit','ret','profit','bet','invalid','result','settle')
    cur=('attack3','wall12','_st','_ex','lap','turn','straight','orig','tilt','exh','tenji','display')
    return [c for c in q if c.startswith('f__') and not any(x in c.lower() for x in bad) and not any(x in c.lower() for x in cur)]
def learned_features(tr,cs):
    y=tr._target.astype(int); fs=[]
    for c in cs:
        x=num(tr,c); a=x[y==1].dropna(); b=x[y==0].dropna(); sd=x.std()
        if len(a)>=5 and len(b)>=20 and np.isfinite(sd) and sd>1e-12:
            e=(a.mean()-b.mean())/sd
            if np.isfinite(e): fs.append((abs(e),e,c))
    return sorted(fs,reverse=True)[:12]
def score_with(tr,te,fs):
    s=pd.Series(0.,index=te.index,dtype=float)
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
    ms=sorted(q.month.unique()); cs=precols(q); pred=[]; threshold_log={}
    for i,m in enumerate(ms):
        if i<2: continue
        tr=q[q.month.isin(ms[:i])].copy(); te=q[q.month==m].copy()
        fs=learned_features(tr,cs)
        tr_score=score_with(tr,tr,fs); te['_score']=score_with(tr,te,fs)
        s_thr=float(tr_score.quantile(S_Q)); a_thr=float(tr_score.quantile(A_Q))
        te['grade']=np.where(te._score>=s_thr,'S',np.where(te._score>=a_thr,'A','B'))
        pred.append(te)
        threshold_log[m]={'train_months':ms[:i],'s_threshold':s_thr,'a_threshold':a_thr,'test_rows':len(te)}
    u=pd.concat(pred,ignore_index=True); u=u[u.grade.isin(['S','A'])].copy()
    final_mask=u._target==1
    core=(num(u,'f__c_b3_minus_b4_waku_st')<=WAKU34)&(num(u,'f__c_b3_minus_b4_st')>=ST34)&(num(u,'f__c_b3_meetst')<=MEETST)
    s=final_mask & core
    purch=u.bet==1
    a=purch & (~s) & (num(u,'f__c_b3_minus_b4_st')>=A_ST34) & (num(u,'f__c_wall12_weak')<=A_WALL)
    b=purch & (~s) & (~a) & (num(u,'f__c_b3_minus_b2_motor')>=B_MOTOR) & (num(u,'f__c_b3_inside_nst')<=B_NST)
    u['route']=np.where(s,'S',np.where(a,'A',np.where(b,'B','NO_BET')))
    sel=u[u.route!='NO_BET'].copy()
    out={'semantics':'Leakage-free operational PRE: current test month scored with prior-month-trained score; S/A cutpoints are 70th/20th percentiles of prior training-universe scores only. Then canonical v288 S>A>B routes.',
         'pre_sa_candidates':len(u),'pre_target_capture':int(u._target.sum()),'routes':{},'combined':metrics(sel),'monthly':{},'thresholds':threshold_log}
    for r in ['S','A','B']: out['routes'][r]=metrics(u[u.route==r])
    for m,g in sel.groupby('month'): out['monthly'][m]=metrics(g)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2)); print('V288_OPERATIONAL_PRE_REPLAY_OK')
if __name__=='__main__': main()
