"""v96: fixed lambda=0.1 monthly walk-forward validation for 4-corner 2nd/3rd conservative tiebreak.

Design
- Source opponent features/ranks are v93 pre-race frozen features.
- Lambda is fixed at 0.1 from v95 and is NEVER re-selected here.
- For each target month, role-specific weights are fit only on head-hit races strictly before that month.
- 2025-11 and 2025-12 act as warm-up; first eligible month requires >=40 prior head-hit races.
- Compare exact 4-ticket and 6-ticket spend against CURRENT ranking for CORR20 A/S.

Pre-fixed adoption rule
1) Aggregate over all eligible walk-forward months: all four cells (A4/A6/S4/S6) must have
   coverage >= CURRENT and ROI >= CURRENT.
2) At least one aggregate cell must improve coverage.
3) Among month-cells with >=5 head-hit races, cells where BOTH coverage and ROI worsen
   must be <=25%.
"""
from __future__ import annotations
import csv, math
from collections import defaultdict
from datetime import date

SRC='analysis_v93_4corner_second_third.csv'
OUT='analysis_v96_4corner_monthly_walkforward_tiebreak.csv'
SUMMARY='summary_v96_4corner_monthly_walkforward_tiebreak.md'
BOATS=(1,2,3,5,6)
FEATS=('grade','national','local','motor','waku','nst','direct')
A=55.0; S=67.0; LAMBDA=0.1
MIN_TRAIN=40
L2=0.15; ITERS=700; LR=0.22
MONTHS=[f'2026-{m:02d}' for m in range(1,9)]


def ff(x,d=0.0):
    try:
        if x is None or str(x).strip()=='': return d
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

def headrows_before(rs,month):
    return [r for r in rs if r.get('date','')[:7] < month and eligible(r) and ii(r.get('winner'))==4 and ii(r.get('second')) in BOATS and ii(r.get('third')) in BOATS]

def monthrows(rs,month):return [r for r in rs if r.get('date','')[:7]==month]

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

def role_scores(r,w2,w3,mu,sd):
    cur={b:ff(r.get(f'opp_score_b{b}_v93'),0.0) for b in BOATS};zc=zmap(cur)
    sp2={};sp3={}
    for b in BOATS:
        x=xvec(r,b,mu,sd)
        sp2[b]=sum(w2[j]*x[j] for j in range(len(w2)))
        sp3[b]=sum(w3[j]*x[j] for j in range(len(w3)))
    z2=zmap(sp2);z3=zmap(sp3)
    b2={b:(1-LAMBDA)*zc[b]+LAMBDA*z2[b] for b in BOATS}
    b3={b:(1-LAMBDA)*zc[b]+LAMBDA*z3[b] for b in BOATS}
    return b2,b3

def current_rank(r):return [ii(x) for x in r.get('ranked_others_v93','').split('-') if ii(x) in BOATS]

def exact_current(r,k):
    rr=current_rank(r);n3=3 if k==4 else 4
    pairs=[(a,b) for a in rr[:2] for b in rr[:n3] if a!=b]
    return pairs[:k]

def exact_blend(r,w2,w3,mu,sd,k):
    s2,s3=role_scores(r,w2,w3,mu,sd)
    r2=sorted(BOATS,key=lambda b:s2[b],reverse=True)
    r3=sorted(BOATS,key=lambda b:s3[b],reverse=True)
    n3=3 if k==4 else 4
    cand=[(a,b) for a in r2[:2] for b in r3[:n3] if a!=b]
    cand=sorted(cand,key=lambda p:s2[p[0]]+s3[p[1]],reverse=True)
    if len(cand)<k:
        rest=[(a,b) for a in BOATS for b in BOATS if a!=b and (a,b) not in cand]
        rest=sorted(rest,key=lambda p:s2[p[0]]+s3[p[1]],reverse=True);cand+=rest
    return cand[:k]

def eval_rows(q,cut,k,mode,w2=None,w3=None,mu=None,sd=None):
    rows=[r for r in q if eligible(r) and selected(r,cut)]
    head=covered=0;ret=0;valid_pay_rows=0
    for r in rows:
        ts=exact_current(r,k) if mode=='CURRENT' else exact_blend(r,w2,w3,mu,sd,k)
        if ii(r.get('valid_payout'))==1: valid_pay_rows+=1
        if ii(r.get('winner'))==4:
            head+=1
            if (ii(r.get('second')),ii(r.get('third'))) in ts:
                covered+=1
                if ii(r.get('valid_payout'))==1:ret+=ii(r.get('payout100'))
    inv=100*k*valid_pay_rows
    return {'r':len(rows),'head':head,'covered':covered,'covp':pct(covered,head),'ret':ret,'inv':inv,'roi':pct(ret,inv)}

def addagg(a,z):
    for k in ('r','head','covered','ret','inv'):a[k]+=z[k]

