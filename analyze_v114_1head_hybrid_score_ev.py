"""v114: conservative hybrid-score probability for the v109+v110 1-head model.

Why this exists
- v113 tried to turn the role model's raw conditional probabilities into exact trifecta
  probabilities.  That lost the part of v110 that actually improved ticket coverage: the
  50/50 blend of the current v51 pair score and the role score.
- v114 calibrates that *hybrid score itself* and deliberately shrinks the resulting pair
  distribution toward uniform before any odds are consulted.

NO-LEAK
- v109 head selection is fixed; current-race odds never change head or opponent scores.
- Each month's role model is fit only on races strictly before that month.
- Exact-pair calibration for a target month uses only earlier monthly-WF scored races.
- Head calibration uses only earlier months with p109 available.
- Current-race odds come only from verified od3 rows with acquisition time < cutoff.
- Final/deadline odds and payout are never selection features; payout is settlement only.

Important evaluation note
- August has already been inspected in v112/v113, so v114 treats Aug as a historical
  diagnostic, NOT a pristine model-development holdout.  Any promising result must be
  frozen prospectively from 2026-09-05 before production adoption.
"""
from __future__ import annotations

import csv, math
from collections import Counter
from datetime import date

import numpy as np
from sklearn.linear_model import LogisticRegression

from analyze_v110_1head_role_tickets import (
    read_csv, fit_roles, second_vec, third_vec, rankof, zscores
)
from analyze_v113_1head_exact_prob_ev import load_odds_map, all_odds

RAW='analysis_v108_1head_feasibility.csv'
HEAD='analysis_v109_1head_monthly_walkforward.csv'
V110='analysis_v110_1head_role_tickets.csv'
OUT='analysis_v114_1head_hybrid_score_ev.csv'
SUMMARY='summary_v114_1head_hybrid_score_ev.md'

