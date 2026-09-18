#!/usr/bin/env python3
from __future__ import annotations
"""v375: fixed robustness audit for formal-overlay 2x equal staking.

No parameter search. Compare three pre-defined signals:
- EITHER = formal wall3 OR formal 5->6 fires
- FIVE6 = formal 5->6 fires
- WALL3 = formal wall3 fires
Selected races keep the same formal 3 tickets but stake 200/200/200 instead of
100/100/100. All other races stay 100/100/100.
"""
from pathlib import Path
import argparse,itertools,json
import pandas as pd

OUT=Path('/tmp/v375-overlay-staking-robustness');OUT.mkdir(parents=True,exist_ok=True)
DEV=('2026-02','2026-03','2026-04','2026-05','2026-06')
SUP=('2026-07','2026-08')
UNIVERSES=('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276')
SIGNALS={'EITHER':'either','FIVE6':'five6','WALL3':'wall3'}

def base(z):
    stake=len(z)*300
    ret=int(z.loc[z.hit.eq(1),'payout100'].sum())
    return {'R':len(z),'stake':stake,'return':ret,'profit':ret-stake,'roi':ret/stake if stake else 0.0}

def doubled(z,col):
    stake=ret=0;boost_R=0
    for r in z.itertuples():
        m=2 if int(getattr(r,col)) else 1
        boost_R+=int(m==2)
        stake+=300*m
        if int(r.hit):ret+=int(r.payout100)*m
    return {'R':len(z),'boost_R':boost_R,'stake':stake,'return':ret,
            'profit':ret-stake,'roi':ret/stake if stake else 0.0}

def compare(z,col):
    b=base(z);d=doubled(z,col)
    return {**{f'base_{k}':v for k,v in b.items()},
            **{f'double_{k}':v for k,v in d.items()},
            'delta_roi_pp':100*(d['roi']-b['roi']),
            'delta_profit':d['profit']-b['profit']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--v374-dir',required=True,type=Path);a=ap.parse_args()
    rows={}
    for u in UNIVERSES:
        p=a.v374_dir/f'rows_{u}.csv'
        if not p.exists():raise FileNotFoundError(p)
        z=pd.read_csv(p,dtype={'race_code':str});z.race_code=z.race_code.astype(str).str.zfill(12)
        rows[u]=z
    live=rows['LIVE165']
    if (len(live),int(live.hit.sum()),int(live.loc[live.hit.eq(1),'payout100'].sum()))!=(165,87,63700):
        raise RuntimeError('LIVE165 sentinel drift')

    signal_results={};monthly=[];lomo=[];subsets=[];universes=[];bands=[]
    months=sorted(live.month.unique())
    for sig,col in SIGNALS.items():
        allm=compare(live,col)
        dev=compare(live[live.month.isin(DEV)],col)
        sup=compare(live[live.month.isin(SUP)],col)
        signal_results[sig]={'all':allm,'dev':dev,'support':sup}

        for mon,g in live.groupby('month',sort=True):
            monthly.append({'signal':sig,'month':mon,**compare(g,col)})

        # Leave exactly one month out. Signal/rule is fixed; no reselection.
        for hold in months:
            q=live[live.month.ne(hold)]
            lomo.append({'signal':sig,'holdout_month':hold,**compare(q,col)})

        # All month subsets of size >=4.
        for k in range(4,len(months)+1):
            for chosen in itertools.combinations(months,k):
                q=live[live.month.isin(chosen)]
                m=compare(q,col)
                subsets.append({'signal':sig,'months':';'.join(chosen),'n_months':k,**m})

        # Full expanded universes.
        for u,z in rows.items():
            universes.append({'signal':sig,'universe':u,**compare(z,col)})

        # Disjoint env=.05 chain.
        chain=('LIVE165','H078_M375','H0775_M375','H0775_M350')
        prev=set()
        for u in chain:
            z=rows[u];ids=set(z.race_code);bid=ids-prev
            q=z[z.race_code.isin(bid)]
            bands.append({'signal':sig,'band':u if not prev else f'ADDED_TO_{u}',**compare(q,col)})
            prev=ids

    monthly_df=pd.DataFrame(monthly);lomo_df=pd.DataFrame(lomo)
    subset_df=pd.DataFrame(subsets);univ_df=pd.DataFrame(universes);band_df=pd.DataFrame(bands)

    robust={}
    for sig in SIGNALS:
        lm=lomo_df[lomo_df.signal.eq(sig)]
        ss=subset_df[subset_df.signal.eq(sig)]
        mm=monthly_df[monthly_df.signal.eq(sig)]
        robust[sig]={
          'months_positive_delta':int((mm.delta_roi_pp>0).sum()),
          'months_nonnegative_delta':int((mm.delta_roi_pp>=0).sum()),
          'months_total':len(mm),
          'lomo_positive':int((lm.delta_roi_pp>0).sum()),
          'lomo_nonnegative':int((lm.delta_roi_pp>=0).sum()),
          'lomo_total':len(lm),
          'subset_nonnegative_share':float((ss.delta_roi_pp>=0).mean()),
          'subset_positive_share':float((ss.delta_roi_pp>0).mean()),
          'subset_worst_delta_roi_pp':float(ss.delta_roi_pp.min()),
          'subset_median_delta_roi_pp':float(ss.delta_roi_pp.median()),
        }

    monthly_df.to_csv(OUT/'monthly.csv',index=False)
    lomo_df.to_csv(OUT/'leave_one_month_out.csv',index=False)
    subset_df.to_csv(OUT/'month_subsets.csv',index=False)
    univ_df.to_csv(OUT/'universes.csv',index=False)
    band_df.to_csv(OUT/'disjoint_bands.csv',index=False)

    result={
      'signals':signal_results,'robustness':robust,
      'NO_PARAMETER_SEARCH':True,'STAKE_RULE':'signal races 200/200/200; otherwise 100/100/100',
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)

if __name__=='__main__':main()