def main():
    rs=read();out=[];monthly=[]
    agg=defaultdict(lambda:{'r':0,'head':0,'covered':0,'ret':0,'inv':0})
    eligible_months=[]
    for month in MONTHS:
        tr=headrows_before(rs,month)
        if len(tr)<MIN_TRAIN:continue
        eligible_months.append(month)
        mu,sd=scalers(tr);w2=fit(tr,'second',mu,sd);w3=fit(tr,'third',mu,sd)
        q=monthrows(rs,month)
        for r0 in q:
            r=dict(r0);s2,s3=role_scores(r,w2,w3,mu,sd)
            r['v96_month']=month;r['v96_train_head_n']=len(tr);r['v96_lambda']=LAMBDA
            r['rank2_v96']='-'.join(map(str,sorted(BOATS,key=lambda b:s2[b],reverse=True)))
            r['rank3_v96']='-'.join(map(str,sorted(BOATS,key=lambda b:s3[b],reverse=True)))
            r['tickets4_v96']=';'.join(f'{a}-{b}' for a,b in exact_blend(r,w2,w3,mu,sd,4))
            r['tickets6_v96']=';'.join(f'{a}-{b}' for a,b in exact_blend(r,w2,w3,mu,sd,6))
            out.append(r)
        for label,cut in (('A',A),('S',S)):
            for k in (4,6):
                c=eval_rows(q,cut,k,'CURRENT');v=eval_rows(q,cut,k,'V96',w2,w3,mu,sd)
                monthly.append({'month':month,'train':len(tr),'label':label,'k':k,'current':c,'v96':v})
                addagg(agg[(label,k,'CURRENT')],c);addagg(agg[(label,k,'V96')],v)

    if out:
        fs=sorted(set().union(*(r.keys() for r in out)))
        with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)

    L=['# v96 4カド 2着/3着 λ=0.1 月別walk-forward','',
       f'- λ: **{LAMBDA:.1f}固定**（v95から変更なし）',
       f'- 最小学習4頭的中R: {MIN_TRAIN}',
       f'- 評価対象月: {", ".join(eligible_months) if eligible_months else "なし"}',
       '- 各月の役割別重みは、その月より前の4号艇頭的中だけで再学習。',
       '- CURRENT/V96は4点・6点で完全同額比較。','']
    L+=['## 月別','',
        '|月|事前学習R|選別|点|CURRENTカバー|V96カバー|差|CURRENT ROI|V96 ROI|差|',
        '|---|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    stable_n=both_worse=0
    for m in monthly:
        c=m['current'];v=m['v96'];dc=v['covp']-c['covp'];dr=v['roi']-c['roi']
        L.append(f'|{m["month"]}|{m["train"]}|{m["label"]}|{m["k"]}|{c["covered"]}/{c["head"]} ({c["covp"]:.1f}%)|{v["covered"]}/{v["head"]} ({v["covp"]:.1f}%)|{dc:+.1f}pt|{c["roi"]:.1f}%|{v["roi"]:.1f}%|{dr:+.1f}pt|')
        if c['head']>=5:
            stable_n+=1
            if dc<0 and dr<0:both_worse+=1

    L+=['','## 全walk-forward月 合算','',
        '|選別|点|CURRENTカバー|V96カバー|差|CURRENT ROI|V96 ROI|差|','|---|---:|---:|---:|---:|---:|---:|---:|']
    pass_cells=[];improve=False
    for label in ('A','S'):
        for k in (4,6):
            c=agg[(label,k,'CURRENT')];v=agg[(label,k,'V96')]
            cp=pct(c['covered'],c['head']);vp=pct(v['covered'],v['head']);cr=pct(c['ret'],c['inv']);vr=pct(v['ret'],v['inv'])
            L.append(f'|{label}|{k}|{c["covered"]}/{c["head"]} ({cp:.1f}%)|{v["covered"]}/{v["head"]} ({vp:.1f}%)|{vp-cp:+.1f}pt|{cr:.1f}%|{vr:.1f}%|{vr-cr:+.1f}pt|')
            pass_cells.append(vp>=cp and vr>=cr)
            improve=improve or vp>cp
    worse_share=pct(both_worse,stable_n)
    adopt=all(pass_cells) and improve and worse_share<=25.0
    L+=['','## 月別安定性',
        f'- 頭的中5R以上の月×セル: **{stable_n}**',
        f'- カバー率・ROIが同時悪化: **{both_worse}/{stable_n} ({worse_share:.1f}%)**',
        '', '## 判定',
        '- 事前条件: 合算4セルすべてcoverage/ROI非悪化 + どこかcoverage改善 + 月別同時悪化<=25%。',
        f'- 結果: **{"PASS" if adopt else "FAIL"}**.',
        f'- production: **{"採用候補を維持。ただしprospective確認後に正式採用" if adopt else "現行相手順位を維持し、v95補正はproduction不採用"}**.']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
