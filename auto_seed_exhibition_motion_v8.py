#!/usr/bin/env python3
"""Short-horizon validated, geometry-aware auto seeding for exhibition SES.

v8 keeps v7's safe candidate-time geometry selection, but no longer applies an
extreme-motion shift just because a row is an isolated motion outlier. For each
isolated extreme row, it compares the original v3 seed with the proposed shifted
seed using a result-blind short-horizon template-consistency test. The shift is
accepted only when its visual tracking score is materially better.

This is a small bounded local check, not a race-result-driven sweep and not a
full 1.5-second tracker search.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

import auto_seed_exhibition_motion_v3 as v3


def read_frame(cap, sec):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000.0)
    ok, fr = cap.read()
    return fr if ok else None


def crop_center(img, cx, cy, w=54, h=30):
    x1=max(0,int(round(cx-w/2))); x2=min(img.shape[1],int(round(cx+w/2)))
    y1=max(0,int(round(cy-h/2))); y2=min(img.shape[0],int(round(cy+h/2)))
    if x2-x1 < w-2 or y2-y1 < h-2:
        return None
    return img[y1:y2,x1:x2].copy()


def seed_consistency(cap, sec, cx, cy, dominant_dx, dt=.18):
    a=read_frame(cap, sec); b=read_frame(cap, sec+dt)
    if a is None or b is None:
        return {'ok':False,'ncc':0.0,'dy':999.0,'score':-999.0}
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    templ=crop_center(ga,cx,cy)
    if templ is None:
        return {'ok':False,'ncc':0.0,'dy':999.0,'score':-999.0}
    pred_x=float(cx + dominant_dx * (dt/.10)); pred_y=float(cy)
    th,tw=templ.shape[:2]; sx,sy=52,16
    x1=max(0,int(round(pred_x-tw/2-sx))); x2=min(gb.shape[1],int(round(pred_x+tw/2+sx)))
    y1=max(0,int(round(pred_y-th/2-sy))); y2=min(gb.shape[0],int(round(pred_y+th/2+sy)))
    roi=gb[y1:y2,x1:x2]
    if roi.shape[0] < th or roi.shape[1] < tw:
        return {'ok':False,'ncc':0.0,'dy':999.0,'score':-999.0}
    res=cv2.matchTemplate(roi,templ,cv2.TM_CCOEFF_NORMED)
    _,ncc,_,loc=cv2.minMaxLoc(res)
    mx=x1+loc[0]+tw/2; my=y1+loc[1]+th/2
    dy=abs(float(my-pred_y))
    # penalize vertical identity drift. x is allowed to differ because pan and
    # perspective are exactly why raw motion seeds are imperfect.
    score=float(ncc) - 0.012*dy
    return {'ok':bool(ncc>=.45 and dy<=16),'ncc':round(float(ncc),4),'dy':round(dy,3),
            'matched_center':[round(float(mx),2),round(float(my),2)],'score':round(score,4)}


def spacing_metrics(rows):
    cy=np.array([float(r['center'][1]) for r in rows],dtype=float)
    gaps=np.diff(cy)
    return gaps,float(np.min(gaps)),float(np.median(gaps))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0)
    ap.add_argument('--scan-radius',type=float,default=4.0)
    ap.add_argument('--scan-step',type=float,default=.25)
    ap.add_argument('--extreme-ratio',type=float,default=1.5)
    ap.add_argument('--max-shift',type=float,default=120.0)
    ap.add_argument('--preferred-min-gap',type=float,default=30.0)
    ap.add_argument('--hard-min-gap',type=float,default=22.0)
    ap.add_argument('--validation-margin',type=float,default=.035,
                    help='shift score must exceed base by at least this amount')
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v8.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v8.json'))
    args=ap.parse_args()

    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]:
        raise SystemExit('--entry-order must contain 1..6 exactly once')

    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened(): raise SystemExit('cannot open video')

    cand=[]; t=args.nominal_sec-args.scan_radius; hi=args.nominal_sec+args.scan_radius
    while t<=hi+1e-9:
        r=v3.detect_at(cap,t)
        if r:
            gaps,min_gap,med_gap=spacing_metrics(r['rows'])
            if min_gap>=args.hard_min_gap:
                spacing_bonus=2.5*min(min_gap,42.0)
                narrow_penalty=6.0*max(0.0,args.preferred_min_gap-min_gap)
                time_penalty=2.0*abs(t-args.nominal_sec)
                r['selection_score_v8']=r['score']+spacing_bonus-narrow_penalty-time_penalty
                r['min_gap']=min_gap; r['median_gap']=med_gap; r['gaps']=gaps.tolist(); cand.append(r)
        t+=args.scan_step
    if not cand:
        cap.release(); raise SystemExit('FAIL_CLOSED: no six-row candidate with safe seed geometry')

    best=max(cand,key=lambda x:x['selection_score_v8'])
    abs_dx=np.array([abs(float(r['dominant_dx'])) for r in best['rows']],dtype=float)
    med_abs_dx=float(np.median(abs_dx)); threshold=args.extreme_ratio*med_abs_dx
    extreme=[bool(med_abs_dx>0 and x>=threshold) for x in abs_dx]
    isolated=[]
    for i,flag in enumerate(extreme):
        adj=(i>0 and extreme[i-1]) or (i+1<len(extreme) and extreme[i+1])
        isolated.append(bool(flag and not adj))

    seeds={}; details={}; corrected=0; suppressed_ambiguous=0; rejected_by_visual=0
    for idx,(boat,row) in enumerate(zip(entry,best['rows'])):
        base_x,cy=map(float,row['center']); dx=float(row['dominant_dx']); final_x=base_x; shift=0.0
        base_eval=None; shifted_eval=None; decision='base_non_extreme'
        if isolated[idx]:
            proposed_shift=float(np.sign(dx)*args.max_shift); proposed_x=base_x+proposed_shift
            base_eval=seed_consistency(cap,float(best['sec']),base_x,cy,dx)
            shifted_eval=seed_consistency(cap,float(best['sec']),proposed_x,cy,dx)
            if shifted_eval['ok'] and shifted_eval['score'] >= base_eval['score'] + args.validation_margin:
                final_x=proposed_x; shift=proposed_shift; corrected+=1; decision='shift_visual_win'
            else:
                rejected_by_visual+=1; decision='base_visual_gate'
        elif extreme[idx]:
            suppressed_ambiguous+=1; decision='base_adjacent_extreme_ambiguous'

        seeds[str(boat)]=[round(final_x,2),round(cy,2)]
        details[str(boat)]={
            'motion_center':[round(base_x,2),round(cy,2)],'dominant_dx':round(dx,3),'abs_dx':round(abs(dx),3),
            'fleet_median_abs_dx':round(med_abs_dx,3),'extreme_threshold':round(threshold,3),
            'extreme_motion':bool(extreme[idx]),'isolated_extreme':bool(isolated[idx]),
            'ambiguous_adjacent_extreme':bool(extreme[idx] and not isolated[idx]),
            'base_validation':base_eval,'shifted_validation':shifted_eval,'decision':decision,
            'applied_shift_x':round(shift,3),'final_seed':[round(final_x,2),round(cy,2)],
            'direction':row['direction'],'coherent_count':int(row['coherent_count']),'spread_x':round(float(row['spread_x']),3)}

    cap.release()
    payload={
        'video':str(args.video),'result_blind':True,'race_results_read':False,
        'method':'v3 LK + geometry-aware time selection + short-horizon visual validation of isolated extreme shifts',
        'entry_order':entry,'nominal_sec':args.nominal_sec,'selected_sec':round(float(best['sec']),3),
        'frame_size':[best['frame_width'],best['frame_height']],
        'selected_min_gap':round(float(best['min_gap']),3),'selected_median_gap':round(float(best['median_gap']),3),
        'selected_gaps':[round(float(x),3) for x in best['gaps']],
        'fleet_median_abs_dx':round(med_abs_dx,3),'extreme_ratio':args.extreme_ratio,'extreme_threshold':round(threshold,3),
        'max_shift':args.max_shift,'validation_margin':args.validation_margin,'corrected_row_count':corrected,
        'suppressed_ambiguous_extreme_count':suppressed_ambiguous,'rejected_by_visual_count':rejected_by_visual,
        'seeds':seeds,'row_details':details,'candidate_count':len(cand),
        'warning':'EXPERIMENTAL result-blind seed v8; technical validation only until multi-race generalization.'}
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
