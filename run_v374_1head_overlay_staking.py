#!/usr/bin/env python3
from __future__ import annotations
"""v374: stake concentration on already-formal wall3 / 5->6 overlay races.

No new predictive gate is tuned here. The stake signal is only whether either of
the already-promoted formal post-exhibition reranks fires. Race/ticket identities
are otherwise frozen per supplied universe. September outcomes are forbidden.
"""
from pathlib import Path
import argparse,json,pickle
import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import run_v369_1head_ticket_rank_staking as v369

OUT=Path('/tmp/v374-overlay-staking');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
UNIVERSES=('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276')

def tickets_for(r):
    p2,pc=v365.formal_post_five6(r)
    pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
    top=v299.STRATEGIES['HYBRID'](p2,pc,pair)[:3]
    return [f'1-{s}-{t}' for s,t in top]

def flags(r):
    wall=(float(r['opp_mass'])>=prod.WATCH_OPPONENT_MASS_MIN and bool(r.get('ex_ready',False))
          and float(r['score4'])>=prod.WALL3_SHADOW_ATTACK4_MIN
          and float(r['score4'])>float(r['score3']))
    five=(bool(r.get('ex_ready',False))
          and float(r['score6'])>=prod.FIVE6_SHADOW_SCORE6_MIN
          and (float(r['st6'])-float(r['st5']))>=prod.FIVE6_SHADOW_ST_GAP_MIN)
    return bool(wall),bool(five)

def build(rows,payouts):
    rec=[]
    for r in rows:
        code=str(r['race_code']).zfill(12);actual=str(r['actual_combo'])
        ts=tickets_for(r);wall,five=flags(r)
        if wall and five:cat='BOTH'
        elif wall:cat='WALL3'
        elif five:cat='FIVE6'
        else:cat='NONE'
        rec.append({'race_code':code,'month':str(r['month']),'actual_combo':actual,
                    'hit':int(actual in ts),'payout100':int(payouts[code]),
                    'wall3':int(wall),'five6':int(five),'either':int(wall or five),
                    'overlay_cat':cat,'tickets':';'.join(ts)})
    return pd.DataFrame(rec)

def basic_metric(z):
    stake=len(z)*300
    ret=int(z.loc[z.hit.eq(1),'payout100'].sum())
    return {'R':len(z),'hits':int(z.hit.sum()),'stake':stake,'return':ret,
            'profit':ret-stake,'roi':ret/stake if stake else 0.0}

def subset_metric(z,mask):
    q=z[mask].copy()
    return basic_metric(q)

def portfolio(z,multiplier):
    # Base = 100 each. Overlay races receive multiplier*100 on each of 3 tickets.
    stake=ret=0
    for r in z.itertuples():
        m=int(multiplier) if int(r.either) else 1
        stake+=300*m
        if int(r.hit):ret+=int(r.payout100)*m
    return {'multiplier':int(multiplier),'R':len(z),'overlay_R':int(z.either.sum()),
            'stake':stake,'return':ret,'profit':ret-stake,'roi':ret/stake if stake else 0.0}

