#!/usr/bin/env python3
from __future__ import annotations
"""v369: decompose current formal trifecta tickets by ticket rank and audit staking.

Current formal ticket composition is frozen: opponentCore -> wall3 -> 5->6 ST.
This script changes no production logic. Selection of staking weights uses Feb-Jun
DEV only; Jul-Aug SUPPORT is evaluation only.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, json, pickle, statistics, urllib.request
import pandas as pd

import backtest
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v351_1head_third_close_margin_audit as pay
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v369-ticket-rank-staking');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')

def install_payout_cache(rows):
    days=sorted({str(r['race_code'])[:8] for r in rows})
    paths=[f"data/results/payouts/{d[:4]}/{d[4:6]}/{d[6:8]}.csv" for d in days]
    original=backtest.fetch
    def one(path):
        try:
            with urllib.request.urlopen(backtest.BASE+path,timeout=30) as resp:
                return path,resp.read().decode('utf-8-sig')
        except Exception:
            return path,''
    cache={}
    with ThreadPoolExecutor(max_workers=24) as ex:
        for path,txt in ex.map(one,paths):cache[path]=txt
    def cached(path):
        if path in cache:return cache[path]
        return original(path)
    backtest.fetch=cached
    return {'days':len(days),'nonempty':sum(bool(v) for v in cache.values())}

def payouts_for(rows):
    cache={};out={}
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901':raise RuntimeError(f'September entered {code}')
        _,p=pay._payout(code,str(r['actual_combo']),cache);out[code]=int(p)
    return out

def build(rows,payouts):
    rec=[]
    for r in rows:
        code=str(r['race_code']).zfill(12);actual=str(r['actual_combo'])
        p2,pc=v365.formal_post_five6(r)
        pair=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        top=v299.STRATEGIES['HYBRID'](p2,pc,pair)[:3]
        ts=[f'1-{s}-{t}' for s,t in top]
        rank=(ts.index(actual)+1) if actual in ts else 0
        rec.append({
          'race_code':code,'month':str(r['month']),'actual_combo':actual,
          'ticket1':ts[0],'ticket2':ts[1],'ticket3':ts[2],
          'hit':int(rank>0),'hit_rank':rank,'payout100':int(payouts[code]),
          'return_equal100':int(payouts[code]) if rank>0 else 0,
        })
    z=pd.DataFrame(rec)
    return z

def subset_summary(z,label):
    hits=z[z.hit_rank.gt(0)]
    out={'label':label,'R':len(z),'hits':int(len(hits)),'hit_rate':float(len(hits)/len(z)) if len(z) else 0.0,
         'stake_equal3_yen':len(z)*300,'return_equal3_yen':int(hits.payout100.sum())}
    out['roi_equal3']=out['return_equal3_yen']/out['stake_equal3_yen'] if out['stake_equal3_yen'] else 0.0
    for rank in (1,2,3):
        q=z[z.hit_rank.eq(rank)]
        vals=[int(v) for v in q.payout100.tolist()]
        out[f'rank{rank}_hits']=len(vals)
        out[f'rank{rank}_share_of_hits']=len(vals)/len(hits) if len(hits) else 0.0
        out[f'rank{rank}_return_yen']=sum(vals)
        out[f'rank{rank}_return_share']=sum(vals)/int(hits.payout100.sum()) if len(hits) and int(hits.payout100.sum()) else 0.0
        out[f'rank{rank}_avg_payout100']=sum(vals)/len(vals) if vals else 0.0
        out[f'rank{rank}_median_payout100']=statistics.median(vals) if vals else 0.0
        # Standalone: rank only, 100 yen per race.
        out[f'rank{rank}_solo_stake_yen']=len(z)*100
        out[f'rank{rank}_solo_roi']=sum(vals)/(len(z)*100) if len(z) else 0.0
    return out

def strategy(z,ranks):
    ranks=set(ranks);hit=z.hit_rank.isin(ranks)
    stake=len(z)*100*len(ranks);ret=int(z.loc[hit,'payout100'].sum())
    return {'ranks':'+'.join(map(str,sorted(ranks))),'R':len(z),'hits':int(hit.sum()),
            'hit_rate':float(hit.mean()),'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def weighted(z,w):
    w=tuple(int(x) for x in w);stake=len(z)*sum(w)*100;ret=0;hits=0
    for _,r in z.iterrows():
        rank=int(r.hit_rank)
        if rank>0:
            hits+=1;ret+=int(r.payout100)*w[rank-1]
    return {'w1':w[0],'w2':w[1],'w3':w[2],'units_total':sum(w),
            'R':len(z),'hits':hits,'stake_yen':stake,'return_yen':ret,
            'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0}

def weight_combos(total):
    out=[]
    for a in range(1,total-1):
      for b in range(1,total-a):
        c=total-a-b
        if c>=1:out.append((a,b,c))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));rows=x['rows']['LIVE165']
    if len(rows)!=165:raise RuntimeError(f'LIVE165 drift {len(rows)}')
    prefetch=install_payout_cache(rows);payouts=payouts_for(rows)
    z=build(rows,payouts)
    base=subset_summary(z,'ALL')
    if (base['R'],base['hits'],base['return_equal3_yen'])!=(165,87,63700):
        raise RuntimeError(f'formal baseline drift {base}')

    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()
    summaries=[base,subset_summary(dev,'DEV'),subset_summary(sup,'SUPPORT')]
    monthly=[subset_summary(g,str(mon)) for mon,g in z.groupby('month')]

    # Coverage subsets at equal 100 per selected rank.
    cover=[]
    for ranks in ((1,),(2,),(3,),(1,2),(1,3),(2,3),(1,2,3)):
        for label,df in [('ALL',z),('DEV',dev),('SUPPORT',sup)]:
            d=strategy(df,ranks);d['period']=label;cover.append(d)
    cover=pd.DataFrame(cover)

    # Fixed all-three staking budgets. Select weights by DEV ROI only.
    weight_rows=[];best_by_budget={}
    for units in (4,5,6):
        cand=[]
        for w in weight_combos(units):
            dm=weighted(dev,w);sm=weighted(sup,w);am=weighted(z,w)
            row={**{f'dev_{k}':v for k,v in dm.items()},
                 **{f'support_{k}':v for k,v in sm.items()},
                 **{f'all_{k}':v for k,v in am.items()}}
            weight_rows.append(row);cand.append(row)
        best=max(cand,key=lambda r:(r['dev_roi'],-r['dev_units_total'],r['dev_w1'],-r['dev_w3']))
        best_by_budget[str(units*100)]=best
    weights=pd.DataFrame(weight_rows)

    # Rank-wise return per one unit across DEV, useful to see which ticket merits extra stake.
    dev_rank_unit={}
    sup_rank_unit={}
    for rank in (1,2,3):
        dev_rank_unit[str(rank)]=int(dev.loc[dev.hit_rank.eq(rank),'payout100'].sum())
        sup_rank_unit[str(rank)]=int(sup.loc[sup.hit_rank.eq(rank),'payout100'].sum())

    # Save hit rows ordered by ticket rank for direct inspection.
    hits=z[z.hit_rank.gt(0)].copy().sort_values(['hit_rank','month','race_code'])
    z.to_csv(OUT/'all_races.csv',index=False);hits.to_csv(OUT/'hit_rows.csv',index=False)
    pd.DataFrame(summaries).to_csv(OUT/'rank_summary.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly_rank_summary.csv',index=False)
    cover.to_csv(OUT/'coverage_strategies.csv',index=False)
    weights.to_csv(OUT/'weight_grid.csv',index=False)

    result={
      'formal_baseline':base,
      'dev':summaries[1],'support':summaries[2],
      'best_weights_by_budget':best_by_budget,
      'dev_rank_return_per_100_unit':dev_rank_unit,
      'support_rank_return_per_100_unit':sup_rank_unit,
      'payout_prefetch':prefetch,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
