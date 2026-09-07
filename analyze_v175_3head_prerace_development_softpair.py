#!/usr/bin/env python3
"""v175: pre-race 3-head development probabilities softly re-rank frozen v166 pairs.

NO-LEAK / design:
- actual kimarite is used only as a historical training label on prior 3-head wins;
- development classifier features are pre-result fields already used by the frozen v108/v166 pipeline;
- each evaluated month trains both classifier and method-conditioned pair priors on strictly earlier dates;
- v165 3-head probability and v166 direct-pair model are unchanged;
- alpha is selected on Mar-May only, then frozen for Jun-Aug;
- Jun-Aug result/payout are evaluation/settlement only.
"""
from __future__ import annotations
import csv, math
from collections import Counter,defaultdict
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from analyze_v166_3head_pair_direct import (
    read,ff,ii,combo,strength,hstrength,ranks,pvec,fit,zs,
    SRC,HEADSRC,VAL_MONTHS,TEST_MONTHS,OPP,VENUES
)

OUT='analysis_v175_3head_prerace_development_softpair.csv'
SUMMARY='summary_v175_3head_prerace_development_softpair.md'
CUT=.30
N=10
ALPHAS=[0,.10,.20,.35,.50,.75,1.0,1.5]
SMOOTH=25.0
METHOD_KEYS=['kimarite','winning_method','win_method','decision','kime','race_kimarite','actual_kimarite']
CLASSES=['makuri','makuri-sashi','other']

def method(r):
    raw=''
    for k in METHOD_KEYS:
        if str(r.get(k,'')).strip(): raw=str(r.get(k,'')).strip();break
    s=raw.replace(' ','').replace('　','');sl=s.lower()
    if 'まくり差し' in s or '捲り差し' in s or 'makurizashi' in sl or 'makuri-sashi' in sl:return 'makuri-sashi'
    if 'まくり' in s or '捲り' in s or ('makuri' in sl and 'sashi' not in sl):return 'makuri'
    return 'other' if raw else ''

def race_feat(r):
    vals=[strength(r,b) for b in [1,2,3,4,5,6]]
    opp=[strength(r,b) for b in OPP]
    rk=ranks(r)
    x=vals + [
        hstrength(r)-strength(r,1),hstrength(r)-strength(r,2),
        hstrength(r)-strength(r,4),hstrength(r)-max(strength(r,4),strength(r,5),strength(r,6)),
        strength(r,1)-strength(r,2),max(opp)-sum(opp)/len(opp),
        ff(r.get('margin2')),ff(r.get('margin3')),ff(r.get('margin_all')),
        ff(r.get('st_margin23')),ff(r.get('ex_margin23')),ff(r.get('turn_margin23')),ff(r.get('straight_margin23')),
        float(rk[1]),float(rk[2]),float(rk[4]),float(rk[5]),float(rk[6])]
    v=str(r.get('venue','')).zfill(2);x += [1. if v==z else 0. for z in VENUES]
    return x

def train_dev(train):
    X=[];y=[]
    for r in train:
        if ii(r.get('valid_result'))!=1:continue
        a=combo(r.get('actual_combo'));m=method(r)
        if len(a)!=3 or a[0]!=3 or not m:continue
        X.append(race_feat(r));y.append(m)
    if len(X)<300 or len(set(y))<3:raise RuntimeError(f'not enough dev labels: n={len(X)} classes={set(y)}')
    mdl=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.25,max_iter=1800,solver='lbfgs'))])
    mdl.fit(np.asarray(X,float),np.asarray(y));return mdl,len(X)

def pair_priors(train):
    glob=Counter();by=defaultdict(Counter);n=Counter();gn=0
    pairs=[(s,t) for s in OPP for t in OPP if s!=t]
    for r in train:
        if ii(r.get('valid_result'))!=1:continue
        a=combo(r.get('actual_combo'));m=method(r)
        if len(a)!=3 or a[0]!=3 or not m or a[1]==a[2] or a[1] not in OPP or a[2] not in OPP:continue
        p=(a[1],a[2]);glob[p]+=1;by[m][p]+=1;n[m]+=1;gn+=1
    gp={p:(glob[p]+1)/(gn+len(pairs)) for p in pairs}
    tab={}
    for m in CLASSES:
        tab[m]={p:(by[m][p]+SMOOTH*gp[p])/(n[m]+SMOOTH) for p in pairs}
    return tab,dict(n)

def dev_probs(r,mdl):
    q=mdl.predict_proba(np.asarray([race_feat(r)],float))[0]
    names=list(mdl.named_steps['m'].classes_)
    return {m:float(q[names.index(m)]) if m in names else 0. for m in CLASSES}

def base_scores(r,pair_model):
    pairs=[];logs=[]
    for s in OPP:
        for t in OPP:
            if s==t:continue
            q=float(pair_model.predict_proba(np.asarray([pvec(r,s,t)],float))[0,1])
            pairs.append((s,t));logs.append(math.log(max(q,1e-12)))
    return pairs,zs(logs)

def rerank(r,pair_model,dev_model,pri,alpha):
    pairs,bz=base_scores(r,pair_model);dp=dev_probs(r,dev_model);dr=[]
    for p in pairs:
        mix=sum(dp[m]*pri[m][p] for m in CLASSES)
        dr.append(math.log(max(mix,1e-12)))
    dz=zs(dr);z=[(b+alpha*d,p) for b,d,p in zip(bz,dz,pairs)]
    z.sort(key=lambda q:(-q[0],q[1][0],q[1][1]))
    return [f'3-{p[0]}-{p[1]}' for _,p in z],dp

