#!/usr/bin/env python3
"""v179: apply validated v178 racer-style development signal to frozen v166 pair ranking.

Design / no leak
- v165 p3head and v166 direct-pair model remain frozen.
- Development classifier uses v175 base race features + v178 STYLE only.
- STYLE is reconstructed from racer histories strictly BEFORE each race via v177.
- Classifier target is only historical 3-head makuri vs makuri-sashi.
- Method-conditioned ordered-pair priors are trained only on earlier races.
- alpha is selected on Mar-May only and then frozen for Jun-Aug OOS.
- Jun-Aug result/payout are evaluation/settlement only.
"""
from __future__ import annotations
import csv, math
from collections import Counter, defaultdict
from datetime import date
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from analyze_v166_3head_pair_direct import (
    read, ff, ii, combo, pvec, fit, zs,
    SRC, HEADSRC, VAL_MONTHS, TEST_MONTHS, OPP
)
from analyze_v175_3head_prerace_development_softpair import race_feat, method
from analyze_v177_3head_historical_web_enrichment import reconstruct
from analyze_v178_3head_prerace_ablation import STYLE

OUT='analysis_v179_3head_style_softpair.csv'
SUMMARY='summary_v179_3head_style_softpair.md'
CUT=.30
N=10
ALPHAS=[0,.05,.10,.15,.20,.30,.40,.50,.75,1.00]
SMOOTH=25.0
METHODS=['makuri','makuri-sashi']


def dev_vec(r,e):
    x=list(race_feat(r))
    x.extend(float(e[k]) for k in STYLE)
    return x


def train_dev(src,extra,first):
    X=[];y=[]
    for i,r in enumerate(src):
        if date.fromisoformat(r['date'])>=first or ii(r.get('valid_result'))!=1:continue
        a=combo(r.get('actual_combo'));m=method(r)
        if len(a)!=3 or a[0]!=3 or m not in METHODS:continue
        X.append(dev_vec(r,extra[i]));y.append(m)
    if len(X)<300 or len(set(y))<2:raise RuntimeError(f'not enough binary dev labels: {len(X)} {set(y)}')
    mdl=Pipeline([('s',StandardScaler()),('m',LogisticRegression(C=.25,max_iter=1800,solver='lbfgs'))])
    mdl.fit(np.asarray(X,float),np.asarray(y));return mdl,len(y)


def dev_probs(r,e,mdl):
    q=mdl.predict_proba(np.asarray([dev_vec(r,e)],float))[0]
    cls=list(mdl.named_steps['m'].classes_)
    return {m:(float(q[cls.index(m)]) if m in cls else 0.) for m in METHODS}


def pair_priors(src,first):
    pairs=[(s,t) for s in OPP for t in OPP if s!=t]
    glob=Counter();by=defaultdict(Counter);n=Counter();gn=0
    for r in src:
        if date.fromisoformat(r['date'])>=first or ii(r.get('valid_result'))!=1:continue
        a=combo(r.get('actual_combo'));m=method(r)
        if len(a)!=3 or a[0]!=3 or m not in METHODS or a[1] not in OPP or a[2] not in OPP or a[1]==a[2]:continue
        p=(a[1],a[2]);glob[p]+=1;by[m][p]+=1;n[m]+=1;gn+=1
    gp={p:(glob[p]+1)/(gn+len(pairs)) for p in pairs}
    tab={m:{p:(by[m][p]+SMOOTH*gp[p])/(n[m]+SMOOTH) for p in pairs} for m in METHODS}
    return tab,dict(n)


def base_scores(r,pm):
    pairs=[];logs=[]
    for s in OPP:
        for t in OPP:
            if s==t:continue
            q=float(pm.predict_proba(np.asarray([pvec(r,s,t)],float))[0,1])
            pairs.append((s,t));logs.append(math.log(max(q,1e-12)))
    return pairs,zs(logs)


def base_order(r,pm):
    z=[]
    for s in OPP:
        for t in OPP:
            if s==t:continue
            q=float(pm.predict_proba(np.asarray([pvec(r,s,t)],float))[0,1])
            z.append((q,s,t))
    z.sort(key=lambda x:(-x[0],x[1],x[2]))
    return [f'3-{s}-{t}' for _,s,t in z]


def rerank(r,e,pm,dm,pri,alpha):
    pairs,bz=base_scores(r,pm);dp=dev_probs(r,e,dm);logs=[]
    for p in pairs:
        mix=sum(dp[m]*pri[m][p] for m in METHODS)
        logs.append(math.log(max(mix,1e-12)))
    dz=zs(logs)
    z=[(b+alpha*d,p) for b,d,p in zip(bz,dz,pairs)]
    z.sort(key=lambda x:(-x[0],x[1][0],x[1][1]))
    return [f'3-{p[0]}-{p[1]}' for _,p in z],dp


