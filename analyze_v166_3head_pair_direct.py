#!/usr/bin/env python3
"""v166: direct ordered-pair model for 3-head tickets.

NO-LEAK:
- ranking features come from frozen v108 rows only;
- pair labels use actual_combo only for historical training/evaluation;
- each evaluated month trains pair model only on earlier dates;
- Mar-May is used only to choose blend lambda;
- Jun-Aug uses frozen v165 p3head for thresholded evaluation;
- payout is settlement-only after ticket ranking is fixed.
"""
from __future__ import annotations
import csv, math
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC='analysis_v108_1head_feasibility.csv'
HEADSRC='analysis_v165_3head_monthly_walkforward.csv'
OUT='analysis_v166_3head_pair_direct.csv'
SUMMARY='summary_v166_3head_pair_direct.md'
VAL_MONTHS=['2026-03','2026-04','2026-05']
TEST_MONTHS=['2026-06','2026-07','2026-08']
LAMBDAS=[0,.15,.25,.35,.50,.65,.80,1.0]
POINTS=[1,3,5,7,10]
CUTS=[.20,.25,.30,.35,.40]
OPP=[1,2,4,5,6]
VENUES=[f'{i:02d}' for i in range(1,25)]

def ff(x,d=0.):
    try:return float(x)
    except:return d

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def pct(n,d):return 100*n/d if d else 0.
def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def combo(x):
    try:
        a=[int(z) for z in str(x).replace(' ','').split('-')]
        return a if len(a)==3 else []
    except:return []

def strength(r,b):
    # v108 stores lane1's canonical score as one_score and lanes2-6 as threatN.
    # These are frozen pre-result/direct strength summaries, not outcome-derived labels.
    return ff(r.get('one_score')) if b==1 else ff(r.get(f'threat{b}'))
def hstrength(r):return ff(r.get('threat3'))
def ranks(r):
    vals=sorted(OPP,key=lambda b:(-strength(r,b),b))
    return {b:i+1 for i,b in enumerate(vals)}

def pvec(r,s,t):
    ss,tt=strength(r,s),strength(r,t); rk=ranks(r);rs,rt=rk[s],rk[t]
    vals=[strength(r,b) for b in OPP];mx=max(vals);av=sum(vals)/len(vals); hs=hstrength(r)
    dist=abs(t-s)
    x=[ss,tt,ss+tt,ss-tt,min(ss,tt),max(ss,tt),
       1-(rs-1)/4,1-(rt-1)/4,rs-rt,rs+rt,
       ss-mx,tt-mx,ss-av,tt-av,hs-ss,hs-tt,
       ff(r.get('margin2')),ff(r.get('margin3')),ff(r.get('margin_all')),
       ff(r.get('st_margin23')),ff(r.get('ex_margin23')),ff(r.get('turn_margin23')),ff(r.get('straight_margin23')),
       float(dist),1. if dist==1 else 0.,1. if s<t else 0.]
    x += [1. if s==b else 0. for b in OPP]
    x += [1. if t==b else 0. for b in OPP]
    v=str(r.get('venue','')).zfill(2);x += [1. if v==z else 0. for z in VENUES]
    return x

def fit(train):
    X=[];y=[];n=0
    for r in train:
        if ii(r.get('valid_result'))!=1:continue
        a=combo(r.get('actual_combo'))
        if len(a)!=3 or a[0]!=3 or a[1] not in OPP or a[2] not in OPP or a[1]==a[2]:continue
        n+=1;s0,t0=a[1],a[2]
        for s in OPP:
            for t in OPP:
                if s==t:continue
                X.append(pvec(r,s,t));y.append(int(s==s0 and t==t0))
    if n<100:raise RuntimeError(f'not enough prior 3-head wins: {n}')
    m=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs'))])
    m.fit(np.asarray(X,float),np.asarray(y,int));return m,n

def zs(v):
    a=np.asarray(v,float);sd=float(a.std());return ((a-a.mean())/sd if sd>1e-12 else np.zeros(len(a))).tolist()
def order(r,m,lam):
    rk=ranks(r);pairs=[];ps=[];cur=[]
    for s in OPP:
        for t in OPP:
            if s==t:continue
            q=float(m.predict_proba(np.asarray([pvec(r,s,t)],float))[0,1]);pairs.append((s,t));ps.append(math.log(max(q,1e-12)));cur.append(-(rk[s]+.7*rk[t]))
    pz,cz=zs(ps),zs(cur);z=[((1-lam)*c+lam*p,s,t) for p,c,(s,t) in zip(pz,cz,pairs)]
    z.sort(key=lambda q:(-q[0],q[1],q[2]));return [f'3-{s}-{t}' for _,s,t in z]
def current_order(r):
    rk=ranks(r);z=[]
    for s in OPP:
        for t in OPP:
            if s!=t:z.append((rk[s]+.7*rk[t],s,t))
    z.sort();return [f'3-{s}-{t}' for _,s,t in z]

