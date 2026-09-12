#!/usr/bin/env python3
"""Result-blind 2D direction-consistent persistence rescue for SES auto seeding v14.

v14 addresses a generic failure mode seen on an independent September sample:
the six-row detector can get the correct row ordering but place a row seed on
water/wake at the wrong vertical coordinate. v13 only searched horizontally,
so no direction-consistent hull patch could be recovered.

This version starts from v12 and applies the same persistence + direction check
as v13, but failed rows are rescued on a resolution-relative 2D grid. Candidate
selection is constrained by fleet row ordering/gaps and local x/y geometry.
No race result, boat-number rule, or race-specific offset is used.
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


def direction_metrics(ev, seed_x, dominant_dx, min_motion_px=2.5):
    matched=[s.get('matched_center') for s in ev.get('samples',[]) if s.get('ok') and s.get('matched_center')]
    if not matched:
        return {'ok':False,'net_dx':0.0,'reason':'no_valid_matches'}
    net=float(matched[-1][0])-float(seed_x)
    if abs(float(dominant_dx)) < min_motion_px:
        return {'ok':True,'net_dx':round(net,3),'reason':'dominant_motion_near_zero'}
    aligned=(net*float(dominant_dx) > 0.0) and abs(net)>=4.0
    return {'ok':bool(aligned),'net_dx':round(net,3),'reason':'aligned' if aligned else 'opposite_or_static'}


def eval_candidate(cap, sec, x, y, dx):
    ev=v9.eval_seed(cap,sec,x,y,dx)
    dm=direction_metrics(ev,x,dx)
    return ev,dm,bool(ev.get('ok',False) and dm['ok'])


def expected_xy(xs, ys, i, cand_y=None):
    """Local linear fleet expectation, evaluated at candidate y when supplied."""
    n=len(xs); y=float(ys[i] if cand_y is None else cand_y)
    if 0<i<n-1:
        y0,y1=float(ys[i-1]),float(ys[i+1])
        if abs(y1-y0)<1e-6:
            return float((xs[i-1]+xs[i+1])/2.0), float((ys[i-1]+ys[i+1])/2.0)
        a=(y-y0)/(y1-y0)
        ex=float(xs[i-1]+a*(xs[i+1]-xs[i-1]))
        ey=float((ys[i-1]+ys[i+1])/2.0)
        return ex,ey
    if i==0 and n>=3:
        # Extrapolate from the next two rows.
        y0,y1=float(ys[1]),float(ys[2]); x0,x1=float(xs[1]),float(xs[2])
        slope=(x1-x0)/(y1-y0) if abs(y1-y0)>1e-6 else 0.0
        ex=x0+slope*(y-y0)
        ey=float(ys[1]-(ys[2]-ys[1]))
        return float(ex),ey
    if i==n-1 and n>=3:
        y0,y1=float(ys[n-3]),float(ys[n-2]); x0,x1=float(xs[n-3]),float(xs[n-2])
        slope=(x1-x0)/(y1-y0) if abs(y1-y0)>1e-6 else 0.0
        ex=x1+slope*(y-y1)
        ey=float(ys[n-2]+(ys[n-2]-ys[n-3]))
        return float(ex),ey
    return float(xs[i]),float(ys[i])


def row_geometry_ok(trial_x, trial_y, i, width, height, min_gap_frac, max_gap_frac, max_x_jump_frac):
    order=np.argsort(trial_y)
    # Identity/order must remain the original top-to-bottom index order.
    if not np.array_equal(order,np.arange(len(trial_y))):
        return False,{}
    gaps=np.diff(trial_y)
    if np.any(gaps < min_gap_frac*height) or np.any(gaps > max_gap_frac*height):
        return False,{'gaps':[round(float(g),2) for g in gaps]}
    xj=np.abs(np.diff(trial_x))
    local=[]
    if i>0: local.append(float(xj[i-1]))
    if i<len(trial_x)-1: local.append(float(xj[i]))
    mj=max(local) if local else 0.0
    if mj > max_x_jump_frac*width:
        return False,{'gaps':[round(float(g),2) for g in gaps],'max_neighbor_x_jump':round(mj,2)}
    return True,{'gaps':[round(float(g),2) for g in gaps],'max_neighbor_x_jump':round(mj,2)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v14.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v14.json'))
    ap.add_argument('--rescue-max-x-frac',type=float,default=.11)
    ap.add_argument('--rescue-max-y-frac',type=float,default=.10)
    ap.add_argument('--visual-near-best',type=float,default=.06)
    ap.add_argument('--min-final-gap-frac',type=float,default=.015)
    ap.add_argument('--max-final-gap-frac',type=float,default=.20)
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
    width=float(meta['frame_size'][0]); height=float(meta['frame_size'][1]); sec=float(meta['selected_sec'])
    xs=np.array([float(seeds[str(b)][0]) for b in entry],float)
    ys=np.array([float(seeds[str(b)][1]) for b in entry],float)
    starting_xs=xs.copy(); starting_ys=ys.copy(); details={}; rescued=0

    xunit=max(18.0,width/48.0)
    yunit=max(12.0,height/45.0)
    max_x=max(xunit,args.rescue_max_x_frac*width)
    max_y=max(yunit,args.rescue_max_y_frac*height)
    kx=max(1,int(round(max_x/xunit))); ky=max(1,int(round(max_y/yunit)))
    xoffs=[float(k*xunit) for k in range(-kx,kx+1)]
    yoffs=[float(k*yunit) for k in range(-ky,ky+1)]

    for i,boat in enumerate(entry):
        dx=float(meta['row_details'][str(boat)]['dominant_dx']); bx=float(xs[i]); by=float(ys[i])
        base_ev,base_dm,base_ok=eval_candidate(cap,sec,bx,by,dx)
        row={'base_seed':[round(bx,2),round(by,2)],'base_validation':base_ev,
             'base_direction':base_dm,'base_combined_ok':base_ok,'decision':'keep_direction_consistent','rescue_candidates':[]}
        if not base_ok:
            cands=[]
            for oy in yoffs:
                cy=by+oy
                if cy<30 or cy>height-30: continue
                for ox in xoffs:
                    if ox==0 and oy==0: continue
                    cx=bx+ox
                    if cx<30 or cx>width-30: continue
                    tx=xs.copy(); ty=ys.copy(); tx[i]=cx; ty[i]=cy
                    gok,gmeta=row_geometry_ok(tx,ty,i,width,height,args.min_final_gap_frac,args.max_final_gap_frac,args.max_final_neighbor_jump_frac)
                    if not gok: continue
                    ev,dm,ok=eval_candidate(cap,sec,cx,cy,dx)
                    if not ok: continue
                    ex,ey=expected_xy(xs,ys,i,cy)
                    # Normalize geometry residual so x/y are comparable across resolution.
                    gres=((cx-ex)/max(xunit,1.0))**2 + ((cy-ey)/max(yunit,1.0))**2
                    cands.append({'x':cx,'y':cy,'ox':ox,'oy':oy,'eval':ev,'direction':dm,
                                  'expected_x':ex,'expected_y':ey,'geom_resid_norm':float(gres),'geometry':gmeta})
            if not cands:
                cap.release(); raise SystemExit(f'FAIL_CLOSED: no 2D direction-consistent rescue for boat {boat}')
            best_score=max(float(c['eval']['score']) for c in cands)
            near=[c for c in cands if float(c['eval']['score'])>=best_score-args.visual_near_best]
            chosen=min(near,key=lambda c:(c['geom_resid_norm'],-float(c['eval']['score']),abs(c['oy']),abs(c['ox'])))
            xs[i]=chosen['x']; ys[i]=chosen['y']; seeds[str(boat)]=[round(chosen['x'],2),round(chosen['y'],2)]; rescued+=1
            row['decision']='rescue_2d_direction_or_persistence_failure'
            row['chosen']={'x':round(chosen['x'],2),'y':round(chosen['y'],2),
                           'offset_x':round(chosen['ox'],2),'offset_y':round(chosen['oy'],2),
                           'expected_x':round(chosen['expected_x'],2),'expected_y':round(chosen['expected_y'],2),
                           'geom_resid_norm':round(chosen['geom_resid_norm'],3),
                           'validation':chosen['eval'],'direction':chosen['direction'],'geometry':chosen['geometry']}
            row['rescue_candidates']=[{'x':round(c['x'],2),'y':round(c['y'],2),'offset_x':round(c['ox'],2),'offset_y':round(c['oy'],2),
                'score':round(float(c['eval']['score']),4),'net_dx':c['direction']['net_dx'],
                'geom_resid_norm':round(c['geom_resid_norm'],3)} for c in sorted(cands,key=lambda c:c['eval']['score'],reverse=True)[:12]]
        details[str(boat)]=row

    cap.release()
    final_order=np.argsort(ys)
    if not np.array_equal(final_order,np.arange(len(ys))): raise SystemExit('FAIL_CLOSED: v14 final y-order changed')
    final_gaps=np.diff(ys); final_xj=np.abs(np.diff(xs))
    if np.any(final_gaps < args.min_final_gap_frac*height) or np.any(final_gaps > args.max_final_gap_frac*height):
        raise SystemExit('FAIL_CLOSED: v14 final row spacing implausible')
    if np.max(final_xj)>args.max_final_neighbor_jump_frac*width:
        raise SystemExit('FAIL_CLOSED: v14 final fleet horizontal separation implausible')

    payload=dict(meta)
    payload.update({'method':'v12 persistence rescue + 2D dominant-motion direction-consistent rescue',
        'v14_result_blind':True,'race_results_read':False,
        'v14_starting_seeds':{str(b):[round(float(starting_xs[i]),2),round(float(starting_ys[i]),2)] for i,b in enumerate(entry)},
        'seeds':seeds,'v14_rescued_row_count':rescued,'v14_details':details,
        'v14_final_y_gaps':[round(float(x),2) for x in final_gaps],
        'v14_final_adj_x_jumps':[round(float(x),2) for x in final_xj],
        'v14_x_unit_px':round(xunit,3),'v14_y_unit_px':round(yunit,3),
        'v14_rescue_max_x_px':round(max_x,3),'v14_rescue_max_y_px':round(max_y,3),
        'warning':'EXPERIMENTAL result-blind seed v14; validate unchanged across independent September races.'})
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
