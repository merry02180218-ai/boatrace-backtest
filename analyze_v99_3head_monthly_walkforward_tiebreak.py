"""v99: strict monthly walk-forward stability for v98 3HEAD role tiebreak.

- Lambda is FIXED at 0.2 from v98 validation (Mar-May).
- Therefore adoption evaluation uses ONLY Jun/Jul/Aug 2026, which were not used to choose lambda.
- For each month, 2nd/3rd role weights and feature scalers are trained only on head-hit races strictly before that month.
- Current vs v99 use exact equal-spend 4- and 6-ticket sets.
"""
from __future__ import annotations
import csv,math
from datetime import date

SRC='analysis_v97_3head5head_second_third.csv'
OUT='analysis_v99_3head_monthly_walkforward_tiebreak.csv'
SUMMARY='summary_v99_3head_monthly_walkforward_tiebreak.md'
LAM=.2;A=55.;S=67.;HEAD=3;BOATS=(1,2,4,5,6);FEATS=('grade','national','local','motor','waku','nst','direct')
MONTHS=('2026-06','2026-07','2026-08');MIN_TRAIN=40;L2=.15;ITERS=700;LR=.22

def ff(x,d=0.):
    try:
        if x is None or str(x).strip()=='':return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.
def read():
    with open(SRC,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def elig(r):return r.get('group_v97')=='3HEAD' and ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1
def rawfeat(r,b):return [ff(r.get(f'opp_{k}_b{b}_v97'),.5) for k in FEATS]
def trainrows(rs,before):return [r for r in rs if elig(r) and r.get('date','')<before and ii(r.get('winner'))==HEAD and ii(r.get('second')) in BOATS and ii(r.get('third')) in BOATS]

def scalers(tr):
    vals=[[] for _ in FEATS]
    for r in tr:
        for b in BOATS:
            for j,v in enumerate(rawfeat(r,b)):vals[j].append(v)
    mu=[];sd=[]
    for a in vals:
        m=sum(a)/len(a) if a else 0.;s=math.sqrt(sum((v-m)**2 for v in a)/len(a)) if a else 1.;mu.append(m);sd.append(s if s>1e-9 else 1.)
    return mu,sd

def xvec(r,b,mu,sd):
    z=[(v-mu[j])/sd[j] for j,v in enumerate(rawfeat(r,b))];z += [1. if b==k else 0. for k in BOATS];return z

def fit(tr,target,mu,sd):
    p=len(FEATS)+len(BOATS);w=[0.]*p
    for it in range(ITERS):
        g=[0.]*p;n=0
        for r in tr:
            y=ii(r.get(target));xs=[xvec(r,b,mu,sd) for b in BOATS];ss=[sum(w[j]*x[j] for j in range(p)) for x in xs];mx=max(ss);es=[math.exp(s-mx) for s in ss];den=sum(es)
            for bi,b in enumerate(BOATS):
                e=es[bi]/den-(1. if b==y else 0.)
                for j in range(p):g[j]+=e*xs[bi][j]
            n+=1
        if not n:break
        lr=LR/math.sqrt(1+it/120)
        for j in range(p):w[j]-=lr*(g[j]/n+L2*w[j])
    return w

def zmap(v):
    a=list(v.values());m=sum(a)/len(a);s=math.sqrt(sum((x-m)**2 for x in a)/len(a));return {b:(0. if s<1e-9 else (x-m)/s) for b,x in v.items()}
def scores(r,w2,w3,mu,sd):
    cur={b:ff(r.get(f'opp_score_b{b}_v97'),0.) for b in BOATS};zc=zmap(cur);p2={};p3={}
    for b in BOATS:
        x=xvec(r,b,mu,sd);p2[b]=sum(w2[j]*x[j] for j in range(len(w2)));p3[b]=sum(w3[j]*x[j] for j in range(len(w3)))
    z2=zmap(p2);z3=zmap(p3);return ({b:(1-LAM)*zc[b]+LAM*z2[b] for b in BOATS},{b:(1-LAM)*zc[b]+LAM*z3[b] for b in BOATS})
def current(r,k):
    rr=[ii(x) for x in r.get('ranked_others_v97','').split('-') if ii(x)];n3=3 if k==4 else 4;return [(a,b) for a in rr[:2] for b in rr[:n3] if a!=b][:k]
def blend(r,k,w2,w3,mu,sd):
    s2,s3=scores(r,w2,w3,mu,sd);r2=sorted(BOATS,key=lambda b:s2[b],reverse=True);r3=sorted(BOATS,key=lambda b:s3[b],reverse=True);n3=3 if k==4 else 4
    c=[(a,b) for a in r2[:2] for b in r3[:n3] if a!=b];c.sort(key=lambda p:s2[p[0]]+s3[p[1]],reverse=True)
    if len(c)<k:
        x=[(a,b) for a in BOATS for b in BOATS if a!=b and (a,b) not in c];x.sort(key=lambda p:s2[p[0]]+s3[p[1]],reverse=True);c+=x
    return c[:k]
def evalrows(rows,cut,k,mode,w2,w3,mu,sd):
    q=[r for r in rows if elig(r) and ff(r.get('score'),-999)>=cut];h=[r for r in q if ii(r.get('winner'))==HEAD];cov=ret=0
    for r in q:
        ts=current(r,k) if mode=='CURRENT' else blend(r,k,w2,w3,mu,sd)
        if ii(r.get('winner'))==HEAD and (ii(r.get('second')),ii(r.get('third'))) in ts:
            cov+=1
            if ii(r.get('valid_payout'))==1:ret+=ii(r.get('payout100'))
    inv=100*k*sum(ii(r.get('valid_payout'))==1 for r in q)
    return {'r':len(q),'head':len(h),'cov':cov,'covp':pct(cov,len(h)),'ret':ret,'inv':inv,'roi':pct(ret,inv)}
def month_end(m):
    y,mo=map(int,m.split('-'));return f'{y+1:04d}-01-01' if mo==12 else f'{y:04d}-{mo+1:02d}-01'

def main():
    rs=read();detail=[];agg={(lab,k,mode):{'head':0,'cov':0,'ret':0,'inv':0} for lab in ('A','S') for k in (4,6) for mode in ('CURRENT','V99')}
    L=['# v99 3頭 λ=0.2 厳密月別walk-forward','',
       '- λ=**0.2固定**（v98のMar-May validationで決定）。','- 採否評価はλ選択に未使用の **2026-06〜08** のみ。',
       '- 各月の役割別重みはその月より前の3頭頭的中だけで再学習。','- 4点/6点はCURRENTと完全同額。','']
    L += ['## 月別','|月|事前学習R|級|点|CURRENTカバー|V99カバー|差|CURRENT ROI|V99 ROI|差|','|---|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    bad=eligible_cells=0
    for m in MONTHS:
        start=m+'-01';end=month_end(m);tr=trainrows(rs,start)
        if len(tr)<MIN_TRAIN:continue
        mu,sd=scalers(tr);w2=fit(tr,'second',mu,sd);w3=fit(tr,'third',mu,sd);mr=[r for r in rs if start<=r.get('date','')<end]
        for lab,cut in (('A',A),('S',S)):
            for k in (4,6):
                c=evalrows(mr,cut,k,'CURRENT',w2,w3,mu,sd);v=evalrows(mr,cut,k,'V99',w2,w3,mu,sd)
                L.append(f'|{m}|{len(tr)}|{lab}|{k}|{c["cov"]}/{c["head"]} ({c["covp"]:.1f}%)|{v["cov"]}/{v["head"]} ({v["covp"]:.1f}%)|{v["covp"]-c["covp"]:+.1f}pt|{c["roi"]:.1f}%|{v["roi"]:.1f}%|{v["roi"]-c["roi"]:+.1f}pt|')
                for mode,z in (('CURRENT',c),('V99',v)):
                    a=agg[(lab,k,mode)];a['head']+=z['head'];a['cov']+=z['cov'];a['ret']+=z['ret'];a['inv']+=z['inv']
                if c['head']>=5:
                    eligible_cells+=1
                    if v['covp']<c['covp'] and v['roi']<c['roi']:bad+=1
                detail.append({'month':m,'train_n':len(tr),'grade':lab,'tickets':k,'current_covp':c['covp'],'v99_covp':v['covp'],'current_roi':c['roi'],'v99_roi':v['roi']})
    L += ['','## Jun-Aug合算','|級|点|CURRENTカバー|V99カバー|差|CURRENT ROI|V99 ROI|差|','|---|---:|---:|---:|---:|---:|---:|---:|']
    flags=[];improve=False
    for lab in ('A','S'):
        for k in (4,6):
            c=agg[(lab,k,'CURRENT')];v=agg[(lab,k,'V99')];cp=pct(c['cov'],c['head']);vp=pct(v['cov'],v['head']);cr=pct(c['ret'],c['inv']);vr=pct(v['ret'],v['inv'])
            L.append(f'|{lab}|{k}|{c["cov"]}/{c["head"]} ({cp:.1f}%)|{v["cov"]}/{v["head"]} ({vp:.1f}%)|{vp-cp:+.1f}pt|{cr:.1f}%|{vr:.1f}%|{vr-cr:+.1f}pt|')
            flags.append(vp>=cp and vr>=cr);improve|=vp>cp
    badpct=pct(bad,eligible_cells);passed=all(flags) and improve and badpct<=25
    L += ['','## 月別安定性',f'- 頭的中5R以上の月×セル: **{eligible_cells}**',f'- coverage/ROI同時悪化: **{bad}/{eligible_cells} ({badpct:.1f}%)**','',
          '## 判定','- 事前条件: Jun-Aug合算4セルすべてcoverage/ROI非悪化 + どこかcoverage改善 + 月別同時悪化<=25%。',f'- 結果: **{"PASS" if passed else "FAIL"}**.',
          f'- production: **{"prospective採用候補。正式採用は実戦記録後" if passed else "不採用。現行相手順位維持"}**.']
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(detail[0].keys()) if detail else ['month'];w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(detail)
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))
if __name__=='__main__':main()
