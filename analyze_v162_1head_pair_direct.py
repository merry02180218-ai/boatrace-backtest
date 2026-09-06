"""v162: direct pair model for 1-head opponent ranking.

Goal: improve v110's fixed top-7 coverage by scoring the full ordered pair (2nd,3rd)
directly instead of factorizing second and third roles.

NO-LEAK
- Source rows are v108 pre-result-frozen features.
- Pair model is trained only on races strictly before each evaluated month and only
  on races where 1 actually won; actual combo is a training label only.
- Mar-May is used only to choose one conservative blend lambda.
- Jun-Aug is retrospective holdout comparison versus CURRENT and v110. Because
  these months have been examined in prior project work, this is diagnostic rather
  than a fresh prospective adoption test.
- No current/final odds in ranking. Payout is settlement-only.
"""
from __future__ import annotations
import csv, math
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import analyze_v110_1head_role_tickets as v110

SRC='analysis_v108_1head_feasibility.csv'
HEADSRC='analysis_v109_1head_monthly_walkforward.csv'
OUT='analysis_v162_1head_pair_direct.csv'
SUMMARY='summary_v162_1head_pair_direct.md'
VAL_MONTHS=['2026-03','2026-04','2026-05']
TEST_MONTHS=['2026-06','2026-07','2026-08']
LAMBDAS=[0.0,0.15,0.25,0.35,0.50,0.65,0.80,1.0]
POINTS=[1,3,5,7,10]
A_CUT=.65;S_CUT=.72
VENUES=[f'{i:02d}' for i in range(1,25)]

def ii(x,d=0):
    try:return int(float(x))
    except:return d

def ff(x,d=0.0):
    try:return float(x)
    except:return d

def pct(n,d):return 100*n/d if d else 0.0

def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def threat(r,b):return ff(r.get(f'threat{b}'))
def rankof(r,b):return v110.rankof(r,b)

def pair_vec(r,s,t):
    ths,tht=threat(r,s),threat(r,t)
    rs,rt=rankof(r,s),rankof(r,t)
    allth=[threat(r,b) for b in range(2,7)]
    mx=max(allth) if allth else 0.0; av=sum(allth)/len(allth) if allth else 0.0
    dist=abs(t-s)
    row=[
      ths,tht,ths+tht,ths-tht,min(ths,tht),max(ths,tht),
      1-(rs-1)/4,1-(rt-1)/4,rs-rt,rs+rt,
      ths-mx,tht-mx,ths-av,tht-av,
      ff(r.get('one_score'))-ths,ff(r.get('one_score'))-tht,
      ff(r.get('margin2')),ff(r.get('margin3')),ff(r.get('margin_all')),
      ff(r.get('st_margin23')),ff(r.get('ex_margin23')),ff(r.get('turn_margin23')),ff(r.get('straight_margin23')),
      float(dist),1.0 if dist==1 else 0.0,1.0 if s<t else 0.0,
      1.0 if s==2 else 0.0,1.0 if s==3 else 0.0,1.0 if s==4 else 0.0,1.0 if s==5 else 0.0,1.0 if s==6 else 0.0,
      1.0 if t==2 else 0.0,1.0 if t==3 else 0.0,1.0 if t==4 else 0.0,1.0 if t==5 else 0.0,1.0 if t==6 else 0.0,
    ]
    vv=str(r.get('venue','')).zfill(2);row.extend(1.0 if vv==v else 0.0 for v in VENUES)
    return row

def fit_pair(train):
    X=[];y=[];nr=0
    for r in train:
        if ii(r.get('valid_result'))!=1 or ii(r.get('head_hit'))!=1:continue
        a=v110.parse_combo(r.get('actual_combo'))
        if len(a)!=3 or a[0]!=1:continue
        s0,t0=a[1],a[2]
        if s0 not in range(2,7) or t0 not in range(2,7) or s0==t0:continue
        nr+=1
        for s in range(2,7):
            for t in range(2,7):
                if s==t:continue
                X.append(pair_vec(r,s,t));y.append(int(s==s0 and t==t0))
    if nr<100:raise RuntimeError(f'not enough training head wins: {nr}')
    p=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.35,max_iter=1800,solver='lbfgs',class_weight=None))])
    p.fit(np.asarray(X,float),np.asarray(y,int));return p,nr

def zscores(vals):
    m=float(np.mean(vals));sd=float(np.std(vals));return [(x-m)/sd if sd>1e-12 else 0.0 for x in vals]

def pair_order(r,model,lam):
    pairs=[];scores=[];cur=[]
    for s in range(2,7):
        for t in range(2,7):
            if s==t:continue
            q=float(model.predict_proba(np.asarray([pair_vec(r,s,t)],float))[0,1])
            q=max(q,1e-12);scores.append(math.log(q));cur.append(-(rankof(r,s)+.7*rankof(r,t)));pairs.append((s,t))
    pz=zscores(scores);cz=zscores(cur);out=[]
    for (s,t),p,c in zip(pairs,pz,cz):out.append(((1-lam)*c+lam*p,s,t))
    out.sort(key=lambda x:(-x[0],x[1],x[2]));return [f'1-{s}-{t}' for _,s,t in out]

