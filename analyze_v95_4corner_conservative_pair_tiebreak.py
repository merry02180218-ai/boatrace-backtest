"""v95: conservative 4-corner 2nd/3rd role tiebreak.

Why
- v94 showed role-specific signal, but full replacement hurt recent3 S badly.
- Keep current v93 opponent score as the anchor and add only a bounded role-specific blend.

Temporal design
- early4 (2025-11..2026-02): fit role-specific softmax weights.
- val3   (2026-03..2026-05): choose ONE blend lambda from a pre-fixed grid, using only coverage.
- recent3(2026-06..2026-08): untouched parameter test.
- Then refit role weights on prior7 (Nov..May), freeze chosen lambda, evaluate recent3.

Ticket fairness
- Compare exactly 4-ticket and 6-ticket head-fixed sets.
- CURRENT uses current shared ranking shapes (2nd Top2 x 3rd Top3/4), naturally 4/6 tickets.
- BLEND builds the same role-specific candidate shapes, and if they produce extra ordered pairs,
  keeps the best exact K by blended role scores. Therefore spend is identical.
"""
from __future__ import annotations
import csv, math

SRC='analysis_v93_4corner_second_third.csv'
OUT='analysis_v95_4corner_conservative_pair_tiebreak.csv'
SUMMARY='summary_v95_4corner_conservative_pair_tiebreak.md'
BOATS=(1,2,3,5,6)
FEATS=('grade','national','local','motor','waku','nst','direct')
A=55.0; S=67.0
EARLY_END='2026-02-28'; VAL_START='2026-03-01'; VAL_END='2026-05-31'; TEST_START='2026-06-01'
LAMBDAS=(0.0,0.1,0.2,0.3,0.4)
L2=0.15; ITERS=700; LR=0.22