def score_month(src,extra,mo,alpha):
    first=date.fromisoformat(mo+'-01')
    tr=[r for r in src if date.fromisoformat(r['date'])<first]
    pm,pn=fit(tr);dm,dn=train_dev(src,extra,first);pri,counts=pair_priors(src,first)
    out=[]
    for i,r0 in enumerate(src):
        if r0.get('month')!=mo or ii(r0.get('valid_result'))!=1:continue
        r=dict(r0);base=base_order(r,pm);new,dp=rerank(r,extra[i],pm,dm,pri,alpha);act=(r.get('actual_combo') or '').strip()
        r['v179_month']=mo;r['pair_train_3wins']=pn;r['dev_train_binary']=dn
        r['p_makuri']=dp['makuri'];r['p_makuri_sashi']=dp['makuri-sashi']
        r['v166_rank20']=base.index(act)+1 if act in base else 0
        r['v179_rank20']=new.index(act)+1 if act in new else 0
        r['v179_20']=';'.join(new);r['dev_prior_counts']=str(counts);out.append(r)
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
    ret=sum(ff(r.get('payout100')) for r in settled if 0<ii(r.get(col))<=N)
    inv=len(settled)*N*100
    return dict(races=len(q),head=len(h),hit=100*hit/len(q) if q else 0.,cov=cov,roi=100*ret/inv if inv else 0.)


def main():
    src=read(SRC);extra,covrec=reconstruct(src)
    hp={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    for i,r in enumerate(src):r['p3head']=hp.get(i,'')
    keyp={(r['date'],r.get('race_code')):hp.get(i,'') for i,r in enumerate(src)}

    tune=[]
    for a in ALPHAS:
        vv=[]
        for mo in VAL_MONTHS:vv+=score_month(src,extra,mo,a)
        b=coverage(vv,'v166_rank20');n=coverage(vv,'v179_rank20')
        md=[]
        for mo in VAL_MONTHS:
            x=[r for r in vv if r.get('v179_month')==mo]
            md.append(coverage(x,'v179_rank20')-coverage(x,'v166_rank20'))
        tune.append((a,n-b,min(md),n))
    eligible=[x for x in tune if x[2]>=-1.5] or tune
    alpha=max(eligible,key=lambda x:(x[1],x[2],-x[0]))[0]

    out=[]
    for mo in TEST_MONTHS:out+=score_month(src,extra,mo,alpha)
    for r in out:r['p3head']=keyp.get((r['date'],r.get('race_code')),'')

    rows=[]
    for label,rs in [('ALL',out)]+[(mo,[r for r in out if r.get('v179_month')==mo]) for mo in TEST_MONTHS]:
        b=metric(rs,'v166_rank20');n=metric(rs,'v179_rank20')
        rows.append(dict(month=label,alpha=alpha,races=b['races'],head3=b['head'],v166_hit=b['hit'],v179_hit=n['hit'],v166_cov=b['cov'],v179_cov=n['cov'],v166_roi=b['roi'],v179_roi=n['roi']))

    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

    L=['# v179 ③頭・racer-style soft-pair OOS比較','',
       '- v178で安定改善したracer-style特徴だけを展開分類器へ追加。',
       '- v165 ③頭確率とv166 direct pairは固定。',
       '- style履歴は評価レースより前だけでrolling生成。現在レース展示は不使用。',
       '- 展開classifier targetは過去③頭のまくり vs まくり差しのみ。',
       '- alphaはMar-Mayだけで選択し、Jun-Augは固定完全OOS。','',
       '## reconstruction coverage',f"- SRC matched: {covrec['matched_src']}",f"- prior exhibition available (not used in v179 classifier): {covrec['matched_prev_ex']}",'',
       '## Mar-May alpha tuning','|alpha|coverage差|月別worst差|v179 coverage|','|---:|---:|---:|---:|']
    for a,d,w,c in tune:L.append(f'|{a:.2f}|{d:+.2f}pt|{w:+.2f}pt|{c:.2f}%|')
    L+=['',f'選択 alpha = **{alpha:.2f}**','','## p3>=0.30 / top10 Jun-Aug OOS',
        '|month|R|③頭R|v166 hit|v179 hit|v166 cov|v179 cov|v166 ROI|v179 ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:L.append(f"|{r['month']}|{r['races']}|{r['head3']}|{r['v166_hit']:.2f}%|{r['v179_hit']:.2f}%|{r['v166_cov']:.2f}%|{r['v179_cov']:.2f}%|{r['v166_roi']:.1f}%|{r['v179_roi']:.1f}%|")
    L+=['','## Decision rule','- v166に対して全体coverage/hit/ROIだけでなくJun/Jul/Augの月別安定性も確認する。','- Jun-Augを見てalphaや特徴定義を後付け変更しない。','- 一貫改善しなければv166を維持する。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))

if __name__=='__main__':main()
