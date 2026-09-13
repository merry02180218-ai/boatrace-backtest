#!/usr/bin/env python3
"""Anchor-memory joint six-boat tracker for result-blind SES.

v9 keeps v8's joint fleet assignment, lane/order/jump/edge constraints, stride,
NCC thresholds and fallback caps. It adds immutable seed-frame appearance memory
for each boat alongside the adaptive template. Candidate patches are proposed by
both memories, scored against both, and adaptive templates update only after a
high-confidence match that still agrees with the immutable anchor. This is meant
to prevent gradual template contamination by wake/background texture. No race
result, boat-specific rule, or race-specific offset is used.
"""
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path
import cv2
import numpy as np
import track_exhibition_boats_v6 as base
import track_exhibition_boats_v8 as v8

OFFSETS=(0.0,0.5,1.0,1.5)


def patch_ncc(cur_g, template, center):
    h,w=template.shape[:2]
    p=base.crop_center(cur_g,float(center[0]),float(center[1]),w,h)
    if p is None or p.shape!=template.shape:
        return -1.0
    return float(cv2.matchTemplate(p,template,cv2.TM_CCOEFF_NORMED)[0,0])


def dual_candidates(cur_g, adaptive, anchor, pred, ylo, yhi, search_x, search_y, topk):
    raw=[]
    for source,tmpl in (("adaptive",adaptive),("anchor",anchor)):
        for c,_ in v8.template_candidates(cur_g,tmpl,pred,ylo,yhi,search_x,search_y,topk):
            # Blend only after a concrete image candidate is found, exactly as v8.
            est=(.72*c+.28*pred).astype(np.float32)
            an=patch_ncc(cur_g,anchor,est)
            ad=patch_ncc(cur_g,adaptive,est)
            raw.append((est,ad,an,source))
    # Deduplicate nearly identical proposals, retaining the stronger dual-memory one.
    raw.sort(key=lambda z:(max(z[1],z[2]),z[1]+z[2]),reverse=True)
    out=[]
    for item in raw:
        if any(np.linalg.norm(item[0]-x[0])<10.0 for x in out):
            continue
        out.append(item)
        if len(out)>=max(2,int(topk)+1): break
    return out