def ff(x,d=0.0):
    try:
        if x is None or str(x).strip()=='':return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def read():
    with open(SRC,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def eligible(r):return ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1

def selected(r,cut):return ff(r.get('score_CORR20_v91'),-999)>=cut

def rawfeat(r,b):return [ff(r.get(f'opp_{k}_b{b}_v93'),0.5) for k in FEATS]

def headrows(rs,start='',end='9999-99-99'):
    return [r for r in rs if start<=r.get('date','')<=end and eligible(r) and ii(r.get('winner'))==4 and ii(r.get('second')) in BOATS and ii(r.get('third')) in BOATS]

def scalers(tr):
    vals=[[] for _ in FEATS]
    for r in tr:
        for b in BOATS:
            for j,v in enumerate(rawfeat(r,b)):vals[j].append(v)
    mu=[];sd=[]
    for a in vals:
        m=sum(a)/len(a) if a else 0.0
        s=math.sqrt(sum((v-m)**2 for v in a)/len(a)) if a else 1.0
        mu.append(m);sd.append(s if s>1e-9 else 1.0)
    return mu,sd

def xvec(r,b,mu,sd):
    z=[(v-mu[j])/sd[j] for j,v in enumerate(rawfeat(r,b))]
    z += [1.0 if b==k else 0.0 for k in BOATS]
    return z

def fit(tr,target,mu,sd):
    p=len(FEATS)+len(BOATS);w=[0.0]*p
    for it in range(ITERS):
        g=[0.0]*p;n=0
        for r in tr:
            y=ii(r.get(target));xs=[xvec(r,b,mu,sd) for b in BOATS]
            ss=[sum(w[j]*x[j] for j in range(p)) for x in xs]
            m=max(ss);es=[math.exp(s-m) for s in ss];den=sum(es)
            for bi,b in enumerate(BOATS):
                e=es[bi]/den-(1.0 if b==y else 0.0)
                for j in range(p):g[j]+=e*xs[bi][j]
            n+=1
        if not n:break
        lr=LR/math.sqrt(1+it/120)
        for j in range(p):w[j]-=lr*(g[j]/n+L2*w[j])
    return w

def zmap(vals):
    a=list(vals.values());m=sum(a)/len(a);s=math.sqrt(sum((v-m)**2 for v in a)/len(a))
    if s<1e-9:return {b:0.0 for b in vals}
    return {b:(v-m)/s for b,v in vals.items()}

def role_scores(r,w2,w3,mu,sd,lam):
    cur={b:ff(r.get(f'opp_score_b{b}_v93'),0.0) for b in BOATS};zc=zmap(cur)
    sp2={};sp3={}
    for b in BOATS:
        x=xvec(r,b,mu,sd);sp2[b]=sum(w2[j]*x[j] for j in range(len(w2)));sp3[b]=sum(w3[j]*x[j] for j in range(len(w3)))
    z2=zmap(sp2);z3=zmap(sp3)
    b2={b:(1-lam)*zc[b]+lam*z2[b] for b in BOATS};b3={b:(1-lam)*zc[b]+lam*z3[b] for b in BOATS}
    return b2,b3

def current_rank(r):return [ii(x) for x in r.get('ranked_others_v93','').split('-') if ii(x) in BOATS]

def exact_current(r,k):
    rr=current_rank(r);n3=3 if k==4 else 4
    pairs=[(a,b) for a in rr[:2] for b in rr[:n3] if a!=b]
    return pairs[:k]

def exact_blend(r,w2,w3,mu,sd,lam,k):
    s2,s3=role_scores(r,w2,w3,mu,sd,lam)
    r2=sorted(BOATS,key=lambda b:s2[b],reverse=True);r3=sorted(BOATS,key=lambda b:s3[b],reverse=True)
    n3=3 if k==4 else 4
    cand=[(a,b) for a in r2[:2] for b in r3[:n3] if a!=b]
    cand=sorted(cand,key=lambda p:s2[p[0]]+s3[p[1]],reverse=True)
    if len(cand)<k:
        rest=[(a,b) for a in BOATS for b in BOATS if a!=b and (a,b) not in cand]
        rest=sorted(rest,key=lambda p:s2[p[0]]+s3[p[1]],reverse=True);cand+=rest
    return cand[:k]

def coverage(q,cut,k,mode,w2=None,w3=None,mu=None,sd=None,lam=0):
    h=[r for r in q if eligible(r) and selected(r,cut) and ii(r.get('winner'))==4]
    hit=0
    for r in h:
        ts=exact_current(r,k) if mode=='CURRENT' else exact_blend(r,w2,w3,mu,sd,lam,k)
        if (ii(r.get('second')),ii(r.get('third'))) in ts:hit+=1
    return hit,len(h),pct(hit,len(h))

def roi(q,cut,k,mode,w2=None,w3=None,mu=None,sd=None,lam=0):
    rows=[r for r in q if eligible(r) and selected(r,cut)]
    ret=0;inv=100*k*len(rows);hits=0
    for r in rows:
        ts=exact_current(r,k) if mode=='CURRENT' else exact_blend(r,w2,w3,mu,sd,lam,k)
        if ii(r.get('winner'))==4 and (ii(r.get('second')),ii(r.get('third'))) in ts:
            hits+=1
            if ii(r.get('valid_payout'))==1:ret+=ii(r.get('payout100'))
    return hits,pct(ret,inv)

def choose_lambda(val,w2,w3,mu,sd):
    scored=[]
    for lam in LAMBDAS:
        metrics=[]
        for cut in (A,S):
            for k in (4,6):metrics.append(coverage(val,cut,k,'BLEND',w2,w3,mu,sd,lam)[2])
        obj=sum(metrics)/len(metrics)
        scored.append((obj,-lam,lam,metrics))
    scored.sort(reverse=True)
    return scored[0][2],sorted(scored,key=lambda x:x[2])

def main():
    rs=read();early=headrows(rs,'2025-11-01',EARLY_END);val=[r for r in rs if VAL_START<=r.get('date','')<=VAL_END]
    mu_e,sd_e=scalers(early);w2e=fit(early,'second',mu_e,sd_e);w3e=fit(early,'third',mu_e,sd_e)
    lam,grid=choose_lambda(val,w2e,w3e,mu_e,sd_e)
    prior=headrows(rs,'2025-11-01',VAL_END);mu,sd=scalers(prior);w2=fit(prior,'second',mu,sd);w3=fit(prior,'third',mu,sd)
    test=[r for r in rs if TEST_START<=r.get('date','')<='2026-08-31']

    out=[]
    for r0 in rs:
        r=dict(r0);s2,s3=role_scores(r,w2,w3,mu,sd,lam)
        r['v95_lambda']=lam
        r['rank2_v95']='-'.join(map(str,sorted(BOATS,key=lambda b:s2[b],reverse=True)))
        r['rank3_v95']='-'.join(map(str,sorted(BOATS,key=lambda b:s3[b],reverse=True)))
        r['tickets4_v95']=';'.join(f'{a}-{b}' for a,b in exact_blend(r,w2,w3,mu,sd,lam,4))
        r['tickets6_v95']=';'.join(f'{a}-{b}' for a,b in exact_blend(r,w2,w3,mu,sd,lam,6))
        out.append(r)
    fs=sorted(set().union(*(r.keys() for r in out)))
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    L=['# v95 4カド 2着/3着 保守型タイブレーク','',
       f'- early4学習R: {len(early)} / prior7最終学習R: {len(prior)}',
       f'- validationだけで選んだblend λ: **{lam:.1f}**',
       '- recent3はλ選択・重み学習とも未使用。',
       '- 現行v93相手点を主軸に、役割別スコアはλ分だけ混ぜる。4点/6点は厳密に同額比較。','']
    L+=['## validation λ選択','', '|λ|A 4点|A 6点|S 4点|S 6点|平均カバー|','|---:|---:|---:|---:|---:|---:|']
    for obj,neg,la,m in grid:L.append(f'|{la:.1f}|{m[0]:.1f}%|{m[1]:.1f}%|{m[2]:.1f}%|{m[3]:.1f}%|{obj:.1f}%|')
    L+=['','## recent3 完全固定比較','', '|選別|点数|CURRENTカバー|V95カバー|差|CURRENT ROI|V95 ROI|ROI差|','|---|---:|---:|---:|---:|---:|---:|---:|']
    pass_flags=[]
    for label,cut in (('CORR20_A',A),('CORR20_S',S)):
        for k in (4,6):
            hc,n,pc=coverage(test,cut,k,'CURRENT');hv,n2,pv=coverage(test,cut,k,'BLEND',w2,w3,mu,sd,lam)
            _,rc=roi(test,cut,k,'CURRENT');_,rv=roi(test,cut,k,'BLEND',w2,w3,mu,sd,lam)
            L.append(f'|{label}|{k}|{hc}/{n} ({pc:.1f}%)|{hv}/{n2} ({pv:.1f}%)|{pv-pc:+.1f}pt|{rc:.1f}%|{rv:.1f}%|{rv-rc:+.1f}pt|')
            pass_flags.append(pv>=pc and rv>=rc)
    adopt=all(pass_flags) and any(coverage(test,c,k,'BLEND',w2,w3,mu,sd,lam)[2]>coverage(test,c,k,'CURRENT')[2] for c in (A,S) for k in (4,6))
    L+=['','## 判定',f'- pre-fixed conservative criterion: 4比較すべてでカバー率・ROIがCURRENT以上、かつどこかでカバー率改善 → **{"PASS" if adopt else "FAIL"}**.',
        f'- production: **{"候補（追加のprospective確認が必要）" if adopt else "不採用。現行相手順位を維持"}**.']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
