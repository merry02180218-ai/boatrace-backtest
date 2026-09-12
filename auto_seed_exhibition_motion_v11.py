#!/usr/bin/env python3
"""2D fleet-coherence guarded SES auto seeding v11.

v11 extends v10's result-blind vertical fleet geometry with a horizontal
continuity guard. Six real boats in the start-exhibition perspective form a
continuous fleet; a single adjacent-row x jump spanning a large fraction of the
screen is characteristic of mixed background/boat motion clusters.

The guard is resolution-relative and boat-number independent. v9's 0.6 s
multi-horizon base-vs-shift visual persistence gate is retained unchanged.
No race result/outcome information is read.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

import auto_seed_exhibition_motion_v3 as v3
import auto_seed_exhibition_motion_v9 as v9


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
    ap.add_argument('--min-top-frac',type=float,default=.22)
    ap.add_argument('--min-span-frac',type=float,default=.16)
    ap.add_argument('--max-span-frac',type=float,default=.50)
    ap.add_argument('--max-gap-frac',type=float,default=.20)
    ap.add_argument('--max-adj-x-jump-frac',type=float,default=.24)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v11.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v11.json'))
    args=ap.parse_args()

    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]:
        raise SystemExit('--entry-order must contain 1..6 exactly once')
    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened(): raise SystemExit('cannot open video')

    cand=[]; rejected_geometry=[]
    t=args.nominal_sec-args.scan_radius; hi=args.nominal_sec+args.scan_radius
    while t<=hi+1e-9:
        r=v3.detect_at(cap,t)
        if r:
            gaps,min_gap,med_gap=v9.spacing_metrics(r['rows'])
            ys=np.array([float(row['center'][1]) for row in r['rows']],dtype=float)
            xs=np.array([float(row['center'][0]) for row in r['rows']],dtype=float)
            h=float(r['frame_height']); w=float(r['frame_width'])
            top_y=float(ys[0]); bottom_y=float(ys[-1]); span=bottom_y-top_y
            max_gap=float(np.max(gaps)); x_jumps=np.abs(np.diff(xs)); max_x_jump=float(np.max(x_jumps))
            checks={
                'min_gap':bool(min_gap>=args.hard_min_gap),
                'top_region':bool(top_y>=args.min_top_frac*h),
                'min_span':bool(span>=args.min_span_frac*h),
                'max_span':bool(span<=args.max_span_frac*h),
                'max_gap':bool(max_gap<=args.max_gap_frac*h),
                'max_adj_x_jump':bool(max_x_jump<=args.max_adj_x_jump_frac*w),
            }
            summary={'sec':round(float(t),3),'top_y':round(top_y,2),'bottom_y':round(bottom_y,2),
                     'span_y':round(span,2),'min_gap':round(min_gap,2),'max_gap':round(max_gap,2),
                     'max_adj_x_jump':round(max_x_jump,2),'xs':[round(float(x),1) for x in xs],
                     'checks':checks}
            if all(checks.values()):
                spacing_bonus=2.5*min(min_gap,42.0)
                narrow_penalty=6.0*max(0.0,args.preferred_min_gap-min_gap)
                time_penalty=2.0*abs(t-args.nominal_sec)
                span_penalty=.08*abs(span-.31*h)
                x_jump_penalty=.025*max_x_jump
                r['selection_score_v11']=r['score']+spacing_bonus-narrow_penalty-time_penalty-span_penalty-x_jump_penalty
                r['min_gap']=min_gap; r['median_gap']=med_gap; r['max_gap']=max_gap
                r['gaps']=gaps.tolist(); r['top_y']=top_y; r['bottom_y']=bottom_y; r['span_y']=span
                r['max_x_jump']=max_x_jump; r['xs']=xs.tolist(); r['candidate_summary']=summary
                cand.append(r)
            else:
                rejected_geometry.append(summary)
        t+=args.scan_step

    if not cand:
        cap.release(); raise SystemExit('FAIL_CLOSED: no six-row candidate with plausible 2D fleet geometry')
    best=max(cand,key=lambda x:x['selection_score_v11'])

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
            base_eval=v9.eval_seed(cap,float(best['sec']),base_x,cy,dx)
            shifted_eval=v9.eval_seed(cap,float(best['sec']),proposed_x,cy,dx)
            if shifted_eval['ok'] and shifted_eval['score'] >= base_eval['score'] + args.validation_margin:
                final_x=proposed_x; shift=proposed_shift; corrected+=1; decision='shift_multi_horizon_win'
            else:
                rejected+=1; decision='base_multi_horizon_gate'
        elif extreme[idx]:
            ambiguous+=1; decision='base_adjacent_extreme_ambiguous'
        seeds[str(boat)]=[round(final_x,2),round(cy,2)]
        details[str(boat)]={'motion_center':[round(base_x,2),round(cy,2)],'dominant_dx':round(dx,3),
            'abs_dx':round(abs(dx),3),'fleet_median_abs_dx':round(med_abs_dx,3),
            'extreme_threshold':round(threshold,3),'extreme_motion':bool(extreme[idx]),
            'isolated_extreme':bool(isolated[idx]),'base_validation':base_eval,'shifted_validation':shifted_eval,
            'decision':decision,'applied_shift_x':round(shift,3),'final_seed':[round(final_x,2),round(cy,2)],
            'direction':row['direction'],'coherent_count':int(row['coherent_count']),'spread_x':round(float(row['spread_x']),3)}
    cap.release()

    accepted_summaries=[]
    for r in sorted(cand,key=lambda x:x['selection_score_v11'],reverse=True)[:10]:
        s=dict(r['candidate_summary']); s['selection_score_v11']=round(float(r['selection_score_v11']),3)
        accepted_summaries.append(s)
    payload={'video':str(args.video),'result_blind':True,'race_results_read':False,
        'method':'v9 multi-horizon visual gate + resolution-relative 2D fleet geometry guard',
        'entry_order':entry,'nominal_sec':args.nominal_sec,'selected_sec':round(float(best['sec']),3),
        'frame_size':[best['frame_width'],best['frame_height']],
        'selected_top_y':round(float(best['top_y']),3),'selected_bottom_y':round(float(best['bottom_y']),3),
        'selected_span_y':round(float(best['span_y']),3),'selected_min_gap':round(float(best['min_gap']),3),
        'selected_median_gap':round(float(best['median_gap']),3),'selected_max_gap':round(float(best['max_gap']),3),
        'selected_max_adj_x_jump':round(float(best['max_x_jump']),3),
        'selected_gaps':[round(float(x),3) for x in best['gaps']],
        'selected_xs':[round(float(x),2) for x in best['xs']],
        'geometry_guard':{'min_top_frac':args.min_top_frac,'min_span_frac':args.min_span_frac,
            'max_span_frac':args.max_span_frac,'max_gap_frac':args.max_gap_frac,
            'max_adj_x_jump_frac':args.max_adj_x_jump_frac,'rejected_candidate_count':len(rejected_geometry)},
        'fleet_median_abs_dx':round(med_abs_dx,3),'extreme_threshold':round(threshold,3),
        'max_shift':args.max_shift,'validation_margin':args.validation_margin,'corrected_row_count':corrected,
        'rejected_by_visual_count':rejected,'suppressed_ambiguous_extreme_count':ambiguous,
        'seeds':seeds,'row_details':details,'candidate_count':len(cand),
        'accepted_candidate_preview':accepted_summaries,'rejected_geometry_preview':rejected_geometry[:10],
        'warning':'EXPERIMENTAL result-blind seed v11; validate across independent September races.'}
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
