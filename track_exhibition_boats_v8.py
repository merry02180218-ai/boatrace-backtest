#!/usr/bin/env python3
"""Joint-assignment six-boat tracker for result-blind SES.

v8 keeps v7's LK/template fusion, NCC thresholds, fallback caps, stride and
fail-closed quality gate.  The change is only in template-fallback identity:
each boat contributes several center-gated template candidates and all six are
assigned jointly.  The joint objective rewards NCC and temporal continuity while
rejecting entry-order/lane-cell violations, implausible per-step motion and
near-duplicate image patches.  This is intended to prevent independent trackers
from latching onto wake/background texture.  No race result, boat-specific rule,
or race-specific offset is used.
"""
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path
import cv2
import numpy as np
import track_exhibition_boats_v6 as base

OFFSETS=(0.0,0.5,1.0,1.5)


def template_candidates(cur_g, template, pred, ylo, yhi, search_x=68, search_y=20, topk=3):
    th,tw=template.shape[:2]
    pcx,pcy=float(pred[0]),float(pred[1])
    x1=max(0,int(round(pcx-tw/2-search_x)))
    x2=min(cur_g.shape[1],int(round(pcx+tw/2+search_x)))
    y1=max(0,int(round(pcy-th/2-search_y)))
    y2=min(cur_g.shape[0],int(round(pcy+th/2+search_y)))
    roi=cur_g[y1:y2,x1:x2]
    if roi.shape[0]<th or roi.shape[1]<tw:
        return []
    res=cv2.matchTemplate(roi,template,cv2.TM_CCOEFF_NORMED)
    if res.size==0:
        return []
    center_ys=y1+np.arange(res.shape[0],dtype=np.float32)+th/2.0
    valid_rows=(center_ys>=float(ylo))&(center_ys<=float(yhi))
    if not np.any(valid_rows):
        return []
    work=res.copy(); work[~valid_rows,:]=-np.inf
    out=[]
    # Greedy local non-maximum suppression so top-k are distinct patches.
    radx=max(4,tw//5); rady=max(3,th//5)
    for _ in range(max(1,int(topk))):
        flat=int(np.argmax(work)); r,c=np.unravel_index(flat,work.shape)
        score=float(work[r,c])
        if not np.isfinite(score): break
        center=np.array([x1+c+tw/2.0,y1+r+th/2.0],np.float32)
        out.append((center,score))
        rr1=max(0,r-rady); rr2=min(work.shape[0],r+rady+1)
        cc1=max(0,c-radx); cc2=min(work.shape[1],c+radx+1)
        work[rr1:rr2,cc1:cc2]=-np.inf
    return out


def joint_assign(cand_lists, centers, preds, cells, fleet, advance, min_ncc):
    """Return one candidate index per boat. Last candidate in each list may be fallback."""
    best=None; best_score=-1e100
    # Lists are deliberately capped (top3 + fallback), at most 4^6 combinations.
    for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
        pts=[]; score=0.0; ok=True
        for i,j in enumerate(idxs):
            c,ncc,is_fb=cand_lists[i][j]
            ylo,yhi=cells[i]
            if not (ylo<=float(c[1])<=yhi): ok=False; break
            step_vec=c-centers[i]
            # Generous resolution/time-relative continuity gate. Genuine stretch
            # differences are much smaller than this per stride; wake jumps are not.
            if np.linalg.norm(step_vec)>24.0*advance: ok=False; break
            if not is_fb:
                if ncc is None or ncc<min_ncc: ok=False; break
                if abs(float(c[1]-preds[i][1]))>10.0*advance: ok=False; break
                # Reward NCC; mildly penalize distance from physically predicted center
                # and from robust fleet step. This does not force equal x motion.
                score += 3.0*float(ncc)
                score -= 0.010*np.linalg.norm(c-preds[i])
                score -= 0.004*np.linalg.norm(step_vec-fleet)
            else:
                # Existing behavior when template evidence is unusable.
                score -= 1.25
            pts.append(c)
        if not ok: continue
        P=np.asarray(pts,np.float32)
        # Preserve supplied entry-order geometry and reject near-duplicate patches.
        ys=P[:,1]
        order=np.argsort(centers[:,1])
        if not np.array_equal(np.argsort(ys),order): continue
        if np.any(np.diff(ys[order])<=4.0): continue
        for a in range(6):
            for b in range(a+1,6):
                if np.linalg.norm(P[a]-P[b])<20.0:
                    ok=False; break
            if not ok: break
        if not ok: continue
        if score>best_score:
            best_score=score; best=idxs
    return best


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--slit-sec',type=float,required=True)
    ap.add_argument('--seed-json',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=Path('exhibition_tracking_v8.json'))
    ap.add_argument('--stride',type=int,default=2)
    ap.add_argument('--template-w',type=int,default=54)
    ap.add_argument('--template-h',type=int,default=30)
    ap.add_argument('--min-ncc',type=float,default=.48)
    ap.add_argument('--strong-ncc',type=float,default=.80)
    ap.add_argument('--weak-fallback-frac',type=float,default=.35)
    ap.add_argument('--strong-fallback-frac',type=float,default=.50)
    ap.add_argument('--cell-margin',type=float,default=3.0)
    ap.add_argument('--topk',type=int,default=3)
    args=ap.parse_args()
    if args.stride<1: raise SystemExit('--stride must be >=1')

    seed_obj=json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int,seed_obj))!=[1,2,3,4,5,6]: raise SystemExit('seed-json must contain 1..6')
    centers0=base.parse_seeds(seed_obj); centers=centers0.copy()
    initial_order=np.argsort(centers0[:,1]); entry_order=[int(i+1) for i in initial_order]

    cap=cv2.VideoCapture(str(args.video)); fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC,args.slit_sec*1000.0)
    ok,prev=cap.read()
    if not ok: raise SystemExit('cannot read slit frame')
    prev_g=cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY); H,W=prev_g.shape[:2]
    if base.dynamic_cells(centers,initial_order,H,args.cell_margin) is None:
        raise SystemExit('FAIL_CLOSED: invalid initial lane cells')
    templates=[]
    for cx,cy in centers:
        t=base.crop_center(prev_g,float(cx),float(cy),args.template_w,args.template_h)
        if t is None: raise SystemExit('FAIL_CLOSED: cannot initialize boat template')
        templates.append(t)

    total_native=int(round(1.5*fps)); steps=int(np.ceil(total_native/args.stride))
    sample_native={int(round(o*fps)):o for o in OFFSETS[1:]}
    samples={'0.0':{'centers':centers.tolist()}}
    fallback=np.zeros(6,int); ncc_hist=[[] for _ in range(6)]
    prev_velocity=np.zeros((6,2),np.float32); min_sep=1e9; native_done=0

    for step in range(1,steps+1):
        advance=min(args.stride,total_native-native_done)
        if advance<=0: break
        for _ in range(advance-1):
            if not cap.grab(): raise SystemExit('video ended during stride grab')
        ok,cur=cap.read()
        if not ok: raise SystemExit('video ended during stride read')
        native_done+=advance; cur_g=cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY)
        cells=base.dynamic_cells(centers,initial_order,H,args.cell_margin)
        if cells is None: raise SystemExit('FAIL_CLOSED: dynamic lane cells collapsed')

        lk=[]; ns=[]; spreads=[]
        for cx,cy in centers:
            d,n,s=base.local_motion(prev_g,cur_g,float(cx),float(cy),max_mag=24*advance)
            lk.append(d); ns.append(n); spreads.append(s)
        valid=np.array([d is not None for d in lk])
        if valid.any():
            Dv=np.array([d if d is not None else [np.nan,np.nan] for d in lk],np.float32)
            fleet=np.nanmedian(Dv,axis=0)
        else: fleet=np.median(prev_velocity,axis=0)

        preds=[]; cand_lists=[]
        for i in range(6):
            ylo,yhi=cells[i]; d=lk[i]
            if d is not None and np.linalg.norm(d-fleet)<=24*advance: pred=centers[i]+d
            elif np.linalg.norm(prev_velocity[i])>0: pred=centers[i]+prev_velocity[i]
            else: pred=centers[i]+fleet
            pred=pred.astype(np.float32)
            if float(pred[1])<ylo or float(pred[1])>yhi:
                pred=pred.copy(); pred[1]=np.clip(pred[1],ylo+1.0,yhi-1.0)
            preds.append(pred)
            raw=template_candidates(cur_g,templates[i],pred,ylo,yhi,34*advance,10*advance,args.topk)
            opts=[]
            for m,ncc in raw:
                est=(.72*m+.28*pred).astype(np.float32)
                opts.append((est,float(ncc),False))
            opts.append((pred.astype(np.float32),None,True))
            cand_lists.append(opts)
        preds=np.asarray(preds,np.float32)
        choice=joint_assign(cand_lists,centers,preds,cells,np.asarray(fleet,np.float32),advance,args.min_ncc)
        if choice is None: raise SystemExit('FAIL_CLOSED: no feasible joint six-boat assignment')

        new=centers.copy(); frame_ncc=[]
        for i,j in enumerate(choice):
            est,ncc,is_fb=cand_lists[i][j]
            frame_ncc.append(ncc)
            if is_fb:
                fallback[i]+=1
            else:
                ncc_hist[i].append(float(ncc))
                if ncc>=.72:
                    nt=base.crop_center(cur_g,float(est[0]),float(est[1]),args.template_w,args.template_h)
                    if nt is not None and nt.shape==templates[i].shape:
                        templates[i]=cv2.addWeighted(templates[i],.85,nt,.15,0)
            new[i]=est

        velocities=new-centers; centers=new; prev_velocity=.65*prev_velocity+.35*velocities
        cur_order=np.argsort(centers[:,1])
        if not np.array_equal(cur_order,initial_order):
            raise SystemExit(f'FAIL_CLOSED: entry-order violation; expected {entry_order}, got {[int(i+1) for i in cur_order]}')
        gaps=np.diff(centers[initial_order,1]); min_sep=min(min_sep,float(np.min(gaps)))
        if not np.all(gaps>4): raise SystemExit('FAIL_CLOSED: lane separation too small')
        # Physical sanity: centers must remain comfortably on-frame.
        if np.any(centers[:,0]<8) or np.any(centers[:,0]>W-8) or np.any(centers[:,1]<8) or np.any(centers[:,1]>H-8):
            raise SystemExit('FAIL_CLOSED: tracked center reached frame edge')
        prev_g=cur_g
        for nf,off in sample_native.items():
            if f'{off:.1f}' not in samples and native_done>=nf:
                samples[f'{off:.1f}']={'centers':centers.tolist(),'features':ns,'spread':spreads,
                    'ncc':[None if x is None else round(float(x),3) for x in frame_ncc]}

    cap.release(); median_ncc=np.array([float(np.median(x)) if x else 0.0 for x in ncc_hist])
    fb_frac=fallback/max(1,steps); quality=[]; okboats=[]
    for i in range(6):
        strong=median_ncc[i]>=args.strong_ncc
        lim=args.strong_fallback_frac if strong else args.weak_fallback_frac
        ok=bool(median_ncc[i]>=args.min_ncc and fb_frac[i]<=lim); okboats.append(ok)
        quality.append('HIGH' if strong and fb_frac[i]<=args.weak_fallback_frac else ('MEDIUM' if ok else 'LOW'))
    accepted=bool(all(okboats) and all(q!='LOW' for q in quality))
    payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'stride':args.stride,
      'effective_fps':fps/args.stride,'leakage_guard':'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER',
      'method':'v7 center-gated tracking + top-k joint six-boat assignment + unchanged confidence fail-closed gate',
      'entry_order':entry_order,'min_lane_separation_px':None if min_sep==1e9 else round(min_sep,3),
      'template_fallbacks':{str(i+1):int(x) for i,x in enumerate(fallback)},
      'fallback_fraction':{str(i+1):round(float(x),3) for i,x in enumerate(fb_frac)},
      'median_template_ncc':{str(i+1):round(float(x),3) for i,x in enumerate(median_ncc)},
      'quality_tier':{str(i+1):quality[i] for i in range(6)},'samples':samples,'accepted':accepted}
    if not accepted: payload['reason']='FAIL_CLOSED: confidence-aware tracking quality insufficient'
    else:
        horizons={}; y0=centers0[:,1]; final_res=None
        for off in OFFSETS[1:]:
            c=np.array(samples[f'{off:.1f}']['centers'],float); dx=c[:,0]-centers0[:,0]
            rel,trend=base.robust_linear_residual(y0,dx)
            horizons[f'{off:.1f}']={'dx_px':[round(float(x),3) for x in dx],'perspective_trend':trend,
              'relative_forward_px':[round(float(x),3) for x in rel]}
            if off==1.5: final_res=rel
        med=np.median(final_res); mad=np.median(np.abs(final_res-med)); scale=max(1.0,1.4826*mad)
        ses=np.clip(np.rint((final_res-med)/scale),-3,3).astype(int)
        order=np.argsort(-final_res); ranks=np.empty(6,int); ranks[order]=np.arange(1,7)
        payload['horizons']=horizons
        payload['boats']={str(i+1):{'relative_forward_1_5px':round(float(final_res[i]),3),
            'stretch_rank':int(ranks[i]),'ses_v8':int(ses[i]),'quality':quality[i]} for i in range(6)}
        payload['ses_scale_px']=round(float(scale),3)
        payload['warning']='EXPERIMENTAL live score; use only after multi-race blind validation.'
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
