"""v98: conservative role-specific 2nd/3rd tiebreak for 3-head and 5-head.

Temporal design (per group)
- early4: 2025-11..2026-02 fit separate 2nd/3rd role softmax weights.
- val3:   2026-03..2026-05 choose ONE lambda from fixed grid.
- recent3:2026-06..2026-08 untouched parameter test.
- Then refit role weights on prior7, freeze lambda, evaluate recent3.

Current v51 opponent score remains anchor. Role-specific signal is only a bounded blend.
Ticket comparison is exact 4- and 6-ticket equal spend.
"""
from __future__ import annotations
import csv, math

SRC='analysis_v97_3head5head_second_third.csv'
OUT='analysis_v98_3head5head_conservative_pair_tiebreak.csv'
SUMMARY='summary_v98_3head5head_conservative_pair_tiebreak.md'
A=55.0;S=67.0
EARLY_END='2026-02-28';VAL_START='2026-03-01';VAL_END='2026-05-31';TEST_START='2026-06-01';END='2026-08-31'
LAMBDAS=(0.0,0.1,0.2,0.3,0.4)
FEATS=('grade','national','local','motor','waku','nst','direct')
GROUPS={'3HEAD':{'head':3,'boats':(1,2,4,5,6)},'5HEAD':{'head':5,'boats':(1,2,3,4,6)}}
L2=.15;ITERS=700;LR=.22

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
def selected(r,cut):return ff(r.get('score'),-999)>=cut

def rawfeat(r,b):return [ff(r.get(f'opp_{k}_b{b}_v97'),.5) for k in FEATS]

def headrows(rs,g,start='',end='9999-99-99'):
    h=GROUPS[g]['head'];boats=GROUPS[g]['boats']
    return [r for r in rs if r.get('group_v97')==g and start<=r.get('date','')<=end and eligible(r) and ii(r.get('winner'))==h and ii(r.get('second')) in boats and ii(r.get('third')) in boats]

def scalers(tr,g):
    boats=GROUPS[g]['boats'];vals=[[] for _ in FEATS]
    for r in tr:
        for b in boats:
            for j,v in enumerate(rawfeat(r,b)):vals[j].append(v)
    mu=[];sd=[]
    for a in vals:
        m=sum(a)/len(a) if a else 0.;s=math.sqrt(sum((v-m)**2 for v in a)/len(a)) if a else 1.
        mu.append(m);sd.append(s if s>1e-9 else 1.)
    return mu,sd

def xvec(r,b,g,mu,sd):
    boats=GROUPS[g]['boats'];z=[(v-mu[j])/sd[j] for j,v in enumerate(rawfeat(r,b))]
    z += [1. if b==k else 0. for k in boats]
    return z

def fit(tr,g,target,mu,sd):
    boats=GROUPS[g]['boats'];p=len(FEATS)+len(boats);w=[0.]*p
    for it in range(ITERS):
        grad=[0.]*p;n=0
        for r in tr:
            y=ii(r.get(target));xs=[xvec(r,b,g,mu,sd) for b in boats]
            ss=[sum(w[j]*x[j] for j in range(p)) for x in xs];mx=max(ss);es=[math.exp(s-mx) for s in ss];den=sum(es)
            for bi,b in enumerate(boats):
                e=es[bi]/den-(1. if b==y else 0.)
                for j in range(p):grad[j]+=e*xs[bi][j]
            n+=1
        if not n:break
        lr=LR/math.sqrt(1+it/120)
        for j in range(p):w[j]-=lr*(grad[j]/n+L2*w[j])
    return w

def zmap(vals):
    a=list(vals.values());m=sum(a)/len(a);s=math.sqrt(sum((v-m)**2 for v in a)/len(a))
    if s<1e-9:return {b:0. for b in vals}
    return {b:(v-m)/s for b,v in vals.items()}

def role_scores(r,g,w2,w3,mu,sd,lam):
    boats=GROUPS[g]['boats'];cur={b:ff(r.get(f'opp_score_b{b}_v97'),0.) for b in boats};zc=zmap(cur)
    sp2={};sp3={}
    for b in boats:
        x=xvec(r,b,g,mu,sd);sp2[b]=sum(w2[j]*x[j] for j in range(len(w2)));sp3[b]=sum(w3[j]*x[j] for j in range(len(w3)))
    z2=zmap(sp2);z3=zmap(sp3)
    return ({b:(1-lam)*zc[b]+lam*z2[b] for b in boats},{b:(1-lam)*zc[b]+lam*z3[b] for b in boats})

def current_rank(r):return [ii(x) for x in r.get('ranked_others_v97','').split('-') if ii(x)]
def current_tickets(r,k):
    rr=current_rank(r);n3=3 if k==4 else 4
    pairs=[(a,b) for a in rr[:2] for b in rr[:n3] if a!=b]
    return pairs[:k]

def blend_tickets(r,g,w2,w3,mu,sd,lam,k):
    boats=GROUPS[g]['boats'];s2,s3=role_scores(r,g,w2,w3,mu,sd,lam);r2=sorted(boats,key=lambda b:s2[b],reverse=True);r3=sorted(boats,key=lambda b:s3[b],reverse=True)
    n3=3 if k==4 else 4;c=[(a,b) for a in r2[:2] for b in r3[:n3] if a!=b]
    c=sorted(c,key=lambda p:s2[p[0]]+s3[p[1]],reverse=True)
    if len(c)<k:
        rest=[(a,b) for a in boats for b in boats if a!=b and (a,b) not in c];rest.sort(key=lambda p:s2[p[0]]+s3[p[1]],reverse=True);c+=rest
    return c[:k]

