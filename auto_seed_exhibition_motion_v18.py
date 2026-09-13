#!/usr/bin/env python3
"""Result-blind fleet-motion constrained rescued-row seeding v18.

v17 proved that a rescued row can have excellent standalone NCC survival while
following a coherent wake/background texture. v18 keeps every v14 healthy row
fixed and uses those trusted rows only as a reference fleet. Rescued rows are
chosen from the bounded v14 candidate pool using:
  * the unchanged v17 long persistence/direction/on-frame gate;
  * robust fleet long-motion consistency (Theil-Sen net-dx vs initial y);
  * horizon-by-horizon entry-order / mutual-exclusion checks against trusted
    neighboring rows;
  * the existing v14 initial geometry guard.
No race result, boat-number rule, race-specific offset, or relaxed tracker gate
is used. If the trusted fleet cannot support a rescued row, fail closed.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
import cv2
import numpy as np
import auto_seed_exhibition_motion_v14 as v14
import auto_seed_exhibition_motion_v17 as v17


def eval_centers(ev):
    out={}
    for s in ev.get('samples',[]):
        if s.get('ok') and s.get('matched_center'):
            out[round(float(s['h']),2)]=tuple(map(float,s['matched_center']))
    return out


def robust_line(ys, vals):
    ys=np.asarray(ys,float); vals=np.asarray(vals,float)
    slopes=[]
    for i in range(len(ys)):
        for j in range(i+1,len(ys)):
            dy=ys[j]-ys[i]
            if abs(dy)>1e-6: slopes.append((vals[j]-vals[i])/dy)
    slope=float(np.median(slopes)) if slopes else 0.0
    intercept=float(np.median(vals-slope*ys))
    resid=np.abs(vals-(slope*ys+intercept))
    mad=float(np.median(resid)) if len(resid) else 0.0
    return slope,intercept,mad


def neighbor_ok(i, centers, ref_centers, min_sep=8.0, min_dist=18.0):
    # Entry-order y must remain ordered at common horizons; candidate must also
    # not collapse onto an already trusted center (wake/background collision).
    for h,c in centers.items():
        x,y=c
        for j,rcs in ref_centers.items():
            if h not in rcs: continue
            rx,ry=rcs[h]
            if j<i and not (y>=ry+min_sep): return False, f'y_order_above_h{h}'
            if j>i and not (y<=ry-min_sep): return False, f'y_order_below_h{h}'
            if ((x-rx)**2+(y-ry)**2)**0.5 < min_dist:
                return False, f'center_collision_h{h}'
    return True,'ok'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v18.json'))
    ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v18.json'))
    args=ap.parse_args()
    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]: raise SystemExit('--entry-order must contain 1..6 exactly once')

    with tempfile.TemporaryDirectory() as td:
        td=Path(td); m14=td/'meta14.json'; s14=td/'seeds14.json'
        p=subprocess.run([sys.executable,'auto_seed_exhibition_motion_v14.py',str(args.video),
            '--entry-order',args.entry_order,'--nominal-sec',str(args.nominal_sec),
            '--out',str(m14),'--seed-out',str(s14)])
        if p.returncode!=0 or not m14.exists(): raise SystemExit('FAIL_CLOSED: v14 base seeding failed')
        meta=json.loads(m14.read_text(encoding='utf-8')); seeds=json.loads(s14.read_text(encoding='utf-8'))

    width=float(meta['frame_size'][0]); height=float(meta['frame_size'][1]); sec=float(meta['selected_sec'])
    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened(): raise SystemExit('cannot open video')
    xs=np.array([float(seeds[str(b)][0]) for b in entry],float)
    ys=np.array([float(seeds[str(b)][1]) for b in entry],float)
    xunit=float(meta.get('v14_x_unit_px',max(18.0,width/48.0)))
    yunit=float(meta.get('v14_y_unit_px',max(12.0,height/45.0)))

    rescued=[]; refs=[]; ref_centers={}; reference_details={}
    for i,b in enumerate(entry):
        vd=meta.get('v14_details',{}).get(str(b),{})
        if vd.get('decision')=='rescue_2d_direction_or_persistence_failure':
            rescued.append(i); continue
        dx=float(meta['row_details'][str(b)]['dominant_dx'])
        x,y=map(float,seeds[str(b)])
        ev,gm,_=v17.long_gate(cap,sec,x,y,dx,width,height)
        cs=eval_centers(ev)
        # Reference use is stricter than seed preservation: the row stays fixed
        # regardless, but only high-quality long evidence may constrain rescues.
        usable=(gm.get('survives') and gm.get('ok_horizons',0)>=5 and
                gm.get('median_ncc',0)>=.55 and gm.get('min_ncc',0)>=.35 and len(cs)>=5)
        reference_details[str(b)]={'seed':[x,y],'usable':bool(usable),'gate':gm}
        if usable:
            net=float(list(cs.values())[-1][0]-x)
            refs.append((i,y,net)); ref_centers[i]=cs

    if rescued and len(refs)<3:
        cap.release(); raise SystemExit('FAIL_CLOSED: fewer than 3 trusted fleet rows for v18 rescue')
    if refs:
        slope,intercept,mad=robust_line([r[1] for r in refs],[r[2] for r in refs])
    else:
        slope=intercept=mad=0.0
    motion_scale=max(45.0,3.0*mad)
    details={}; changed=0

    # Rescue rows from inside outward so a chosen rescue becomes an additional
    # mutual-exclusion reference, but never a fleet-line training reference.
    for i in rescued:
        b=entry[i]; dx=float(meta['row_details'][str(b)]['dominant_dx'])
        bx,by=map(float,seeds[str(b)]); vd=meta['v14_details'][str(b)]
        raw=[(bx,by,'v14_chosen')]
        st=meta.get('v14_starting_seeds',{}).get(str(b))
        if st: raw.append((float(st[0]),float(st[1]),'v14_start'))
        for c in vd.get('rescue_candidates',[]): raw.append((float(c['x']),float(c['y']),'v14_top'))
        uniq=[];seen=set()
        for x,y,src in raw:
            k=(round(x,2),round(y,2))
            if k not in seen: seen.add(k);uniq.append((x,y,src))
        tested=[]; passing=[]
        expected_net=slope*by+intercept
        for x,y,src in uniq:
            tx=xs.copy();ty=ys.copy();tx[i]=x;ty[i]=y
            gok,gmeta=v14.row_geometry_ok(tx,ty,i,width,height,.015,.20,.20)
            if not gok: continue
            ev,gm,ok=v17.long_gate(cap,sec,x,y,dx,width,height)
            if not ok: continue
            cs=eval_centers(ev)
            nok,nreason=neighbor_ok(i,cs,ref_centers)
            net=float(gm.get('net_dx',0.0)); mres=abs(net-expected_net)
            ex,ey=v14.expected_xy(xs,ys,i,y)
            gres=((x-ex)/max(xunit,1.0))**2+((y-ey)/max(yunit,1.0))**2
            # Reject gross fleet-motion outliers rather than rewarding a wake
            # merely for very high NCC. 4*scale is intentionally broad; the
            # ranking below, not a tight threshold, does most of the work.
            fleet_ok=bool(mres<=4.0*motion_scale)
            visual=float(ev.get('score',0.0))
            objective=mres/motion_scale + .10*gres - .12*visual
            rec={'x':x,'y':y,'source':src,'eval':ev,'gate':gm,'centers':cs,
                 'geometry':gmeta,'motion_resid':mres,'geom_resid_norm':gres,
                 'neighbor_ok':nok,'neighbor_reason':nreason,'fleet_ok':fleet_ok,
                 'objective':objective}
            tested.append({'x':round(x,2),'y':round(y,2),'source':src,'net_dx':round(net,3),
                'expected_net_dx':round(expected_net,3),'motion_resid':round(mres,3),
                'motion_scale':round(motion_scale,3),'neighbor_ok':nok,'neighbor_reason':nreason,
                'fleet_ok':fleet_ok,'geom_resid_norm':round(gres,3),'visual_score':round(visual,4),
                'objective':round(objective,4)})
            if nok and fleet_ok: passing.append(rec)
        if not passing:
            cap.release(); raise SystemExit(f'FAIL_CLOSED: no fleet-consistent v18 rescue candidate for boat {b}')
        chosen=min(passing,key=lambda c:c['objective'])
        xs[i]=chosen['x'];ys[i]=chosen['y'];seeds[str(b)]=[round(chosen['x'],2),round(chosen['y'],2)]
        ref_centers[i]=chosen['centers']
        if round(chosen['x'],2)!=round(bx,2) or round(chosen['y'],2)!=round(by,2): changed+=1
        details[str(b)]={'decision':'fleet_motion_rescue','previous_v14_seed':[bx,by],
            'expected_net_dx':round(expected_net,3),'chosen':tested[[ (r['x'],r['y']) for r in passing ].index((chosen['x'],chosen['y']))] if False else {
                'x':round(chosen['x'],2),'y':round(chosen['y'],2),'source':chosen['source'],
                'net_dx':chosen['gate'].get('net_dx'),'motion_resid':round(chosen['motion_resid'],3),
                'objective':round(chosen['objective'],4),'gate':chosen['gate']},'tested':tested}

    cap.release()
    if not np.array_equal(np.argsort(ys),np.arange(6)): raise SystemExit('FAIL_CLOSED: v18 final y-order changed')
    payload=dict(meta)
    payload.update({'method':'v14 healthy rows frozen + v17 long gate + robust fleet-motion/mutual-exclusion rescue',
        'v18_result_blind':True,'race_results_read':False,'seeds':seeds,'v18_changed_row_count':changed,
        'v18_reference_details':reference_details,'v18_reference_count':len(refs),
        'v18_fleet_motion':{'slope_per_y':round(slope,6),'intercept':round(intercept,3),
                            'mad':round(mad,3),'scale':round(motion_scale,3)},
        'v18_details':details,
        'warning':'EXPERIMENTAL result-blind seed v18; healthy v14 seeds are frozen; rescued rows require fleet-motion and mutual-exclusion consistency.'})
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
