"""v110: 1号艇専用 2着/3着 role model + conservative ticket reranking.

NO-LEAK
- Source features are v108 pre-result-frozen rows.
- Head selection is v108 validation p1 for Mar-May and v109 monthly-WF p109 for Jun-Aug.
- Role models use ONLY races strictly before the evaluated month and ONLY rows where 1号艇 actually won.
  Outcome is used as training label only after the source race had been frozen; never as a current-race feature.
- Mar-May is tuning only for one blend lambda. Jun-Aug is untouched holdout for that lambda.
- No current/final odds are used. Payout is settlement-only for equal-stake ROI.

Role structure
- second model: candidate boat 2..6 -> P(2着 | 1号艇1着)
- third model: candidate third 2..6 conditioned on a proposed second boat -> P(3着 | 1号艇1着, proposed second)
- current v51 20-ticket order is blended conservatively with role log-probability.
"""
from __future__ import annotations
import csv, math
from collections import defaultdict
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
LAMBDAS=[0.0,0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50]
POINTS=[4,6,7,8,10]
VENUES=[f'{i:02d}' for i in range(1,25)]
A_CUT=.65; S_CUT=.72


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
    a=ranked(r)
    return a.index(b)+1 if b in a else 5

def zscores(vals):
    if not vals:return []
    m=sum(vals)/len(vals);v=sum((x-m)**2 for x in vals)/len(vals);sd=math.sqrt(v)
    return [(x-m)/sd if sd>1e-12 else 0.0 for x in vals]

def second_vec(r,b):
    th=[threat(r,x) for x in range(2,7)];tb=threat(r,b);rk=rankof(r,b)
    row=[tb,1-(rk-1)/4,(tb-max(th) if th else 0),(tb-sum(th)/len(th) if th else 0),ff(r.get('one_score'))-tb]
    row.extend(1.0 if b==x else 0.0 for x in range(2,7))
    vv=str(r.get('venue','')).zfill(2);row.extend(1.0 if vv==v else 0.0 for v in VENUES)
    return row

def third_vec(r,s,t):
    th=[threat(r,x) for x in range(2,7)];tt=threat(r,t);ts=threat(r,s);rt=rankof(r,t);rs=rankof(r,s)
    row=[tt,1-(rt-1)/4,ts,1-(rs-1)/4,tt-ts,rt-rs,(tt-max(th) if th else 0),ff(r.get('one_score'))-tt]
    row.extend(1.0 if t==x else 0.0 for x in range(2,7))
    row.extend(1.0 if s==x else 0.0 for x in range(2,7))
    vv=str(r.get('venue','')).zfill(2);row.extend(1.0 if vv==v else 0.0 for v in VENUES)
    return row

def fit_binary(X,y):
    p=Pipeline([('scale',StandardScaler()),('lr',LogisticRegression(C=.5,max_iter=1500,solver='lbfgs'))])
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
            if b==s:continue
            X3.append(third_vec(r,s,b));y3.append(int(b==t))
    if nr<100:raise RuntimeError(f'not enough 1-head training races: {nr}')
    return fit_binary(X2,y2),fit_binary(X3,y3),nr

def pair_order(r,m2,m3,lam):
    boats=list(range(2,7))
    p2raw={b:float(m2.predict_proba(np.asarray([second_vec(r,b)],dtype=float))[0,1]) for b in boats}
    s2=sum(p2raw.values()) or 1.0;p2={b:max(p2raw[b]/s2,1e-9) for b in boats}
    pairs=[]
    for s in boats:
        rem=[t for t in boats if t!=s]
        p3raw={t:float(m3.predict_proba(np.asarray([third_vec(r,s,t)],dtype=float))[0,1]) for t in rem}
        z=sum(p3raw.values()) or 1.0
        for t in rem:
            role=math.log(p2[s])+math.log(max(p3raw[t]/z,1e-9))
            cur=-(rankof(r,s)+.7*rankof(r,t))
            pairs.append((s,t,cur,role))
    cz=zscores([x[2] for x in pairs]);rz=zscores([x[3] for x in pairs])
    out=[]
    for x,c,r in zip(pairs,cz,rz):
        s,t=x[0],x[1];score=(1-lam)*c+lam*r
        out.append((score,s,t,c,r))
    out.sort(key=lambda x:(-x[0],x[1],x[2]))
    return [f'1-{s}-{t}' for _,s,t,_,_ in out]

def current_order(r):
    a=ranked(r);pairs=[]
    for s in a:
        for t in a:
            if s==t:continue
            pairs.append((rankof(r,s)+.7*rankof(r,t),rankof(r,s),rankof(r,t),f'1-{s}-{t}'))
    pairs.sort();return [x[3] for x in pairs]

def score_month(src,mo,lam):
    first=date.fromisoformat(mo+'-01');train=[r for r in src if date.fromisoformat(r['date'])<first]
    test=[dict(r) for r in src if r.get('month')==mo and ii(r.get('valid_result'))==1]
    m2,m3,ntrain=fit_roles(train)
    for r in test:
        cur=current_order(r);hyb=pair_order(r,m2,m3,lam);act=(r.get('actual_combo') or '').strip()
        r['v110_month']=mo;r['v110_lambda']=lam;r['role_train_headwins']=ntrain
        r['current_rank20']=cur.index(act)+1 if act in cur else 0
        r['v110_rank20']=hyb.index(act)+1 if act in hyb else 0
        r['current20']=';'.join(cur);r['v110_20']=';'.join(hyb)
    return test

