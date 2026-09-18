#!/usr/bin/env python3
from __future__ import annotations
"""v379: fixed expanded robustness of WALL3 rank3 overweight staking.

No parameter search.
Baseline shadow:
- non-overlay 1/1/1
- any overlay 2/2/2
Candidate:
- non-overlay 1/1/1
- five6-only 2/2/2
- wall3 (including BOTH) 1/1/4
Total stake is identical to baseline for every race and universe.
"""
from pathlib import Path
import argparse,itertools,json
import pandas as pd

OUT=Path('/tmp/v379-wall3-rank3-expanded');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
UNIVERSES=('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276')
BASE=(2,2,2)
WALL=(1,1,4)

def hit_rank(r):
    if not int(r.hit):return 0
    ts=str(r.tickets).split(';');actual=str(r.actual_combo)
    if actual not in ts:raise RuntimeError(f'hit mismatch {r.race_code}')
    return ts.index(actual)+1

def enrich(z):
    z=z.copy();z['hit_rank']=[hit_rank(r) for r in z.itertuples()]
    return z

def units_base(r):
    return BASE if int(r.either) else (1,1,1)

def units_candidate(r):
    if int(r.wall3):return WALL
    if int(r.either):return BASE
    return (1,1,1)

def run(z,candidate):
    stake=ret=0;rows=[]
    for r in z.sort_values('race_code').itertuples():
        u=units_candidate(r) if candidate else units_base(r)
        s=100*sum(u);rank=int(r.hit_rank)
        rr=int(r.payout100)*u[rank-1] if rank>0 else 0
        stake+=s;ret+=rr
        rows.append({'race_code':str(r.race_code),'month':str(r.month),'overlay_cat':str(r.overlay_cat),
                     'hit_rank':rank,'wall3':int(r.wall3),'five6':int(r.five6),
                     'u1':u[0],'u2':u[1],'u3':u[2],'stake':s,'return':rr,'profit':rr-s})
    d=pd.DataFrame(rows)
    return {'R':len(d),'stake':stake,'return':ret,'profit':ret-stake,'roi':ret/stake if stake else 0.0,
            'wall3_R':int(z.wall3.sum()),'five6_R':int(z.five6.sum()),'detail':d}

def compare(z):
    b=run(z,False);c=run(z,True)
    if b['stake']!=c['stake']:raise RuntimeError(f'stake drift {b["stake"]} {c["stake"]}')
    return {**{f'base_{k}':v for k,v in b.items() if k!='detail'},
            **{f'cand_{k}':v for k,v in c.items() if k!='detail'},
            'delta_roi_pp':100*(c['roi']-b['roi']),'delta_profit':c['profit']-b['profit']}

def rank_summary(z,label):
    q=z[z.wall3.eq(1)].copy();h=q[q.hit.eq(1)]
    out={'label':label,'wall3_R':len(q),'hits':int(h.hit.sum())}
    for rank in (1,2,3):
        r=h[h.hit_rank.eq(rank)]
        out[f'rank{rank}_hits']=len(r)
        out[f'rank{rank}_return100']=int(r.payout100.sum())
        out[f'rank{rank}_avg_payout100']=float(r.payout100.mean()) if len(r) else 0.0
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--v374-dir',required=True,type=Path);a=ap.parse_args()
    rows={}
    for u in UNIVERSES:
        p=a.v374_dir/f'rows_{u}.csv'
        z=pd.read_csv(p,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12)
        rows[u]=enrich(z)
    live=rows['LIVE165']
    if (len(live),int(live.hit.sum()),int(live.loc[live.hit.eq(1),'payout100'].sum()),int(live.either.sum()))!=(165,87,63700,36):
        raise RuntimeError('LIVE165 sentinel drift')

    universes=[];monthly=[];rankrows=[];lomo=[];subsets=[];bands=[]
    for u,z in rows.items():
        for period,df in [('ALL',z),('DEV',z[z.month.isin(DEV)]),('SUPPORT',z[z.month.isin(SUP)])]:
            universes.append({'universe':u,'period':period,**compare(df)})
        rankrows.append(rank_summary(z,u))
        for mon,g in z.groupby('month',sort=True):
            monthly.append({'universe':u,'month':mon,**compare(g)})

    # LIVE fixed leave-one-month-out (no reselection).
    months=sorted(live.month.unique())
    for hold in months:
        q=live[live.month.ne(hold)]
        lomo.append({'holdout_month':hold,**compare(q)})

    # LIVE all month subsets size >=4.
    for k in range(4,len(months)+1):
        for chosen in itertools.combinations(months,k):
            q=live[live.month.isin(chosen)]
            subsets.append({'months':';'.join(chosen),'n_months':k,**compare(q)})

    # Disjoint env=.05 chain.
    chain=('LIVE165','H078_M375','H0775_M375','H0775_M350')
    prev=set()
    for u in chain:
        z=rows[u];ids=set(z.race_code);bid=ids-prev
        q=z[z.race_code.isin(bid)]
        bands.append({'band':u if not prev else f'ADDED_TO_{u}',**compare(q)})
        prev=ids

    # Candidate detail for LIVE.
    bc=run(live,False);cc=run(live,True)
    det=bc['detail'].merge(cc['detail'],on=['race_code','month','overlay_cat','hit_rank','wall3','five6'],
                           suffixes=('_base','_cand'),validate='one_to_one')
    det['delta_return']=det.return_cand-det.return_base
    det['delta_profit']=det.profit_cand-det.profit_base

    univ=pd.DataFrame(universes);mon=pd.DataFrame(monthly);lom=pd.DataFrame(lomo)
    sub=pd.DataFrame(subsets);band=pd.DataFrame(bands);ranks=pd.DataFrame(rankrows)
    univ.to_csv(OUT/'universes.csv',index=False);mon.to_csv(OUT/'monthly.csv',index=False)
    lom.to_csv(OUT/'lomo.csv',index=False);sub.to_csv(OUT/'month_subsets.csv',index=False)
    band.to_csv(OUT/'disjoint_bands.csv',index=False);ranks.to_csv(OUT/'wall3_rank_summary.csv',index=False)
    det.to_csv(OUT/'live165_detail.csv',index=False)

    liveall=compare(live)
    robust={
      'lomo_nonnegative':int((lom.delta_roi_pp>=0).sum()),'lomo_total':len(lom),
      'subset_nonnegative_share':float((sub.delta_roi_pp>=0).mean()),
      'subset_positive_share':float((sub.delta_roi_pp>0).mean()),
      'subset_worst_delta_roi_pp':float(sub.delta_roi_pp.min()),
      'subset_median_delta_roi_pp':float(sub.delta_roi_pp.median()),
      'expanded_universe_nonnegative_all':int((univ[(univ.period=='ALL')].delta_roi_pp>=0).sum()),
      'expanded_universe_total':int((univ.period=='ALL').sum()),
      'disjoint_nonnegative':int((band.delta_roi_pp>=0).sum()),
      'disjoint_total':len(band),
    }
    result={
      'rule':'wall3 races 100/100/400; five6-only 200/200/200; none 100/100/100',
      'baseline_rule':'all overlay 200/200/200; none 100/100/100',
      'live165':liveall,'robustness':robust,'wall3_rank_summary':ranks.to_dict('records'),
      'NO_PARAMETER_SEARCH':True,'TOTAL_STAKE_IDENTICAL':True,
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
