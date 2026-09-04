"""v104: stack prior-only value tiebreak on top of validated role-aware pair rankings.

3HEAD base: v99/v100 role-aware lambda=.2.
4C base: v96 role-aware lambda=.1 (CORR20 shadow lineage).
5HEAD: intentionally untouched (v103 value rerank hurt holdout hit rate).

Current-race final odds are never used for ranking. Value score is based only on
strictly prior-date mean final implied probabilities for exact ticket patterns.
Value lambda is chosen on Mar-May 2026 and frozen for Jun-Aug holdout.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from statistics import mean

import analyze_v99_3head_monthly_walkforward_tiebreak as h3
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v103_value_aware_opponent_ranking as vo

OUT='analysis_v104_role_value_hybrid.csv'
SUMMARY='summary_v104_role_value_hybrid.md'
VAL_START='2026-03-01';VAL_END='2026-05-31';TEST_START='2026-06-01';TEST_END='2026-08-31'
VLAMS=[0.0,0.02,0.05,0.08,0.10,0.12,0.15,0.20]
NS=(4,6,7,8,10)
A=55.;S=67.

def ff(x,d=0.):
    try:
        if x is None or str(x).strip()=='':return d
        return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.

def month_start(ds):return ds[:7]+'-01'

def pairs(head):
    bs=[b for b in range(1,7) if b!=head]
    return [(a,b) for a in bs for b in bs if a!=b]

def tstr(head,p):return f'{head}-{p[0]}-{p[1]}'

def role_orders_3(rs):
    out={}
    for month in [f'2026-{m:02d}' for m in range(3,9)]:
        start=month+'-01';tr=h3.trainrows(rs,start)
        if len(tr)<40:continue
        mu,sd=h3.scalers(tr);w2=h3.fit(tr,'second',mu,sd);w3=h3.fit(tr,'third',mu,sd)
        for r in rs:
            if r.get('date','')[:7]!=month or not h3.elig(r):continue
            s2,s3=h3.scores(r,w2,w3,mu,sd)
            ps=pairs(3);ps.sort(key=lambda p:s2[p[0]]+s3[p[1]],reverse=True)
            out[(r.get('date',''),r.get('race_code',''))]=ps
    return out

def role_orders_4(rs):
    out={}
    for month in [f'2026-{m:02d}' for m in range(3,9)]:
        tr=c4.headrows_before(rs,month)
        if len(tr)<40:continue
        mu,sd=c4.scalers(tr);w2=c4.fit(tr,'second',mu,sd);w3=c4.fit(tr,'third',mu,sd)
        for r in rs:
            if r.get('date','')[:7]!=month or not c4.eligible(r):continue
            s2,s3=c4.role_scores(r,w2,w3,mu,sd)
            ps=pairs(4);ps.sort(key=lambda p:s2[p[0]]+s3[p[1]],reverse=True)
            out[(r.get('date',''),r.get('race_code',''))]=ps
    return out

def fetch_odds(rows3,rows4):
    need=sorted({r.get('race_code','') for r in rows3+rows4 if len(r.get('race_code',''))>=12})
    from concurrent.futures import ThreadPoolExecutor,as_completed
    fmap={}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs={ex.submit(vo.fetch_final,c):c for c in need}
        done=0
        for f in as_completed(futs):
            c,d=f.result();done+=1
            if d:fmap[c]=d
            if done%100==0 or done==len(need):print('odds',done,'/',len(need),'ok',len(fmap),flush=True)
    return fmap

def prior_price_scores(rows,group,head,fmap):
    """Strict prior-date price rank for each race, based on all source rows in group."""
    bydate=defaultdict(list)
    for r in rows:bydate[r.get('date','')].append(r)
    hs=defaultdict(float);hn=defaultdict(int);out={}
    for ds in sorted(bydate):
        for r in bydate[ds]:
            ps=pairs(head);vals=[]
            for i,p in enumerate(ps):
                t=tstr(head,p);n=hn.get(t,0);v=hs.get(t,0.)/n if n>=15 else None
                vals.append((p,v,i))
            known=sorted([x for x in vals if x[1] is not None],key=lambda x:(x[1],x[2]))
            rk={p:i for i,(p,_,_) in enumerate(known)};den=max(1,len(known)-1)
            score={}
            for p,v,i in vals:
                score[p]=(1-rk[p]/den) if v is not None else None
            out[(ds,r.get('race_code',''))]=score
        # only after scoring date
        for r in bydate[ds]:
            od=fmap.get(r.get('race_code',''),{})
            for p in pairs(head):
                o=od.get(tstr(head,p))
                if o and o>1:
                    hs[tstr(head,p)]+=1/o;hn[tstr(head,p)]+=1
    return out

def hybrid(role_order,price,lam):
    rscore={p:1-i/19 for i,p in enumerate(role_order)}
    score={p:(1-lam)*rscore[p]+lam*(price.get(p) if price.get(p) is not None else rscore[p]) for p in role_order}
    return sorted(role_order,key=lambda p:(score[p],rscore[p]),reverse=True)

def mkrows(src,group,head,rolemap,pricemap,scorefield):
    out=[]
    for r in src:
        k=(r.get('date',''),r.get('race_code',''));ro=rolemap.get(k)
        if not ro:continue
        out.append({'date':r.get('date',''),'race_code':r.get('race_code',''),'group':group,'head':head,
                    'score':ff(r.get(scorefield),-999),'winner':ii(r.get('winner')),'second':ii(r.get('second')),'third':ii(r.get('third')),
                    'actual':(ii(r.get('second')),ii(r.get('third'))),'payout100':ii(r.get('payout100')),
                    'valid_payout':ii(r.get('valid_payout')),'role':ro,'price':pricemap.get(k,{}),'raw':r})
    return out

def metrics(q,lam,n,fmap):
    hit=0;ret=0;cr=[]
    for r in q:
        order=r['role'] if lam==0 else hybrid(r['role'],r['price'],lam)
        sel=order[:n]
        if r['winner']==r['head'] and r['actual'] in sel:
            hit+=1
            if r['valid_payout']:ret+=r['payout100']
        od=fmap.get(r['race_code'],{})
        if od:
            rr=vo.composite_rate(od,[tstr(r['head'],p) for p in sel])
            if rr is not None:cr.append(rr)
    inv=sum(r['valid_payout'] for r in q)*n*100
    return {'r':len(q),'hit':hit,'hitp':pct(hit,len(q)),'comp':mean(cr) if cr else 0.,'roi':pct(ret,inv) if inv else 0.,'odn':len(cr)}

def choose(rows,group):
    q=[r for r in rows if r['group']==group and VAL_START<=r['date']<=VAL_END and r['score']>=A]
    base={n:metrics(q,0,n,FMAP) for n in NS};bh=mean(x['hitp'] for x in base.values());bc=mean(x['comp'] for x in base.values())
    cand=[]
    for lam in VLAMS:
        mm={n:metrics(q,lam,n,FMAP) for n in NS};ah=mean(x['hitp'] for x in mm.values());ac=mean(x['comp'] for x in mm.values())
        md=max(base[n]['hitp']-mm[n]['hitp'] for n in NS)
        ok=ah>=bh-.5-1e-9 and md<=1.0+1e-9
        cand.append((lam,ok,ah,ac,bc-ac,md,mm))
    good=[x for x in cand if x[1]]
    best=max(good,key=lambda x:(x[4],-x[0])) if good else cand[0]
    return best,cand,base

def main():
    global FMAP
    r3=h3.read();r4=c4.read()
    FMAP=fetch_odds(r3,r4)
    ro3=role_orders_3(r3);ro4=role_orders_4(r4)
    pp3=prior_price_scores(r3,'3HEAD',3,FMAP);pp4=prior_price_scores(r4,'4C',4,FMAP)
    rows=mkrows(r3,'3HEAD',3,ro3,pp3,'score')+mkrows(r4,'4C',4,ro4,pp4,'score_CORR20_v91')
    chosen={};detail={}
    for g in ('3HEAD','4C'):
        b,c,ba=choose(rows,g);chosen[g]=b[0];detail[g]=(b,c,ba);print('chosen',g,b[:6],flush=True)
    out=[]
    for lab,cut in (('A',A),('S',S)):
        for g in ('3HEAD','4C'):
            q=[r for r in rows if r['group']==g and TEST_START<=r['date']<=TEST_END and r['score']>=cut];lam=chosen[g]
            for n in range(1,21):
                b=metrics(q,0,n,FMAP);v=metrics(q,lam,n,FMAP)
                out.append({'grade':lab,'group':g,'value_lambda':lam,'tickets_n':n,'races':len(q),'role_hit_rate_pct':b['hitp'],'hybrid_hit_rate_pct':v['hitp'],'hit_diff_pt':v['hitp']-b['hitp'],'role_comp_rate_pct':b['comp'],'hybrid_comp_rate_pct':v['comp'],'comp_reduction_pt':b['comp']-v['comp'],'role_roi_pct':b['roi'],'hybrid_roi_pct':v['roi'],'odds_races':v['odn']})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        fs=list(out[0].keys());w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(out)
    L=['# v104 役割別相手順位 × 価格補正 hybrid','',
       '- 3HEAD: v99/v100役割別20%補正を土台。','- 4C: v96役割別10%補正（CORR20 shadow）を土台。',
       '- 価格補正は当該レースの確定オッズを使わず、その日より前の同パターン確定オッズだけ。',
       '- value λはMar-Mayで選び、Jun-Augでは固定。','']
    L += ['## validation選択','|対象|value λ|平均的中率差|平均合成率低下|最大単一点数低下|','|---|---:|---:|---:|---:|']
    for g in ('3HEAD','4C'):
        b=detail[g][0];base=detail[g][2];baseh=mean(x['hitp'] for x in base.values())
        L.append(f'|{g}|{b[0]:.2f}|{b[2]-baseh:+.2f}pt|{b[4]:+.2f}pt|{-b[5]:+.2f}pt|')
    L += ['','## holdout Jun-Aug','']
    for lab in ('A','S'):
        L += [f'### {lab}以上','|対象|λ|点数|役割的中率|hybrid的中率|差|役割合成率|hybrid合成率|低下|役割ROI|hybrid ROI|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for g in ('3HEAD','4C'):
            for x in [z for z in out if z['grade']==lab and z['group']==g and z['tickets_n'] in NS]:
                L.append(f'|{g}|{x["value_lambda"]:.2f}|{x["tickets_n"]}|{x["role_hit_rate_pct"]:.1f}%|{x["hybrid_hit_rate_pct"]:.1f}%|{x["hit_diff_pt"]:+.1f}pt|{x["role_comp_rate_pct"]:.1f}%|{x["hybrid_comp_rate_pct"]:.1f}%|{x["comp_reduction_pt"]:+.1f}pt|{x["role_roi_pct"]:.1f}%|{x["hybrid_roi_pct"]:.1f}%|')
        L.append('')
    L += ['## 判定','- 的中率を維持しつつ合成率が下がる場合だけprospective候補。','- holdoutで的中率が明確に低下した場合は価格補正を捨て、役割別順位へ戻す。','- production自動採用はしない。']
    with open(SUMMARY,'w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L),flush=True)

if __name__=='__main__':main()
