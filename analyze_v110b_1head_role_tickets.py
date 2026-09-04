"""v110b: optimized implementation of v110 1-head role tickets.
Same no-leak design as v110, but role predictions are batched once per month and
all blend lambdas are evaluated from cached pair components.
"""
from __future__ import annotations
import csv, math
from datetime import date

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SRC='analysis_v108_1head_feasibility.csv'
HEADSRC='analysis_v109_1head_monthly_walkforward.csv'
OUT='analysis_v110_1head_role_tickets.csv'
SUMMARY='summary_v110_1head_role_tickets.md'
VAL_MONTHS=['2026-03','2026-04','2026-05']
TEST_MONTHS=['2026-06','2026-07','2026-08']
ALL_MONTHS=VAL_MONTHS+TEST_MONTHS
LAMBDAS=[0.0,0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50]
POINTS=[4,6,7,8,10]
VENUES=[f'{i:02d}' for i in range(1,25)]
A_CUT=.65;S_CUT=.72


def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def parse_combo(s):
    try:
        a=[int(x) for x in (s or '').replace(' ','').split('-')]
        return a if len(a)==3 else []
    except Exception:return []

def ranked(r):
    try:return [int(x) for x in (r.get('ranked_others') or '').split('-') if int(x) in range(2,7)]
    except Exception:return []
def threat(r,b):return ff(r.get(f'threat{b}'),0.0)
def rankof(r,b):
    a=ranked(r);return a.index(b)+1 if b in a else 5

def second_vec(r,b):
    th=[threat(r,x) for x in range(2,7)];tb=threat(r,b);rk=rankof(r,b)
    row=[tb,1-(rk-1)/4,tb-max(th),tb-sum(th)/5,ff(r.get('one_score'))-tb]
    row += [1.0 if b==x else 0.0 for x in range(2,7)]
    vv=str(r.get('venue','')).zfill(2);row += [1.0 if vv==v else 0.0 for v in VENUES]
    return row

def third_vec(r,s,t):
    th=[threat(r,x) for x in range(2,7)];tt=threat(r,t);ts=threat(r,s);rt=rankof(r,t);rs=rankof(r,s)
    row=[tt,1-(rt-1)/4,ts,1-(rs-1)/4,tt-ts,rt-rs,tt-max(th),ff(r.get('one_score'))-tt]
    row += [1.0 if t==x else 0.0 for x in range(2,7)]
    row += [1.0 if s==x else 0.0 for x in range(2,7)]
    vv=str(r.get('venue','')).zfill(2);row += [1.0 if vv==v else 0.0 for v in VENUES]
    return row

def fit_binary(X,y):
    p=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1000,solver='lbfgs'))])
    p.fit(np.asarray(X,dtype=float),np.asarray(y,dtype=int));return p

def fit_roles(train):
    X2=[];y2=[];X3=[];y3=[];nr=0
    for r in train:
        if ii(r.get('valid_result'))!=1 or ii(r.get('head_hit'))!=1:continue
        a=parse_combo(r.get('actual_combo'))
        if len(a)!=3 or a[0]!=1 or a[1] not in range(2,7) or a[2] not in range(2,7):continue
        s,t=a[1],a[2];nr+=1
        for b in range(2,7):X2.append(second_vec(r,b));y2.append(int(b==s))
        for b in range(2,7):
            if b!=s:X3.append(third_vec(r,s,b));y3.append(int(b==t))
    if nr<100:raise RuntimeError(f'not enough role train races {nr}')
    return fit_binary(X2,y2),fit_binary(X3,y3),nr

def zmap(vals):
    a=list(vals.values());m=sum(a)/len(a);sd=(sum((x-m)**2 for x in a)/len(a))**.5
    return {k:((v-m)/sd if sd>1e-12 else 0.0) for k,v in vals.items()}

def prepare_month(src,mo):
    first=date.fromisoformat(mo+'-01');train=[r for r in src if date.fromisoformat(r['date'])<first]
    test=[dict(r) for r in src if r.get('month')==mo and ii(r.get('valid_result'))==1]
    m2,m3,ntrain=fit_roles(train)
    # batch second rows
    X2=[];meta2=[];X3=[];meta3=[]
    for i,r in enumerate(test):
        for b in range(2,7):X2.append(second_vec(r,b));meta2.append((i,b))
        for s in range(2,7):
            for t in range(2,7):
                if t!=s:X3.append(third_vec(r,s,t));meta3.append((i,s,t))
    pp2=m2.predict_proba(np.asarray(X2,dtype=float))[:,1]
    pp3=m3.predict_proba(np.asarray(X3,dtype=float))[:,1]
    sec=[{} for _ in test];third=[{} for _ in test]
    for (i,b),p in zip(meta2,pp2):sec[i][b]=float(p)
    for (i,s,t),p in zip(meta3,pp3):third[i][(s,t)]=float(p)
    for i,r in enumerate(test):
        ssum=sum(sec[i].values()) or 1.0
        p2={b:max(sec[i][b]/ssum,1e-12) for b in range(2,7)}
        pairs_role={};pairs_cur={}
        for s in range(2,7):
            rem=[t for t in range(2,7) if t!=s];den=sum(third[i][(s,t)] for t in rem) or 1.0
            for t in rem:
                pairs_role[(s,t)]=math.log(p2[s])+math.log(max(third[i][(s,t)]/den,1e-12))
                pairs_cur[(s,t)]=-(rankof(r,s)+.7*rankof(r,t))
        rz=zmap(pairs_role);cz=zmap(pairs_cur);act=(r.get('actual_combo') or '').strip()
        r['v110_month']=mo;r['role_train_headwins']=ntrain
        # current rank is lambda 0
        for lam in LAMBDAS:
            arr=sorted(pairs_cur,key=lambda k:(-((1-lam)*cz[k]+lam*rz[k]),k[0],k[1]))
            order=[f'1-{s}-{t}' for s,t in arr]
            key=f'rank_l{int(round(lam*100)):02d}'
            r[key]=order.index(act)+1 if act in order else 0
            if lam in (0.0,0.10,0.20,0.30,0.40,0.50):r[f'order_l{int(round(lam*100)):02d}']=';'.join(order)
    return test