def joint_assign(cand_lists, centers, preds, cells, fleet, advance, min_ncc):
    best=None; best_score=-1e100
    for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
        pts=[]; score=0.0; ok=True
        for i,j in enumerate(idxs):
            c,ad,an,is_fb=cand_lists[i][j]
            ylo,yhi=cells[i]
            if not (ylo<=float(c[1])<=yhi): ok=False; break
            step_vec=c-centers[i]
            if np.linalg.norm(step_vec)>24.0*advance: ok=False; break
            if not is_fb:
                identity=max(float(ad),float(an))
                if identity<min_ncc: ok=False; break
                if abs(float(c[1]-preds[i][1]))>10.0*advance: ok=False; break
                # Adaptive similarity handles changing scale/appearance; immutable anchor
                # similarity resists drift. Both contribute, but neither is a race rule.
                score += 1.8*float(ad)+1.8*float(an)+0.8*identity
                score -= 0.010*np.linalg.norm(c-preds[i])
                score -= 0.004*np.linalg.norm(step_vec-fleet)
            else:
                score -= 1.25
            pts.append(c)
        if not ok: continue
        P=np.asarray(pts,np.float32); ys=P[:,1]; order=np.argsort(centers[:,1])
        if not np.array_equal(np.argsort(ys),order): continue
        if np.any(np.diff(ys[order])<=4.0): continue
        for a in range(6):
            for b in range(a+1,6):
                if np.linalg.norm(P[a]-P[b])<20.0:
                    ok=False; break
            if not ok: break
        if not ok: continue
        if score>best_score: best_score=score; best=idxs
    return best,best_score


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path); ap.add_argument('--slit-sec',type=float,required=True)
    ap.add_argument('--seed-json',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=Path('exhibition_tracking_v9.json'))
    ap.add_argument('--stride',type=int,default=2); ap.add_argument('--template-w',type=int,default=54)
    ap.add_argument('--template-h',type=int,default=30); ap.add_argument('--min-ncc',type=float,default=.48)
    ap.add_argument('--strong-ncc',type=float,default=.80); ap.add_argument('--weak-fallback-frac',type=float,default=.35)
    ap.add_argument('--strong-fallback-frac',type=float,default=.50); ap.add_argument('--cell-margin',type=float,default=3.0)
    ap.add_argument('--topk',type=int,default=2); args=ap.parse_args()
    if args.stride<1: raise SystemExit('--stride must be >=1')

    seed_obj=json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int,seed_obj))!=[1,2,3,4,5,6]: raise SystemExit('seed-json must contain 1..6')
    centers0=base.parse_seeds(seed_obj); centers=centers0.copy()
    initial_order=np.argsort(centers0[:,1]); entry_order=[int(i+1) for i in initial_order]
    cap=cv2.VideoCapture(str(args.video)); fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC,args.slit_sec*1000.0); ok,prev=cap.read()
    if not ok: raise SystemExit('cannot read slit frame')
    prev_g=cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY); H,W=prev_g.shape[:2]
    if base.dynamic_cells(centers,initial_order,H,args.cell_margin) is None: raise SystemExit('FAIL_CLOSED: invalid initial lane cells')
    anchors=[]
    for cx,cy in centers:
        t=base.crop_center(prev_g,float(cx),float(cy),args.template_w,args.template_h)
        if t is None: raise SystemExit('FAIL_CLOSED: cannot initialize boat template')
        anchors.append(t.copy())
    templates=[x.copy() for x in anchors]

    total_native=int(round(1.5*fps)); steps=int(np.ceil(total_native/args.stride))
    sample_native={int(round(o*fps)):o for o in OFFSETS[1:]}; samples={'0.0':{'centers':centers.tolist()}}
    fallback=np.zeros(6,int); identity_hist=[[] for _ in range(6)]; anchor_hist=[[] for _ in range(6)]; adaptive_hist=[[] for _ in range(6)]
    prev_velocity=np.zeros((6,2),np.float32); min_sep=1e9; native_done=0
    diagnostic={'last_completed_step':0,'last_native_frame':0,'last_centers':centers.tolist(),'failure':None,'joint_score':None}

    def fail(reason):
        diagnostic['failure']=reason
        payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'stride':args.stride,
          'method':'v8 joint assignment + immutable anchor appearance memory + guarded adaptive updates',
          'entry_order':entry_order,'accepted':False,'reason':reason,'diagnostic':diagnostic,
          'template_fallbacks':{str(i+1):int(x) for i,x in enumerate(fallback)},'samples':samples}
        args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(payload,ensure_ascii=False,indent=2)); raise SystemExit(2)

    for step in range(1,steps+1):
        advance=min(args.stride,total_native-native_done)
        if advance<=0: break
        for _ in range(advance-1):
            if not cap.grab(): fail('FAIL_CLOSED: video ended during stride grab')
        ok,cur=cap.read()
        if not ok: fail('FAIL_CLOSED: video ended during stride read')
        native_done+=advance; cur_g=cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY)
        cells=base.dynamic_cells(centers,initial_order,H,args.cell_margin)
        if cells is None: fail('FAIL_CLOSED: dynamic lane cells collapsed')
        lk=[]; ns=[]; spreads=[]
        for cx,cy in centers:
            d,n,s=base.local_motion(prev_g,cur_g,float(cx),float(cy),max_mag=24*advance); lk.append(d); ns.append(n); spreads.append(s)
        valid=np.array([d is not None for d in lk])
        if valid.any():
            Dv=np.array([d if d is not None else [np.nan,np.nan] for d in lk],np.float32); fleet=np.nanmedian(Dv,axis=0)
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
            preds.append(pred); opts=[]
            for est,ad,an,_src in dual_candidates(cur_g,templates[i],anchors[i],pred,ylo,yhi,34*advance,10*advance,args.topk):
                opts.append((est,float(ad),float(an),False))
            opts.append((pred.astype(np.float32),None,None,True)); cand_lists.append(opts)
        preds=np.asarray(preds,np.float32)
        choice,jscore=joint_assign(cand_lists,centers,preds,cells,np.asarray(fleet,np.float32),advance,args.min_ncc)
        if choice is None:
            diagnostic['candidate_counts']=[len(x) for x in cand_lists]; fail('FAIL_CLOSED: no feasible joint six-boat assignment')

        new=centers.copy(); frame_id=[]; frame_an=[]; frame_ad=[]
        for i,j in enumerate(choice):
            est,ad,an,is_fb=cand_lists[i][j]
            if is_fb:
                fallback[i]+=1; frame_id.append(None); frame_an.append(None); frame_ad.append(None)
            else:
                identity=max(float(ad),float(an)); identity_hist[i].append(identity); anchor_hist[i].append(float(an)); adaptive_hist[i].append(float(ad))
                frame_id.append(identity); frame_an.append(float(an)); frame_ad.append(float(ad))
                # Update only when the current patch is strong AND remains recognizably
                # related to the immutable seed-frame appearance. Otherwise freeze.
                if ad>=.72 and an>=.55:
                    nt=base.crop_center(cur_g,float(est[0]),float(est[1]),args.template_w,args.template_h)
                    if nt is not None and nt.shape==templates[i].shape: templates[i]=cv2.addWeighted(templates[i],.90,nt,.10,0)
            new[i]=est
        velocities=new-centers; centers=new; prev_velocity=.65*prev_velocity+.35*velocities
        cur_order=np.argsort(centers[:,1])
        if not np.array_equal(cur_order,initial_order): fail(f'FAIL_CLOSED: entry-order violation; expected {entry_order}, got {[int(i+1) for i in cur_order]}')
        gaps=np.diff(centers[initial_order,1]); min_sep=min(min_sep,float(np.min(gaps)))
        if not np.all(gaps>4): fail('FAIL_CLOSED: lane separation too small')
        if np.any(centers[:,0]<8) or np.any(centers[:,0]>W-8) or np.any(centers[:,1]<8) or np.any(centers[:,1]>H-8): fail('FAIL_CLOSED: tracked center reached frame edge')
        diagnostic.update({'last_completed_step':step,'last_native_frame':native_done,'last_centers':centers.tolist(),'joint_score':round(float(jscore),4),'candidate_counts':[len(x) for x in cand_lists]})
        prev_g=cur_g
        for nf,off in sample_native.items():
            if f'{off:.1f}' not in samples and native_done>=nf:
                samples[f'{off:.1f}']={'centers':centers.tolist(),'features':ns,'spread':spreads,
                  'identity_ncc':[None if x is None else round(float(x),3) for x in frame_id],
                  'anchor_ncc':[None if x is None else round(float(x),3) for x in frame_an],
                  'adaptive_ncc':[None if x is None else round(float(x),3) for x in frame_ad]}

    cap.release(); med_id=np.array([float(np.median(x)) if x else 0.0 for x in identity_hist]); med_an=np.array([float(np.median(x)) if x else 0.0 for x in anchor_hist]); med_ad=np.array([float(np.median(x)) if x else 0.0 for x in adaptive_hist])
    fb_frac=fallback/max(1,steps); quality=[]; okboats=[]
    for i in range(6):
        strong=med_id[i]>=args.strong_ncc; lim=args.strong_fallback_frac if strong else args.weak_fallback_frac
        ok=bool(med_id[i]>=args.min_ncc and fb_frac[i]<=lim); okboats.append(ok)
        quality.append('HIGH' if strong and fb_frac[i]<=args.weak_fallback_frac else ('MEDIUM' if ok else 'LOW'))
    accepted=bool(all(okboats) and all(q!='LOW' for q in quality))
    payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'stride':args.stride,'effective_fps':fps/args.stride,
      'leakage_guard':'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER','method':'v8 joint assignment + immutable anchor appearance memory + guarded adaptive updates',
      'entry_order':entry_order,'min_lane_separation_px':None if min_sep==1e9 else round(min_sep,3),
      'template_fallbacks':{str(i+1):int(x) for i,x in enumerate(fallback)},'fallback_fraction':{str(i+1):round(float(x),3) for i,x in enumerate(fb_frac)},
      'median_identity_ncc':{str(i+1):round(float(x),3) for i,x in enumerate(med_id)},'median_anchor_ncc':{str(i+1):round(float(x),3) for i,x in enumerate(med_an)},
      'median_adaptive_ncc':{str(i+1):round(float(x),3) for i,x in enumerate(med_ad)},'quality_tier':{str(i+1):quality[i] for i in range(6)},
      'samples':samples,'diagnostic':diagnostic,'accepted':accepted}
    if not accepted: payload['reason']='FAIL_CLOSED: confidence-aware tracking quality insufficient'
    else:
        horizons={}; y0=centers0[:,1]; final_res=None
        for off in OFFSETS[1:]:
            c=np.array(samples[f'{off:.1f}']['centers'],float); dx=c[:,0]-centers0[:,0]; rel,trend=base.robust_linear_residual(y0,dx)
            horizons[f'{off:.1f}']={'dx_px':[round(float(x),3) for x in dx],'perspective_trend':trend,'relative_forward_px':[round(float(x),3) for x in rel]}
            if off==1.5: final_res=rel
        med=np.median(final_res); mad=np.median(np.abs(final_res-med)); scale=max(1.0,1.4826*mad); ses=np.clip(np.rint((final_res-med)/scale),-3,3).astype(int)
        order=np.argsort(-final_res); ranks=np.empty(6,int); ranks[order]=np.arange(1,7); payload['horizons']=horizons
        payload['boats']={str(i+1):{'relative_forward_1_5px':round(float(final_res[i]),3),'stretch_rank':int(ranks[i]),'ses_v9':int(ses[i]),'quality':quality[i]} for i in range(6)}
        payload['ses_scale_px']=round(float(scale),3); payload['warning']='EXPERIMENTAL live score; use only after multi-race blind validation.'
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(payload,ensure_ascii=False,indent=2))
    if not accepted: raise SystemExit(2)

if __name__=='__main__': main()