def score_month(src,mo,lam):
    first=date.fromisoformat(mo+'-01');tr=[r for r in src if date.fromisoformat(r['date'])<first]
    te=[dict(r) for r in src if r.get('month')==mo and ii(r.get('valid_result'))==1]
    m,n=fit(tr)
    for r in te:
        act=(r.get('actual_combo') or '').strip();new=order(r,m,lam);cur=current_order(r)
        r['v166_month']=mo;r['pair_train_3wins']=n;r['v166_lambda']=lam;r['current3_rank20']=cur.index(act)+1 if act in cur else 0;r['v166_rank20']=new.index(act)+1 if act in new else 0;r['v166_20']=';'.join(new)
    return te

def cov(rs,n,col):
    h=[r for r in rs if combo(r.get('actual_combo'))[:1]==[3]]
    return pct(sum(1 for r in h if 0<ii(r.get(col))<=n),len(h))
def choose(src):
    rows=[]
    for lam in LAMBDAS:
        q=[]
        for mo in VAL_MONTHS:q+=score_month(src,mo,lam)
        ds=[cov(q,n,'v166_rank20')-cov(q,n,'current3_rank20') for n in [3,5,7,10]]
        rows.append((lam,sum(ds)/len(ds),min(ds)))
    ok=[x for x in rows if x[2]>=-.75 and x[1]>=0] or rows
    return max(ok,key=lambda x:(x[1],x[2],x[0]))[0],rows

def metric(rs,cut,n,col):
    q=[r for r in rs if ff(r.get('p3head'))>=cut]
    h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    hit=[r for r in q if 0<ii(r.get(col))<=n]
    cv=pct(sum(1 for r in h if 0<ii(r.get(col))<=n),len(h))
    hr=pct(len(hit),len(q))
    settled=[r for r in q if ii(r.get('valid_payout'))==1]
    ret=sum(ff(r.get('payout100')) for r in settled if 0<ii(r.get(col))<=n)
    roi=100*ret/(len(settled)*n*100) if settled else 0
    return len(q),pct(len(h),len(q)),hr,cv,roi

def main():
    src=read(SRC);hp={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    for i,r in enumerate(src):r['p3head']=hp.get(i,'')
    lam,tune=choose(src);out=[]
    for mo in TEST_MONTHS:out+=score_month(src,mo,lam)
    # restore frozen v165 probability by source row identity after dict copies
    keyp={(r['date'],r.get('race_code')):hp.get(i,'') for i,r in enumerate(src)}
    for r in out:r['p3head']=keyp.get((r['date'],r.get('race_code')),'')
    fs=sorted(set().union(*(r.keys() for r in out)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    L=['# v166 3号艇 direct pair model','', '- v165の③頭確率は固定。③頭時の相手20組を ordered pair として直接学習。','- pair学習は各評価月より前の日付の③頭実績のみ。','- Mar-Mayでblend λのみ選択、Jun-Augで評価。','- payoutは順位固定後のsettlementにのみ使用。','','## λ tuning vs strength baseline','|λ|平均coverage差|最悪差|','|---:|---:|---:|']
    for a,b,c in tune:L.append(f'|{a:.2f}|{b:+.2f}pt|{c:+.2f}pt|')
    L += ['',f'選択 λ = **{lam:.2f}**','','## Jun-Aug threshold / 7-ticket','|p3 cut|R|③頭率|baseline 7hit|v166 7hit|baseline cov|v166 cov|baseline ROI|v166 ROI|','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for cut in CUTS:
        n,h,ch,cc,cr=metric(out,cut,7,'current3_rank20');_,_,vh,vc,vr=metric(out,cut,7,'v166_rank20')
        L.append(f'|{cut:.2f}|{n}|{h:.2f}%|{ch:.2f}%|{vh:.2f}%|{cc:.2f}%|{vc:.2f}%|{cr:.1f}%|{vr:.1f}%|')
    L += ['','## S候補検討用: p3>=0.30 月別 7点','|月|R|③頭率|baseline cov|v166 cov|v166 hit|v166 ROI|','|---|---:|---:|---:|---:|---:|---:|']
    for mo in TEST_MONTHS:
        q=[r for r in out if r.get('v166_month')==mo];n,h,_,cc,_=metric(q,.30,7,'current3_rank20');_,_,vh,vc,vr=metric(q,.30,7,'v166_rank20');L.append(f'|{mo}|{n}|{h:.2f}%|{cc:.2f}%|{vc:.2f}%|{vh:.2f}%|{vr:.1f}%|')
    L += ['','## 点数別 p3>=0.30','|点数|baseline cov|v166 cov|v166 hit|v166 ROI|','|---:|---:|---:|---:|---:|']
    for npt in POINTS:
        _,_,_,cc,_=metric(out,.30,npt,'current3_rank20');_,_,vh,vc,vr=metric(out,.30,npt,'v166_rank20');L.append(f'|{npt}|{cc:.2f}%|{vc:.2f}%|{vh:.2f}%|{vr:.1f}%|')
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
