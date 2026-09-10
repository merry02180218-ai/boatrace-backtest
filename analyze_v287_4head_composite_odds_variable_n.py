#!/usr/bin/env python3
"""v287: variable ticket count from composite odds for independent 4-head models.

Purpose
-------
Use the already-frozen composite-odds target 10.5 from HEAD4_V268/V273, but
replace the old v96-lineage opponent order with the independent v283/v284 order.
For every S+A BET race, including races boat 4 later loses, infer the opponent
order first, then use the archived odds row to choose N before settlement.

Policies
--------
For each candidate N, composite odds = 1 / sum(1 / ticket_odds).
Choose N minimizing abs(composite_odds - 10.5), tie -> smaller N.
Candidate sets:
  ODDS_4610_T10.5 : N in {4,6,8,10}
  ODDS_2_10_T10.5 : N in 2..10
  ODDS_2_20_T10.5 : N in 2..20

Discipline
----------
* Target 10.5 is inherited unchanged from the pre-September frozen v268/v273
  ticket rule; it is NOT tuned on Apr-Jun here.
* v283/v284 are completely independent of v96 for ranking.
* N selection uses odds, but never result/payout.
* Every evaluable BET race costs exactly 10,000 yen; miss = payout 0.
* Inverse-odds Dutch, 100-yen Hamilton rounding.
* Archived odds are a retrospective proxy, not immutable pre-deadline snapshots.
* Jul/Aug excluded; September outcomes are not read.
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd
from scipy.special import logsumexp

import analyze_v251_4head_newroi_bridge as v251
import analyze_v274_4head_opponent_feature_audit as v274
import analyze_v279_4head_opponent_listwise_rebuild as v279
import analyze_v281_4head_opponent_third_scenario as v281
import analyze_v282_4head_conditional_third as v282
import analyze_v283_4head_conditional_pair_order as v283
import analyze_v284_4head_conditional_third_regime as v284
import analyze_v285_4head_independent_newroi_topn as v285
import analyze_v286_4head_variable_n_dutch as v286
from analyze_v205_3head_operational_replay import load_odds

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis_v287_4head_composite_odds_variable_n.csv'
MONTH=ROOT/'analysis_v287_4head_composite_odds_variable_n_monthly.csv'
DETAIL=ROOT/'analysis_v287_4head_composite_odds_variable_n_detail.csv'
VERIFY=ROOT/'analysis_v287_4head_composite_odds_reinfer_verify.csv'
SUM=ROOT/'summary_v287_4head_composite_odds_variable_n.md'
BANK=10000
TARGET=10.5
HOLD=('2026-04','2026-05','2026-06')
POLICIES={
    'ODDS_4610_T10.5':(4,6,8,10),
    'ODDS_2_10_T10.5':tuple(range(2,11)),
    'ODDS_2_20_T10.5':tuple(range(2,21)),
}


def ii(x,d=0):
    try:return int(float(x))
    except:return d


def actual_map():
    return v286.actual_map()


def odds_row(oi,code):
    if code not in oi.index:return None
    r=oi.loc[code]
    return r.iloc[-1] if isinstance(r,pd.DataFrame) else r


def comp_for(order,n,odr):
    vals=[];tickets=[]
    for s,t in order[:int(n)]:
        ticket=f'4-{s}-{t}'
        try:v=float(odr[ticket])
        except:return None
        if not np.isfinite(v) or v<=1:return None
        vals.append(v);tickets.append(ticket)
    if len(vals)!=int(n):return None
    comp=1.0/sum(1.0/x for x in vals)
    return float(comp),tickets,vals


def choose_by_target(order,odr,cands):
    rows=[]
    for n in cands:
        z=comp_for(order,n,odr)
        if z is None:return None
        comp,tickets,vals=z
        rows.append((abs(comp-TARGET),int(n),comp,tickets,vals))
    rows.sort(key=lambda x:(x[0],x[1]))
    _,n,comp,tickets,vals=rows[0]
    return n,comp,tickets,vals,[(x[1],x[2]) for x in rows]


def test_long_for_portfolio(d,port,train_base):
    # Build five candidate-opponent rows for every portfolio race, regardless of
    # the eventual winner. No result is used to construct these feature rows.
    z=v286.allrace_long(d,set(port.race_code.astype(str)))
    z=v281.add_scenario(z)
    relseed=[c for c in list(v279.ABILITY)+list(v279.PLAYER)+list(v279.PRIOR_HINTS)+list(v279.START_HINTS)+list(v279.POSITION)+list(v279.CURRENT) if c in z]
    z=v279.add_relative(z,relseed)

    # v282.make_pairs needs one y2/y3 solely to form four candidates per possible
    # second boat. Dummy labels are never used for test scoring or ordering.
    dummy=z.copy()
    dummy['y2']=(dummy.boat.astype(int)==1).astype(int)
    dummy['y3']=(dummy.boat.astype(int)==2).astype(int)
    pairs,_=v282.make_pairs(dummy,train_base)
    return z,pairs


def second_prob_for_month(trainz,test,base,mon):
    tr=trainz[trainz.month<mon].copy();te=test[test.month==mon].copy()
    fs=base['PLAYER_START'];use=v279.good_features(tr,fs)
    m=v279.ListwiseSoftmax(10.0).fit(tr,use,'y2');te=te.copy();te['s2']=m.score(te)
    out={}
    for code,g in te.groupby('race_code'):
        if len(g)==5:out[str(code).zfill(12)]=v279.probs_within_race(g,'s2')
    return out


def cond_probs_from_scored(te):
    out={}
    for code,g in te.groupby('race_code'):
        pc={}
        for s,gs in g.groupby('second_boat'):
            ss=gs.sc.to_numpy(float);pp=np.exp(ss-logsumexp(ss))
            for t,p in zip(gs.third_boat.astype(int),pp):pc[(int(s),int(t))]=float(p)
        if len(pc)==20:out[str(code).zfill(12)]=pc
    return out


def cond283_for_month(trainpairs,testpairs,fams,mon):
    tr=trainpairs[(trainpairs.month<mon)&(trainpairs.train_group==1)].copy()
    te=testpairs[testpairs.month==mon].copy()
    use=v282.good(tr,fams['COND_BASE']);m=v282.ListwiseN(.3).fit(tr,use);te['sc']=m.score(te)
    return cond_probs_from_scored(te)


def cond284_for_month(trainpairs,testpairs,fams,mon):
    tr0=trainpairs[(trainpairs.month<mon)&(trainpairs.train_group==1)].copy()
    te=testpairs[testpairs.month==mon].copy()
    guse=v282.good(tr0,fams['COND_BASE']);gm=v282.ListwiseN(.3).fit(tr0,guse)
    models={}
    for rg in ('INNER','OUTER'):
        trg=tr0[tr0.second_boat.map(v284.side)==rg].copy()
        if trg.race_code.nunique()>=v284.MIN_REGIME_RACES:
            use=v282.good(trg,fams['COND_COMPACT']);models[rg]=v282.ListwiseN(.3).fit(trg,use)
        else:models[rg]=gm
    scores=[]
    for _,r in te.iterrows():
        m=models[v284.side(r.second_boat)]
        scores.append(float(m.score(pd.DataFrame([r]))[0]))
    te['sc']=scores
    return cond_probs_from_scored(te)


def infer_orders(port):
    trainz,base=v282.prep();trainpairs,fams=v282.make_pairs(trainz,base)
    d,_=v279.build_source();d=d[d._date<pd.Timestamp('2026-07-01')].copy();d['date']=d.date.astype(str)
    test,testpairs=test_long_for_portfolio(d,port,base)
    orders={'v283':{},'v284':{}}
    for mon in HOLD:
        p2=second_prob_for_month(trainz,test,base,mon)
        pc283=cond283_for_month(trainpairs,testpairs,fams,mon)
        pc284=cond284_for_month(trainpairs,testpairs,fams,mon)
        codes=set(test.loc[test.month==mon,'race_code'].astype(str))
        for code in codes:
            code=str(code).zfill(12)
            if code not in p2 or code not in pc283 or code not in pc284:continue
            orders['v283'][code]=v283.order_policy(p2[code],pc283[code],.60,'TOP2XTOP2',1.50)
            orders['v284'][code]=v284.order_policy(p2[code],pc284[code],.60,'TOP2XTOP2')
    missing=set(port.race_code.astype(str))-set(orders['v283'])
    missing2=set(port.race_code.astype(str))-set(orders['v284'])
    if missing or missing2:raise RuntimeError(f'missing reinferred orders v283={len(missing)} v284={len(missing2)}')
    return orders


def settle_tickets(tickets,odr,actual):
    z=v251.settle('',tickets,odr,actual)
    if z is None:return None
    hit,ret,comp=z
    return int(hit),float(ret),float(comp)


def agg(g):
    cost=len(g)*BANK;ret=float(g.return_yen.sum())
    dist=','.join(f'{int(n)}:{int(c)}' for n,c in g.n.value_counts().sort_index().items())
    return {'R':len(g),'avg_n':g.n.mean(),'n_dist':dist,'head4_wins':int(g.head4_win.sum()),'hits':int(g.hit.sum()),
            'hit_rate_pct':100*g.hit.mean(),'avg_selected_comp':g.selected_comp.mean(),'avg_abs_target_gap':g.target_gap.mean(),
            'return_yen':ret,'profit_yen':ret-cost,'roi_pct':100*ret/cost if cost else np.nan}


def main():
    port=v286.hold_portfolio().copy();port['race_code']=port.race_code.astype(str).str.zfill(12)
    orders=infer_orders(port)
    am=actual_map();od=load_odds();oi=od.set_index('race_code',drop=False) if not od.empty else pd.DataFrame()

    # Odds are part of N selection, so require an odds row for every included BET
    # race, not only boat-4 wins. Missing-odds races are excluded solely by odds
    # availability and are reported explicitly.
    eligible=[];missing_odds=[]
    for _,r in port.iterrows():
        code=str(r.race_code);a=am.get(code);odr=odds_row(oi,code)
        if not a or a[3]!=1:continue
        if odr is None:missing_odds.append(code);continue
        eligible.append((r,a,odr))
    if len(eligible)<.95*len(port):raise RuntimeError(f'too much odds missing: {len(missing_odds)}/{len(port)}')

    rows=[]
    for r,a,odr in eligible:
        code=str(r.race_code)
        for model in ('v283','v284'):
            order=orders[model][code]
            for policy,cands in POLICIES.items():
                ch=choose_by_target(order,odr,cands)
                if ch is None:raise RuntimeError(f'invalid odds for {code} {model} {policy}')
                n,selcomp,tickets,vals,curve=ch
                st=settle_tickets(tickets,odr,a)
                if st is None:raise RuntimeError(f'settle failed {code} {model} {policy}')
                hit,ret,realcomp=st
                rows.append({'date':r.date,'month':r.month,'race_code':code,'layer':r.layer,'model':model,'policy':policy,'n':n,
                             'winner':a[0],'second':a[1],'third':a[2],'head4_win':int(a[0]==4),'hit':hit,'return_yen':ret,
                             'profit_yen':ret-BANK,'selected_comp':selcomp,'settle_comp':realcomp,'target_gap':abs(selcomp-TARGET),
                             'tickets':'|'.join(tickets),'comp_curve':'|'.join(f'{nn}:{cc:.6f}' for nn,cc in sorted(curve))})
            # Same-path fixed baselines for verification against v285.
            for policy,n in [('FIXED_N4',4),('FIXED_N10',10)]:
                z=comp_for(order,n,odr)
                if z is None:raise RuntimeError(f'invalid fixed odds {code}')
                comp,tickets,_=z;hit,ret,realcomp=settle_tickets(tickets,odr,a)
                rows.append({'date':r.date,'month':r.month,'race_code':code,'layer':r.layer,'model':model,'policy':policy,'n':n,
                             'winner':a[0],'second':a[1],'third':a[2],'head4_win':int(a[0]==4),'hit':hit,'return_yen':ret,
                             'profit_yen':ret-BANK,'selected_comp':comp,'settle_comp':realcomp,'target_gap':abs(comp-TARGET),
                             'tickets':'|'.join(tickets),'comp_curve':''})
    z=pd.DataFrame(rows);z.to_csv(DETAIL,index=False)

    # Verify independent reinference reproduces v285 fixed baselines on the same
    # odds-covered race set. With full 100-race coverage it should match exactly.
    vr=[]
    old=pd.read_csv(v285.OUT)
    for model,n,pol in [('v283',4,'FIXED_N4'),('v284',10,'FIXED_N10')]:
        q=z[(z.model==model)&(z.policy==pol)];newret=q.return_yen.sum();newroi=100*newret/(len(q)*BANK)
        oo=old[(old.scope=='S+A')&(old.model==model)&(old.n==n)]
        oldret=float(oo.return_yen.iloc[0]) if len(oo) else np.nan;oldroi=float(oo.roi_pct.iloc[0]) if len(oo) else np.nan
        vr.append({'model':model,'n':n,'R':len(q),'new_return':newret,'old_v285_return':oldret,'return_diff':newret-oldret,
                   'new_roi':newroi,'old_v285_roi':oldroi,'roi_diff':newroi-oldroi})
    V=pd.DataFrame(vr);V.to_csv(VERIFY,index=False)
    if len(port)==100 and len(missing_odds)==0 and (V.return_diff.abs()>1e-6).any():
        raise RuntimeError('reinference verification does not reproduce v285 fixed baseline')

    out=[]
    use=z[z.policy.str.startswith('ODDS_')]
    for (model,policy),g in use.groupby(['model','policy']):
        out.append({'scope':'S+A','model':model,'policy':policy,**agg(g)})
        for layer,gg in g.groupby('layer'):out.append({'scope':layer,'model':model,'policy':policy,**agg(gg)})
    O=pd.DataFrame(out);O.to_csv(OUT,index=False)

    mr=[]
    for (model,policy,mon),g in use.groupby(['model','policy','month']):mr.append({'model':model,'policy':policy,'month':mon,**agg(g)})
    M=pd.DataFrame(mr);M.to_csv(MONTH,index=False)

    L=['# v287 composite-odds variable N — independent 4-head opponents','',
       f'- Target composite odds: **{TARGET:.1f}**, inherited unchanged from frozen v268/v273 before September outcomes.',
       '- For every BET race, opponent order is inferred first, then N is chosen from the odds row; result/payout is not used in N selection.',
       '- Composite odds = 1 / sum(1/ticket_odds). Exact 10,000-yen inverse-odds Dutch, 100-yen Hamilton rounding.',
       '- v283/v284 are independent opponent models; v96 is not used in ranking or N selection.',
       '- Archived odds are retrospective proxy only, not immutable pre-deadline LIVE snapshots.',
       '- Jul/Aug excluded; September outcomes not read.','',
       f'- portfolio races: **{len(port)}**',f'- odds-evaluable races: **{len(eligible)}**',f'- missing odds rows: **{len(missing_odds)}**','',
       '## Reinference verification vs v285','',
       '|model|fixed N|R|new return|v285 return|diff|new ROI|v285 ROI|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for _,r in V.iterrows():L.append(f'|{r.model}|{int(r.n)}|{int(r.R)}|{r.new_return:.0f}|{r.old_v285_return:.0f}|{r.return_diff:+.0f}|{r.new_roi:.2f}%|{r.old_v285_roi:.2f}%|')
    L += ['','## Apr-Jun S+A aggregate','',
          '|model|policy|R|avg N|N distribution|hits|avg comp|avg |comp-10.5||return|profit|ROI|',
          '|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|']
    for _,r in O[O.scope=='S+A'].sort_values(['model','policy']).iterrows():
        L.append(f'|{r.model}|{r.policy}|{int(r.R)}|{r.avg_n:.2f}|{r.n_dist}|{int(r.hits)}|{r.avg_selected_comp:.3f}|{r.avg_abs_target_gap:.3f}|{r.return_yen:.0f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    L += ['','## S / A separately','',
          '|scope|model|policy|R|avg N|hits|profit|ROI|','|---|---|---|---:|---:|---:|---:|---:|']
    for _,r in O[O.scope.isin(['S','A'])].sort_values(['scope','model','policy']).iterrows():
        L.append(f'|{r.scope}|{r.model}|{r.policy}|{int(r.R)}|{r.avg_n:.2f}|{int(r.hits)}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    L += ['','## Monthly S+A','',
          '|month|model|policy|R|avg N|hits|avg comp|profit|ROI|','|---|---|---|---:|---:|---:|---:|---:|---:|']
    for _,r in M.sort_values(['model','policy','month']).iterrows():
        L.append(f'|{r.month}|{r.model}|{r.policy}|{int(r.R)}|{r.avg_n:.2f}|{int(r.hits)}|{r.avg_selected_comp:.3f}|{r.profit_yen:+.0f}|{r.roi_pct:.2f}%|')
    best=O[O.scope=='S+A'].sort_values(['roi_pct','R'],ascending=[False,False]).iloc[0]
    L += ['','## Descriptive result','',
          f'- Best of these frozen-target odds-variable policies: **{best.model} / {best.policy} = ROI {best.roi_pct:.2f}%**, avg N {best.avg_n:.2f}, profit {best.profit_yen:+.0f} yen.',
          '- This uses archived historical odds to choose N and settle the same races, so it is development evidence only. For prospective use, N must be chosen from an immutable pre-deadline odds snapshot.']
    SUM.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
