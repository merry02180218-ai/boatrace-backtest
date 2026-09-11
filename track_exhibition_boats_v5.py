#!/usr/bin/env python3
"""Low-latency six-boat tracker for live exhibition SES.

Result-blind research/live helper.

v5 changes from v4:
- processes every Nth frame (default stride=2) to cut live latency
- template/LK fusion retained with wider per-step motion budget
- fail-closed quality uses both fallback ratio and template confidence
- a boat may use up to 50% prediction fallback only when its median template
  confidence is strong; weak-confidence boats remain capped at 35%
- persists per-boat quality tier for downstream NO-BET gating
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
        if len(v)==2: x,y=v
        elif len(v)==4:
            x,y,w,h=v; x=x+w/2; y=y+h/2
        else: raise ValueError('each seed must be [cx,cy] or [x,y,w,h]')
        centers.append([float(x),float(y)])
    return np.array(centers,np.float32)


def crop_center(img,cx,cy,w,h):
    x1=max(0,int(round(cx-w/2))); x2=min(img.shape[1],int(round(cx+w/2)))
    y1=max(0,int(round(cy-h/2))); y2=min(img.shape[0],int(round(cy+h/2)))
    if x2-x1<max(8,w//2) or y2-y1<max(8,h//2): return None
    return img[y1:y2,x1:x2].copy()


def local_motion(prev_g,cur_g,cx,cy,roi_w=84,roi_h=46,max_mag=42):
    mask=np.zeros_like(prev_g)
    x1=max(0,int(round(cx-roi_w*.45))); x2=min(prev_g.shape[1],int(round(cx+roi_w*.55)))
    y1=max(0,int(round(cy-roi_h/2))); y2=min(prev_g.shape[0],int(round(cy+roi_h/2)))
    mask[y1:y2,x1:x2]=255
    p0=cv2.goodFeaturesToTrack(prev_g,maxCorners=70,qualityLevel=.01,minDistance=3,mask=mask,blockSize=3)
    if p0 is None or len(p0)<4: return None,0,None
    kw=dict(winSize=(29,29),maxLevel=3,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,30,.01))
    p1,st,_=cv2.calcOpticalFlowPyrLK(prev_g,cur_g,p0,None,**kw)
    pb,stb,_=cv2.calcOpticalFlowPyrLK(cur_g,prev_g,p1,None,**kw)
    p0v=p0.reshape(-1,2); p1v=p1.reshape(-1,2); pbv=pb.reshape(-1,2)
    fb=np.linalg.norm(pbv-p0v,axis=1); d=p1v-p0v; mag=np.linalg.norm(d,axis=1)
    good=(st[:,0]==1)&(stb[:,0]==1)&np.isfinite(fb)&(fb<2.2)&(mag<max_mag)
    d=d[good]
    if len(d)<4: return None,int(len(d)),None
    med=np.median(d,axis=0); radial=np.linalg.norm(d-med,axis=1); rmed=float(np.median(radial))
    d=d[radial < max(4.0,3.5*rmed)]
    if len(d)<4: return None,int(len(d)),None
    med=np.median(d,axis=0); spread=float(np.median(np.linalg.norm(d-med,axis=1)))
    return med.astype(np.float32),int(len(d)),spread


def template_match(cur_g,template,pred,search_x=68,search_y=20):
    th,tw=template.shape[:2]; pcx,pcy=float(pred[0]),float(pred[1])
    x1=max(0,int(round(pcx-tw/2-search_x))); x2=min(cur_g.shape[1],int(round(pcx+tw/2+search_x)))
    y1=max(0,int(round(pcy-th/2-search_y))); y2=min(cur_g.shape[0],int(round(pcy+th/2+search_y)))
    roi=cur_g[y1:y2,x1:x2]
    if roi.shape[0]<th or roi.shape[1]<tw: return None,None
    res=cv2.matchTemplate(roi,template,cv2.TM_CCOEFF_NORMED)
    _,score,_,loc=cv2.minMaxLoc(res)
    return np.array([x1+loc[0]+tw/2,y1+loc[1]+th/2],np.float32),float(score)


def robust_linear_residual(y,values):
    y=np.asarray(y,float); v=np.asarray(values,float); w=np.ones(len(y),float)
    X=np.c_[np.ones(len(y)),y]; beta=None
    for _ in range(4):
        beta=np.linalg.lstsq(X*w[:,None],v*w,rcond=None)[0]
        r=v-X@beta; s=max(1.0,1.4826*np.median(np.abs(r-np.median(r))))
        w=1.0/np.maximum(1.0,np.abs(r)/(2.5*s))
    return v-X@beta,{'intercept':float(beta[0]),'slope_per_y_px':float(beta[1])}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path); ap.add_argument('--slit-sec',type=float,required=True)
    ap.add_argument('--seed-json',type=Path,required=True); ap.add_argument('--out',type=Path,default=Path('exhibition_tracking_v5.json'))
    ap.add_argument('--stride',type=int,default=2); ap.add_argument('--template-w',type=int,default=54); ap.add_argument('--template-h',type=int,default=30)
    ap.add_argument('--min-ncc',type=float,default=.48); ap.add_argument('--strong-ncc',type=float,default=.80)
    ap.add_argument('--weak-fallback-frac',type=float,default=.35); ap.add_argument('--strong-fallback-frac',type=float,default=.50)
    args=ap.parse_args()
    if args.stride<1: raise SystemExit('--stride must be >=1')
    seed_obj=json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int,seed_obj))!=[1,2,3,4,5,6]: raise SystemExit('seed-json must contain 1..6')
    centers0=parse_seeds(seed_obj); centers=centers0.copy(); initial_order=np.argsort(centers0[:,1]); entry_order=[int(i+1) for i in initial_order]

    cap=cv2.VideoCapture(str(args.video)); fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC,args.slit_sec*1000.0); ok,prev=cap.read()
    if not ok: raise SystemExit('cannot read slit frame')
    prev_g=cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY)
    templates=[]
    for cx,cy in centers:
        t=crop_center(prev_g,float(cx),float(cy),args.template_w,args.template_h)
        if t is None: raise SystemExit('FAIL_CLOSED: cannot initialize boat template')
        templates.append(t)

    total_native=int(round(1.5*fps)); steps=int(np.ceil(total_native/args.stride))
    sample_native={int(round(o*fps)):o for o in OFFSETS[1:]}; samples={'0.0':{'centers':centers.tolist()}}
    fallback=np.zeros(6,int); ncc_hist=[[] for _ in range(6)]; prev_velocity=np.zeros((6,2),np.float32)
    native_done=0
    for step in range(1,steps+1):
        advance=min(args.stride,total_native-native_done)
        if advance<=0: break
        for _ in range(advance-1):
            if not cap.grab(): raise SystemExit('video ended during stride grab')
        ok,cur=cap.read()
        if not ok: raise SystemExit('video ended during stride read')
        native_done += advance; cur_g=cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY)
        lk=[]; ns=[]; spreads=[]
        for cx,cy in centers:
            d,n,s=local_motion(prev_g,cur_g,float(cx),float(cy),max_mag=24*advance); lk.append(d); ns.append(n); spreads.append(s)
        valid=np.array([d is not None for d in lk])
        if valid.any():
            Dv=np.array([d if d is not None else [np.nan,np.nan] for d in lk],np.float32); fleet=np.nanmedian(Dv,axis=0)
        else: fleet=np.median(prev_velocity,axis=0)
        new=centers.copy(); frame_ncc=[]
        for i in range(6):
            d=lk[i]
            if d is not None and np.linalg.norm(d-fleet)<=24*advance: pred=centers[i]+d
            elif np.linalg.norm(prev_velocity[i])>0: pred=centers[i]+prev_velocity[i]
            else: pred=centers[i]+fleet
            m,score=template_match(cur_g,templates[i],pred,search_x=34*advance,search_y=10*advance); frame_ncc.append(score)
            if m is not None and score is not None and score>=args.min_ncc and abs(float(m[1]-pred[1]))<=10*advance:
                est=(.72*m+.28*pred).astype(np.float32)
                if np.linalg.norm(est-centers[i])>20*advance:
                    fallback[i]+=1; est=pred.astype(np.float32)
                else:
                    ncc_hist[i].append(score)
                    if score>=.72:
                        nt=crop_center(cur_g,float(est[0]),float(est[1]),args.template_w,args.template_h)
                        if nt is not None and nt.shape==templates[i].shape: templates[i]=cv2.addWeighted(templates[i],.85,nt,.15,0)
            else:
                fallback[i]+=1; est=pred.astype(np.float32)
            new[i]=est
        velocities=new-centers; centers=new; prev_velocity=.65*prev_velocity+.35*velocities
        cur_order=np.argsort(centers[:,1])
        if not np.array_equal(cur_order,initial_order): raise SystemExit(f'FAIL_CLOSED: entry-order violation; expected {entry_order}, got {[int(i+1) for i in cur_order]}')
        if not np.all(np.diff(centers[initial_order,1])>4): raise SystemExit('FAIL_CLOSED: lane separation too small')
        prev_g=cur_g
        for nf,off in sample_native.items():
            if f'{off:.1f}' not in samples and native_done>=nf:
                samples[f'{off:.1f}']={'centers':centers.tolist(),'features':ns,'spread':spreads,'ncc':[None if x is None else round(float(x),3) for x in frame_ncc]}

    cap.release(); median_ncc=np.array([float(np.median(x)) if x else 0.0 for x in ncc_hist])
    fb_frac=fallback/max(1,steps); quality=[]; okboats=[]
    for i in range(6):
        strong=median_ncc[i]>=args.strong_ncc
        lim=args.strong_fallback_frac if strong else args.weak_fallback_frac
        ok=bool(median_ncc[i]>=args.min_ncc and fb_frac[i]<=lim)
        okboats.append(ok)
        quality.append('HIGH' if strong and fb_frac[i]<=args.weak_fallback_frac else ('MEDIUM' if ok else 'LOW'))
    accepted=bool(all(okboats) and sum(q!='LOW' for q in quality)>=6)
    payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'stride':args.stride,'effective_fps':fps/args.stride,
             'leakage_guard':'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER','method':'stride LK prediction + bounded adaptive template match + confidence-aware fail-closed gate',
             'entry_order':entry_order,'template_fallbacks':{str(i+1):int(x) for i,x in enumerate(fallback)},
             'fallback_fraction':{str(i+1):round(float(x),3) for i,x in enumerate(fb_frac)},
             'median_template_ncc':{str(i+1):round(float(x),3) for i,x in enumerate(median_ncc)},
             'quality_tier':{str(i+1):quality[i] for i in range(6)},'samples':samples,'accepted':accepted}
    if not accepted: payload['reason']='FAIL_CLOSED: confidence-aware tracking quality insufficient'
    else:
        horizons={}; y0=centers0[:,1]; final_res=None
        for off in OFFSETS[1:]:
            c=np.array(samples[f'{off:.1f}']['centers'],float); dx=c[:,0]-centers0[:,0]; rel,trend=robust_linear_residual(y0,dx)
            horizons[f'{off:.1f}']={'dx_px':[round(float(x),3) for x in dx],'perspective_trend':trend,'relative_forward_px':[round(float(x),3) for x in rel]}
            if off==1.5: final_res=rel
        med=np.median(final_res); mad=np.median(np.abs(final_res-med)); scale=max(1.0,1.4826*mad)
        ses=np.clip(np.rint((final_res-med)/scale),-3,3).astype(int); order=np.argsort(-final_res); ranks=np.empty(6,int); ranks[order]=np.arange(1,7)
        payload['horizons']=horizons; payload['boats']={str(i+1):{'relative_forward_1_5px':round(float(final_res[i]),3),'stretch_rank':int(ranks[i]),'ses_v5':int(ses[i]),'quality':quality[i]} for i in range(6)}
        payload['ses_scale_px']=round(float(scale),3); payload['warning']='EXPERIMENTAL live score; use only after multi-race blind validation.'
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