def sel_prob(r,phase,grade):
    p=ff(r.get('p1' if phase=='val' else 'p109'))
    return p >= (S_CUT if grade=='S' else A_CUT)

def score_month(src,mo,lam,phase):
    first=date.fromisoformat(mo+'-01');train=[r for r in src if date.fromisoformat(r['date'])<first]
    test=[dict(r) for r in src if r.get('month')==mo and ii(r.get('valid_result'))==1]
    pm,ntr=fit_pair(train);m2,m3,_=v110.fit_roles(train)
    for r in test:
        cur=v110.current_order(r);old=v110.pair_order(r,m2,m3,.50);new=pair_order(r,pm,lam);act=(r.get('actual_combo') or '').strip()
        r['v162_month']=mo;r['v162_lambda']=lam;r['pair_train_headwins']=ntr
        for name,ordr in [('current',cur),('v110',old),('v162',new)]:r[f'{name}_rank20']=ordr.index(act)+1 if act in ordr else 0
        r['v162_20']=';'.join(new)
    return test

def metric(rs,phase,grade,npt,col):
    q=[r for r in rs if sel_prob(r,phase,grade)]
    heads=[r for r in q if ii(r.get('head_hit'))==1]
    cov=sum(1 for r in heads if 0<ii(r.get(col))<=npt)
    tri=sum(1 for r in q if 0<ii(r.get(col))<=npt)
    return len(q),pct(tri,len(q)),pct(cov,len(heads))

def choose_lambda(src):
    rows=[]
    for lam in LAMBDAS:
        rr=[]
        for mo in VAL_MONTHS:rr.extend(score_month(src,mo,lam,'val'))
        ds=[];worst=999
        for g in ['A','S']:
            for n in [3,5,7,10]:
                _,_,old=metric(rr,'val',g,n,'v110_rank20');_,_,new=metric(rr,'val',g,n,'v162_rank20')
                d=new-old;ds.append(d);worst=min(worst,d)
        avg=sum(ds)/len(ds);ad=(worst>=-0.75 and avg>=0)
        rows.append((lam,avg,worst,ad))
    ok=[x for x in rows if x[3]] or rows
    return max(ok,key=lambda x:(x[1],x[2],-abs(x[0]-.5)))[0],rows

def main():
    src=read_csv(SRC);hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read_csv(HEADSRC)}
    for r in src:
        if r.get('month') in TEST_MONTHS:r['p109']=hp.get((r.get('date'),r.get('race_code')),'')
    lam,tune=choose_lambda(src)
    out=[]
    for mo in TEST_MONTHS:out.extend(score_month(src,mo,lam,'test'))
    fs=sorted(set().union(*(r.keys() for r in out)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    L=['# v162 1号艇 direct pair model','',
       '- 1号艇頭はv109固定。相手20組を「2着×3着ペア」そのものとして直接学習。',
       '- Mar-Mayでblend λだけ選択。Jun-Augは月次walk-forward比較。',
       '- Jun-Augは過去に既に参照済みのため retrospective diagnostic。production採用にはSep以降のprospective確認が必要。','',
       '## λ tuning vs v110','|λ|平均coverage差|最悪差|admissible|','|---:|---:|---:|---|']
    for x in tune:L.append(f'|{x[0]:.2f}|{x[1]:+.2f}pt|{x[2]:+.2f}pt|{"YES" if x[3] else "NO"}|')
    L+=['',f'選択 λ = **{lam:.2f}**','',
        '## Jun-Aug aggregate','|層|点数|CURRENT coverage|v110 coverage|v162 coverage|v162-v110|v110的中率|v162的中率|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for g in ['A','S']:
        for n in POINTS:
            _,_,cc=metric(out,'test',g,n,'current_rank20');_,oh,oc=metric(out,'test',g,n,'v110_rank20');_,nh,nc=metric(out,'test',g,n,'v162_rank20')
            L.append(f'|{g}|{n}|{cc:.2f}%|{oc:.2f}%|{nc:.2f}%|{nc-oc:+.2f}pt|{oh:.2f}%|{nh:.2f}%|')
    L+=['','## 月別 S 7点','|月|R|CURRENT|v110|v162|v162-v110|','|---|---:|---:|---:|---:|---:|']
    for mo in TEST_MONTHS:
        q=[r for r in out if r.get('v162_month')==mo];n,_,cc=metric(q,'test','S',7,'current_rank20');_,_,oc=metric(q,'test','S',7,'v110_rank20');_,_,nc=metric(q,'test','S',7,'v162_rank20')
        L.append(f'|{mo}|{n}|{cc:.2f}%|{oc:.2f}%|{nc:.2f}%|{nc-oc:+.2f}pt|')
    L+=['','## 判定','- v162はv110を置き換えずshadow。','- S・7点coverageの改善と月別安定性を最優先。','- retrospectiveで改善してもSep以降prospectiveで再確認する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