def split(z):
    return {
      'all':basic_metric(z),
      'dev':basic_metric(z[z.month.isin(DEV)]),
      'support':basic_metric(z[z.month.isin(SUP)]),
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));allrows=x['rows']
    for name in UNIVERSES:
        if name not in allrows:raise RuntimeError(f'missing universe {name}')
    union={}
    for name in UNIVERSES:
        for r in allrows[name]:union[str(r['race_code']).zfill(12)]=r
    unionrows=list(union.values())
    v369.install_payout_cache(unionrows);payouts=v369.payouts_for(unionrows)

    summaries=[];portfolio_rows=[];monthly=[];built={}
    for name in UNIVERSES:
        z=build(allrows[name],payouts);built[name]=z
        b=split(z)
        either_all=subset_metric(z,z.either.eq(1))
        none_all=subset_metric(z,z.either.eq(0))
        either_dev=subset_metric(z,z.either.eq(1)&z.month.isin(DEV))
        either_sup=subset_metric(z,z.either.eq(1)&z.month.isin(SUP))
        row={'universe':name,
             **{f'base_{k}':v for k,v in b['all'].items()},
             'overlay_R':either_all['R'],'overlay_hits':either_all['hits'],'overlay_roi':either_all['roi'],
             'none_R':none_all['R'],'none_hits':none_all['hits'],'none_roi':none_all['roi'],
             'dev_overlay_R':either_dev['R'],'dev_overlay_roi':either_dev['roi'],
             'support_overlay_R':either_sup['R'],'support_overlay_roi':either_sup['roi']}
        summaries.append(row)
        for m in (1,2,3,4):
            for label,df in [('ALL',z),('DEV',z[z.month.isin(DEV)]),('SUPPORT',z[z.month.isin(SUP)])]:
                q=portfolio(df,m);portfolio_rows.append({'universe':name,'period':label,**q})
        for mon,g in z.groupby('month',sort=True):
            ov=subset_metric(g,g.either.eq(1));base=basic_metric(g)
            p2=portfolio(g,2)
            monthly.append({'universe':name,'month':mon,
                            'R':len(g),'overlay_R':ov['R'],'base_roi':base['roi'],
                            'overlay_roi':ov['roi'],'double_roi':p2['roi'],
                            'base_profit':base['profit'],'double_profit':p2['profit']})
    summary=pd.DataFrame(summaries);ports=pd.DataFrame(portfolio_rows);mon=pd.DataFrame(monthly)

    # Current LIVE165 sentinel.
    live=built['LIVE165'];lm=basic_metric(live)
    if (lm['R'],lm['hits'],lm['return'])!=(165,87,63700):
        raise RuntimeError(f'LIVE165 formal sentinel drift {lm}')
    liveov=subset_metric(live,live.either.eq(1))
    if liveov['R']!=36:raise RuntimeError(f'overlay count drift {liveov}')

    # Category audit on LIVE165.
    cats=[]
    for cat,g in live.groupby('overlay_cat',sort=True):
        m=basic_metric(g);cats.append({'category':cat,**m,
                                      'dev_R':len(g[g.month.isin(DEV)]),
                                      'dev_roi':basic_metric(g[g.month.isin(DEV)])['roi'],
                                      'support_R':len(g[g.month.isin(SUP)]),
                                      'support_roi':basic_metric(g[g.month.isin(SUP)])['roi']})

    # Disjoint nested added bands among env=.05 chain.
    chain=('LIVE165','H078_M375','H0775_M375','H0775_M350')
    bands=[];prev=set()
    for name in chain:
        z=built[name];ids=set(z.race_code);bid=ids-prev
        q=z[z.race_code.isin(bid)].copy()
        ov=subset_metric(q,q.either.eq(1));base=basic_metric(q);p2=portfolio(q,2)
        bands.append({'band':name if not prev else f'ADDED_TO_{name}',
                      'R':len(q),'base_roi':base['roi'],'overlay_R':ov['R'],
                      'overlay_roi':ov['roi'],'double_roi':p2['roi'],
                      'base_profit':base['profit'],'double_profit':p2['profit']})
        prev=ids

    summary.to_csv(OUT/'universe_summary.csv',index=False)
    ports.to_csv(OUT/'portfolios.csv',index=False)
    mon.to_csv(OUT/'monthly.csv',index=False)
    pd.DataFrame(cats).to_csv(OUT/'live165_categories.csv',index=False)
    pd.DataFrame(bands).to_csv(OUT/'disjoint_bands.csv',index=False)
    for name,z in built.items():z.to_csv(OUT/f'rows_{name}.csv',index=False)

    result={
      'live165_baseline':lm,'live165_overlay':liveov,
      'live165_categories':cats,
      'universe_summary':summaries,
      'disjoint_bands':bands,
      'stake_multipliers_tested':[1,2,3,4],
      'signal':'already-promoted formal wall3 OR five6 applied',
      'PARAMETER_TUNING_PERFORMED':False,
      'ODDS_USED_AS_FEATURE':False,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
