#!/usr/bin/env python3
from __future__ import annotations
"""v388: opponent-confidence rescue inside the frozen added71 band.

LIVE165 remains fixed. Scores use only model/exhibition-derived probabilities
available before the race. Outcomes/payouts are evaluation-only. September is
forbidden.
"""
from pathlib import Path
import argparse,json,math,pickle
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v388-added71-opponent-confidence'); OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
QS=(.25,.35,.45,.55,.65,.75)
FAMILIES={
  'PAIR_MASS': {'top3_mass':1.0},
  'PAIR_MARGIN': {'margin34':1.0},
  'PAIR_CONC': {'concentration':1.0},
  'PAIR_CONF': {'top3_mass':1.0,'margin34':1.0,'concentration':1.0},
  'PAIR_CONF_EX': {'top3_mass':1.0,'margin34':1.0,'concentration':1.0,'v332_score':0.5},
}

def build_one(r,payout):
    p2,pc=v365.formal_post_five6(r)
    pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    hybrid=v299.STRATEGIES['HYBRID'](p2,pc,pair)
    if len(hybrid)<4: raise RuntimeError('HYBRID ranking shorter than 4')
    formal=hybrid[:3]
    ts=';'.join(f'1-{s}-{t}' for s,t in formal)
    actual=str(r['actual_combo']); hit=int(actual in ts.split(';'))
    vals=np.array([max(float(v),1e-15) for v in pair.values()],dtype=float)
    vals=vals/vals.sum()
    ent=float(-(vals*np.log(vals)).sum()/math.log(len(vals))) if len(vals)>1 else 0.0
    return {
      'race_code':str(r['race_code']).zfill(12),'month':str(r['month']),
      'head_hit':int(r['head_hit']),'actual_combo':actual,'tickets':ts,'hit':hit,
      'payout100':int(payout),'p_head':float(r['p_head']),'opp_mass':float(r['opp_mass']),
      'v332_score':float(r['v332_score']),
      'top3_mass':float(sum(float(pair[x]) for x in formal)),
      'margin34':float(pair[formal[2]]-pair[hybrid[3]]),
      'concentration':float(1.0-ent),
      'pair_entropy_norm':ent,
      'top1_pair_prob':float(pair[formal[0]]),
    }

def metric(z):
    if len(z)==0:
        return {'R':0,'head':0,'head_rate':0.0,'hits':0,'exact3_rate':0.0,'stake':0,'return':0,'profit':0,'roi':0.0}
    ret=int(z.loc[z.hit.eq(1),'payout100'].sum()); stake=len(z)*300
    return {'R':int(len(z)),'head':int(z.head_hit.sum()),'head_rate':float(z.head_hit.mean()),
            'hits':int(z.hit.sum()),'exact3_rate':float(z.hit.mean()),'stake':int(stake),
            'return':ret,'profit':int(ret-stake),'roi':float(ret/stake)}

def fit_scores(train,test,weights):
    mu={c:float(train[c].mean()) for c in weights}
    sd={c:float(train[c].std(ddof=0)) for c in weights}
    for c in weights:
        if not math.isfinite(sd[c]) or sd[c]<1e-12: sd[c]=1.0
    def sc(df):
        out=np.zeros(len(df),dtype=float); den=sum(abs(float(w)) for w in weights.values())
        for c,w in weights.items(): out+=float(w)*((df[c].to_numpy(float)-mu[c])/sd[c])
        return out/den
    return sc(train),sc(test),{'mean':mu,'sd':sd}

