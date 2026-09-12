#!/usr/bin/env python3
"""Multi-horizon visually validated auto seeding for exhibition SES.

v9 addresses the v8 failure where a wake/background seed can have excellent
very-short-horizon NCC. Candidate time selection remains geometry-aware. For an
isolated extreme-motion row, base and proposed shifted seeds are evaluated over
multiple result-blind horizons through 0.6 s. A shift is accepted only when its
multi-horizon visual persistence is materially better than the base candidate.

No race outcomes/results are read. The validation is bounded and substantially
shorter than the 1.5 s SES tracker horizon.
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


def eval_seed(cap, sec, cx, cy, dominant_dx, horizons=(.15,.30,.45,.60)):
    f0=read_frame(cap,sec)
    if f0 is None:
        return {'ok':False,'score':-999.0,'reason':'no_base_frame'}
    g0=cv2.cvtColor(f0,cv2.COLOR_BGR2GRAY)
    templ=crop_center(g0,cx,cy)
    if templ is None:
        return {'ok':False,'score':-999.0,'reason':'bad_template'}

    th,tw=templ.shape[:2]
    samples=[]
    # Start with a conservative velocity estimate. Re-center velocity from each
    # successful match so camera pan is learned from the video, not assumed.
    vx=float(dominant_dx)/0.10
    last_t=0.0; last_x=float(cx); last_y=float(cy)
    current_templ=templ.copy()
    for h in horizons:
        fr=read_frame(cap,sec+h)
        if fr is None:
            samples.append({'h':h,'ok':False,'ncc':0.0,'dy':999.0})
            continue
        g=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY)
        dt=h-last_t
        pred_x=last_x+vx*dt; pred_y=last_y
        sx=max(58,int(32+abs(vx)*dt*.35)); sy=20
        x1=max(0,int(round(pred_x-tw/2-sx))); x2=min(g.shape[1],int(round(pred_x+tw/2+sx)))
        y1=max(0,int(round(pred_y-th/2-sy))); y2=min(g.shape[0],int(round(pred_y+th/2+sy)))
        roi=g[y1:y2,x1:x2]
        if roi.shape[0]<th or roi.shape[1]<tw:
            samples.append({'h':h,'ok':False,'ncc':0.0,'dy':999.0})
            continue
        res=cv2.matchTemplate(roi,current_templ,cv2.TM_CCOEFF_NORMED)
        _,ncc,_,loc=cv2.minMaxLoc(res)
        mx=float(x1+loc[0]+tw/2); my=float(y1+loc[1]+th/2)
        dy=abs(my-pred_y)
        ok=bool(ncc>=.45 and dy<=20)
        samples.append({'h':h,'ok':ok,'ncc':round(float(ncc),4),'dy':round(float(dy),3),
                        'matched_center':[round(mx,2),round(my,2)]})
        if ok:
            if dt>0:
                observed_vx=(mx-last_x)/dt
                vx=.55*vx+.45*observed_vx
            last_x,last_y,last_t=mx,my,h
            nt=crop_center(g,mx,my)
            if nt is not None and nt.shape==current_templ.shape and ncc>=.68:
                current_templ=cv2.addWeighted(current_templ,.88,nt,.12,0)

    nccs=np.array([s.get('ncc',0.0) for s in samples],float)
    dys=np.array([s.get('dy',999.0) for s in samples],float)
    oks=sum(bool(s.get('ok')) for s in samples)
    median=float(np.median(nccs)); min_ncc=float(np.min(nccs)); mean_dy=float(np.mean(np.minimum(dys,40.0)))
    # Persistence matters more than one high early NCC. Penalize failed horizons,
    # worst-frame degradation, and vertical identity drift.
    score=median + .25*min_ncc - .006*mean_dy - .11*(len(samples)-oks)
    return {'ok':bool(oks>=3 and median>=.58 and min_ncc>=.42),
            'score':round(score,4),'median_ncc':round(median,4),'min_ncc':round(min_ncc,4),
            'mean_dy':round(mean_dy,3),'ok_horizons':int(oks),'samples':samples}


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
    ap.add_argument('--validation-margin',type=float,default=.025)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v9.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v9.json'))
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
                r['selection_score_v9']=r['score']+spacing_bonus-narrow_penalty-time_penalty
                r['min_gap']=min_gap; r['median_gap']=med_gap; r['gaps']=gaps.tolist(); cand.append(r)
        t+=args.scan_step
    if not cand:
        cap.release(); raise SystemExit('FAIL_CLOSED: no six-row candidate with safe seed geometry')
    best=max(cand,key=lambda x:x['selection_score_v9'])

    abs_dx=np.array([abs(float(r['dominant_dx'])) for r in best['rows']],dtype=float)
    med_abs_dx=float(np.median(abs_dx)); threshold=args.extreme_ratio*med_abs_dx
    extreme=[bool(med_abs_dx>0 and x>=threshold) for x in abs_dx]
    isolated=[]
    for i,flag in enumerate(extreme):
        adj=(i>0 and extreme[i-1]) or (i+1<len(extreme) and extreme[i+1])
        isolated.append(bool(flag and not adj))

    seeds={}; details={}; corrected=0; rejected=0; ambiguous=0
    for idx,(boat,row) in enumerate(zip(entry,best['rows'])):
        base_x,cy=map(float,row['center']); dx=float(row['dominant_dx']); final_x=base_x; shift=0.0
        base_eval=None; shifted_eval=None; decision='base_non_extreme'
        if isolated[idx]:
            proposed_shift=float(np.sign(dx)*args.max_shift); proposed_x=base_x+proposed_shift
            base_eval=eval_seed(cap,float(best['sec']),base_x,cy,dx)
            shifted_eval=eval_seed(cap,float(best['sec']),proposed_x,cy,dx)
            if shifted_eval['ok'] and shifted_eval['score'] >= base_eval['score'] + args.validation_margin:
                final_x=proposed_x; shift=proposed_shift; corrected+=1; decision='shift_multi_horizon_win'
            else:
                rejected+=1; decision='base_multi_horizon_gate'
        elif extreme[idx]:
            ambiguous+=1; decision='base_adjacent_extreme_ambiguous'
        seeds[str(boat)]=[round(final_x,2),round(cy,2)]
        details[str(boat)]={
            'motion_center':[round(base_x,2),round(cy,2)],'dominant_dx':round(dx,3),'abs_dx':round(abs(dx),3),
            'fleet_median_abs_dx':round(med_abs_dx,3),'extreme_threshold':round(threshold,3),
            'extreme_motion':bool(extreme[idx]),'isolated_extreme':bool(isolated[idx]),
            'base_validation':base_eval,'shifted_validation':shifted_eval,'decision':decision,
            'applied_shift_x':round(shift,3),'final_seed':[round(final_x,2),round(cy,2)],
            'direction':row['direction'],'coherent_count':int(row['coherent_count']),'spread_x':round(float(row['spread_x']),3)}
    cap.release()
    payload={
        'video':str(args.video),'result_blind':True,'race_results_read':False,
        'method':'v3 LK + geometry-aware candidate time + 0.6s multi-horizon visual persistence gate',
        'entry_order':entry,'nominal_sec':args.nominal_sec,'selected_sec':round(float(best['sec']),3),
        'frame_size':[best['frame_width'],best['frame_height']],
        'selected_min_gap':round(float(best['min_gap']),3),'selected_median_gap':round(float(best['median_gap']),3),
        'selected_gaps':[round(float(x),3) for x in best['gaps']],
        'fleet_median_abs_dx':round(med_abs_dx,3),'extreme_threshold':round(threshold,3),
        'max_shift':args.max_shift,'validation_margin':args.validation_margin,
        'corrected_row_count':corrected,'rejected_by_visual_count':rejected,
        'suppressed_ambiguous_extreme_count':ambiguous,'seeds':seeds,'row_details':details,'candidate_count':len(cand),
        'warning':'EXPERIMENTAL result-blind seed v9; validate across independent September races.'}
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
