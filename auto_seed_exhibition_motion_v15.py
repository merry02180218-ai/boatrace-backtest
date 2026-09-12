#!/usr/bin/env python3
"""Fast result-blind 2D direction-consistent SES seed rescue v15.

v14 proved that a vertically misplaced wake/background seed can be rescued by
2D search, but exhaustive grid evaluation was too slow for live use. v15 keeps
the same persistence/direction/fleet geometry gates while evaluating a small,
geometry-focused shortlist first. Only if that shortlist yields no valid
candidate does it expand to a bounded fallback shortlist.

No race result, boat-number special case, or race-specific offset is used.
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
    n=len(xs); y=float(ys[i] if cand_y is None else cand_y)
    if 0<i<n-1:
        y0,y1=float(ys[i-1]),float(ys[i+1]); x0,x1=float(xs[i-1]),float(xs[i+1])
        a=(y-y0)/(y1-y0) if abs(y1-y0)>1e-6 else .5
        return float(x0+a*(x1-x0)), float((ys[i-1]+ys[i+1])/2.0)
    if i==0 and n>=3:
        y0,y1=float(ys[1]),float(ys[2]); x0,x1=float(xs[1]),float(xs[2])
        slope=(x1-x0)/(y1-y0) if abs(y1-y0)>1e-6 else 0.0
        return float(x0+slope*(y-y0)), float(ys[1]-(ys[2]-ys[1]))
    if i==n-1 and n>=3:
        y0,y1=float(ys[n-3]),float(ys[n-2]); x0,x1=float(xs[n-3]),float(xs[n-2])
        slope=(x1-x0)/(y1-y0) if abs(y1-y0)>1e-6 else 0.0
        return float(x1+slope*(y-y1)), float(ys[n-2]+(ys[n-2]-ys[n-3]))
    return float(xs[i]),float(ys[i])


def expected_y(ys,i):
    n=len(ys)
    if 0<i<n-1:
        return float((ys[i-1]+ys[i+1])/2.0)
    if i==0 and n>=3:
        return float(ys[1]-(ys[2]-ys[1]))
    if i==n-1 and n>=3:
        return float(ys[n-2]+(ys[n-2]-ys[n-3]))
    return float(ys[i])


def row_geometry_ok(trial_x, trial_y, i, width, height, min_gap_frac, max_gap_frac, max_x_jump_frac):
    if not np.array_equal(np.argsort(trial_y),np.arange(len(trial_y))):
        return False,{}
    gaps=np.diff(trial_y)
    if np.any(gaps < min_gap_frac*height) or np.any(gaps > max_gap_frac*height):
        return False,{'gaps':[round(float(g),2) for g in gaps]}
    xj=np.abs(np.diff(trial_x)); local=[]
    if i>0: local.append(float(xj[i-1]))
    if i<len(trial_x)-1: local.append(float(xj[i]))
    mj=max(local) if local else 0.0
    if mj > max_x_jump_frac*width:
        return False,{'gaps':[round(float(g),2) for g in gaps],'max_neighbor_x_jump':round(mj,2)}
    return True,{'gaps':[round(float(g),2) for g in gaps],'max_neighbor_x_jump':round(mj,2)}


def uniq(vals, nd=3):
    out=[]; seen=set()
    for v in vals:
        k=round(float(v),nd)
        if k not in seen:
            seen.add(k); out.append(float(v))
    return out


def candidate_stage(cap,sec,dx,bx,by,i,xs,ys,width,height,xunit,yunit,xoffs,yvals,args,seen):
    cands=[]; tested=0
    for cy in yvals:
        if cy<30 or cy>height-30: continue
        for ox in xoffs:
            cx=bx+ox
            key=(round(cx,2),round(cy,2))
            if key in seen or (abs(cx-bx)<1e-6 and abs(cy-by)<1e-6): continue
            seen.add(key)
            if cx<30 or cx>width-30: continue
            tx=xs.copy(); ty=ys.copy(); tx[i]=cx; ty[i]=cy
            gok,gmeta=row_geometry_ok(tx,ty,i,width,height,args.min_final_gap_frac,args.max_final_gap_frac,args.max_final_neighbor_jump_frac)
            if not gok: continue
            tested+=1
            ev,dm,ok=eval_candidate(cap,sec,cx,cy,dx)
            if not ok: continue
            ex,ey=expected_xy(xs,ys,i,cy)
            gres=((cx-ex)/max(xunit,1.0))**2 + ((cy-ey)/max(yunit,1.0))**2
            cands.append({'x':cx,'y':cy,'ox':ox,'oy':cy-by,'eval':ev,'direction':dm,
                          'expected_x':ex,'expected_y':ey,'geom_resid_norm':float(gres),'geometry':gmeta})
    return cands,tested


def choose(cands,near_best):
    best=max(float(c['eval']['score']) for c in cands)
    near=[c for c in cands if float(c['eval']['score'])>=best-near_best]
    return min(near,key=lambda c:(c['geom_resid_norm'],-float(c['eval']['score']),abs(c['oy']),abs(c['ox'])))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v15.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v15.json'))
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
    starting_xs=xs.copy(); starting_ys=ys.copy(); details={}; rescued=0; total_rescue_evals=0
    xunit=max(18.0,width/48.0); yunit=max(12.0,height/45.0)

    for i,boat in enumerate(entry):
        dx=float(meta['row_details'][str(boat)]['dominant_dx']); bx=float(xs[i]); by=float(ys[i])
        base_ev,base_dm,base_ok=eval_candidate(cap,sec,bx,by,dx)
        row={'base_seed':[round(bx,2),round(by,2)],'base_validation':base_ev,'base_direction':base_dm,
             'base_combined_ok':base_ok,'decision':'keep_direction_consistent','rescue_candidates':[],
             'rescue_stage':0,'rescue_eval_count':0}
        if not base_ok:
            ey=expected_y(ys,i)
            # Fast stage: geometry-predicted row center +/- one y step, original x +/- two x steps.
            y1=uniq([ey-yunit,ey,ey+yunit])
            x1=[-2*xunit,-xunit,0.0,xunit,2*xunit]
            seen=set(); cands,n1=candidate_stage(cap,sec,dx,bx,by,i,xs,ys,width,height,xunit,yunit,x1,y1,args,seen)
            row['rescue_eval_count']+=n1; total_rescue_evals+=n1; stage=1
            if not cands:
                # Bounded fallback: two wider geometry y hypotheses and +/-3 x steps.
                y2=uniq([ey-2*yunit,ey+2*yunit, (ey+by)/2.0])
                x2=[-3*xunit,-2*xunit,-xunit,0.0,xunit,2*xunit,3*xunit]
                c2,n2=candidate_stage(cap,sec,dx,bx,by,i,xs,ys,width,height,xunit,yunit,x2,y2,args,seen)
                cands.extend(c2); row['rescue_eval_count']+=n2; total_rescue_evals+=n2; stage=2
            if not cands:
                cap.release(); raise SystemExit(f'FAIL_CLOSED: no fast 2D direction-consistent rescue for boat {boat}')
            chosen=choose(cands,args.visual_near_best)
            xs[i]=chosen['x']; ys[i]=chosen['y']; seeds[str(boat)]=[round(chosen['x'],2),round(chosen['y'],2)]; rescued+=1
            row['decision']='fast_2d_direction_or_persistence_rescue'; row['rescue_stage']=stage
            row['predicted_y']=round(ey,2)
            row['chosen']={'x':round(chosen['x'],2),'y':round(chosen['y'],2),'offset_x':round(chosen['ox'],2),
                'offset_y':round(chosen['oy'],2),'expected_x':round(chosen['expected_x'],2),'expected_y':round(chosen['expected_y'],2),
                'geom_resid_norm':round(chosen['geom_resid_norm'],3),'validation':chosen['eval'],'direction':chosen['direction'],'geometry':chosen['geometry']}
            row['rescue_candidates']=[{'x':round(c['x'],2),'y':round(c['y'],2),'offset_x':round(c['ox'],2),'offset_y':round(c['oy'],2),
                'score':round(float(c['eval']['score']),4),'net_dx':c['direction']['net_dx'],'geom_resid_norm':round(c['geom_resid_norm'],3)}
                for c in sorted(cands,key=lambda c:c['eval']['score'],reverse=True)[:12]]
        details[str(boat)]=row

    cap.release()
    if not np.array_equal(np.argsort(ys),np.arange(len(ys))): raise SystemExit('FAIL_CLOSED: v15 final y-order changed')
    gaps=np.diff(ys); xj=np.abs(np.diff(xs))
    if np.any(gaps < args.min_final_gap_frac*height) or np.any(gaps > args.max_final_gap_frac*height):
        raise SystemExit('FAIL_CLOSED: v15 final row spacing implausible')
    if np.max(xj)>args.max_final_neighbor_jump_frac*width:
        raise SystemExit('FAIL_CLOSED: v15 final fleet horizontal separation implausible')

    payload=dict(meta)
    payload.update({'method':'v12 persistence base + geometry-focused fast 2D direction-consistent rescue',
        'v15_result_blind':True,'race_results_read':False,
        'v15_starting_seeds':{str(b):[round(float(starting_xs[i]),2),round(float(starting_ys[i]),2)] for i,b in enumerate(entry)},
        'seeds':seeds,'v15_rescued_row_count':rescued,'v15_total_rescue_evals':total_rescue_evals,'v15_details':details,
        'v15_final_y_gaps':[round(float(x),2) for x in gaps],'v15_final_adj_x_jumps':[round(float(x),2) for x in xj],
        'v15_x_unit_px':round(xunit,3),'v15_y_unit_px':round(yunit,3),
        'warning':'EXPERIMENTAL result-blind seed v15; fast shortlist preserves v14 quality gates and requires unchanged multi-race regression.'})
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