def combine(a,b): return pd.concat([a,b],ignore_index=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--prepared',required=True,type=Path); a=ap.parse_args()
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD: raise RuntimeError('September guard disabled')
    x=pickle.load(a.prepared.open('rb')); rows=x['rows']
    live_ids={str(r['race_code']).zfill(12) for r in rows['LIVE165']}
    broad={str(r['race_code']).zfill(12):r for r in rows['H078_M375']}
    added=[r for c,r in broad.items() if c not in live_ids]
    if len(added)!=71 or len(rows['LIVE165'])!=165: raise RuntimeError('universe drift')
    union=list({str(r['race_code']).zfill(12):r for r in list(rows['LIVE165'])+added}.values())
    v365.install_payout_cache(union); payouts=v365.payouts_for(union)
    add=pd.DataFrame([build_one(r,payouts[str(r['race_code']).zfill(12)]) for r in added])
    live=pd.DataFrame([build_one(r,payouts[str(r['race_code']).zfill(12)]) for r in rows['LIVE165']])
    if any(add.race_code.str[:8].ge('20260901')): raise RuntimeError('September entered')

    adev=add[add.month.isin(DEV)].copy(); asup=add[add.month.isin(SUP)].copy()
    ldev=live[live.month.isin(DEV)].copy(); lsup=live[live.month.isin(SUP)].copy()
    base={'live_all':metric(live),'live_dev':metric(ldev),'live_support':metric(lsup),
          'added_all':metric(add),'added_dev':metric(adev),'added_support':metric(asup)}

    rec=[]; caches={}
    for fam,w in FAMILIES.items():
        sd,sa,pars=fit_scores(adev,add,w); caches[fam]=(sd,sa,pars)
        for q in QS:
            th=float(np.quantile(sd,q)); sel=add[sa>=th-1e-12].copy()
            d=sel[sel.month.isin(DEV)]; s=sel[sel.month.isin(SUP)]
            ma,md,ms=metric(sel),metric(d),metric(s)
            ca=metric(combine(live,sel)); cd=metric(combine(ldev,d)); cs=metric(combine(lsup,s))
            rec.append({'family':fam,'q':q,'threshold':th,
                        'selected_R':ma['R'],'selected_exact3_rate':ma['exact3_rate'],'selected_roi':ma['roi'],
                        'dev_R':md['R'],'dev_head_rate':md['head_rate'],'dev_exact3_rate':md['exact3_rate'],'dev_hits':md['hits'],'dev_roi':md['roi'],'dev_profit':md['profit'],
                        'support_R':ms['R'],'support_head_rate':ms['head_rate'],'support_exact3_rate':ms['exact3_rate'],'support_hits':ms['hits'],'support_roi':ms['roi'],'support_profit':ms['profit'],
                        'combined_R':ca['R'],'combined_roi':ca['roi'],'combined_profit':ca['profit'],
                        'combined_dev_R':cd['R'],'combined_dev_roi':cd['roi'],'combined_dev_profit':cd['profit'],
                        'combined_support_R':cs['R'],'combined_support_roi':cs['roi'],'combined_support_profit':cs['profit']})
    grid=pd.DataFrame(rec)

    # DEV-only volume-first pick. Support outcomes are excluded from selection.
    strict=grid[
      grid.dev_R.between(15,35) &
      grid.dev_roi.ge(1.0) &
      grid.dev_exact3_rate.ge(base['added_dev']['exact3_rate']-1e-12) &
      grid.combined_dev_roi.ge(base['live_dev']['roi']-0.03)
    ].copy()
    if len(strict):
        pick=strict.sort_values(['dev_R','combined_dev_roi','dev_roi'],ascending=[False,False,False]).iloc[0]
        mode='STRICT_VOLUME_FIRST'
    else:
        z=grid[grid.dev_R.ge(15)].copy()
        pick=z.sort_values(['combined_dev_roi','dev_roi','dev_R'],ascending=[False,False,False]).iloc[0] if len(z) else None
        mode='FALLBACK_DIAGNOSTIC'

    chosen=None
    if pick is not None:
        fam=str(pick.family); q=float(pick.q); sd,sa,pars=caches[fam]; th=float(pick.threshold)
        sel=add[sa>=th-1e-12].copy(); sel.to_csv(OUT/'selected_added.csv',index=False)
        chosen={'selection_mode':mode,'family':fam,'q':q,'threshold':th,'standardization':pars,
                'metrics':pick.to_dict(),'selected_codes':sel.race_code.tolist()}

    grid.to_csv(OUT/'grid.csv',index=False); add.to_csv(OUT/'added71_confidence.csv',index=False)
    result={'prepared_source':'v360 Artifact 10539401122','band_R':71,'baseline':base,
            'families':FAMILIES,'quantiles':QS,'grid_cells':len(grid),'dev_only_pick':chosen,
            'SELECTION_USED_SUPPORT_OUTCOMES':False,'RESULT_OR_PAYOUT_USED_AS_SCORE_INPUT':False,
            'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str),flush=True)
    cols=['family','q','selected_R','dev_R','dev_exact3_rate','dev_roi','combined_dev_roi','support_R','support_exact3_rate','support_roi','combined_support_roi','combined_R','combined_roi']
    print('\nGRID',flush=True); print(grid.sort_values(['dev_R','combined_dev_roi'],ascending=[False,False])[cols].to_string(index=False),flush=True)

if __name__=='__main__': main()
