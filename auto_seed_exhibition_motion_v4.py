#!/usr/bin/env python3
"""Result-blind six-boat exhibition auto seeding v4.

Starts from v3-style permissive six-row LK detection, then refines each row with a
small lead-side appearance search using only pre-race exhibition frames. The goal
is to move the seed from wake/water texture toward a temporally stable hull/body
patch without running a full 1.5 s tracker sweep.

Experimental: calibration/validation only until it generalizes across races/venues.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import cv2
import numpy as np


def read_frame(cap, sec):
    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000.0)
    ok, fr = cap.read()
    return fr if ok else None


def crop(g, cx, cy, w=54, h=30):
    x1 = max(0, int(round(cx - w/2))); x2 = min(g.shape[1], int(round(cx + w/2)))
    y1 = max(0, int(round(cy - h/2))); y2 = min(g.shape[0], int(round(cy + h/2)))
    if x2-x1 != w or y2-y1 != h:
        return None
    return g[y1:y2, x1:x2].copy()


def cluster_rows(points, k=6):
    ys = points[:,1].astype(np.float32).reshape(-1,1)
    if len(ys) < 30: return None
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 50, .5)
    _, lab, cen = cv2.kmeans(ys, k, None, crit, 8, cv2.KMEANS_PP_CENTERS)
    groups = []
    for idx in np.argsort(cen[:,0]):
        ii = np.flatnonzero(lab[:,0] == idx)
        if len(ii) < 5: return None
        groups.append(ii)
    cy = np.array([np.median(points[ii,1]) for ii in groups])
    if np.min(np.diff(cy)) < 18: return None
    return groups


def motion_row(points, motion, ii):
    p = points[ii]; d = motion[ii]; dx = d[:,0]
    med = float(np.median(dx)); direction = -1.0 if med < 0 else 1.0
    same = (dx * direction) > 0
    if np.sum(same) >= 4:
        sp = np.abs(dx[same]); thr = max(.6, float(np.percentile(sp,35)) * .75)
        coherent = same & (np.abs(dx) >= thr)
    else:
        coherent = np.ones(len(p), dtype=bool)
    if np.sum(coherent) < 4:
        coherent = same if np.sum(same) >= 4 else np.ones(len(p), dtype=bool)
    q = p[coherent]
    qx = 35.0 if direction < 0 else 65.0
    anchor = float(np.percentile(q[:,0], qx))
    band = np.abs(q[:,0]-anchor) <= 48.0
    qb = q[band] if np.sum(band) >= 3 else q
    cx = float(np.median(qb[:,0])); cy = float(np.median(qb[:,1]))
    return {
        'motion_center':[cx,cy], 'dominant_dx':med,
        'direction':'left' if direction < 0 else 'right',
        'raw_count':int(len(p)), 'coherent_count':int(np.sum(coherent)),
        'spread_x':float(np.median(np.abs(qb[:,0]-cx)))
    }


def appearance_score(g0, futures, cx, cy, direction, step_dx):
    t = crop(g0,cx,cy)
    if t is None: return None
    texture = float(np.std(t))
    if texture < 5.0: return None
    scores=[]; disps=[]; predx=float(cx); predy=float(cy)
    for dt, gf in futures:
        expected = predx + step_dx * (dt/.10)
        sx, sy = 58, 14
        x1=max(0,int(round(expected-27-sx))); x2=min(gf.shape[1],int(round(expected+27+sx)))
        y1=max(0,int(round(predy-15-sy))); y2=min(gf.shape[0],int(round(predy+15+sy)))
        roi=gf[y1:y2,x1:x2]
        if roi.shape[0] < 30 or roi.shape[1] < 54: return None
        r=cv2.matchTemplate(roi,t,cv2.TM_CCOEFF_NORMED)
        _, sc, _, loc=cv2.minMaxLoc(r)
        mx=x1+loc[0]+27; my=y1+loc[1]+15
        scores.append(float(sc)); disps.append(float(mx-cx))
    if not scores: return None
    medncc=float(np.median(scores)); finaldx=disps[-1]
    align = 1.0 if finaldx*direction > 0 else 0.0
    # Temporal match dominates; texture only breaks ties and alignment rejects static/wrong-side patches.
    score = medncc + 0.08*min(texture/40.0,1.0) + 0.08*align
    return {'score':score,'median_ncc':medncc,'texture_std':texture,'final_dx':finaldx}


def refine_appearance(cap, sec, row):
    f0=read_frame(cap,sec)
    if f0 is None: return None
    g0=cv2.cvtColor(f0,cv2.COLOR_BGR2GRAY)
    futures=[]
    for dt in (.10,.20,.30):
        fr=read_frame(cap,sec+dt)
        if fr is None: return None
        futures.append((dt,cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY)))
    cx,cy=row['motion_center']
    direction=-1.0 if row['direction']=='left' else 1.0
    # Search farther on the leading side than v3. This is deliberately small enough for live use.
    offsets=[-160,-120,-80,-40,0,40] if direction<0 else [-40,0,40,80,120,160]
    cands=[]
    step_dx=float(np.clip(row['dominant_dx'], -20, 20))
    for off in offsets:
        for dy in (-8,0,8):
            ax=float(cx+off); ay=float(cy+dy)
            z=appearance_score(g0,futures,ax,ay,direction,step_dx)
            if z is None: continue
            z.update({'x':ax,'y':ay,'dx_from_motion':float(off),'dy_from_motion':float(dy)})
            cands.append(z)
    if not cands: return None
    # Require plausible temporal consistency. If none passes, retain motion seed and mark weak.
    good=[c for c in cands if c['median_ncc']>=0.58 and c['final_dx']*direction>0]
    best=max(good if good else cands,key=lambda x:x['score'])
    best['appearance_pass']=bool(best in good)
    return best


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
    rows=[motion_row(pts,d,ii) for ii in groups]
    cy=np.array([r['motion_center'][1] for r in rows]); spacing=np.diff(cy)
    if np.min(spacing)<18: return None
    score=sum(min(r['coherent_count'],30) for r in rows)+.5*float(np.min(spacing))-.25*sum(max(0,r['spread_x']-24) for r in rows)
    return {'sec':sec,'rows':rows,'score':float(score),'frame_width':w,'frame_height':h}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('video',type=Path); ap.add_argument('--entry-order',required=True)
    ap.add_argument('--nominal-sec',type=float,default=29.0); ap.add_argument('--scan-radius',type=float,default=4.0); ap.add_argument('--scan-step',type=float,default=.25)
    ap.add_argument('--out',type=Path,default=Path('auto_seed_meta_v4.json')); ap.add_argument('--seed-out',type=Path,default=Path('auto_seeds_v4.json')); args=ap.parse_args()
    entry=[int(x) for x in args.entry_order.split(',')]
    if sorted(entry)!=[1,2,3,4,5,6]: raise SystemExit('--entry-order must contain 1..6 exactly once')
    cap=cv2.VideoCapture(str(args.video))
    if not cap.isOpened(): raise SystemExit('cannot open video')
    cand=[]; t=args.nominal_sec-args.scan_radius; hi=args.nominal_sec+args.scan_radius
    while t<=hi+1e-9:
        r=detect_at(cap,t)
        if r:
            r['selection_score']=r['score']-2.0*abs(t-args.nominal_sec); cand.append(r)
        t+=args.scan_step
    if not cand:
        cap.release(); raise SystemExit('FAIL_CLOSED: no stable six-row motion detection')
    best=max(cand,key=lambda x:x['selection_score'])
    seeds={}; details={}; weak=0
    for boat,row in zip(entry,best['rows']):
        ar=refine_appearance(cap,float(best['sec']),row)
        mcx,mcy=row['motion_center']
        if ar is None:
            cx,cy=mcx,mcy; weak+=1
            appearance={'appearance_pass':False,'reason':'no appearance candidates'}
        else:
            cx,cy=ar['x'],ar['y']; appearance=ar
            if not ar.get('appearance_pass'): weak+=1
        seeds[str(boat)]=[round(float(cx),2),round(float(cy),2)]
        details[str(boat)]={
            'motion_center':[round(float(mcx),2),round(float(mcy),2)],
            'dominant_dx':round(float(row['dominant_dx']),3),'direction':row['direction'],
            'raw_count':row['raw_count'],'coherent_count':row['coherent_count'],'spread_x':round(float(row['spread_x']),3),
            'appearance':{k:(round(v,3) if isinstance(v,float) else v) for k,v in appearance.items()}
        }
    cap.release()
    if weak>2: raise SystemExit(f'FAIL_CLOSED: appearance refinement weak for {weak} boats')
    payload={'video':str(args.video),'result_blind':True,'race_results_read':False,
             'method':'v3 permissive six-row LK + short-horizon lead-side appearance refinement',
             'entry_order':entry,'nominal_sec':args.nominal_sec,'selected_sec':round(float(best['sec']),3),
             'frame_size':[best['frame_width'],best['frame_height']],'seeds':seeds,'row_details':details,
             'candidate_count':len(cand),'weak_appearance_count':weak,
             'warning':'EXPERIMENTAL result-blind seed v4; requires multi-race blind validation before production use.'}
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    args.seed_out.write_text(json.dumps(seeds,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
