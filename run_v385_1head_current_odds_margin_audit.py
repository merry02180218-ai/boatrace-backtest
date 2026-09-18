#!/usr/bin/env python3
from __future__ import annotations
"""v385: deterministic current-odds safety-margin audit.

No new outcome-based parameter search.  Starting from v382 threshold 3.5, derive
a conservative current-odds ratio threshold for an assumed symmetric relative
odds drift +/-d:
    T_safe = 3.5 * (1+d)/(1-d)

Race-level v382/v379 results are reused.  For non-WALL3 races:
- closing ratio >= candidate threshold -> use v382 combined allocation
- otherwise -> use v379 allocation
WALL3 allocation is odds-independent and unchanged.
"""
from pathlib import Path
import argparse, json, math
import pandas as pd

OUT=Path('/tmp/v385-current-odds-margin'); OUT.mkdir(parents=True,exist_ok=True)
CORE=3.5
DRIFTS=(0.00,0.05,0.10,0.15,0.20)
DEV={'2026-02','2026-03','2026-04','2026-05','2026-06'}
SUP={'2026-07','2026-08'}

def ceil_tenth(x:float)->float:
    return math.ceil((x-1e-12)*10.0)/10.0

def risk(profits:list[float]):
    eq=[];s=0.0
    for p in profits:
        s+=float(p);eq.append(s)
    peak=0.0;maxdd=0.0
    for e in eq:
        peak=max(peak,e)
        maxdd=max(maxdd,peak-e)
    def worst_window(n:int):
        if not profits:return 0.0
        if len(profits)<n:return float(sum(profits))
        return min(sum(profits[i:i+n]) for i in range(len(profits)-n+1))
    return {'max_drawdown_yen':maxdd,'worst10R_yen':worst_window(10),'worst20R_yen':worst_window(20)}

def summarize(z:pd.DataFrame):
    stake=int(z.stake.sum()); ret=int(z['return'].sum()); profit=ret-stake
    out={'R':len(z),'stake_yen':stake,'return_yen':ret,'profit_yen':profit,
         'roi':ret/stake if stake else 0.0,'soft_changed_R':int(z.use_soft.sum())}
    out.update(risk(z.profit.tolist()))
    return out

def apply_threshold(alloc:pd.DataFrame, comb:pd.DataFrame, threshold:float):
    key=['race_code','month','overlay_cat','wall3','five6','hit_rank','odds_ratio']
    a=alloc.copy(); c=comb.copy()
    # Race identity/order guard.
    if a.race_code.astype(str).tolist()!=c.race_code.astype(str).tolist():
        raise RuntimeError('race order mismatch alloc vs combined')
    z=a[key+['stake','return','profit']].rename(columns={'stake':'alloc_stake','return':'alloc_return','profit':'alloc_profit'})
    z=z.merge(c[['race_code','stake','return','profit','soft_changed']],
              on='race_code',how='left',validate='one_to_one',
              suffixes=('','_combined'))
    # Only non-WALL3 races are odds-sensitive in v382.
    z['use_soft']=(z.wall3.eq(0)&z.odds_ratio.ge(threshold-1e-12)&z.soft_changed.eq(1))
    z['stake']=z.alloc_stake.where(~z.use_soft,z.stake)
    z['return']=z.alloc_return.where(~z.use_soft,z['return'])
    # merge collision handling: after merge, combined columns may be bare because
    # alloc columns were renamed before merge.
    if 'profit' not in z.columns:
        raise RuntimeError(f'combined profit missing columns={list(z.columns)}')
    z['profit']=z.alloc_profit.where(~z.use_soft,z.profit)
    return z

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--artifact-dir',required=True,type=Path)
    a=ap.parse_args()
    alloc=pd.read_csv(a.artifact_dir/'live_alloc_detail.csv',dtype={'race_code':str})
    comb=pd.read_csv(a.artifact_dir/'live_combined_detail.csv',dtype={'race_code':str})
    alloc.race_code=alloc.race_code.str.zfill(12); comb.race_code=comb.race_code.str.zfill(12)
    if len(alloc)!=165 or len(comb)!=165: raise RuntimeError(f'LIVE165 drift alloc={len(alloc)} comb={len(comb)}')

    # Sentinels.
    alloc_m={'stake':int(alloc.stake.sum()),'return':int(alloc['return'].sum())}
    comb_m={'stake':int(comb.stake.sum()),'return':int(comb['return'].sum())}
    if alloc_m!={'stake':60300,'return':85810}:raise RuntimeError(f'v379 sentinel drift {alloc_m}')
    if comb_m!={'stake':60300,'return':88530}:raise RuntimeError(f'v382 sentinel drift {comb_m}')

    rows=[]; monthly=[]
    for d in DRIFTS:
        exact=CORE*(1+d)/(1-d)
        practical=ceil_tenth(exact)
        for mode,t in [('EXACT',exact),('CEIL_0P1',practical)]:
            z=apply_threshold(alloc,comb,t)
            allm=summarize(z)
            devm=summarize(z[z.month.isin(DEV)])
            supm=summarize(z[z.month.isin(SUP)])
            months=[]
            for mon,g in z.groupby('month',sort=True):
                mm=summarize(g); months.append({'drift':d,'mode':mode,'threshold':t,'month':mon,**mm})
            monthly.extend(months)
            worst=min(months,key=lambda x:x['profit_yen']) if months else None
            rows.append({
              'assumed_drift':d,'mode':mode,'threshold':t,
              **{f'all_{k}':v for k,v in allm.items()},
              **{f'dev_{k}':v for k,v in devm.items()},
              **{f'support_{k}':v for k,v in supm.items()},
              'worst_month':worst['month'] if worst else None,
              'worst_month_profit_yen':worst['profit_yen'] if worst else None,
              'delta_roi_pp_vs_alloc':100*(allm['roi']-85810/60300),
              'delta_roi_pp_vs_v382':100*(allm['roi']-88530/60300),
            })
    df=pd.DataFrame(rows)
    mon=pd.DataFrame(monthly)
    df.to_csv(OUT/'thresholds.csv',index=False)
    mon.to_csv(OUT/'monthly.csv',index=False)

    # For each drift, report practical rule only as implementation candidate.
    practical=df[df['mode'].eq('CEIL_0P1')].copy()
    result={
      'core_threshold':CORE,
      'v379_alloc':{'stake_yen':60300,'return_yen':85810,'roi':85810/60300},
      'v382_closing':{'stake_yen':60300,'return_yen':88530,'roi':88530/60300},
      'formula':'T_safe = 3.5 * (1+d)/(1-d); practical threshold = ceil(T_safe, 0.1)',
      'practical':practical.to_dict('records'),
      'SEPTEMBER_OUTCOMES_READ':False,
      'PRODUCTION_CHANGED':False,
      'AUDIT_OK':True,
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