def score_month(src,mo,alpha):
    first=date.fromisoformat(mo+'-01');tr=[r for r in src if date.fromisoformat(r['date'])<first]
    te=[dict(r) for r in src if r.get('month')==mo and ii(r.get('valid_result'))==1]
    pm,pn=fit(tr);dm,dn=train_dev(tr);pri,counts=pair_priors(tr)
    out=[]
    for r in te:
        base,_=base_scores(r,pm); # v166 lambda=1.00 => direct pair probability ordering
        bl=[]
        for p in base:
            q=float(pm.predict_proba(np.asarray([pvec(r,p[0],p[1])],float))[0,1]);bl.append((q,p))
        bl.sort(key=lambda x:(-x[0],x[1][0],x[1][1]));base_list=[f'3-{p[0]}-{p[1]}' for _,p in bl]
        new,dp=rerank(r,pm,dm,pri,alpha);act=(r.get('actual_combo') or '').strip()
        r['v175_month']=mo;r['pair_train_3wins']=pn;r['dev_train_3wins']=dn
        r['p_makuri']=dp['makuri'];r['p_makuri_sashi']=dp['makuri-sashi'];r['p_otherdev']=dp['other']
        r['v166_rank20']=base_list.index(act)+1 if act in base_list else 0
        r['v175_rank20']=new.index(act)+1 if act in new else 0;r['v175_20']=';'.join(new)
        r['dev_prior_counts']=str(counts);out.append(r)
    return out

def coverage(rs,col,n=N):
    h=[r for r in rs if combo(r.get('actual_combo'))[:1]==[3]]
    return 100*sum(1 for r in h if 0<ii(r.get(col))<=n)/len(h) if h else 0.

def metric(rs,col):
    q=[r for r in rs if ff(r.get('p3head'))>=CUT]
    h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    hit=sum(1 for r in q if 0<ii(r.get(col))<=N)
    cov=100*sum(1 for r in h if 0<ii(r.get(col))<=N)/len(h) if h else 0.
    settled=[r for r in q if ii(r.get('valid_payout'))==1]
    ret=sum(ff(r.get('payout100')) for r in settled if 0<ii(r.get(col))<=N);inv=len(settled)*N*100
    return dict(races=len(q),head=len(h),hit=100*hit/len(q) if q else 0.,cov=cov,roi=100*ret/inv if inv else 0.)

def main():
    src=read(SRC);hp={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    for i,r in enumerate(src):r['p3head']=hp.get(i,'')
    keyp={(r['date'],r.get('race_code')):hp.get(i,'') for i,r in enumerate(src)}
    tune=[]
    for a in ALPHAS:
        vv=[]
        for mo in VAL_MONTHS:vv+=score_month(src,mo,a)
        b=coverage(vv,'v166_rank20');n=coverage(vv,'v175_rank20')
        md=[]
        for mo in VAL_MONTHS:
            x=[r for r in vv if r.get('v175_month')==mo];md.append(coverage(x,'v175_rank20')-coverage(x,'v166_rank20'))
        tune.append((a,n-b,min(md),n))
    eligible=[x for x in tune if x[2]>=-1.5] or tune
    alpha=max(eligible,key=lambda x:(x[1],x[2],-x[0]))[0]
    out=[]
    for mo in TEST_MONTHS:out+=score_month(src,mo,alpha)
    for r in out:r['p3head']=keyp.get((r['date'],r.get('race_code')),'')
    rows=[]
    for label,rs in [('ALL',out)]+[(mo,[r for r in out if r.get('v175_month')==mo]) for mo in TEST_MONTHS]:
        b=metric(rs,'v166_rank20');n=metric(rs,'v175_rank20')
        rows.append(dict(month=label,alpha=alpha,races=b['races'],head3=b['head'],v166_hit=b['hit'],v175_hit=n['hit'],v166_cov=b['cov'],v175_cov=n['cov'],v166_roi=b['roi'],v175_roi=n['roi']))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    L=['# v175 ③頭・事前展開確率 soft-pair OOS比較','',
       '- 実決まり手は過去③頭レースの学習ラベルにのみ使用。評価対象レース自身の決まり手は特徴に使わない。',
       '- 事前特徴はv108/v166で既に固定された強さ・margin・場などのみ。','- v165 ③頭確率とv166 direct pairは固定。',
       '- 各評価月はその月より前だけで展開分類器と展開別pair priorを再学習。','- alphaはMar-Mayだけで選びJun-Aug固定。Jun-Augは完全OOS評価。','',
       '## Mar-May alpha tuning','|alpha|coverage差|月別worst差|v175 coverage|','|---:|---:|---:|---:|']
    for a,d,w,c in tune:L.append(f'|{a:.2f}|{d:+.2f}pt|{w:+.2f}pt|{c:.2f}%|')
    L+=['',f'選択 alpha = **{alpha:.2f}**','','## p3>=0.30 / top10 Jun-Aug OOS',
        '|month|R|③頭R|v166 hit|v175 hit|v166 cov|v175 cov|v166 ROI|v175 ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:L.append(f"|{r['month']}|{r['races']}|{r['head3']}|{r['v166_hit']:.2f}%|{r['v175_hit']:.2f}%|{r['v166_cov']:.2f}%|{r['v175_cov']:.2f}%|{r['v166_roi']:.1f}%|{r['v175_roi']:.1f}%|")
    L+=['','## Decision rule','- 全体coverageだけでなくJun/Jul/Augの月別安定性とROIも確認し、v166を一貫して改善する場合のみ採用候補。','- Jun-Augを見てalphaや展開分類ルールを再調整しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
