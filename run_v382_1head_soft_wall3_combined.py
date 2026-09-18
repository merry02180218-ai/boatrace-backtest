#!/usr/bin/env python3
from __future__ import annotations
"""v382: fixed combination of soft-Dutch and WALL3 rank3 allocation.

No parameter search. Inputs are frozen artifacts:
- v374 overlay rows (formal ticket/overlay identity)
- v374 soft-Dutch expanded rows (fixed threshold 3.5 allocations)

Policies:
OFFICIAL: 1/1/1 every race.
SOFT: fixed v372 soft-Dutch 300-yen allocation.
ALLOC: v379 rule: WALL3 1/1/4; five6-only 2/2/2; none 1/1/1.
COMBINED:
  WALL3 -> 1/1/4
  five6-only -> 2x soft units (2/2/2 or scaled 4/2/0)
  none -> soft units
ALLOC and COMBINED have identical total stake race-by-race.
"""
from pathlib import Path
import argparse,json,math
import pandas as pd
import numpy as np

OUT=Path('/tmp/v382-soft-wall3-combined');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
UNIVERSES=('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276')
CHAIN=('LIVE165','H078_M375','H0775_M375','H0775_M350')

def load_pair(overlay_dir,soft_dir,name):
    a=pd.read_csv(overlay_dir/f'rows_{name}.csv',dtype={'race_code':str})
    b=pd.read_csv(soft_dir/f'{name}_race_level.csv',dtype={'race_code':str})
    a['race_code']=a.race_code.astype(str).str.zfill(12)
    b['race_code']=b.race_code.astype(str).str.zfill(12)
    # overlay artifact may not carry hit_rank; derive from frozen formal ticket order.
    if 'hit_rank' not in a.columns:
        def hr(r):
            if int(r.hit)==0:return 0
            ts=str(r.tickets).split(';');actual=str(r.actual_combo)
            if actual not in ts:raise RuntimeError(f'hit/ticket mismatch {r.race_code}')
            return ts.index(actual)+1
        a['hit_rank']=a.apply(hr,axis=1)
    keep=['race_code','hit_rank','u1','u2','u3','changed','lost_hit','odds_ratio']
    q=a.merge(b[keep],on='race_code',how='inner',suffixes=('','_soft'),validate='one_to_one')
    if len(q)!=len(a) or len(q)!=len(b):raise RuntimeError(f'{name} merge drift {len(a)} {len(b)} {len(q)}')
    if not (q.hit_rank.astype(int)==q.hit_rank_soft.astype(int)).all():
        bad=q[q.hit_rank.astype(int)!=q.hit_rank_soft.astype(int)].head()
        raise RuntimeError(f'{name} hit rank mismatch {bad.to_dict("records")}')
    if int(q.lost_hit.sum())!=0:raise RuntimeError(f'{name} soft artifact has lost hits {int(q.lost_hit.sum())}')
    return q

def units(row,policy):
    wall=bool(int(row.wall3));five=bool(int(row.five6))
    soft=(int(row.u1),int(row.u2),int(row.u3))
    if sum(soft)!=3:raise RuntimeError(f'bad soft units {row.race_code} {soft}')
    if policy=='OFFICIAL':return (1,1,1)
    if policy=='SOFT':return soft
    if policy=='ALLOC':
        if wall:return (1,1,4)
        if five:return (2,2,2)
        return (1,1,1)
    if policy=='COMBINED':
        if wall:return (1,1,4)
        if five:return tuple(2*x for x in soft)
        return soft
    raise ValueError(policy)

def run(z,policy,detail=False):
    rows=[];stake=ret=lost=0
    for r in z.sort_values('race_code').itertuples():
        u=units(r,policy);s=100*sum(u);rank=int(r.hit_rank)
        rr=int(r.payout100)*u[rank-1] if rank>0 and u[rank-1]>0 else 0
        is_lost=int(rank>0 and u[rank-1]==0)
        stake+=s;ret+=rr;lost+=is_lost
        if detail:
            rows.append({'race_code':str(r.race_code),'month':str(r.month),'overlay_cat':str(r.overlay_cat),
                         'wall3':int(r.wall3),'five6':int(r.five6),'hit_rank':rank,
                         'soft_changed':int(r.changed),'odds_ratio':float(r.odds_ratio),
                         'u1':u[0],'u2':u[1],'u3':u[2],'stake':s,'return':rr,
                         'profit':rr-s,'lost_hit':is_lost})
    return {'R':len(z),'hits':int((z.hit_rank.astype(int)>0).sum()),'lost_hits':lost,
            'stake':stake,'return':ret,'profit':ret-stake,'roi':ret/stake if stake else 0.0,
            'detail':pd.DataFrame(rows)}

def risk(detail):
    d=detail.sort_values('race_code').copy()
    p=d.profit.astype(float).to_numpy()
    cum=np.cumsum(p);curve=np.concatenate(([0.0],cum))
    peaks=np.maximum.accumulate(curve);dd=peaks-curve
    maxdd=float(dd.max())
    end=int(np.argmax(dd))
    start=int(np.argmax(curve[:end+1])) if end>0 else 0
    def worst_window(n):
        if len(p)<n:return float(p.sum())
        return float(min(p[i:i+n].sum() for i in range(len(p)-n+1)))
    longest=cur=0
    for x in p:
        if x<0:cur+=1;longest=max(longest,cur)
        else:cur=0
    monthly=d.groupby('month').profit.sum()
    return {'max_drawdown_yen':maxdd,'drawdown_span_R':max(0,end-start),
            'longest_losing_streak':longest,'worst10R_profit':worst_window(10),
            'worst20R_profit':worst_window(20),
            'monthly_profit_std':float(monthly.std(ddof=0)) if len(monthly) else 0.0,
            'worst_month_profit':float(monthly.min()) if len(monthly) else 0.0,
            'profit_per_maxdd':float(d.profit.sum()/maxdd) if maxdd>0 else None}

