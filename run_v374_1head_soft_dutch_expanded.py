#!/usr/bin/env python3
from __future__ import annotations
"""v374: apply fixed v372 threshold=3.5 soft-Dutch rule to expanded universes.

No re-optimization. Ticket generation uses current formal opponent rerank machinery
on v360 prepared rows. Closing odds are official repo snapshots with official-web
fallback only. September outcomes are forbidden.
"""
from pathlib import Path
import argparse,json,pickle
import numpy as np
import pandas as pd

import run_v369_1head_ticket_rank_staking as v369
import run_v370_1head_odds_dynamic_staking as v370

OUT=Path('/tmp/v374-soft-dutch-expanded');OUT.mkdir(parents=True,exist_ok=True)
THRESHOLD=3.5
UNIVERSES=('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276')
CHAIN=('LIVE165','H078_M375','H0775_M375','H0775_M350')

def build(rr,payouts,odds):
    rec=[];missing=[]
    for r in rr:
        code=str(r['race_code']).zfill(12)
        z=v370.formal_record(r,payouts[code],odds.get(code))
        if z is None:missing.append(code)
        else:rec.append(z)
    return pd.DataFrame(rec),missing

def eval_policy(z):
    ret=0;hits=0;lost=0;changed=0;doublewin=0
    rows=[]
    for _,r in z.iterrows():
        o=np.array([r.o1,r.o2,r.o3],float);u=np.ones(3,dtype=int)
        ratio=float(o.max()/o.min());src=tgt=-1
        if ratio>=THRESHOLD:
            src=int(np.argmax(o));tgt=int(np.argmin(o));u[src]-=1;u[tgt]+=1;changed+=1
        rank=int(r.hit_rank)
        h=rank>0 and u[rank-1]>0
        if h:
            hits+=1;ret+=int(r.payout100)*int(u[rank-1])
            if u[rank-1]>1:doublewin+=1
        elif rank>0:lost+=1
        rows.append({'race_code':str(r.race_code).zfill(12),'month':r.month,'hit_rank':rank,
                     'odds_ratio':ratio,'u1':int(u[0]),'u2':int(u[1]),'u3':int(u[2]),
                     'changed':int(ratio>=THRESHOLD),'lost_hit':int(rank>0 and not h),
                     'return_yen':int(r.payout100)*int(u[rank-1]) if h else 0})
    stake=len(z)*300
    return {'R':len(z),'hits':hits,'lost_hits':lost,'changed_R':changed,'doubled_win_R':doublewin,
            'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0},pd.DataFrame(rows)

def baseline(z):
    ret=int(z.loc[z.hit_rank.gt(0),'payout100'].sum());stake=len(z)*300
    return {'R':len(z),'hits':int(z.hit_rank.gt(0).sum()),'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));allrows=x['rows']
    union={}
    for name in UNIVERSES:
        for r in allrows[name]:
            code=str(r['race_code']).zfill(12)
            if code[:8]>='20260901':raise RuntimeError(f'September entered {code}')
            union[code]=r
    unionrows=list(union.values())
    v369.install_payout_cache(unionrows);payouts=v369.payouts_for(unionrows)
    odds,source=v370.load_daily_odds(list(union))
    coverage={'union_R':len(union),'covered_R':sum(odds[c] is not None for c in union),
              'repo_csv_R':sum(v=='repo_csv' for v in source.values()),
              'official_web_fallback_R':sum(v=='official_web_fallback' for v in source.values()),
              'failed_R':sum(odds[c] is None for c in union)}
    if coverage['failed_R']>0:
        miss=[c for c in union if odds[c] is None]
        raise RuntimeError(f'odds coverage incomplete {coverage} missing={miss[:20]}')

    frames={};summaries=[]
    for name in UNIVERSES:
        z,missing=build(allrows[name],payouts,odds)
        if missing or len(z)!=len(allrows[name]):raise RuntimeError(f'{name} build drift missing={missing}')
        b=baseline(z);p,rows=eval_policy(z)
        frames[name]=z
        rows.to_csv(OUT/f'{name}_race_level.csv',index=False)
        summaries.append({'universe':name,
                          'base_R':b['R'],'base_hits':b['hits'],'base_return_yen':b['return_yen'],'base_roi':b['roi'],
                          'policy_hits':p['hits'],'policy_lost_hits':p['lost_hits'],'policy_return_yen':p['return_yen'],
                          'policy_roi':p['roi'],'changed_R':p['changed_R'],'doubled_win_R':p['doubled_win_R'],
                          'delta_hits':p['hits']-b['hits'],'delta_roi_pp':100*(p['roi']-b['roi'])})

    # Disjoint nested bands. Fixed rule, no selection.
    bands=[];prev=set()
    for name in CHAIN:
        z=frames[name];ids=set(z.race_code.astype(str).str.zfill(12));bid=ids-prev
        q=z[z.race_code.astype(str).str.zfill(12).isin(bid)].copy()
        b=baseline(q);p,_=eval_policy(q)
        bands.append({'band':name if not prev else f'ADDED_TO_{name}',
                      'R':len(q),'base_hits':b['hits'],'policy_hits':p['hits'],'lost_hits':p['lost_hits'],
                      'base_roi':b['roi'],'policy_roi':p['roi'],'delta_roi_pp':100*(p['roi']-b['roi']),
                      'changed_R':p['changed_R']})
        prev=ids

    sd=pd.DataFrame(summaries);bd=pd.DataFrame(bands)
    sd.to_csv(OUT/'universes.csv',index=False);bd.to_csv(OUT/'bands.csv',index=False)
    result={
      'threshold_fixed':THRESHOLD,'odds_coverage':coverage,
      'universes':summaries,'bands':bands,
      'all_universes_zero_lost_hits':bool((sd.policy_lost_hits==0).all()),
      'all_nested_bands_zero_lost_hits':bool((bd.lost_hits==0).all()),
      'universes_nonnegative_roi_delta':int((sd.delta_roi_pp>=-1e-12).sum()),
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
