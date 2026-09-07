#!/usr/bin/env python3
"""v173: add a venue-specific second-place prior to frozen v166 pair ranking.

Guardrails:
- boat-3 head model is unchanged;
- v166 ordered-pair model is unchanged;
- only the SECOND leg gets a venue prior;
- each evaluated month builds priors from strictly earlier 3-head results;
- alpha is selected on Mar-May only, then frozen for Jun-Aug;
- Jun-Aug is evaluation only; payout is settlement-only.
"""
from __future__ import annotations
import csv, math
from collections import Counter, defaultdict
from datetime import date
import numpy as np
from analyze_v166_3head_pair_direct import read,ff,ii,combo,choose,score_month,SRC,HEADSRC,VAL_MONTHS,TEST_MONTHS,OPP

OUT='analysis_v173_3head_venue_second_prior.csv'
SUMMARY='summary_v173_3head_venue_second_prior.md'
ALPHAS=[0,.15,.30,.50,.75,1.0,1.5,2.0]
CUT=.30
N=10
SMOOTH=12.0

def vc(r):
    try:return f"{int(float(r.get('venue',''))):02d}"
    except:return str(r.get('venue') or 'NA')

def prior_table(train):
    glob=Counter(); byv=defaultdict(Counter); gn=0; vn=Counter()
    for r in train:
        if ii(r.get('valid_result'))!=1: continue
        a=combo(r.get('actual_combo'))
        if len(a)!=3 or a[0]!=3 or a[1] not in OPP: continue
        s=a[1]; v=vc(r); glob[s]+=1; byv[v][s]+=1; gn+=1; vn[v]+=1
    gp={s:(glob[s]+1)/(gn+len(OPP)) for s in OPP}
    tab={}
    for v in [f'{i:02d}' for i in range(1,25)]:
        n=vn[v]
        tab[v]={s:(byv[v][s]+SMOOTH*gp[s])/(n+SMOOTH) for s in OPP}
    return tab,dict(vn),gp

def zscore(vals):
    a=np.asarray(vals,float); sd=float(a.std())
    return ((a-a.mean())/sd if sd>1e-12 else np.zeros(len(a))).tolist()

def rerank(r,alpha,pri):
    base=[x for x in str(r.get('v166_20','')).split(';') if x]
    if not base:return []
    base_raw=[-i for i in range(len(base))]
    v=vc(r); p_raw=[]
    for x in base:
        s=int(x.split('-')[1]);p_raw.append(math.log(max(pri.get(v,{}).get(s,1/5),1e-12)))
    bz,pz=zscore(base_raw),zscore(p_raw)
    z=[(b+alpha*p,x) for b,p,x in zip(bz,pz,base)]
    z.sort(key=lambda q:(-q[0],q[1]))
    return [x for _,x in z]

def rank_actual(r,col):
    a=(r.get('actual_combo') or '').strip(); xs=r.get(col,[])
    return xs.index(a)+1 if a in xs else 0

def build_month(src,mo,lam,alpha):
    first=date.fromisoformat(mo+'-01')
    train=[r for r in src if date.fromisoformat(r['date'])<first]
    pri,vn,gp=prior_table(train)
    out=score_month(src,mo,lam)
    for r in out:
        rr=rerank(r,alpha,pri);r['_v173_list']=rr;r['v173_rank20']=rank_actual(r,'_v173_list');r['v173_20']=';'.join(rr);r['prior_train_3wins_venue']=vn.get(vc(r),0)
    return out

def coverage(rs,col,n=N):
    h=[r for r in rs if combo(r.get('actual_combo'))[:1]==[3]]
    return 100*sum(1 for r in h if 0<ii(r.get(col))<=n)/len(h) if h else 0

