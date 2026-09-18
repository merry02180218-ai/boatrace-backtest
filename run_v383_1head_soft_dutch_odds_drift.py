#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse,json,pickle,itertools,math
import numpy as np
import pandas as pd
import run_v369_1head_ticket_rank_staking as v369
import run_v370_1head_odds_dynamic_staking as v370
import run_v374_1head_overlay_staking as ov

OUT=Path('/tmp/v383-odds-drift');OUT.mkdir(parents=True,exist_ok=True)
TH=3.5
DELTAS=(.05,.10,.15,.20)
N=1000
SEED=383

def soft_units(odds):
    o=np.asarray(odds,float);u=np.ones(3,dtype=int)
    if float(o.max()/o.min())>=TH:
        u[int(np.argmax(o))]-=1
        u[int(np.argmin(o))]+=1
    return tuple(map(int,u))

def units_from(row,odds):
    wall=bool(row['wall3']);five=bool(row['five6'])
    if wall:return (1,1,4)
    s=soft_units(odds)
    return tuple(2*x for x in s) if five else s

def settle(rows,unit_map):
    stake=ret=0
    for r in rows:
        u=unit_map[r['race_code']]
        stake+=100*sum(u)
        rank=int(r['hit_rank'])
        if rank>0:ret+=int(r['payout100'])*u[rank-1]
    return stake,ret,ret/stake if stake else 0.0

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',required=True,type=Path);a=ap.parse_args()
    x=pickle.load(a.prepared.open('rb'));rr=x['rows']['LIVE165']
    v369.install_payout_cache(rr);payouts=v369.payouts_for(rr)
    codes=[str(r['race_code']).zfill(12) for r in rr]
    odds,src=v370.load_daily_odds(codes)
    rows=[]
    for r in rr:
        code=str(r['race_code']).zfill(12)
        z=v370.formal_record(r,payouts[code],odds.get(code))
        if z is None:raise RuntimeError(f'missing odds {code}')
        wall,five=ov.flags(r)
        rows.append({**z,'wall3':int(wall),'five6':int(five)})
    base_units={r['race_code']:units_from(r,[r['o1'],r['o2'],r['o3']]) for r in rows}
    stake,ret,roi=settle(rows,base_units)
    if (stake,ret)!=(60300,88530):raise RuntimeError(f'v382 sentinel drift {stake} {ret}')
    alloc_roi=85810/60300
    official_roi=63700/49500
    rng=np.random.default_rng(SEED)
    out=[]
    for d in DELTAS:
        stable=0
        for r in rows:
            base=base_units[r['race_code']]
            if r['wall3']:
                stable+=1;continue
            seen=set()
            o=np.array([r['o1'],r['o2'],r['o3']],float)
            for signs in itertools.product((-1,1),repeat=3):
                mult=np.array([1+s*d for s in signs],float)
                seen.add(units_from(r,o*mult))
            if len(seen)==1 and next(iter(seen))==base:stable+=1
        rois=[];rets=[]
        for _ in range(N):
            um={}
            for r in rows:
                o=np.array([r['o1'],r['o2'],r['o3']],float)
                mult=rng.uniform(1-d,1+d,size=3)
                um[r['race_code']]=units_from(r,o*mult)
            st,re,rrr=settle(rows,um)
            if st!=60300:raise RuntimeError(f'stake drift {st}')
            rois.append(rrr);rets.append(re)
        aroi=np.asarray(rois)
        out.append({
          'delta':d,'stable_R':stable,'stable_share':stable/len(rows),
          'mean_roi':float(aroi.mean()),'median_roi':float(np.median(aroi)),
          'p05_roi':float(np.quantile(aroi,.05)),'p95_roi':float(np.quantile(aroi,.95)),
          'min_roi':float(aroi.min()),'max_roi':float(aroi.max()),
          'share_above_alloc':float((aroi>=alloc_roi).mean()),
          'share_above_official':float((aroi>=official_roi).mean()),
          'mean_delta_pp_vs_closing':float(100*(aroi.mean()-roi))
        })
    df=pd.DataFrame(out);df.to_csv(OUT/'stress.csv',index=False)
    result={'closing_combined':{'stake':stake,'return':ret,'roi':roi},
            'alloc_roi':alloc_roi,'official_roi':official_roi,
            'simulations_per_delta':N,'seed':SEED,'stress':out,
            'SEPTEMBER_OUTCOMES_READ':False,'PRODUCTION_CHANGED':False,'AUDIT_OK':True}
    (OUT/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
