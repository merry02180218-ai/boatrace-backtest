#!/usr/bin/env python3
"""Result-blind long-horizon confirmation for v15 rescued SES seeds.

v15 can find a hull-like patch that is excellent through 0.6 s yet loses
identity later in the 1.5 s SES tracking window. v16 keeps v15 unchanged as the
base detector and only re-checks rows that v15 had to rescue. The existing
v15 shortlist is evaluated at 0.30/0.60/0.90/1.20 s. A candidate must retain
visual persistence and dominant-motion direction over that longer interval.
Selection remains fleet-geometry aware. No race result, boat-number special
case, or race-specific offset is used.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

import auto_seed_exhibition_motion_v9 as v9
import auto_seed_exhibition_motion_v15 as v15

LONG_HORIZONS=(.30,.60,.90,1.20)


def long_eval(cap, sec, x, y, dx):
    ev=v9.eval_seed(cap,sec,x,y,dx,horizons=LONG_HORIZONS)
    dm=v15.direction_metrics(ev,x,dx)
    ok=bool(ev.get('ok',False) and dm.get('ok',False))
    return ev,dm,ok


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v16.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v16.json'))
    ap.add_argument('--long-near-best',type=float,default=.055)
    args=ap.parse_args()

    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]:
        raise SystemExit('--entry-order must contain 1..6 exactly once')

    with tempfile.TemporaryDirectory() as td:
        td=Path(td); meta15=td/'meta15.json'; seeds15=td/'seeds15.json'
        cmd=[sys.executable,'auto_seed_exhibition_motion_v15.py',str(args.video),
             '--entry-order',args.entry_order,'--nominal-sec',str(args.nominal_sec),
             '--out',str(meta15),'--seed-out',str(seeds15)]
        p=subprocess.run(cmd)
        if p.returncode!=0 or not meta15.exists():
            raise SystemExit('FAIL_CLOSED: v15 base seeding failed')
        meta=json.loads(meta15.read_text(encoding='utf-8'))
        seeds=json.loads(seeds15.read_text(encoding='utf-8'))

    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit('cannot open video')
    sec=float(meta['selected_sec']); details={}; changed=0; evals=0

    for boat in entry:
        key=str(boat); d15=meta.get('v15_details',{}).get(key,{})
        dx=float(meta['row_details'][key]['dominant_dx'])
        current=[float(seeds[key][0]),float(seeds[key][1])]
        row={'v15_seed':[round(current[0],2),round(current[1],2)],
             'v15_decision':d15.get('decision'),'long_checked':False,
             'decision':'keep_v15_nonrescued','candidates':[]}
        if d15.get('decision')=='fast_2d_direction_or_persistence_rescue':
            row['long_checked']=True
            pool=[]; seen=set()
            # v15 stores its strongest valid shortlist. Always include the chosen
            # seed even if it falls outside the displayed top candidate list.
            raw=[]
            ch=d15.get('chosen') or {}
            if 'x' in ch and 'y' in ch:
                raw.append({'x':ch['x'],'y':ch['y'],'geom_resid_norm':ch.get('geom_resid_norm',999.0),
                            'short_score':(ch.get('validation') or {}).get('score',-999.0),'source':'chosen'})
            for c in d15.get('rescue_candidates',[]):
                raw.append({'x':c['x'],'y':c['y'],'geom_resid_norm':c.get('geom_resid_norm',999.0),
                            'short_score':c.get('score',-999.0),'source':'shortlist'})
            for c in raw:
                ck=(round(float(c['x']),2),round(float(c['y']),2))
                if ck in seen: continue
                seen.add(ck); evals+=1
                ev,dm,ok=long_eval(cap,sec,float(c['x']),float(c['y']),dx)
                rec=dict(c); rec.update({'long_validation':ev,'long_direction':dm,'long_ok':ok})
                row['candidates'].append(rec)
                if ok: pool.append(rec)
            if not pool:
                cap.release()
                raise SystemExit(f'FAIL_CLOSED: no long-horizon persistent rescue for boat {boat}')
            best=max(float(c['long_validation']['score']) for c in pool)
            near=[c for c in pool if float(c['long_validation']['score'])>=best-args.long_near_best]
            chosen=min(near,key=lambda c:(float(c.get('geom_resid_norm',999.0)),
                                          -float(c['long_validation']['score']),
                                          -float(c.get('short_score',-999.0))))
            nx,ny=float(chosen['x']),float(chosen['y'])
            if abs(nx-current[0])>1e-6 or abs(ny-current[1])>1e-6: changed+=1
            seeds[key]=[round(nx,2),round(ny,2)]
            row['decision']='long_horizon_confirmed_rescue'
            row['chosen']={'x':round(nx,2),'y':round(ny,2),
                           'long_score':chosen['long_validation']['score'],
                           'long_median_ncc':chosen['long_validation']['median_ncc'],
                           'long_min_ncc':chosen['long_validation']['min_ncc'],
                           'long_direction':chosen['long_direction'],
                           'geom_resid_norm':chosen.get('geom_resid_norm'),
                           'short_score':chosen.get('short_score')}
        details[key]=row

    cap.release()
    ys=np.array([float(seeds[str(b)][1]) for b in entry],float)
    xs=np.array([float(seeds[str(b)][0]) for b in entry],float)
    if not np.array_equal(np.argsort(ys),np.arange(6)):
        raise SystemExit('FAIL_CLOSED: v16 final y-order changed')
    height=float(meta['frame_size'][1]); width=float(meta['frame_size'][0])
    gaps=np.diff(ys); xj=np.abs(np.diff(xs))
    if np.any(gaps < .015*height) or np.any(gaps > .20*height):
        raise SystemExit('FAIL_CLOSED: v16 final row spacing implausible')
    if np.max(xj)>.20*width:
        raise SystemExit('FAIL_CLOSED: v16 final fleet horizontal separation implausible')

    payload=dict(meta)
    payload.update({'method':'v15 fast 2D rescue + rescued-row 1.2s long-horizon persistence/direction confirmation',
                    'v16_result_blind':True,'race_results_read':False,
                    'seeds':seeds,'v16_changed_from_v15_count':changed,
                    'v16_long_eval_count':evals,'v16_details':details,
                    'v16_long_horizons_sec':list(LONG_HORIZONS),
                    'v16_final_y_gaps':[round(float(x),2) for x in gaps],
                    'v16_final_adj_x_jumps':[round(float(x),2) for x in xj],
                    'warning':'EXPERIMENTAL result-blind seed v16; long-horizon confirmation is technical video validation only.'})
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
