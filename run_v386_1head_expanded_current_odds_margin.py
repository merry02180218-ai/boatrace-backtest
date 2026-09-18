#!/usr/bin/env python3
from __future__ import annotations
"""v386: expanded-universe safety-margin audit for the fixed v382 allocation rule.

Uses two frozen artifacts:
- v374 overlay rows (formal tickets, payout100, wall3/five6 flags)
- v374 soft-Dutch rows (closing odds ratio and threshold3.5 units)

No tuning on expanded/support data. Thresholds are mechanically derived from
the v382 core 3.5 using the v385 safety formula.
"""
from pathlib import Path
import argparse,json,math
import pandas as pd

OUT=Path('/tmp/v386-expanded-current-odds-margin');OUT.mkdir(parents=True,exist_ok=True)
UNIVERSES=('LIVE165','H078_M375','H0775_M375','H0775_M350','PROD276')
CORE=3.5
DRIFTS=(0.00,0.05,0.10,0.15,0.20)

def ceil_tenth(x):
    return math.ceil((x-1e-12)*10)/10

def load(overlay_dir,soft_dir,name):
    o=pd.read_csv(overlay_dir/f'rows_{name}.csv',dtype={'race_code':str})
    s=pd.read_csv(soft_dir/f'{name}_race_level.csv',dtype={'race_code':str})
    o.race_code=o.race_code.str.zfill(12);s.race_code=s.race_code.str.zfill(12)
    z=o.merge(s[['race_code','odds_ratio','u1','u2','u3','changed']],on='race_code',validate='one_to_one')
    return z

def eval_policy(z,t):
    stake=ret=softR=0
    detail=[]
    for _,r in z.iterrows():
        ts=str(r.tickets).split(';')
        rank=(ts.index(str(r.actual_combo))+1) if str(r.actual_combo) in ts else 0
        if int(r.wall3):
            units=[1,1,4];use=False
        elif int(r.five6):
            use=bool(float(r.odds_ratio)>=t-1e-12 and int(r.changed)==1)
            units=[2*int(r.u1),2*int(r.u2),2*int(r.u3)] if use else [2,2,2]
        else:
            use=bool(float(r.odds_ratio)>=t-1e-12 and int(r.changed)==1)
            units=[int(r.u1),int(r.u2),int(r.u3)] if use else [1,1,1]
        st=100*sum(units);rt=int(r.payout100)*units[rank-1] if rank else 0
        stake+=st;ret+=rt;softR+=int(use)
        detail.append({'race_code':str(r.race_code),'month':str(r.month),'stake':st,'return':rt,'profit':rt-st,'use_soft':int(use)})
    d=pd.DataFrame(detail)
    return {'R':len(z),'stake_yen':stake,'return_yen':ret,'profit_yen':ret-stake,'roi':ret/stake if stake else 0.0,'soft_changed_R':softR},d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--overlay-dir',required=True,type=Path)
    ap.add_argument('--soft-dir',required=True,type=Path)
    a=ap.parse_args()
    result_rows=[];band_rows=[]
    data={u:load(a.overlay_dir,a.soft_dir,u) for u in UNIVERSES}
    for d in DRIFTS:
        exact=CORE*(1+d)/(1-d);t=ceil_tenth(exact)
        for u in UNIVERSES:
            m,_=eval_policy(data[u],t)
            result_rows.append({'assumed_drift':d,'threshold':t,'universe':u,**m})
        # disjoint nested env=.05 chain
        chain=('LIVE165','H078_M375','H0775_M375','H0775_M350')
        prev=set()
        for u in chain:
            z=data[u];ids=set(z.race_code)
            bid=ids-prev
            b=z[z.race_code.isin(bid)].copy()
            m,_=eval_policy(b,t)
            band_rows.append({'assumed_drift':d,'threshold':t,'band':u if not prev else f'ADDED_TO_{u}',**m})
            prev=ids
    res=pd.DataFrame(result_rows);bands=pd.DataFrame(band_rows)
    res.to_csv(OUT/'universes.csv',index=False);bands.to_csv(OUT/'bands.csv',index=False)
    # Sentinel expected at core 3.5 from v382/v374.
    x=res[(res.assumed_drift.eq(0))&(res.universe.eq('LIVE165'))].iloc[0]
    if (int(x.stake_yen),int(x.return_yen))!=(60300,88530):raise RuntimeError(f'v382 sentinel drift {x.to_dict()}')
    result={
      'core_threshold':CORE,
      'formula':'ceil_0.1(3.5*(1+d)/(1-d))',
      'universes':res.to_dict('records'),
      'bands':bands.to_dict('records'),
      'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True
    }
    (OUT/'result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    print(json.dumps(result,indent=2,default=str),flush=True)
if __name__=='__main__':main()
