#!/usr/bin/env python3
from __future__ import annotations
"""v389: ticket-policy consensus rescue for the frozen 1HEAD added71 band.

LIVE165 is untouched. Added candidates are H078_M375 minus LIVE165. Formal
tickets remain HYBRID after current wall3+5>6 reranks. Alternative strategies
are used only to measure result-free consensus/confidence. Candidate choice and
LOMO use Feb-Jun DEV only; Jul-Aug SUPPORT is evaluated after freeze.
"""
from pathlib import Path
import argparse,json,math,pickle
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v389-added71-ticket-consensus'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
QS=(.35,.45,.55,.65,.75)
ALT=('JOINT','TOP2XTOP2','SECOND1X3','SECOND3X1')
FAMILIES={
  'CONSENSUS': {'consensus_mean':1.0},
  'SUPPORTED_SLOTS': {'supported_slots':1.0},
  'CONSENSUS_MASS': {'consensus_mean':1.0,'formal_mass':0.75},
  'CONSENSUS_RISK': {'consensus_mean':1.0,'outside_risk':-0.75},
  'FULL': {'consensus_mean':1.0,'supported_slots':0.75,'formal_mass':0.5,'outside_risk':-0.5},
}

def formal_and_features(r,payout):
    p2,pc=v365.formal_post_five6(r)
    prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    formal_order=v299.STRATEGIES['HYBRID'](p2,pc,prob)
    formal=formal_order[:3]
    if len(formal)!=3 or len(set(formal))!=3: raise RuntimeError('bad formal tickets')
    formal_set=set(formal)
    alt_sets={}
    overlaps=[]
    support_count={x:0 for x in formal}
    for name in ALT:
        order=v299.STRATEGIES[name](p2,pc,prob)
        s=set(order[:3]); alt_sets[name]=s
        ov=len(formal_set&s); overlaps.append(ov/3.0)
        for x in formal:
            support_count[x]+=int(x in s)
    outside=[x for x in prob if x not in formal_set]
    weakest=min(float(prob[x]) for x in formal)
    bestout=max(float(prob[x]) for x in outside) if outside else 0.0
    ts=';'.join(f'1-{s}-{t}' for s,t in formal)
    actual=str(r['actual_combo'])
    return {
      'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),
      'head_hit':int(r['head_hit']),'actual_combo':actual,'tickets':ts,
      'hit':int(actual in ts.split(';')),'payout100':int(payout),
      'p_head':float(r['p_head']),'opp_mass':float(r['opp_mass']),
      'v332_score':float(r['v332_score']),
      'consensus_mean':float(np.mean(overlaps)),
      'consensus_min':float(min(overlaps)),
      'agree_joint':float(overlaps[0]),
      'agree_top2x2':float(overlaps[1]),
      'agree_second1x3':float(overlaps[2]),
      'agree_second3x1':float(overlaps[3]),
      'supported_slots':float(sum(v>=2 for v in support_count.values())/3.0),
      'all_alt_supported_slots':float(sum(v==len(ALT) for v in support_count.values())/3.0),
      'formal_mass':float(sum(prob[x] for x in formal)),
      'weakest_formal_prob':weakest,
      'best_outside_prob':bestout,
      'outside_risk':float(bestout/max(weakest,1e-12)),
    }

def metric(z):
    if len(z)==0:
        return {'R':0,'head':0,'head_rate':0.0,'hits':0,'exact3_rate':0.0,'stake':0,'return':0,'profit':0,'roi':0.0}
    ret=int(z.loc[z.hit.eq(1),'payout100'].sum()); st=len(z)*300
    return {'R':int(len(z)),'head':int(z.head_hit.sum()),'head_rate':float(z.head_hit.mean()),
            'hits':int(z.hit.sum()),'exact3_rate':float(z.hit.mean()),'stake':int(st),
            'return':ret,'profit':int(ret-st),'roi':float(ret/st)}

def combine(a,b): return pd.concat([a,b],ignore_index=True)

