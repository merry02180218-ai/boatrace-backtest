#!/usr/bin/env python3
from __future__ import annotations
"""v370: dynamic staking for current formal 3-ticket policy using official closing odds.

Race/ticket selection is frozen. Every race is bought and all three formal tickets
receive at least 100 yen. Allocation uses only model probabilities and official
closing odds. DEV Feb-Jun selects; Jul-Aug SUPPORT is holdout.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, json, math, pickle, urllib.request
import numpy as np
import pandas as pd

import backtest
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v351_1head_third_close_margin_audit as pay
import run_v365_1head_exact3_hit_push as v365

OUT=Path('/tmp/v370-dynamic-staking'); OUT.mkdir(parents=True,exist_ok=True)
BOATS=(2,3,4,5,6)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
BUDGETS=(600,900,1200)
ALPHAS=(.5,1.0,1.5,2.0)
BETAS=(-1.0,-.5,0.0,.5,1.0)

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
        for path,txt in ex.map(one,paths): cache[path]=txt
    def cached(path):
        if path in cache:return cache[path]
        return original(path)
    backtest.fetch=cached
    return {'days':len(days),'nonempty':sum(bool(v) for v in cache.values())}

def payouts_for(rows):
    cache={};out={}
    for r in rows:
        code=str(r['race_code']).zfill(12)
        if code[:8]>='20260901': raise RuntimeError(f'September entered {code}')
        _,p=pay._payout(code,str(r['actual_combo']),cache);out[code]=int(p)
    return out

def allocate_proportional(scores,total_units):
    scores=[max(float(x),0.0) for x in scores]
    if len(scores)!=3 or total_units<3: raise RuntimeError('bad allocation input')
    if sum(scores)<=0: scores=[1,1,1]
    target=[total_units*x/sum(scores) for x in scores]
    units=[max(1,int(math.floor(x))) for x in target]
    while sum(units)>total_units:
        cand=[i for i,u in enumerate(units) if u>1]
        if not cand: raise RuntimeError('cannot shrink allocation')
        i=max(cand,key=lambda k:(units[k]-target[k],k))
        units[i]-=1
    while sum(units)<total_units:
        i=max(range(3),key=lambda k:(target[k]-units[k],scores[k],-k))
        units[i]+=1
    return tuple(units)

def allocate_top(scores,total_units):
    units=[1,1,1]
    i=max(range(3),key=lambda k:(float(scores[k]),-k))
    units[i]+=total_units-3
    return tuple(units)

def equal_units(total_units):
    if total_units%3: raise RuntimeError('budget not divisible by 3 units')
    return (total_units//3,)*3

def odds_row(code,cache):
    code=str(code).zfill(12); day=code[:8];jcd=code[8:10];rno=int(code[10:12])
    if day>='20260901': raise RuntimeError(f'September odds entered {code}')
    if day not in cache:
        p=Path(f'data/official_closing_odds3t/{day[:4]}/{day[4:6]}/{day[6:8]}.csv')
        if not p.exists():
            cache[day]=None
        else:
            d=pd.read_csv(p,dtype={'jcd':str})
            d['jcd']=d.jcd.astype(str).str.zfill(2)
            cache[day]=d
    d=cache[day]
    if d is None:return None
    q=d[(d.jcd.eq(jcd))&(pd.to_numeric(d.rno,errors='coerce').eq(rno))]
    if len(q)!=1:return None
    return q.iloc[0]

def build(rows,payouts):
    odds_cache={};rec=[];miss=[]
    for r in rows:
        code=str(r['race_code']).zfill(12);actual=str(r['actual_combo'])
        p2,pc=v365.formal_post_five6(r)
        probs=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        top=v299.STRATEGIES['HYBRID'](p2,pc,probs)[:3]
        ts=[f'1-{s}-{t}' for s,t in top]
        if len(ts)!=3 or len(set(ts))!=3:raise RuntimeError(f'invalid formal tickets {code}')
        odr=odds_row(code,odds_cache)
        if odr is None:
            miss.append(code);continue
        ods=[];ps=[]
        bad=False
        for pair,t in zip(top,ts):
            try:o=float(odr[t])
            except Exception:bad=True;break
            if not math.isfinite(o) or o<=0:bad=True;break
            ods.append(o);ps.append(float(probs[pair]))
        if bad:
            miss.append(code);continue
        rank=ts.index(actual)+1 if actual in ts else 0
        rec.append({
          'race_code':code,'month':str(r['month']),'actual_combo':actual,
          'ticket1':ts[0],'ticket2':ts[1],'ticket3':ts[2],
          'p1':ps[0],'p2':ps[1],'p3':ps[2],
          'odds1':ods[0],'odds2':ods[1],'odds3':ods[2],
          'hit_rank':rank,'payout100':int(payouts[code]),
          'wall3_like':int(float(r['score4'])>=prod.WALL3_SHADOW_ATTACK4_MIN and float(r['score4'])>float(r['score3']) and float(r['opp_mass'])>=prod.WATCH_OPPONENT_MASS_MIN),
          'five6_like':int(float(r['score6'])>=prod.FIVE6_SHADOW_SCORE6_MIN and float(r['st6'])-float(r['st5'])>=prod.FIVE6_SHADOW_ST_GAP_MIN),
        })
    return pd.DataFrame(rec),miss

def cfg_name(mode,budget,alpha=None,beta=None):
    if alpha is None:return f'{mode}|B{budget}'
    return f'{mode}|B{budget}|A{alpha:.2f}|O{beta:.2f}'

def units_for(row,mode,budget,alpha=1.0,beta=0.0):
    total=budget//100
    p=[float(row.p1),float(row.p2),float(row.p3)]
    o=[float(row.odds1),float(row.odds2),float(row.odds3)]
    if mode=='EQUAL':return equal_units(total)
    if mode=='DUTCH':return allocate_proportional([1/x for x in o],total)
    if mode=='MODEL':return allocate_proportional(p,total)
    scores=[(max(p[i],1e-12)**alpha)*(max(o[i],1e-12)**beta) for i in range(3)]
    if mode=='VALUE_PROP':return allocate_proportional(scores,total)
    if mode=='VALUE_TOP':return allocate_top(scores,total)
    raise ValueError(mode)

def evaluate(z,mode,budget,alpha=1.0,beta=0.0,detail=False):
    stake=ret=0;byrank=[0,0,0];units_sum=[0,0,0];rows=[]
    for _,r in z.iterrows():
        u=units_for(r,mode,budget,alpha,beta)
        stake+=100*sum(u)
        for i in range(3):units_sum[i]+=u[i]
        rr=0
        if int(r.hit_rank)>0:
            k=int(r.hit_rank)-1;byrank[k]+=1;rr=int(r.payout100)*u[k]
        ret+=rr
        if detail:
            rows.append({'race_code':r.race_code,'month':r.month,'hit_rank':int(r.hit_rank),
                         'u1':u[0],'u2':u[1],'u3':u[2],'stake_yen':100*sum(u),'return_yen':rr,
                         'odds1':r.odds1,'odds2':r.odds2,'odds3':r.odds3,
                         'p1':r.p1,'p2':r.p2,'p3':r.p3})
    return {
      'R':len(z),'hits':int((z.hit_rank>0).sum()),'stake_yen':stake,'return_yen':ret,
      'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,
      'rank1_hits':byrank[0],'rank2_hits':byrank[1],'rank3_hits':byrank[2],
      'avg_units_rank1':units_sum[0]/len(z) if len(z) else 0.0,
      'avg_units_rank2':units_sum[1]/len(z) if len(z) else 0.0,
      'avg_units_rank3':units_sum[2]/len(z) if len(z) else 0.0,
      'detail':rows,
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);args=ap.parse_args()
    x=pickle.load(args.prepared.open('rb'));rows=x['rows']['LIVE165']
    if len(rows)!=165:raise RuntimeError(f'LIVE165 drift {len(rows)}')
    prefetch=install_payout_cache(rows);payouts=payouts_for(rows)
    z,missing=build(rows,payouts)
    if missing: raise RuntimeError(f'closing odds missing {len(missing)} examples={missing[:10]}')
    if len(z)!=165:raise RuntimeError(f'odds coverage drift {len(z)}')
    # Equal 300 yen sentinel uses actual payout, matching formal ROI.
    base_stake=165*300;base_ret=int(z.loc[z.hit_rank.gt(0),'payout100'].sum())
    if (int((z.hit_rank>0).sum()),base_ret)!=(87,63700):
        raise RuntimeError(f'formal baseline drift hits={(z.hit_rank>0).sum()} ret={base_ret}')
    formal300={'R':165,'hits':87,'stake_yen':base_stake,'return_yen':base_ret,
               'profit_yen':base_ret-base_stake,'roi':base_ret/base_stake}
    dev=z[z.month.isin(DEV)].copy();sup=z[z.month.isin(SUP)].copy()

    records=[]
    configs=[]
    for budget in BUDGETS:
        for mode in ('EQUAL','DUTCH','MODEL'):
            configs.append((mode,budget,1.0,0.0))
        for mode in ('VALUE_PROP','VALUE_TOP'):
            for alpha in ALPHAS:
                for beta in BETAS:
                    configs.append((mode,budget,alpha,beta))
    for mode,budget,alpha,beta in configs:
        dm=evaluate(dev,mode,budget,alpha,beta)
        records.append({
          'name':cfg_name(mode,budget,alpha if mode.startswith('VALUE') else None,beta if mode.startswith('VALUE') else None),
          'mode':mode,'budget':budget,'alpha':alpha,'beta':beta,
          **{f'dev_{k}':v for k,v in dm.items() if k!='detail'}
        })
    grid=pd.DataFrame(records)
    # DEV-only selection within each budget; require all races bought by construction.
    selected=[]
    for budget in BUDGETS:
        q=grid[grid.budget.eq(budget)].copy()
        best=q.sort_values(['dev_roi','dev_profit_yen'],ascending=False).iloc[0]
        selected.append(best)
    selected_df=pd.DataFrame(selected)

    final=[]
    monthly=[]
    for _,b in selected_df.iterrows():
        mode=str(b['mode']);budget=int(b['budget']);alpha=float(b['alpha']);beta=float(b['beta'])
        sm=evaluate(sup,mode,budget,alpha,beta)
        am=evaluate(z,mode,budget,alpha,beta,detail=True)
        em=evaluate(z,'EQUAL',budget)
        row={**b.to_dict(),
             **{f'support_{k}':v for k,v in sm.items() if k!='detail'},
             **{f'all_{k}':v for k,v in am.items() if k!='detail'},
             'equal_all_roi':em['roi'],'delta_roi_pp_vs_equal_all':100*(am['roi']-em['roi'])}
        final.append(row)
        pd.DataFrame(am['detail']).to_csv(OUT/f"detail_selected_B{budget}.csv",index=False)
        for mon,g in z.groupby('month'):
            mm=evaluate(g,mode,budget,alpha,beta);eq=evaluate(g,'EQUAL',budget)
            monthly.append({'budget':budget,'mode':mode,'alpha':alpha,'beta':beta,'month':mon,
                            'roi':mm['roi'],'equal_roi':eq['roi'],'delta_roi_pp':100*(mm['roi']-eq['roi']),
                            'profit_yen':mm['profit_yen'],'equal_profit_yen':eq['profit_yen'],
                            'avg_units_rank1':mm['avg_units_rank1'],'avg_units_rank2':mm['avg_units_rank2'],'avg_units_rank3':mm['avg_units_rank3']})

    # Fixed named baselines across all periods.
    baseline_rows=[]
    for budget in BUDGETS:
        for mode in ('EQUAL','DUTCH','MODEL'):
            for period,df in [('DEV',dev),('SUPPORT',sup),('ALL',z)]:
                m=evaluate(df,mode,budget)
                baseline_rows.append({'budget':budget,'mode':mode,'period':period,**{k:v for k,v in m.items() if k!='detail'}})

    # LOMO stability for each DEV-selected budget winner: fixed winner, hold month.
    lomo=[]
    for _,b in selected_df.iterrows():
        mode=str(b['mode']);budget=int(b['budget']);alpha=float(b['alpha']);beta=float(b['beta'])
        for mon in DEV:
            q=z[z.month.eq(mon)]
            mm=evaluate(q,mode,budget,alpha,beta);eq=evaluate(q,'EQUAL',budget)
            lomo.append({'budget':budget,'mode':mode,'alpha':alpha,'beta':beta,'month':mon,
                         'roi':mm['roi'],'equal_roi':eq['roi'],'delta_roi_pp':100*(mm['roi']-eq['roi']),
                         'profit_yen':mm['profit_yen'],'equal_profit_yen':eq['profit_yen']})

    grid.to_csv(OUT/'dev_grid.csv',index=False)
    pd.DataFrame(final).to_csv(OUT/'selected_by_budget.csv',index=False)
    pd.DataFrame(monthly).to_csv(OUT/'monthly_selected.csv',index=False)
    pd.DataFrame(baseline_rows).to_csv(OUT/'named_baselines.csv',index=False)
    pd.DataFrame(lomo).to_csv(OUT/'lomo_fixed_selected.csv',index=False)
    z.to_csv(OUT/'race_inputs.csv',index=False)

    result={
      'formal_equal300':formal300,
      'odds_source':'repo official_closing_odds3t closing_displayed',
      'odds_coverage_R':len(z),'odds_missing_R':len(missing),
      'budgets':list(BUDGETS),'dev_selected_by_budget':pd.DataFrame(final).to_dict('records'),
      'notes':{
        'all_races_bought':True,'all_three_tickets_min_100':True,
        'return_evaluation':'official payout100 * stake units on winning formal ticket',
        'closing_odds_usage':'allocation proxy; exact closing display is not guaranteed available at pre-deadline live order time'
      },
      'payout_prefetch':prefetch,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
