#!/usr/bin/env python3
"""Experimental fail-closed six-boat tracker for start exhibition clips.

Purpose:
- track six seeded boat ROIs for 0.0/0.5/1.0/1.5s after a supplied slit time
- estimate per-boat image-plane motion using sparse optical flow
- compensate common camera pan with fleet median motion
- refuse to emit SES when tracking confidence is insufficient

This is calibration tooling. It does NOT join race results and must remain result-blind.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path
import cv2
import numpy as np

OFFSETS=(0.0,0.5,1.0,1.5)


def read_frame(cap,t):
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000.0)
    ok,fr=cap.read()
    if not ok: raise RuntimeError(f'cannot read frame {t:.3f}s')
    return fr


def roi_features(gray,box):
    x,y,w,h=map(int,box)
    roi=gray[y:y+h,x:x+w]
    pts=cv2.goodFeaturesToTrack(roi,maxCorners=80,qualityLevel=0.01,minDistance=3,blockSize=5)
    if pts is None: return np.empty((0,1,2),np.float32)
    pts[:,:,0]+=x; pts[:,:,1]+=y
    return pts.astype(np.float32)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--slit-sec',type=float,required=True)
    ap.add_argument('--seed-json',type=Path,required=True,help='{"1":[x,y,w,h],...,"6":[...]} on slit frame')
    ap.add_argument('--out',type=Path,default=Path('exhibition_tracking_v1.json'))
    ap.add_argument('--min-points',type=int,default=6)
    ap.add_argument('--min-boats',type=int,default=5)
    args=ap.parse_args()

    seeds=json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int,seeds)) != [1,2,3,4,5,6]:
        raise SystemExit('seed-json must contain boats 1..6')

    cap=cv2.VideoCapture(str(args.video))
    fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    f0=read_frame(cap,args.slit_sec)
    g0=cv2.cvtColor(f0,cv2.COLOR_BGR2GRAY)
    init={int(b):roi_features(g0,box) for b,box in seeds.items()}

    boats={}
    for b in range(1,7):
        p0=init[b]
        rec={'initial_points':int(len(p0)),'samples':{}}
        for off in OFFSETS:
            if off==0:
                rec['samples']['0.0']={'good_points':int(len(p0)),'dx_px':0.0,'dy_px':0.0}
                continue
            fr=read_frame(cap,args.slit_sec+off)
            g=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY)
            if len(p0)==0:
                rec['samples'][f'{off:.1f}']={'good_points':0,'dx_px':None,'dy_px':None}
                continue
            p1,st,err=cv2.calcOpticalFlowPyrLK(g0,g,p0,None,winSize=(41,41),maxLevel=4,
                criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,0.01))
            good=(st[:,0]==1) & np.isfinite(err[:,0]) & (err[:,0] < 35)
            q0=p0[good,0,:]; q1=p1[good,0,:]
            if len(q0):
                d=q1-q0
                med=np.median(d,axis=0)
                mad=np.median(np.abs(d-med),axis=0)+1e-6
                keep=(np.abs(d[:,0]-med[0])<4*max(2.0,mad[0])) & (np.abs(d[:,1]-med[1])<4*max(2.0,mad[1]))
                d=d[keep]
            if len(q0) and len(d):
                med=np.median(d,axis=0)
                dx,dy=float(med[0]),float(med[1])
            else: dx=dy=None
            rec['samples'][f'{off:.1f}']={'good_points':int(len(d)) if len(q0) else 0,'dx_px':dx,'dy_px':dy}
        boats[str(b)]=rec
    cap.release()

    final_dx=[]
    for b in range(1,7):
        s=boats[str(b)]['samples']['1.5']
        if s['dx_px'] is not None and s['good_points']>=args.min_points:
            final_dx.append(s['dx_px'])
    accepted=len(final_dx)>=args.min_boats
    payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'offsets_sec':OFFSETS,
             'leakage_guard':'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER','boats':boats,
             'accepted':accepted,'reason':None}
    if accepted:
        common=float(np.median(final_dx))
        rel={}
        for b in range(1,7):
            s=boats[str(b)]['samples']['1.5']
            rel[str(b)]=None if s['dx_px'] is None or s['good_points']<args.min_points else round(s['dx_px']-common,3)
        vals=[v for v in rel.values() if v is not None]
        mad=float(np.median(np.abs(np.array(vals)-np.median(vals)))) if vals else 0.0
        scale=max(1.0,1.4826*mad)
        ses={b:(None if v is None else int(np.clip(np.rint(v/scale),-3,3))) for b,v in rel.items()}
        payload['camera_common_dx_1_5px']=round(common,3)
        payload['relative_gain_1_5px']=rel
        payload['ses_v1']=ses
    else:
        payload['reason']=f'FAIL_CLOSED: only {len(final_dx)} boats have >= {args.min_points} good points at +1.5s'
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
