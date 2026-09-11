#!/usr/bin/env python3
"""Sequential six-boat tracker with arbitrary exhibition-entry order support.

Result-blind calibration/research tooling only.

Changes from v2:
- boat labels no longer imply screen/lane order
- initial screen order is derived from seed center y positions
- lane-order guard preserves that initial order (e.g. 1-2-4-5-6-3)
- perspective compensation still regresses screen motion versus initial image y
- fail-closed behavior is retained
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import cv2
import numpy as np

OFFSETS=(0.0,0.5,1.0,1.5)


def parse_seeds(obj):
    centers=[]
    for b in range(1,7):
        v=obj[str(b)]
        if len(v)==2:
            x,y=v
        elif len(v)==4:
            x,y,w,h=v; x=x+w/2; y=y+h/2
        else:
            raise ValueError('each seed must be [cx,cy] or [x,y,w,h]')
        centers.append([float(x),float(y)])
    return np.array(centers,np.float32)


def local_motion(prev_g,cur_g,cx,cy,roi_w=90,roi_h=56):
    mask=np.zeros_like(prev_g)
    x1=max(0,int(round(cx-roi_w*0.40))); x2=min(prev_g.shape[1],int(round(cx+roi_w*0.60)))
    y1=max(0,int(round(cy-roi_h/2))); y2=min(prev_g.shape[0],int(round(cy+roi_h/2)))
    mask[y1:y2,x1:x2]=255
    p0=cv2.goodFeaturesToTrack(prev_g,maxCorners=70,qualityLevel=.012,minDistance=3,mask=mask,blockSize=3)
    if p0 is None or len(p0)<5:
        return None,0,None
    kw=dict(winSize=(25,25),maxLevel=3,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    p1,st,_=cv2.calcOpticalFlowPyrLK(prev_g,cur_g,p0,None,**kw)
    pb,stb,_=cv2.calcOpticalFlowPyrLK(cur_g,prev_g,p1,None,**kw)
    fb=np.linalg.norm((pb-p0).reshape(-1,2),axis=1)
    good=(st[:,0]==1)&(stb[:,0]==1)&np.isfinite(fb)&(fb<1.5)
    d=(p1-p0).reshape(-1,2)[good]
    if len(d)<4:
        return None,int(len(d)),None
    med=np.median(d,axis=0)
    radial=np.linalg.norm(d-med,axis=1)
    rmed=float(np.median(radial))
    keep=radial < max(2.5,3.0*rmed)
    d=d[keep]
    if len(d)<4:
        return None,int(len(d)),None
    med=np.median(d,axis=0)
    spread=float(np.median(np.linalg.norm(d-med,axis=1)))
    return med.astype(np.float32),int(len(d)),spread


def robust_linear_residual(y,values):
    y=np.asarray(y,float); v=np.asarray(values,float)
    w=np.ones(len(y),float); X=np.c_[np.ones(len(y)),y]; beta=None
    for _ in range(4):
        WX=X*w[:,None]
        beta=np.linalg.lstsq(WX,v*w,rcond=None)[0]
        r=v-X@beta
        s=max(1.0,1.4826*np.median(np.abs(r-np.median(r))))
        w=1.0/np.maximum(1.0,np.abs(r)/(2.5*s))
    return v-X@beta, {'intercept':float(beta[0]),'slope_per_y_px':float(beta[1])}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--slit-sec',type=float,required=True)
    ap.add_argument('--seed-json',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=Path('exhibition_tracking_v3.json'))
    ap.add_argument('--max-substitution-frac',type=float,default=.25)
    args=ap.parse_args()

    seed_obj=json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int,seed_obj))!=[1,2,3,4,5,6]:
        raise SystemExit('seed-json must contain 1..6')
    centers0=parse_seeds(seed_obj); centers=centers0.copy()
    initial_order=np.argsort(centers0[:,1])
    entry_order=[int(i+1) for i in initial_order]

    cap=cv2.VideoCapture(str(args.video)); fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC,args.slit_sec*1000.0); ok,prev=cap.read()
    if not ok: raise SystemExit('cannot read slit frame')
    prev_g=cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY)
    nmax=int(round(1.5*fps)); sample_frames={int(round(o*fps)):o for o in OFFSETS[1:]}
    samples={'0.0':{'centers':centers.tolist(),'features':[None]*6,'spread':[None]*6}}
    bad_counts=np.zeros(6,int)

    for fi in range(1,nmax+1):
        ok,cur=cap.read()
        if not ok: raise SystemExit(f'video ended at frame {fi}')
        cur_g=cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY)
        motions=[]; ns=[]; spreads=[]
        for cx,cy in centers:
            d,n,s=local_motion(prev_g,cur_g,float(cx),float(cy))
            motions.append(d); ns.append(n); spreads.append(s)
        valid=np.array([d is not None for d in motions])
        if valid.sum()<4:
            raise SystemExit(f'FAIL_CLOSED: only {valid.sum()} local motions at frame {fi}')
        D=np.array([d if d is not None else [np.nan,np.nan] for d in motions],np.float32)
        fleet=np.nanmedian(D,axis=0)
        for i in range(6):
            if not valid[i] or np.linalg.norm(D[i]-fleet)>11.0:
                D[i]=fleet; bad_counts[i]+=1
        centers += D
        cur_order=np.argsort(centers[:,1])
        if not np.array_equal(cur_order,initial_order):
            raise SystemExit(f'FAIL_CLOSED: entry-order violation at frame {fi}; expected {entry_order}, got {[int(i+1) for i in cur_order]}')
        ys=centers[initial_order,1]
        if not np.all(np.diff(ys)>4):
            raise SystemExit(f'FAIL_CLOSED: lane separation too small at frame {fi}')
        prev_g=cur_g
        if fi in sample_frames:
            off=sample_frames[fi]
            samples[f'{off:.1f}']={'centers':centers.tolist(),'features':ns,'spread':spreads}
    cap.release()

    max_bad=max(6,int(args.max_substitution_frac*nmax))
    accepted=bool(np.all(bad_counts <= max_bad))
    payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,
             'leakage_guard':'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER',
             'method':'sequential LK reseed + arbitrary initial entry-order guard + linear perspective trend vs initial y',
             'entry_order':entry_order,
             'bad_motion_substitutions':{str(i+1):int(x) for i,x in enumerate(bad_counts)},
             'max_allowed_substitutions_per_boat':int(max_bad),
             'samples':samples,'accepted':accepted}
    if not accepted:
        payload['reason']='FAIL_CLOSED: excessive motion substitutions for one or more boats'
    else:
        horizons={}; y0=centers0[:,1]; final_res=None
        for off in OFFSETS[1:]:
            c=np.array(samples[f'{off:.1f}']['centers'],float)
            dx=c[:,0]-centers0[:,0]
            rel,trend=robust_linear_residual(y0,dx)
            horizons[f'{off:.1f}']={'dx_px':[round(float(x),3) for x in dx],
                                    'perspective_trend':trend,
                                    'relative_forward_px':[round(float(x),3) for x in rel]}
            if off==1.5: final_res=rel
        med=np.median(final_res); mad=np.median(np.abs(final_res-med)); scale=max(1.0,1.4826*mad)
        ses=np.clip(np.rint((final_res-med)/scale),-3,3).astype(int)
        order=np.argsort(-final_res); ranks=np.empty(6,int); ranks[order]=np.arange(1,7)
        payload['horizons']=horizons
        payload['boats']={str(i+1):{'relative_forward_1_5px':round(float(final_res[i]),3),
                                    'stretch_rank':int(ranks[i]),'ses_v3':int(ses[i])} for i in range(6)}
        payload['ses_scale_px']=round(float(scale),3)
        payload['warning']='EXPERIMENTAL calibration score; perspective correction is first-order and must be validated across venues.'
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
