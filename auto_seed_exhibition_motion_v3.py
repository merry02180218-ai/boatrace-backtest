#!/usr/bin/env python3
"""Hybrid six-boat auto seeding for low-latency exhibition SES.

Uses v1's permissive six-row detection, then refines each row toward the coherent
leading hull side without requiring global direction agreement. Result-blind.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import cv2
import numpy as np

def read_frame(cap, sec):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec*1000.0); ok, fr = cap.read(); return fr if ok else None

def cluster_rows(points, k=6):
    ys=points[:,1].astype(np.float32).reshape(-1,1)
    if len(ys)<30: return None
    crit=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_MAX_ITER,50,.5)
    _,lab,cen=cv2.kmeans(ys,k,None,crit,8,cv2.KMEANS_PP_CENTERS)
    groups=[]
    for idx in np.argsort(cen[:,0]):
        ii=np.flatnonzero(lab[:,0]==idx)
        if len(ii)<5: return None
        groups.append(ii)
    cy=np.array([np.median(points[ii,1]) for ii in groups])
    if np.min(np.diff(cy))<18: return None
    return groups

def refine_row(points, motion, ii):
    p=points[ii]; d=motion[ii]; dx=d[:,0]
    med=float(np.median(dx)); direction=-1.0 if med<0 else 1.0
    same=(dx*direction)>0
    if np.sum(same)>=4:
        sp=np.abs(dx[same]); thr=max(.6,float(np.percentile(sp,35))*0.75)
        coherent=same & (np.abs(dx)>=thr)
    else:
        coherent=np.ones(len(p),dtype=bool)
    if np.sum(coherent)<4: coherent=same if np.sum(same)>=4 else np.ones(len(p),dtype=bool)
    q=p[coherent]
    # conservative lead-side shift: less aggressive than v2, enough to move off wake
    qx=35.0 if direction<0 else 65.0
    anchor=float(np.percentile(q[:,0],qx))
    band=np.abs(q[:,0]-anchor)<=48.0
    qb=q[band] if np.sum(band)>=3 else q
    cx=float(np.median(qb[:,0])); cy=float(np.median(qb[:,1]))
    return {'center':[cx,cy],'dominant_dx':med,'direction':'left' if direction<0 else 'right',
            'raw_count':int(len(p)),'coherent_count':int(np.sum(coherent)),'body_band_count':int(len(qb)),
            'spread_x':float(np.median(np.abs(qb[:,0]-cx)))}

def detect_at(cap, sec, dt=.10):
    a=read_frame(cap,sec); b=read_frame(cap,sec+dt)
    if a is None or b is None: return None
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY); h,w=ga.shape
    mask=np.zeros_like(ga); mask[int(h*.12):int(h*.92),int(w*.10):int(w*.95)]=255
    p0=cv2.goodFeaturesToTrack(ga,maxCorners=1000,qualityLevel=.009,minDistance=4,mask=mask,blockSize=5)
    if p0 is None or len(p0)<40: return None
    kw=dict(winSize=(25,25),maxLevel=3,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    p1,st,_=cv2.calcOpticalFlowPyrLK(ga,gb,p0,None,**kw); pb,stb,_=cv2.calcOpticalFlowPyrLK(gb,ga,p1,None,**kw)
    p0v=p0.reshape(-1,2); p1v=p1.reshape(-1,2); fb=np.linalg.norm(pb.reshape(-1,2)-p0v,axis=1); d=p1v-p0v; mag=np.linalg.norm(d,axis=1)
    good=(st[:,0]==1)&(stb[:,0]==1)&np.isfinite(fb)&(fb<1.7)&(mag>.7)&(mag<20)
    pts=p0v[good]; d=d[good]
    if len(pts)<35: return None
    horiz=np.abs(d[:,0])>=np.abs(d[:,1])*.65; pts=pts[horiz]; d=d[horiz]
    if len(pts)<30: return None
    groups=cluster_rows(pts)
    if groups is None: return None
    rows=[refine_row(pts,d,ii) for ii in groups]; centers=[r['center'] for r in rows]
    cy=np.array([c[1] for c in centers]); spacing=np.diff(cy)
    if np.min(spacing)<18: return None
    score=sum(min(r['coherent_count'],30) for r in rows)+.5*float(np.min(spacing))-.25*sum(max(0,r['spread_x']-24) for r in rows)
    return {'sec':sec,'rows':rows,'centers':centers,'score':float(score),'frame_width':w,'frame_height':h}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('video',type=Path); ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0); ap.add_argument('--scan-radius',type=float,default=4.0); ap.add_argument('--scan-step',type=float,default=.25)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v3.json')); ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v3.json')); args=ap.parse_args()
    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]: raise SystemExit('--entry-order must contain 1..6 exactly once')
    cap=cv2.VideoCapture(str(args.video));
    if not cap.isOpened(): raise SystemExit('cannot open video')
    cand=[]; t=args.nominal_sec-args.scan_radius; hi=args.nominal_sec+args.scan_radius
    while t<=hi+1e-9:
        r=detect_at(cap,t)
        if r:
            r['selection_score']=r['score']-2.0*abs(t-args.nominal_sec); cand.append(r)
        t+=args.scan_step
    cap.release()
    if not cand: raise SystemExit('FAIL_CLOSED: no stable six-row hybrid hull detection')
    best=max(cand,key=lambda x:x['selection_score']); seeds={}; details={}
    for boat,row in zip(entry,best['rows']):
        cx,cy=row['center']; seeds[str(boat)]=[round(cx,2),round(cy,2)]; details[str(boat)]={k:(round(v,3) if isinstance(v,float) else v) for k,v in row.items() if k!='center'}
    payload={'video':str(args.video),'result_blind':True,'race_results_read':False,'method':'permissive six-row LK + per-row coherent lead-side hull refinement',
             'entry_order':entry,'nominal_sec':args.nominal_sec,'selected_sec':round(float(best['sec']),3),'frame_size':[best['frame_width'],best['frame_height']],
             'seeds':seeds,'row_details':details,'candidate_count':len(cand),'warning':'approximate slit anchor; exact start-line detector still required'}
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(payload,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
