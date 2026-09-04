"""v94: 4-corner separate 2nd/3rd opponent ranking.

Goal
- Build separate rankings for 2nd and 3rd place after a 4-corner head win.
- Fit parameters ONLY on prior7 (2025-11-01..2026-05-31) head-hit races.
- Evaluate recent3 (2026-06-01..2026-08-31) without using recent3 outcomes in fitting.
- Compare against current v93 shared opponent ranking at equal-ish ticket shapes.

Important
- v93 opponent component features are pre-race/frozen; results were joined only after ranking freeze.
- This is development validation, not automatic production adoption. The model form was motivated by v93's 10mo diagnostic, so recent3 is a parameter holdout, not a pristine untouched research holdout.
"""
from __future__ import annotations
import csv, math
from collections import defaultdict

SRC='analysis_v93_4corner_second_third.csv'
OUT='analysis_v94_4corner_split_second_third.csv'
SUMMARY='summary_v94_4corner_split_second_third.md'
A=55.0; S=67.0
TRAIN_END='2026-05-31'; TEST_START='2026-06-01'
BOATS=(1,2,3,5,6)
BASEFEAT=('grade','national','local','motor','waku','nst','direct')
L2=0.15; ITERS=700; LR=0.22


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

def selected(r,name):
    if name=='BASE_A':return ff(r.get('score_BASE_v91'),-999)>=A
    if name=='CORR20_A':return ff(r.get('score_CORR20_v91'),-999)>=A
    if name=='BASE_S':return ff(r.get('score_BASE_v91'),-999)>=S
    if name=='CORR20_S':return ff(r.get('score_CORR20_v91'),-999)>=S
    return False

def rawfeat(r,b):
    return [ff(r.get(f'opp_{k}_b{b}_v93'),0.5) for k in BASEFEAT]

def train_rows(rs):
    return [r for r in rs if r.get('date','')<=TRAIN_END and ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1 and ii(r.get('winner'))==4 and ii(r.get('second')) in BOATS and ii(r.get('third')) in BOATS]

def scalers(tr):
    vals=[[] for _ in BASEFEAT]
    for r in tr:
        for b in BOATS:
            x=rawfeat(r,b)
            for j,v in enumerate(x):vals[j].append(v)
    mu=[];sd=[]
    for a in vals:
        m=sum(a)/len(a) if a else 0
        s=math.sqrt(sum((v-m)**2 for v in a)/len(a)) if a else 1
        mu.append(m);sd.append(s if s>1e-9 else 1)
    return mu,sd

def xvec(r,b,mu,sd):
    base=rawfeat(r,b)
    z=[(v-mu[j])/sd[j] for j,v in enumerate(base)]
    # explicit lane identities capture survival/follow patterns after 4 wins.
    z += [1.0 if b==k else 0.0 for k in BOATS]
    return z

def fit_softmax(tr,target_field,mu,sd):
    p=len(BASEFEAT)+len(BOATS);w=[0.0]*p
    for it in range(ITERS):
        g=[0.0]*p;n=0
        for r in tr:
            y=ii(r.get(target_field)); xs=[xvec(r,b,mu,sd) for b in BOATS]
            ss=[sum(w[j]*x[j] for j in range(p)) for x in xs]
            mx=max(ss); ee=[math.exp(s-mx) for s in ss]; den=sum(ee); probs=[e/den for e in ee]
            for bi,b in enumerate(BOATS):
                err=probs[bi]-(1.0 if b==y else 0.0)
                for j in range(p):g[j]+=err*xs[bi][j]
            n+=1
        if not n:break
        lr=LR/math.sqrt(1.0+it/120.0)
        for j in range(p):
            g[j]=g[j]/n + L2*w[j]
            w[j]-=lr*g[j]
    return w

def rank_model(r,w,mu,sd):
    p=len(w);arr=[]
    for b in BOATS:
        x=xvec(r,b,mu,sd);s=sum(w[j]*x[j] for j in range(p));arr.append((b,s))
    arr.sort(key=lambda t:t[1],reverse=True)
    return [b for b,_ in arr],{b:s for b,s in arr}

def current_rank(r):
    return [ii(x) for x in r.get('ranked_others_v93','').split('-') if ii(x) in BOATS]

def tickets(sec_rank,third_rank,n2,n3):
    out=[]
    for a in sec_rank[:n2]:
        for b in third_rank[:n3]:
            if a!=b:out.append((a,b))
    return out

def period(r):return 'prior7' if r.get('date','')<=TRAIN_END else 'recent3'

def evaluate(q,selname,mode,n2,n3):
    qq=[r for r in q if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1 and selected(r,selname)]
    invest=ret=0; head=covered=0; ticket_n=0
    for r in qq:
        if mode=='CURRENT': sr=tr=current_rank(r)
        else: sr=[ii(x) for x in r.get('rank2_v94','').split('-') if x]; tr=[ii(x) for x in r.get('rank3_v94','').split('-') if x]
        ts=tickets(sr,tr,n2,n3);ticket_n+=len(ts);invest+=100*len(ts)
        if ii(r.get('winner'))==4:
            head+=1
            pair=(ii(r.get('second')),ii(r.get('third')))
            if pair in ts:
                covered+=1
                if ii(r.get('valid_payout'))==1:ret+=ii(r.get('payout100'))
    return {'r':len(qq),'head':head,'cov':covered,'covp':pct(covered,head),'avgpts':ticket_n/len(qq) if qq else 0,'roi':pct(ret,invest),'ret':ret,'inv':invest}