def fit_score(train,test,weights):
    mu={c:float(train[c].mean()) for c in weights}
    sd={c:float(train[c].std(ddof=0)) for c in weights}
    for c in weights:
        if not math.isfinite(sd[c]) or sd[c]<1e-12: sd[c]=1.0
    den=sum(abs(float(w)) for w in weights.values())
    def f(df):
        s=np.zeros(len(df),dtype=float)
        for c,w in weights.items():
            s += float(w)*((df[c].to_numpy(float)-mu[c])/sd[c])
        return s/den
    return f(train),f(test),{'mean':mu,'sd':sd}

def lomo_for(add,fam,q):
    w=FAMILIES[fam]; rec=[]; pooled=[]
    for hold in DEV:
        tr=add[add.month.isin([m for m in DEV if m!=hold])].copy()
        te=add[add.month.eq(hold)].copy()
        st,se,_=fit_score(tr,te,w); th=float(np.quantile(st,q))
        sel=te[se>=th-1e-12].copy(); m=metric(sel)
        rec.append({'holdout':hold,'selected_R':m['R'],'hits':m['hits'],
                    'exact3_rate':m['exact3_rate'],'roi':m['roi'],'profit':m['profit']})
        pooled.append(sel)
    p=pd.concat(pooled,ignore_index=True) if pooled else add.iloc[0:0].copy()
    pm=metric(p)
    nonneg=sum(int(x['roi']>=1.0-1e-12) for x in rec if x['selected_R']>0)
    active=sum(int(x['selected_R']>0) for x in rec)
    worst=min((x['roi'] for x in rec if x['selected_R']>0),default=0.0)
    return rec,{'lomo_R':pm['R'],'lomo_roi':pm['roi'],'lomo_profit':pm['profit'],
                'lomo_exact3_rate':pm['exact3_rate'],'lomo_nonnegative_months':nonneg,
                'lomo_active_months':active,'lomo_worst_roi':worst}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--prepared',required=True,type=Path); a=ap.parse_args()
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise RuntimeError('September guard disabled')
    x=pickle.load(a.prepared.open('rb')); rr=x['rows']
    if len(rr['LIVE165'])!=165 or len(rr['H078_M375'])!=236: raise RuntimeError('universe drift')
    live_ids={str(r['race_code']).zfill(12) for r in rr['LIVE165']}
    broad={str(r['race_code']).zfill(12):r for r in rr['H078_M375']}
    added=[r for c,r in broad.items() if c not in live_ids]
    if len(added)!=71: raise RuntimeError(f'added band drift {len(added)}')
    union=list({str(r['race_code']).zfill(12):r for r in list(rr['LIVE165'])+added}.values())
    v365.install_payout_cache(union); payouts=v365.payouts_for(union)
    add=pd.DataFrame([formal_and_features(r,payouts[str(r['race_code']).zfill(12)]) for r in added])
    live=pd.DataFrame([formal_and_features(r,payouts[str(r['race_code']).zfill(12)]) for r in rr['LIVE165']])
    if any(add.race_code.str[:8].ge('20260901')): raise RuntimeError('September entered')

    adev=add[add.month.isin(DEV)].copy(); asup=add[add.month.isin(SUP)].copy()
    ldev=live[live.month.isin(DEV)].copy(); lsup=live[live.month.isin(SUP)].copy()
    base={'live_all':metric(live),'live_dev':metric(ldev),'live_support':metric(lsup),
          'added_all':metric(add),'added_dev':metric(adev),'added_support':metric(asup)}
    if (base['live_all']['R'],base['live_all']['hits'],base['live_all']['return'])!=(165,87,63700):
        raise RuntimeError(f'LIVE sentinel drift {base["live_all"]}')
    if (base['added_all']['R'],base['added_all']['hits'],base['added_all']['return'])!=(71,33,21360):
        raise RuntimeError(f'added sentinel drift {base["added_all"]}')

    grid=[]; cache={}; lomo_rows=[]
    for fam,w in FAMILIES.items():
        sd,sa,pars=fit_score(adev,add,w); cache[fam]=(sd,sa,pars)
        for q in QS:
            th=float(np.quantile(sd,q)); sel=add[sa>=th-1e-12].copy()
            d=sel[sel.month.isin(DEV)]; s=sel[sel.month.isin(SUP)]
            ma,md,ms=metric(sel),metric(d),metric(s)
            ca,cd,cs=metric(combine(live,sel)),metric(combine(ldev,d)),metric(combine(lsup,s))
            lr,lm=lomo_for(add,fam,q)
            for xrow in lr: lomo_rows.append({'family':fam,'q':q,**xrow})
            grid.append({'family':fam,'q':q,'threshold':th,
                         'selected_R':ma['R'],'selected_roi':ma['roi'],'selected_exact3_rate':ma['exact3_rate'],
                         'dev_R':md['R'],'dev_head_rate':md['head_rate'],'dev_hits':md['hits'],
                         'dev_exact3_rate':md['exact3_rate'],'dev_roi':md['roi'],'dev_profit':md['profit'],
                         'support_R':ms['R'],'support_head_rate':ms['head_rate'],'support_hits':ms['hits'],
                         'support_exact3_rate':ms['exact3_rate'],'support_roi':ms['roi'],'support_profit':ms['profit'],
                         'combined_R':ca['R'],'combined_roi':ca['roi'],'combined_profit':ca['profit'],
                         'combined_dev_R':cd['R'],'combined_dev_roi':cd['roi'],
                         'combined_support_R':cs['R'],'combined_support_roi':cs['roi'],
                         **lm})
    g=pd.DataFrame(grid)

    # Selection uses DEV + DEV-LOMO only. SUPPORT columns are deliberately absent.
    eligible=g[
      g.dev_R.between(15,35) &
      g.dev_roi.ge(1.0) &
      g.dev_exact3_rate.ge(base['added_dev']['exact3_rate']-1e-12) &
      g.lomo_active_months.eq(5) &
      g.lomo_nonnegative_months.ge(3) &
      g.lomo_roi.ge(1.0)
    ].copy()
    if len(eligible):
        # Favor temporal robustness, then volume, then combined DEV ROI.
        pick=eligible.sort_values(['lomo_nonnegative_months','lomo_worst_roi','dev_R','combined_dev_roi','dev_roi'],
                                  ascending=[False,False,False,False,False]).iloc[0]
        mode='DEV_LOMO_ROBUST'
    else:
        z=g[g.dev_R.ge(15)].copy()
        pick=z.sort_values(['lomo_nonnegative_months','lomo_roi','combined_dev_roi','dev_R'],
                           ascending=[False,False,False,False]).iloc[0] if len(z) else None
        mode='FALLBACK_DIAGNOSTIC'

    chosen=None
    if pick is not None:
        fam=str(pick.family); q=float(pick.q); sd,sa,pars=cache[fam]; th=float(pick.threshold)
        sel=add[sa>=th-1e-12].copy(); sel.to_csv(OUT/'selected_added.csv',index=False)
        chosen={'selection_mode':mode,'family':fam,'q':q,'threshold':th,'standardization':pars,
                'metrics':pick.to_dict(),'selected_codes':sel.race_code.tolist()}
    g.to_csv(OUT/'grid.csv',index=False)
    pd.DataFrame(lomo_rows).to_csv(OUT/'lomo.csv',index=False)
    add.to_csv(OUT/'added71_consensus_features.csv',index=False)

    result={'prepared_source':'v360 Artifact 10539401122','band_R':71,'baseline':base,
            'families':FAMILIES,'quantiles':QS,'grid_cells':len(g),'dev_only_pick':chosen,
            'eligible_dev_lomo_cells':int(len(eligible)),
            'SELECTION_USED_SUPPORT_OUTCOMES':False,'RESULT_OR_PAYOUT_USED_AS_SCORE_INPUT':False,
            'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    cols=['family','q','dev_R','dev_exact3_rate','dev_roi','lomo_nonnegative_months','lomo_worst_roi','lomo_roi',
          'support_R','support_exact3_rate','support_roi','combined_R','combined_roi','combined_support_roi']
    print('\nGRID',flush=True)
    print(g.sort_values(['lomo_nonnegative_months','lomo_worst_roi','dev_R'],ascending=[False,False,False])[cols].to_string(index=False),flush=True)

if __name__=='__main__': main()