def metrics(q,g,cut,k,mode,w2=None,w3=None,mu=None,sd=None,lam=0.):
    head=GROUPS[g]['head'];rows=[r for r in q if r.get('group_v97')==g and eligible(r) and selected(r,cut)]
    h=[r for r in rows if ii(r.get('winner'))==head];cov=ret=0
    for r in rows:
        ts=current_tickets(r,k) if mode=='CURRENT' else blend_tickets(r,g,w2,w3,mu,sd,lam,k)
        if ii(r.get('winner'))==head and (ii(r.get('second')),ii(r.get('third'))) in ts:
            if r in h:cov+=1
            if ii(r.get('valid_payout'))==1:ret+=ii(r.get('payout100'))
    inv=100*k*sum(1 for r in rows if ii(r.get('valid_payout'))==1)
    return {'r':len(rows),'head':len(h),'cov':cov,'covp':pct(cov,len(h)),'roi':pct(ret,inv)}

def choose_lambda(val,g,w2,w3,mu,sd):
    grid=[]
    for lam in LAMBDAS:
        ms=[]
        for cut in (A,S):
            for k in (4,6):ms.append(metrics(val,g,cut,k,'BLEND',w2,w3,mu,sd,lam)['covp'])
        obj=sum(ms)/len(ms);grid.append((lam,obj,ms))
    best=max(grid,key=lambda z:(z[1],-z[0]))[0]
    return best,grid

def main():
    rs=read();out=[];summary=[]
    L=['# v98 3頭・5頭 2着/3着 保守型タイブレーク','',
       '- 現行v51相手点をアンカーにし、役割別2着/3着スコアを低比率だけブレンド。',
       '- λ候補は0/0.1/0.2/0.3/0.4固定。early4で重み学習、Mar-Mayだけでλ選択、Jun-Augは未使用のparameter test。',
       '- A/S閾値55/67、4点/6点はCURRENTと完全同額。','']
    for g in ('3HEAD','5HEAD'):
        early=headrows(rs,g,'2025-11-01',EARLY_END);val=[r for r in rs if VAL_START<=r.get('date','')<=VAL_END]
        mu_e,sd_e=scalers(early,g);w2e=fit(early,g,'second',mu_e,sd_e);w3e=fit(early,g,'third',mu_e,sd_e);lam,grid=choose_lambda(val,g,w2e,w3e,mu_e,sd_e)
        prior=headrows(rs,g,'2025-11-01',VAL_END);mu,sd=scalers(prior,g);w2=fit(prior,g,'second',mu,sd);w3=fit(prior,g,'third',mu,sd);test=[r for r in rs if TEST_START<=r.get('date','')<=END]
        L += [f'## {g}',f'- early4 head-hit学習R: **{len(early)}** / prior7再学習R: **{len(prior)}**',f'- validation選択λ: **{lam:.1f}**','',
              '|λ|A4|A6|S4|S6|平均カバー|','|---:|---:|---:|---:|---:|---:|']
        for la,obj,ms in grid:L.append(f'|{la:.1f}|{ms[0]:.1f}%|{ms[1]:.1f}%|{ms[2]:.1f}%|{ms[3]:.1f}%|{obj:.1f}%|')
        L += ['','### recent3 完全固定比較','|級|点|CURRENTカバー|V98カバー|差|CURRENT ROI|V98 ROI|差|','|---|---:|---:|---:|---:|---:|---:|---:|']
        flags=[];improve=False
        for label,cut in (('A',A),('S',S)):
            for k in (4,6):
                c=metrics(test,g,cut,k,'CURRENT');v=metrics(test,g,cut,k,'BLEND',w2,w3,mu,sd,lam)
                L.append(f'|{label}|{k}|{c["cov"]}/{c["head"]} ({c["covp"]:.1f}%)|{v["cov"]}/{v["head"]} ({v["covp"]:.1f}%)|{v["covp"]-c["covp"]:+.1f}pt|{c["roi"]:.1f}%|{v["roi"]:.1f}%|{v["roi"]-c["roi"]:+.1f}pt|')
                flags.append(v['covp']>=c['covp'] and v['roi']>=c['roi']);improve|=v['covp']>c['covp']
        passed=all(flags) and improve
        L += ['',f'- pre-fixed criterion → **{"PASS" if passed else "FAIL"}**',f'- production: **{"採用候補。月別walk-forwardへ" if passed else "不採用。現行相手順位維持"}**','']
        summary.append((g,lam,passed))
        for r0 in rs:
            if r0.get('group_v97')!=g:continue
            r=dict(r0);s2,s3=role_scores(r,g,w2,w3,mu,sd,lam);boats=GROUPS[g]['boats']
            r['v98_lambda']=lam;r['rank2_v98']='-'.join(map(str,sorted(boats,key=lambda b:s2[b],reverse=True)));r['rank3_v98']='-'.join(map(str,sorted(boats,key=lambda b:s3[b],reverse=True)))
            r['tickets4_v98']=';'.join(f'{a}-{b}' for a,b in blend_tickets(r,g,w2,w3,mu,sd,lam,4));r['tickets6_v98']=';'.join(f'{a}-{b}' for a,b in blend_tickets(r,g,w2,w3,mu,sd,lam,6));r['v98_parameter_test_pass']=int(passed);out.append(r)
    if out:
        fs=sorted(set().union(*(r.keys() for r in out)))
        with open(OUT,'w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    L += ['## まとめ']
    for g,lam,p in summary:L.append(f'- {g}: λ={lam:.1f} / **{"PASS" if p else "FAIL"}**')
    L.append('- PASSでも即production採用はせず、次にλ固定の月別walk-forwardで安定性確認。')
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))
if __name__=='__main__':main()