def topcov(q,selname,which,k,mode):
    qq=[r for r in q if ii(r.get('entry_gate_keep'))==1 and ii(r.get('valid_result'))==1 and selected(r,selname) and ii(r.get('winner'))==4]
    hit=0
    for r in qq:
        target=ii(r.get('second' if which==2 else 'third'))
        if mode=='CURRENT':rank=current_rank(r)
        else:rank=[ii(x) for x in r.get('rank2_v94' if which==2 else 'rank3_v94','').split('-') if x]
        if target in rank[:k]:hit+=1
    return pct(hit,len(qq)),len(qq)

def main():
    rs=read();tr=train_rows(rs);mu,sd=scalers(tr)
    w2=fit_softmax(tr,'second',mu,sd);w3=fit_softmax(tr,'third',mu,sd)
    final=[]
    for r0 in rs:
        r=dict(r0);r2,s2=rank_model(r,w2,mu,sd);r3,s3=rank_model(r,w3,mu,sd)
        r['rank2_v94']='-'.join(map(str,r2));r['rank3_v94']='-'.join(map(str,r3));r['period_v94']=period(r)
        for b in BOATS:r[f'score2_b{b}_v94']=round(s2[b],6);r[f'score3_b{b}_v94']=round(s3[b],6)
        final.append(r)
    if final:
        fs=sorted(set().union(*(r.keys() for r in final)))
        with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(final)

    featnames=list(BASEFEAT)+[f'boat{b}' for b in BOATS]
    L=['# v94 4カド 2着/3着ランキング分離検証','',
       f'- 学習: 2025-11-01〜{TRAIN_END} の4号艇頭的中のみ ({len(tr)}R)',
       f'- 評価: {TEST_START}〜2026-08-31 は重み学習に未使用',
       '- 入力特徴: v93で結果前に凍結した級別/全国/当地/モーター/枠別/ST/直前＋艇番位置。',
       '- 2着用・3着用を別々の5択softmaxで学習。L2固定、recent3でハイパーパラメータ調整なし。',
       '- 注意: モデル形式自体はv93の10か月診断から着想しているため、recent3は「parameter holdout」であり完全な未知prospectiveではない。','']
    L+=['## 学習された方向','', '|特徴|2着weight|3着weight|','|---|---:|---:|']
    for n,a,b in zip(featnames,w2,w3):L.append(f'|{n}|{a:+.3f}|{b:+.3f}|')

    L+=['','## 順位単体カバー（4号艇頭的中時）','',
        '|期間|選別|方式|2着Top1|2着Top2|2着Top3|3着Top1|3着Top2|3着Top3|3着Top4|頭的中R|','|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for per in ('prior7','recent3'):
        q=[r for r in final if r.get('period_v94')==per]
        for sel in ('BASE_A','CORR20_A','BASE_S','CORR20_S'):
            for mode in ('CURRENT','SPLIT'):
                c21,n=topcov(q,sel,2,1,mode);c22,_=topcov(q,sel,2,2,mode);c23,_=topcov(q,sel,2,3,mode)
                c31,_=topcov(q,sel,3,1,mode);c32,_=topcov(q,sel,3,2,mode);c33,_=topcov(q,sel,3,3,mode);c34,_=topcov(q,sel,3,4,mode)
                L.append(f'|{per}|{sel}|{mode}|{c21:.1f}%|{c22:.1f}%|{c23:.1f}%|{c31:.1f}%|{c32:.1f}%|{c33:.1f}%|{c34:.1f}%|{n}|')

    L+=['','## 買い目形比較（全選別Rに4頭固定で購入）','',
        '|期間|選別|方式|形|平均点数|4頭時カバー|ROI|','|---|---|---|---|---:|---:|---:|']
    shapes=((2,3),(2,4),(3,3))
    for per in ('prior7','recent3'):
        q=[r for r in final if r.get('period_v94')==per]
        for sel in ('BASE_A','CORR20_A','BASE_S','CORR20_S'):
            for n2,n3 in shapes:
                for mode in ('CURRENT','SPLIT'):
                    z=evaluate(q,sel,mode,n2,n3)
                    L.append(f'|{per}|{sel}|{mode}|2着Top{n2}×3着Top{n3}|{z["avgpts"]:.2f}|{z["covered"]}/{z["head"]} ({z["covp"]:.1f}%)|{z["roi"]:.1f}%|')

    L+=['','## 事前採否ルール',
        '- recent3のCORR20_A/Sで、同程度の平均点数においてCURRENTより「4頭時カバー率」とROIがともに改善することを第一候補条件とする。',
        '- 片方だけ改善、またはS/Aで方向不一致ならproduction採用しない。',
        '- 採用候補になっても、次はprospectiveまたは別期間walk-forwardで再確認する。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
