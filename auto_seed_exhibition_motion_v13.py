#!/usr/bin/env python3
"""Direction-consistent persistence-rescue SES auto seeding v13.

v13 extends v12 after an independent September race showed that a wake/background
patch can pass short multi-horizon NCC while moving opposite to the row's
observed coherent motion. This version keeps all result-blind v12 logic and adds
one generic identity check: a persistent seed must also have a net horizontal
trajectory consistent with the sign of the row's dominant LK motion, except for
near-zero-motion rows.

No race outcomes/results are read. No boat-number-specific correction exists.
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


def direction_metrics(ev, seed_x, dominant_dx, min_motion_px=2.5):
    matched=[s.get('matched_center') for s in ev.get('samples',[]) if s.get('ok') and s.get('matched_center')]
    if not matched:
        return {'ok':False,'net_dx':0.0,'reason':'no_valid_matches'}
    net=float(matched[-1][0])-float(seed_x)
    # Very small LK motion is not reliable enough to impose a direction sign.
    if abs(float(dominant_dx)) < min_motion_px:
        return {'ok':True,'net_dx':round(net,3),'reason':'dominant_motion_near_zero'}
    # Require meaningful same-sign displacement. A small deadband avoids rejecting
    # a nearly stationary visual track due one-pixel noise.
    aligned=(net*float(dominant_dx) > 0.0) and abs(net)>=4.0
    return {'ok':bool(aligned),'net_dx':round(net,3),'reason':'aligned' if aligned else 'opposite_or_static'}


def eval_candidate(cap, sec, x, y, dx):
    ev=v9.eval_seed(cap,sec,x,y,dx)
    dm=direction_metrics(ev,x,dx)
    return ev,dm,bool(ev.get('ok',False) and dm['ok'])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v13.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v13.json'))
    ap.add_argument('--rescue-max-frac',type=float,default=.11)
    ap.add_argument('--visual-near-best',type=float,default=.06)
    ap.add_argument('--max-final-neighbor-jump-frac',type=float,default=.20)
    args=ap.parse_args()

    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]: raise SystemExit('--entry-order must contain 1..6 exactly once')

    with tempfile.TemporaryDirectory() as td:
        td=Path(td); meta12=td/'meta12.json'; seeds12=td/'seeds12.json'
        cmd=[sys.executable,'auto_seed_exhibition_motion_v12.py',str(args.video),'--entry-order',args.entry_order,
             '--nominal-sec',str(args.nominal_sec),'--out',str(meta12),'--seed-out',str(seeds12)]
        p=subprocess.run(cmd)
        if p.returncode!=0 or not meta12.exists(): raise SystemExit('FAIL_CLOSED: v12 base seeding failed')
        meta=json.loads(meta12.read_text(encoding='utf-8')); seeds=json.loads(seeds12.read_text(encoding='utf-8'))

    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened(): raise SystemExit('cannot open video')
    width=float(meta['frame_size'][0]); sec=float(meta['selected_sec'])
    xs=np.array([float(seeds[str(b)][0]) for b in entry],float)
    ys=np.array([float(seeds[str(b)][1]) for b in entry],float)
    starting_xs=xs.copy(); details={}; rescued=0
    unit=max(18.0,width/48.0); max_shift=max(unit,args.rescue_max_frac*width)
    kmax=max(1,int(round(max_shift/unit)))
    offsets=[float(k*unit) for k in range(-kmax,kmax+1) if k!=0]

    for i,boat in enumerate(entry):
        dx=float(meta['row_details'][str(boat)]['dominant_dx']); bx=float(xs[i]); cy=float(ys[i])
        base_ev,base_dm,base_ok=eval_candidate(cap,sec,bx,cy,dx)
        row={'base_seed':[round(bx,2),round(cy,2)],'base_validation':base_ev,
             'base_direction':base_dm,'base_combined_ok':base_ok,'decision':'keep_direction_consistent','rescue_candidates':[]}
        if not base_ok:
            expected=expected_x_from_neighbors(xs,ys,i); cands=[]
            for off in offsets:
                cx=bx+off
                if cx<30 or cx>width-30: continue
                ev,dm,ok=eval_candidate(cap,sec,cx,cy,dx)
                if not ok: continue
                trial=xs.copy(); trial[i]=cx
                lj=abs(trial[i]-trial[i-1]) if i>0 else 0.0; rj=abs(trial[i+1]-trial[i]) if i+1<len(trial) else 0.0
                mj=max(lj,rj)
                if mj>args.max_final_neighbor_jump_frac*width: continue
                cands.append({'x':cx,'offset':off,'eval':ev,'direction':dm,'expected_x':expected,
                              'geom_resid':abs(cx-expected),'max_neighbor_jump':mj})
            if not cands:
                cap.release(); raise SystemExit(f'FAIL_CLOSED: no direction-consistent rescue for boat {boat}')
            best_score=max(c['eval']['score'] for c in cands)
            near=[c for c in cands if c['eval']['score']>=best_score-args.visual_near_best]
            chosen=min(near,key=lambda c:(c['geom_resid'],-c['eval']['score'],abs(c['offset'])))
            xs[i]=chosen['x']; seeds[str(boat)]=[round(chosen['x'],2),round(cy,2)]; rescued+=1
            row['decision']='rescue_direction_or_persistence_failure'
            row['chosen']={'x':round(chosen['x'],2),'offset':round(chosen['offset'],2),'expected_x':round(chosen['expected_x'],2),
                           'geom_resid':round(chosen['geom_resid'],2),'max_neighbor_jump':round(chosen['max_neighbor_jump'],2),
                           'validation':chosen['eval'],'direction':chosen['direction']}
            row['rescue_candidates']=[{'x':round(c['x'],2),'offset':round(c['offset'],2),
                'score':round(float(c['eval']['score']),4),'net_dx':c['direction']['net_dx'],
                'geom_resid':round(c['geom_resid'],2)} for c in sorted(cands,key=lambda c:c['eval']['score'],reverse=True)[:10]]
        details[str(boat)]=row
    cap.release()

    final_jumps=np.abs(np.diff(xs))
    if np.max(final_jumps)>args.max_final_neighbor_jump_frac*width:
        raise SystemExit('FAIL_CLOSED: v13 final fleet horizontal separation implausible')

    payload=dict(meta)
    payload.update({'method':'v12 persistence rescue + dominant-motion direction consistency',
        'v13_result_blind':True,'race_results_read':False,
        'v13_starting_seeds':{str(b):[round(float(starting_xs[i]),2),round(float(ys[i]),2)] for i,b in enumerate(entry)},
        'seeds':seeds,'v13_rescued_row_count':rescued,'v13_details':details,
        'v13_final_adj_x_jumps':[round(float(x),2) for x in final_jumps],
        'v13_unit_px':round(unit,3),'v13_rescue_max_px':round(max_shift,3),
        'warning':'EXPERIMENTAL result-blind seed v13; validate unchanged across independent September races.'})
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
