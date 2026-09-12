#!/usr/bin/env python3
"""Persistence-rescue fleet-consistent SES auto seeding v12.

v12 keeps v11's result-blind candidate-time/geometry selection and v9's
multi-horizon persistence logic, but adds one conservative rescue path for a
failure mode seen on independent September video: a motion-row seed can land on
wake/background even when its row geometry looks plausible.

Principle:
- first run v11 unchanged;
- evaluate the FINAL v11 seed of every row over 0.6 s using v9.eval_seed;
- keep every seed whose persistence passes;
- only for a seed whose persistence FAILS, search a small resolution-relative
  horizontal offset grid;
- require candidate persistence to pass;
- prefer candidates that remain consistent with the local fleet x-vs-y shape;
- never use race results or boat-number-specific offsets.

This is intentionally fail-closed and does not relax tracker quality gates.
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


def expected_x_from_neighbors(xs, ys, i):
    n=len(xs)
    if 0<i<n-1:
        y0,y1=ys[i-1],ys[i+1]
        if abs(y1-y0)<1e-6: return float((xs[i-1]+xs[i+1])/2.0)
        a=(ys[i]-y0)/(y1-y0)
        return float(xs[i-1]+a*(xs[i+1]-xs[i-1]))
    if i==0 and n>=3:
        y0,y1=ys[1],ys[2]
        if abs(y1-y0)<1e-6: return float(xs[1])
        slope=(xs[2]-xs[1])/(y1-y0)
        return float(xs[1]+slope*(ys[0]-ys[1]))
    if i==n-1 and n>=3:
        y0,y1=ys[n-3],ys[n-2]
        if abs(y1-y0)<1e-6: return float(xs[n-2])
        slope=(xs[n-2]-xs[n-3])/(y1-y0)
        return float(xs[n-2]+slope*(ys[n-1]-ys[n-2]))
    return float(xs[i])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v12.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v12.json'))
    ap.add_argument('--rescue-max-frac',type=float,default=.085,
                    help='max horizontal rescue radius as fraction of frame width')
    ap.add_argument('--visual-near-best',type=float,default=.05,
                    help='within this score of best visual candidate, prefer fleet geometry')
    ap.add_argument('--max-final-neighbor-jump-frac',type=float,default=.20)
    args=ap.parse_args()

    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]:
        raise SystemExit('--entry-order must contain 1..6 exactly once')

    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        meta11=td/'meta11.json'; seeds11=td/'seeds11.json'
        cmd=[sys.executable,'auto_seed_exhibition_motion_v11.py',str(args.video),
             '--entry-order',args.entry_order,'--nominal-sec',str(args.nominal_sec),
             '--out',str(meta11),'--seed-out',str(seeds11)]
        p=subprocess.run(cmd)
        if p.returncode!=0 or not meta11.exists() or not seeds11.exists():
            raise SystemExit('FAIL_CLOSED: v11 base seeding failed')
        meta=json.loads(meta11.read_text(encoding='utf-8'))
        seeds=json.loads(seeds11.read_text(encoding='utf-8'))

    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened(): raise SystemExit('cannot open video')
    width=float(meta['frame_size'][0])
    selected_sec=float(meta['selected_sec'])
    xs=np.array([float(seeds[str(b)][0]) for b in entry],dtype=float)
    ys=np.array([float(seeds[str(b)][1]) for b in entry],dtype=float)
    base_xs=xs.copy()
    details={}
    rescued=0

    # Resolution-relative offset grid: 40 px increments at 1920 width, bounded
    # by rescue-max-frac. Search is only invoked for a failed base persistence.
    unit=max(18.0,width/48.0)
    max_shift=max(unit,float(args.rescue_max_frac*width))
    kmax=max(1,int(round(max_shift/unit)))
    offsets=[float(k*unit) for k in range(-kmax,kmax+1) if k!=0]

    for i,boat in enumerate(entry):
        dx=float(meta['row_details'][str(boat)]['dominant_dx'])
        bx=float(xs[i]); cy=float(ys[i])
        base_eval=v9.eval_seed(cap,selected_sec,bx,cy,dx)
        row={'base_seed':[round(bx,2),round(cy,2)],'base_validation':base_eval,
             'decision':'keep_v11_persistent','rescue_candidates':[]}
        if not base_eval.get('ok',False):
            expected=expected_x_from_neighbors(xs,ys,i)
            candidates=[]
            for off in offsets:
                cx=bx+off
                if cx<30 or cx>width-30: continue
                ev=v9.eval_seed(cap,selected_sec,cx,cy,dx)
                if not ev.get('ok',False): continue
                trial=xs.copy(); trial[i]=cx
                left_jump=abs(trial[i]-trial[i-1]) if i>0 else 0.0
                right_jump=abs(trial[i+1]-trial[i]) if i+1<len(trial) else 0.0
                max_neighbor=max(left_jump,right_jump)
                if max_neighbor>args.max_final_neighbor_jump_frac*width:
                    continue
                geom_resid=abs(cx-expected)
                candidates.append({'x':float(cx),'offset':float(off),'eval':ev,
                                   'expected_x':float(expected),'geom_resid':float(geom_resid),
                                   'max_neighbor_jump':float(max_neighbor)})
            if not candidates:
                cap.release(); raise SystemExit(f'FAIL_CLOSED: no persistent fleet-consistent rescue for boat {boat}')
            best_visual=max(c['eval']['score'] for c in candidates)
            near=[c for c in candidates if c['eval']['score']>=best_visual-args.visual_near_best]
            chosen=min(near,key=lambda c:(c['geom_resid'],-c['eval']['score'],abs(c['offset'])))
            xs[i]=chosen['x']; seeds[str(boat)]=[round(float(chosen['x']),2),round(cy,2)]
            rescued+=1
            row['decision']='rescue_failed_persistence'
            row['chosen']={'x':round(chosen['x'],2),'offset':round(chosen['offset'],2),
                           'expected_x':round(chosen['expected_x'],2),'geom_resid':round(chosen['geom_resid'],2),
                           'max_neighbor_jump':round(chosen['max_neighbor_jump'],2),
                           'validation':chosen['eval']}
            row['rescue_candidates']=[{'x':round(c['x'],2),'offset':round(c['offset'],2),
                'score':round(float(c['eval']['score']),4),'geom_resid':round(c['geom_resid'],2),
                'ok':bool(c['eval']['ok'])} for c in sorted(candidates,key=lambda c:c['eval']['score'],reverse=True)[:8]]
        details[str(boat)]=row

    cap.release()
    final_jumps=np.abs(np.diff(xs))
    if np.max(final_jumps)>args.max_final_neighbor_jump_frac*width:
        raise SystemExit('FAIL_CLOSED: rescued fleet horizontal separation implausible')

    payload=dict(meta)
    payload.update({
        'method':'v11 geometry + v9 multi-horizon all-row persistence rescue',
        'v12_result_blind':True,'race_results_read':False,
        'v12_base_seeds':{str(b):[round(float(base_xs[i]),2),round(float(ys[i]),2)] for i,b in enumerate(entry)},
        'seeds':seeds,'v12_rescued_row_count':rescued,'v12_rescue_details':details,
        'v12_final_adj_x_jumps':[round(float(x),2) for x in final_jumps],
        'v12_unit_px':round(unit,3),'v12_rescue_max_px':round(max_shift,3),
        'warning':'EXPERIMENTAL result-blind seed v12; validate unchanged across independent September races.'
    })
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