SCORE_MONTHS=['2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
DEV_START='2026-07-19'; DEV_END='2026-07-31'
TEST_START='2026-08-01'; TEST_END='2026-08-31'
A_CUT=.65; S_CUT=.72
BOATS=list(range(2,7))
PAIRS=[(s,t) for s in BOATS for t in BOATS if t!=s]
PAIR_KEYS=[f'1-{s}-{t}' for s,t in PAIRS]
HYBRID_LAMBDA=.50
PAIR_LOGIT_C=.10
UNIFORM_SHRINK=.25
EV_GRID=[1.00,1.05,1.10,1.15,1.20,1.25,1.30,1.40,1.50,1.75,2.00]


def ff(x,d=0.0):
    try:return float(x)
    except Exception:return d

def ii(x,d=0):
    try:return int(float(x))
    except Exception:return d

def pct(n,d):return 100*n/d if d else 0.0

def clip01(x,lo=1e-6,hi=1-1e-6):return max(lo,min(hi,float(x)))
def logit(p):
    p=clip01(p);return math.log(p/(1-p))

def actual_combo(r):return (r.get('actual_combo') or '').strip()
def grade_sel(r,g):return ff(r.get('p109'),-1) >= (S_CUT if g=='S' else A_CUT)


def attach_eval_fields(raw):
    hp={(r.get('date'),r.get('race_code')):r.get('p109','') for r in read_csv(HEAD)}
    vr={(r.get('date'),r.get('race_code')):ii(r.get('v110_rank20')) for r in read_csv(V110)}
    out=[]
    for r0 in raw:
        r=dict(r0);key=(r.get('date'),r.get('race_code'))
        r['p109']=hp.get(key,'')
        r['_v110_rank20']=vr.get(key,0)
        out.append(r)
    return out


def month_hybrid_scores(src,mo):
    first=date.fromisoformat(mo+'-01')
    train=[r for r in src if date.fromisoformat(r['date'])<first]
    test=[dict(r) for r in src if r.get('month')==mo and ii(r.get('valid_result'))==1]
    if not test:return []
    m2,m3,ntrain=fit_roles(train)

    x2=[];x3=[]
    for r in test:
        for b in BOATS:x2.append(second_vec(r,b))
        for s,t in PAIRS:x3.append(third_vec(r,s,t))
    p2=m2.predict_proba(np.asarray(x2,dtype=float))[:,1].reshape(len(test),5)
    p3=m3.predict_proba(np.asarray(x3,dtype=float))[:,1].reshape(len(test),20)

    out=[]
    for i,r in enumerate(test):
        a2=np.maximum(p2[i],1e-12);a2=a2/a2.sum()
        role_raw={};off=0
        for si,s in enumerate(BOATS):
            rem=[t for t in BOATS if t!=s]
            a3=np.maximum(p3[i,off:off+4],1e-12);off+=4;a3=a3/a3.sum()
            for j,t in enumerate(rem):
                role_raw[f'1-{s}-{t}']=math.log(max(float(a2[si]*a3[j]),1e-12))

        cur=[];role=[];keys=[]
        for s,t in PAIRS:
            k=f'1-{s}-{t}';keys.append(k)
            cur.append(-(rankof(r,s)+.7*rankof(r,t)))
            role.append(role_raw[k])
        cz=zscores(cur);rz=zscores(role)
        hs={k:(1-HYBRID_LAMBDA)*c+HYBRID_LAMBDA*q for k,c,q in zip(keys,cz,rz)}
        z=dict(r);z['_hybrid_score']=hs;z['_role_train_headwins']=ntrain
        out.append(z)
    return out


def build_scored(src):
    out=[]
    for mo in SCORE_MONTHS:out.extend(month_hybrid_scores(src,mo))
    return out


class HeadCal:
    """Regularized Platt on p109, fitted only on earlier months."""
    def __init__(self):self.m=None
    def fit(self,rs,g):
        q=[r for r in rs if grade_sel(r,g) and ff(r.get('p109'),-1)>=0]
        if len(q)<200:raise RuntimeError(f'not enough head calibration rows: {len(q)}')
        X=np.asarray([[logit(ff(r.get('p109')))] for r in q],dtype=float)
        y=np.asarray([ii(r.get('head_hit')) for r in q],dtype=int)
        self.m=LogisticRegression(C=1.0,max_iter=1200,solver='lbfgs').fit(X,y)
        return len(q),int(y.sum()),float(np.mean([ff(r.get('p109')) for r in q])),float(y.mean())
    def predict(self,p):
        return float(self.m.predict_proba(np.asarray([[logit(p)]],dtype=float))[0,1])


class HybridPairCal:
    """Calibrate the v110 hybrid score, then normalize and shrink to uniform."""
    def __init__(self):self.m=None
    def fit(self,rs):
        X=[];y=[];heads=0
        for r in rs:
            if ii(r.get('head_hit'))!=1:continue
            act=actual_combo(r)
            hs=r.get('_hybrid_score') or {}
            if act not in hs:continue
            heads+=1
            for k in PAIR_KEYS:
                X.append([float(hs[k])]);y.append(int(k==act))
        if heads<150:raise RuntimeError(f'not enough pair calibration heads: {heads}')
        self.m=LogisticRegression(C=PAIR_LOGIT_C,max_iter=1200,solver='lbfgs').fit(
            np.asarray(X,dtype=float),np.asarray(y,dtype=int)
        )
        return heads,len(X)
    def transform(self,hs):
        x=np.asarray([[float(hs[k])] for k in PAIR_KEYS],dtype=float)
        q=self.m.predict_proba(x)[:,1]
        q=np.maximum(q,1e-12);q=q/q.sum()
        q=(1-UNIFORM_SHRINK)*q + UNIFORM_SHRINK*(1/20)
        q=q/q.sum()
        return {k:float(v) for k,v in zip(PAIR_KEYS,q)}


def prior_scored(scored,target_mo):
    first=date.fromisoformat(target_mo+'-01')
    return [r for r in scored if date.fromisoformat(r['date'])<first]


def fit_target_calibrators(scored,target_mo,g):
    tr=prior_scored(scored,target_mo)
    pc=HybridPairCal();phs=pc.fit(tr)
    # p109 exists only on Jun-Aug monthly-WF rows; head calibration therefore uses the
    # strictly earlier p109-bearing months available at evaluation time.
    hp=HeadCal();hhs=hp.fit(tr,g)
    return hp,pc,{
        'head_rows':hhs[0],'head_hits':hhs[1],'avg_p109':hhs[2],'actual_head':hhs[3],
        'pair_head_rows':phs[0],'pair_examples':phs[1]
    }


def enrich(scored,start,end,g,odds_map,leads,cache):
    out=[]
    for r in scored:
        ds=r.get('date','')
        if not(start<=ds<=end) or not grade_sel(r,g) or ii(r.get('valid_payout'))!=1:continue
        orow=odds_map.get(r.get('race_code',''));od=all_odds(orow) if orow else None
        if od is None:continue
        mo=ds[:7];key=(mo,g)
        if key not in cache:cache[key]=fit_target_calibrators(scored,mo,g)
        hp,pc,stats=cache[key]
        ph=hp.predict(ff(r.get('p109')))
        pairp=pc.transform(r['_hybrid_score'])
        probs={k:ph*pairp[k] for k in PAIR_KEYS}
        z=dict(r);z['_phead_cal']=ph;z['_pair_probs']=pairp;z['_probs']=probs
        z['_odds']=od;z['_lead']=leads.get(r.get('race_code',''),0.0)
        out.append(z)
    return out


def metric(rs,thr):
    bet_r=tickets=hits=ret=0;hist=Counter();evsum=0.0;fixed_hits=fixed_ret=0
    for r in rs:
        act=actual_combo(r);pr=r['_probs'];od=r['_odds']
        if 1<=ii(r.get('_v110_rank20'))<=7:
            fixed_hits+=1;fixed_ret+=ii(r.get('payout100'))
        sel=[k for k in PAIR_KEYS if pr[k]*od[k]>=thr]
        hist[len(sel)]+=1
        if not sel:continue
        bet_r+=1;tickets+=len(sel);evsum+=sum(pr[k]*od[k] for k in sel)
        if act in sel:hits+=1;ret+=ii(r.get('payout100'))
    return {
        'odds_races':len(rs),'bet_races':bet_r,'bet_race_pct':pct(bet_r,len(rs)),
        'tickets':tickets,'avg_tickets_bet':tickets/bet_r if bet_r else 0.0,
        'hits':hits,'hit_rate_bet_pct':pct(hits,bet_r),'roi_pct':pct(ret,tickets*100),
        'avg_selected_model_ev':evsum/tickets if tickets else 0.0,
        'fixed7_hits':fixed_hits,'fixed7_hit_pct':pct(fixed_hits,len(rs)),
        'fixed7_roi_pct':pct(fixed_ret,len(rs)*700),'point_hist':hist,
    }

def hist_text(h):return ', '.join(f'{k}点:{v}R' for k,v in sorted(h.items()) if v)


def main():
    raw=attach_eval_fields(read_csv(RAW))
    scored=build_scored(raw)
    need={r.get('date','') for r in scored if DEV_START<=r.get('date','')<=TEST_END}
    odds_map,leads=load_odds_map(need)
    cache={};dev={};test={}
    for g in ('A','S'):
        dev[g]=enrich(scored,DEV_START,DEV_END,g,odds_map,leads,cache)
        test[g]=enrich(scored,TEST_START,TEST_END,g,odds_map,leads,cache)

    out=[]
    for phase,by in [('DEV',dev),('AUG_DIAGNOSTIC',test)]:
        for g in ('A','S'):
            for th in EV_GRID:
                m=metric(by[g],th)
                out.append({'phase':phase,'grade':g,'ev_threshold':th,
                            **{k:v for k,v in m.items() if k!='point_hist'},
                            'point_hist':';'.join(f'{k}:{v}' for k,v in sorted(m['point_hist'].items()))})
    with open(OUT,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)

    used=[v for v in leads.values() if v is not None]
    L=['# v114 1号艇 hybrid-score probability × conservative EV diagnostic','',
       '- 頭は **v109固定**。相手確率は、v110で実際に効いた **current v51 score 50% + role score 50%** のhybrid scoreから作る。',
       f'- hybrid score→pair確率は、過去月だけで正則化Platt (`C={PAIR_LOGIT_C:.2f}`)し、さらに **{UNIFORM_SHRINK*100:.0f}%を一様分布へ縮小**。高EV側の過大確率を抑える。',
       '- 各月role学習・pair校正・head校正は対象月より前だけ。現在レースod3は買い判定だけに使い、最終/締切オッズは不使用。',
       '- **注意: Augustはv112/v113で既に結果を見ているため、v114では pristine holdout と呼ばない。歴史診断のみ。良くても2026-09-05以降のprospective shadowが必須。','']
    if used:
        L += [f'- 利用pre-close snapshot: **{len(used)}R** / 平均 **{sum(used)/len(used):.2f}分前**。','']

    L += ['## prior-only calibration state','|対象月|層|head学習R|head実1着率|平均p109|pair headR|pair examples|','|---|---|---:|---:|---:|---:|---:|']
    for mo in ('2026-07','2026-08'):
        for g in ('A','S'):
            c=cache.get((mo,g))
            if c:
                s=c[2]
                L.append(f'|{mo}|{g}|{s["head_rows"]:,}|{s["actual_head"]*100:.1f}%|{s["avg_p109"]*100:.1f}%|{s["pair_head_rows"]:,}|{s["pair_examples"]:,}|')

    for title,by in [('Jul19-31 diagnostic',dev),('August historical diagnostic',test)]:
        L += ['',f'## {title}','|EV閾値|A betR|A平均点|A ROI|S betR|S平均点|S ROI|','|---:|---:|---:|---:|---:|---:|---:|']
        for th in EV_GRID:
            ma=metric(by['A'],th);ms=metric(by['S'],th)
            L.append(f'|{th:.2f}|{ma["bet_races"]}|{ma["avg_tickets_bet"]:.2f}|{ma["roi_pct"]:.1f}%|{ms["bet_races"]}|{ms["avg_tickets_bet"]:.2f}|{ms["roi_pct"]:.1f}%|')

    # Robust historical-candidate rule: not an adoption rule. Require two adjacent EV
    # thresholds in the practical 1.05..1.50 range with ROI>=100 for both grades and
    # enough volume.  This deliberately avoids selecting a single lucky threshold.
    practical=[x for x in EV_GRID if 1.05<=x<=1.50]
    good=[]
    for th in practical:
        ma=metric(test['A'],th);ms=metric(test['S'],th)
        ok=(ma['bet_races']>=300 and ms['bet_races']>=180 and
            ma['avg_tickets_bet']<=7 and ms['avg_tickets_bet']<=7 and
            ma['roi_pct']>=100 and ms['roi_pct']>=100)
        good.append((th,ok))
    adjacent=any(good[i][1] and good[i+1][1] for i in range(len(good)-1))
    m110a=metric(test['A'],1.00);m110s=metric(test['S'],1.00)
    # fixed7 fields are independent of EV threshold; use any metric row.
    L += ['','## v114判定',
          f'- August v110固定7点: A 的中 **{m110a["fixed7_hit_pct"]:.1f}%** / ROI **{m110a["fixed7_roi_pct"]:.1f}%**、S 的中 **{m110s["fixed7_hit_pct"]:.1f}%** / ROI **{m110s["fixed7_roi_pct"]:.1f}%**。',
          f'- 実用帯EV 1.05〜1.50で「A/SともROI100%以上」が2つ以上連続: **{"YES" if adjacent else "NO"}**。',
          f'- **V114 HISTORICAL CANDIDATE = {"YES" if adjacent else "NO"}**',
          '- YESでも本番採用不可。次はv115として2026-09-05以降を完全prospective shadowに固定する。',
          '- NOならv109/v110は維持し、オッズEV化は一旦不採用。']
    open(SUMMARY,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