def compare(z,label):
    out={'label':label}
    res={}
    for p in ('OFFICIAL','SOFT','ALLOC','COMBINED'):
        r=run(z,p,detail=True);res[p]=r
        for k,v in r.items():
            if k!='detail':out[f'{p.lower()}_{k}']=v
    if res['ALLOC']['stake']!=res['COMBINED']['stake']:
        raise RuntimeError(f'stake mismatch {label} alloc={res["ALLOC"]["stake"]} combined={res["COMBINED"]["stake"]}')
    out['combined_delta_roi_pp_vs_alloc']=100*(res['COMBINED']['roi']-res['ALLOC']['roi'])
    out['combined_delta_profit_vs_alloc']=res['COMBINED']['profit']-res['ALLOC']['profit']
    out['combined_delta_roi_pp_vs_soft']=100*(res['COMBINED']['roi']-res['SOFT']['roi'])
    return out,res

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--overlay-dir',required=True,type=Path)
    ap.add_argument('--soft-dir',required=True,type=Path)
    a=ap.parse_args()
    frames={u:load_pair(a.overlay_dir,a.soft_dir,u) for u in UNIVERSES}
    live=frames['LIVE165']
    # Core sentinels from frozen upstream audits.
    off=run(live,'OFFICIAL')
    soft=run(live,'SOFT')
    alloc=run(live,'ALLOC')
    if (off['R'],off['hits'],off['stake'],off['return'])!=(165,87,49500,63700):
        raise RuntimeError(f'official sentinel drift {off}')
    if (soft['stake'],soft['return'])!=(49500,66510):
        raise RuntimeError(f'soft sentinel drift {soft}')
    if (alloc['stake'],alloc['return'])!=(60300,85810):
        raise RuntimeError(f'alloc sentinel drift {alloc}')

    summaries=[];details={}
    for name,z in frames.items():
        allc,res=compare(z,f'{name}:ALL');allc['universe']=name;allc['period']='ALL';summaries.append(allc)
        for period,months in [('DEV',DEV),('SUPPORT',SUP)]:
            q=z[z.month.isin(months)].copy()
            c,_=compare(q,f'{name}:{period}');c['universe']=name;c['period']=period;summaries.append(c)
        if name=='LIVE165':
            for p in ('OFFICIAL','SOFT','ALLOC','COMBINED'):
                details[p]=res[p]['detail']
                res[p]['detail'].to_csv(OUT/f'live_{p.lower()}_detail.csv',index=False)

    summary=pd.DataFrame(summaries)
    # Disjoint bands.
    bands=[];prev=set()
    for name in CHAIN:
        z=frames[name];ids=set(z.race_code.astype(str));bid=ids-prev
        q=z[z.race_code.astype(str).isin(bid)].copy()
        c,_=compare(q,name if not prev else f'ADDED_TO_{name}')
        c['band']=name if not prev else f'ADDED_TO_{name}';bands.append(c);prev=ids
    band=pd.DataFrame(bands)

    # LIVE monthly and risk.
    monthly=[]
    for mon,g in live.groupby('month',sort=True):
        c,_=compare(g,str(mon));c['month']=mon;monthly.append(c)
    monthly=pd.DataFrame(monthly)
    risks=[]
    for p,d in details.items():
        r=risk(d);r['policy']=p;r['profit']=float(d.profit.sum());r['stake']=float(d.stake.sum())
        risks.append(r)
    risks=pd.DataFrame(risks)

    # Policy interaction diagnostics.
    comb=details['COMBINED']
    interaction={
      'live_soft_changed_R':int(live.changed.sum()),
      'live_wall3_R':int(live.wall3.sum()),
      'live_five6_only_R':int(((live.five6==1)&(live.wall3==0)).sum()),
      'soft_changed_on_wall3_R':int(((live.changed==1)&(live.wall3==1)).sum()),
      'soft_changed_on_five6_only_R':int(((live.changed==1)&(live.five6==1)&(live.wall3==0)).sum()),
      'soft_changed_on_none_R':int(((live.changed==1)&(live.wall3==0)&(live.five6==0)).sum()),
      'combined_lost_hits':int(comb.lost_hit.sum()),
    }

    summary.to_csv(OUT/'summary.csv',index=False)
    band.to_csv(OUT/'disjoint_bands.csv',index=False)
    monthly.to_csv(OUT/'monthly_live165.csv',index=False)
    risks.to_csv(OUT/'risk_live165.csv',index=False)

    live_all=summary[(summary.universe=='LIVE165')&(summary.period=='ALL')].iloc[0].to_dict()
    result={
      'fixed_rules':{
        'soft_threshold':3.5,
        'wall3_units':[1,1,4],
        'five6_only_combined':'2x fixed soft units',
        'none_combined':'fixed soft units',
      },
      'live165':live_all,
      'interaction':interaction,
      'expanded_all_nonnegative_vs_alloc':int(((summary[summary.period=='ALL'].combined_delta_roi_pp_vs_alloc)>=-1e-12).sum()),
      'expanded_all_total':int((summary.period=='ALL').sum()),
      'disjoint_nonnegative_vs_alloc':int((band.combined_delta_roi_pp_vs_alloc>=-1e-12).sum()),
      'disjoint_total':len(band),
      'risk':risks.to_dict('records'),
      'NO_PARAMETER_SEARCH':True,
      'TOTAL_STAKE_IDENTICAL_VS_ALLOC':True,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