def sel(r,phase,grade):
    p=ff(r.get('p1' if phase=='val' else 'p109'))
    return p >= (S_CUT if grade=='S' else A_CUT)
def metric(rs,phase,grade,npt,col):
    q=[r for r in rs if sel(r,phase,grade) and ii(r.get('valid_payout'))==1]
    hits=[r for r in q if 0<ii(r.get(col))<=npt]
    heads=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(1 for r in heads if 0<ii(r.get(col))<=npt)
    inv=len(q)*npt*100;ret=sum(ii(r.get('payout100')) for r in hits)
    return len(q),pct(len(hits),len(q)),pct(cov,len(heads)),pct(ret,inv)

def main():
    src=read_csv(SRC);hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read_csv(HEADSRC)}
    for r in src:
        if r.get('month') in TEST_MONTHS:r['p109']=hp.get((r.get('date'),r.get('race_code')),'')
    bymo={}
    for mo in ALL_MONTHS:
        print('v110 prepare',mo,flush=True);bymo[mo]=prepare_month(src,mo)
    val=sum((bymo[m] for m in VAL_MONTHS),[]);test=sum((bymo[m] for m in TEST_MONTHS),[])
    tune=[]
    for lam in LAMBDAS:
        col=f'rank_l{int(round(lam*100)):02d}';ds=[];worst=999
        for g in ['A','S']:
            for p in POINTS:
                _,_,base,_=metric(val,'val',g,p,'rank_l00');_,_,hyb,_=metric(val,'val',g,p,col)
                d=hyb-base;ds.append(d);worst=min(worst,d)
        avg=sum(ds)/len(ds);ok=(avg>=0 and worst>=-.5);tune.append((lam,avg,worst,ok))
    admiss=[x for x in tune if x[3]] or [x for x in tune if x[0]==0]
    lam=max(admiss,key=lambda x:(x[1],-x[0]))[0];col=f'rank_l{int(round(lam*100)):02d}'
    for r in test:r['v110_lambda_selected']=lam;r['v110_rank20']=r[col];r['current_rank20']=r['rank_l00']
    fs=sorted(set().union(*(r.keys() for r in test)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(test)
    L=['# v110 1号艇 2着/3着 role model','',
       '1号艇頭モデルv109は固定。相手だけを2着/3着役割分離して改善。各月より前の1号艇1着だけでrole学習し、Mar-Mayでblend λを1個だけ選択、Jun-Augは固定。オッズ不使用。','',
       '## validation λ selection','|λ|平均coverage差|最悪セル差|admissible|','|---:|---:|---:|---|']
    for x in tune:L.append(f'|{x[0]:.2f}|{x[1]:+.2f}pt|{x[2]:+.2f}pt|{"YES" if x[3] else "NO"}|')
    L += ['',f'選択 λ = **{lam:.2f}**','',
          '## Jun-Aug holdout aggregate','|層|点数|current 的中率|v110 的中率|current coverage|v110 coverage|差|current ROI|v110 ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    ds=[];nonw=0;jbad=0
    for g in ['A','S']:
        for p in POINTS:
            n,ch,cc,cr=metric(test,'test',g,p,'rank_l00');_,hh,hc,hr=metric(test,'test',g,p,col)
            d=hc-cc;ds.append(d);nonw+=int(d>=0);jbad+=int(d<0 and hr<cr)
            L.append(f'|{g}|{p}|{ch:.1f}%|{hh:.1f}%|{cc:.1f}%|{hc:.1f}%|{d:+.1f}pt|{cr:.1f}%|{hr:.1f}%|')
    L += ['','## 月別7点 stability','|月|層|R|current coverage|v110 coverage|差|current ROI|v110 ROI|','|---|---|---:|---:|---:|---:|---:|---:|']
    mnw=0
    for mo in TEST_MONTHS:
        q=bymo[mo]
        for g in ['A','S']:
            n,_,cc,cr=metric(q,'test',g,7,'rank_l00');_,_,hc,hr=metric(q,'test',g,7,col);mnw+=int(hc>=cc)
            L.append(f'|{mo}|{g}|{n}|{cc:.1f}%|{hc:.1f}%|{hc-cc:+.1f}pt|{cr:.1f}%|{hr:.1f}%|')
    avg=sum(ds)/len(ds);passed=(avg>=1.0 and nonw>=8 and mnw>=5 and jbad<=1)
    L += ['','## v110判定',f'- 平均coverage差 **{avg:+.2f}pt**',f'- 非悪化セル **{nonw}/10**',f'- 月別7点非悪化 **{mnw}/6**',f'- coverage+ROI同時悪化 **{jbad}**',f'- **V110 ROLE-TICKET = {"PASS" if passed else "FAIL"}**','- PASSでもproduction未採用。次はprior-only価格補正と合成オッズ率を別検証する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