def metric(rs,col):
    q=[r for r in rs if ff(r.get('p3head'))>=CUT]
    h=[r for r in q if combo(r.get('actual_combo'))[:1]==[3]]
    hits=sum(1 for r in q if 0<ii(r.get(col))<=N)
    cov=100*sum(1 for r in h if 0<ii(r.get(col))<=N)/len(h) if h else 0
    settled=[r for r in q if ii(r.get('valid_payout'))==1]
    ret=sum(ff(r.get('payout100')) for r in settled if 0<ii(r.get(col))<=N)
    inv=len(settled)*N*100
    return dict(races=len(q),head=len(h),hit_rate=100*hits/len(q) if q else 0,coverage=cov,roi=100*ret/inv if inv else 0,return_yen=ret,investment=inv)

def main():
    src=read(SRC);hp={int(r['source_index']):ff(r.get('p3head')) for r in read(HEADSRC)}
    for i,r in enumerate(src):r['p3head']=hp.get(i,'')
    keyp={(r['date'],r.get('race_code')):hp.get(i,'') for i,r in enumerate(src)}
    lam,_=choose(src)
    # Tune only on Mar-May, using conditional coverage because v165 TEST p3 probabilities are frozen for Jun-Aug only.
    tune=[]
    for a in ALPHAS:
        vv=[]
        for mo in VAL_MONTHS:vv+=build_month(src,mo,lam,a)
        b=coverage(vv,'v166_rank20');n=coverage(vv,'v173_rank20')
        monthly=[]
        for mo in VAL_MONTHS:
            m=[r for r in vv if r.get('v166_month')==mo];monthly.append(coverage(m,'v173_rank20')-coverage(m,'v166_rank20'))
        tune.append((a,n-b,min(monthly),n))
    eligible=[x for x in tune if x[2]>=-2.0] or tune
    alpha=max(eligible,key=lambda x:(x[1],x[2],-x[0]))[0]
    out=[]
    for mo in TEST_MONTHS:out+=build_month(src,mo,lam,alpha)
    for r in out:r['p3head']=keyp.get((r['date'],r.get('race_code')),'')
    rows=[]
    for label,rs in [('ALL',out)]+[(mo,[r for r in out if r.get('v166_month')==mo]) for mo in TEST_MONTHS]:
        b=metric(rs,'v166_rank20');n=metric(rs,'v173_rank20')
        rows.append(dict(month=label,alpha=alpha,races=b['races'],head3=b['head'],v166_hit=b['hit_rate'],v173_hit=n['hit_rate'],v166_cov=b['coverage'],v173_cov=n['coverage'],v166_roi=b['roi'],v173_roi=n['roi'],v166_return=b['return_yen'],v173_return=n['return_yen'],investment=n['investment']))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    L=['# v173 ③頭・場別2着prior OOS比較','',f'- v165 head probability frozen; v166 pair model λ={lam:.2f} unchanged.','- 補正対象は2着legのみ。3着legは補正しない。','- 各月の場別2着priorはその月より前の実際の③1着レースだけで作成。','- alphaはMar-Mayだけで選び、Jun-Augでは固定。','- Jun-Augは評価のみ。payoutはsettlement-only。','','## Mar-May alpha tuning','|alpha|coverage差|月別worst差|v173 coverage|','|---:|---:|---:|---:|']
    for a,d,w,c in tune:L.append(f'|{a:.2f}|{d:+.2f}pt|{w:+.2f}pt|{c:.2f}%|')
    L += ['',f'選択 alpha = **{alpha:.2f}**','','## p3>=0.30 / top10 Jun-Aug OOS','|month|R|③頭R|v166 hit|v173 hit|v166 cov|v173 cov|v166 ROI|v173 ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:L.append(f"|{r['month']}|{r['races']}|{r['head3']}|{r['v166_hit']:.2f}%|{r['v173_hit']:.2f}%|{r['v166_cov']:.2f}%|{r['v173_cov']:.2f}%|{r['v166_roi']:.1f}%|{r['v173_roi']:.1f}%|")
    L += ['','## Decision rule','- v173が全体だけでなく月別でもv166を安定して上回る場合のみ、次の採用候補にする。','- Jun-Augの結果から場を除外したりalphaを再調整しない。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n');print('\n'.join(L))
if __name__=='__main__':main()