def sel_prob(r,phase,grade):
    p=ff(r.get('p1' if phase=='val' else 'p109'),0)
    return p >= (S_CUT if grade=='S' else A_CUT)

def metric(rs,phase,grade,npt,col):
    q=[r for r in rs if sel_prob(r,phase,grade) and ii(r.get('valid_payout'))==1]
    hits=[r for r in q if 0<ii(r.get(col))<=npt]
    heads=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(1 for r in heads if 0<ii(r.get(col))<=npt)
    inv=len(q)*npt*100;ret=sum(ii(r.get('payout100')) for r in hits)
    return len(q),pct(len(hits),len(q)),pct(cov,len(heads)),pct(ret,inv)

def choose_lambda(src):
    rows=[]
    for lam in LAMBDAS:
        allv=[]
        for mo in VAL_MONTHS:allv.extend(score_month(src,mo,lam))
        diffs=[];worst=999
        for grade in ['A','S']:
            for p in POINTS:
                _,_,cc,_=metric(allv,'val',grade,p,'current_rank20');_,_,hc,_=metric(allv,'val',grade,p,'v110_rank20')
                d=hc-cc;diffs.append(d);worst=min(worst,d)
        avg=sum(diffs)/len(diffs)
        admissible=(worst>=-0.5 and avg>=0)
        rows.append((lam,avg,worst,admissible,allv))
    ok=[x for x in rows if x[3]] or [x for x in rows if x[0]==0]
    best=max(ok,key=lambda x:(x[1],-x[0]))
    return best[0],rows

def main():
    src=read_csv(SRC)
    # attach v109 monthly-WF head probabilities to Jun-Aug rows
    hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read_csv(HEADSRC)}
    for r in src:
        if r.get('month') in TEST_MONTHS:r['p109']=hp.get((r.get('date'),r.get('race_code')),'')

    lam,tune=choose_lambda(src)
    out=[]
    for mo in TEST_MONTHS:out.extend(score_month(src,mo,lam))
    fs=sorted(set().union(*(r.keys() for r in out)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    L=['# v110 1号艇 2着/3着 role model','',
       '1号艇頭モデルv109は固定したまま、相手だけを改善する。2着モデルと3着モデルを分離し、各評価月より前の1号艇1着レースだけでrole学習。',
       'Mar-Mayだけで current v51順位 と role順位 のblend λを選び、Jun-Augは固定λで月次walk-forward。オッズは不使用。','',
       '## validation λ selection','|λ|平均coverage差|最悪1セル差|採用可能|','|---:|---:|---:|---|']
    for x in tune:L.append(f'|{x[0]:.2f}|{x[1]:+.2f}pt|{x[2]:+.2f}pt|{"YES" if x[3] else "NO"}|')
    L+=['',f'選択 λ = **{lam:.2f}**','',
        '## Jun-Aug holdout aggregate','|層|点数|current 的中率|v110 的中率|current 頭的中時coverage|v110 coverage|coverage差|current ROI|v110 ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    pass_cells=0;total_cells=0;joint_bad=0;agg_d=[]
    for grade in ['A','S']:
        for p in POINTS:
            n,ch,cc,cr=metric(out,'test',grade,p,'current_rank20');_,hh,hc,hr=metric(out,'test',grade,p,'v110_rank20')
            d=hc-cc;agg_d.append(d);total_cells+=1;pass_cells+=int(d>=0);joint_bad+=int(d<0 and hr<cr)
            L.append(f'|{grade}|{p}|{ch:.1f}%|{hh:.1f}%|{cc:.1f}%|{hc:.1f}%|{d:+.1f}pt|{cr:.1f}%|{hr:.1f}%|')
    L+=['','## 月別 7点 stability','|月|層|R|current coverage|v110 coverage|差|current ROI|v110 ROI|','|---|---|---:|---:|---:|---:|---:|---:|']
    month_nonworse=0;month_total=0
    for mo in TEST_MONTHS:
        q=[r for r in out if r.get('v110_month')==mo]
        for grade in ['A','S']:
            n,_,cc,cr=metric(q,'test',grade,7,'current_rank20');_,_,hc,hr=metric(q,'test',grade,7,'v110_rank20')
            month_total+=1;month_nonworse+=int(hc>=cc)
            L.append(f'|{mo}|{grade}|{n}|{cc:.1f}%|{hc:.1f}%|{hc-cc:+.1f}pt|{cr:.1f}%|{hr:.1f}%|')
    avg=sum(agg_d)/len(agg_d) if agg_d else 0
    passed=(avg>=1.0 and pass_cells>=8 and month_nonworse>=5 and joint_bad<=1)
    L+=['','## v110判定',
        f'- aggregate平均 coverage差: **{avg:+.2f}pt**',
        f'- 非悪化セル: **{pass_cells}/{total_cells}**',
        f'- 月別7点 非悪化: **{month_nonworse}/{month_total}**',
        f'- coverageとROI同時悪化セル: **{joint_bad}**',
        f'- **V110 ROLE-TICKET = {"PASS" if passed else "FAIL"}**',
        '- PASSでもまだproduction採用ではない。次に合成オッズ率を含むprior-only price overlayを別検証する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')

if __name__=='__main__':main()
