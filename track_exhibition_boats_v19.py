#!/usr/bin/env python3
"""Result-blind predecessor-conditioned fleet beam tracker for exhibition SES.

v18 showed that globally pruning current-frame fleet states before temporal
transition can kill every coherent path even when 96 safe states exist on each
frame. v19 therefore conditions current-frame search on each surviving beam
predecessor. For every boat it combines immutable-anchor peaks from the whole
immutable lane cell with additional immutable-anchor peaks inside the
predecessor's physically reachable window. Joint fleet expansions are built per
predecessor, scored with the unchanged v17 transition/safety function, then
combined and identity-diverse beam-selected.

Quality, geometry, edge, slit-direction, reverse-step, NCC and final confidence
gates are unchanged. No race result, future frame, boat-number special case or
race-specific offset is used.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import cv2
import numpy as np

import track_exhibition_boats_v6 as base
import track_exhibition_boats_v17 as v17

OFFSETS = (0.0, 0.5, 1.0, 1.5)


def _local_anchor_candidates(cur_g, anchor, ylo, yhi, prev_center, radius,
                             topk, min_ncc):
    """Immutable-anchor NCC peaks restricted to a predecessor-reachable window."""
    th, tw = anchor.shape[:2]
    resp = cv2.matchTemplate(cur_g, anchor, cv2.TM_CCOEFF_NORMED)
    rh, rw = resp.shape[:2]
    px, py = map(float, prev_center)
    r0 = max(0, int(np.floor(max(float(ylo), py-radius) - th/2.0)))
    r1 = min(rh, int(np.ceil(min(float(yhi), py+radius) - th/2.0)) + 1)
    c0 = max(0, int(np.floor(px-radius - tw/2.0)))
    c1 = min(rw, int(np.ceil(px+radius - tw/2.0)) + 1)
    if r1 <= r0 or c1 <= c0:
        return []
    work = resp[r0:r1, c0:c1].copy()
    out=[]
    nms_x=max(12,tw//2); nms_y=max(8,th//2)
    for _ in range(max(8,int(topk)*4)):
        _mn,score,_mnl,loc=cv2.minMaxLoc(work)
        if not np.isfinite(score) or float(score)<float(min_ncc): break
        center=np.asarray([c0+loc[0]+tw/2.0,r0+loc[1]+th/2.0],np.float32)
        out.append((center,float(score)))
        yy0=max(0,loc[1]-nms_y); yy1=min(work.shape[0],loc[1]+nms_y+1)
        xx0=max(0,loc[0]-nms_x); xx1=min(work.shape[1],loc[0]+nms_x+1)
        work[yy0:yy1,xx0:xx1]=-2.0
        if len(out)>=int(topk): break
    return out


def _merge_candidates(global_opts, local_opts, prev_center, advance, keep=5):
    """Merge global/local peaks, prefer reachable distinct hypotheses, no gate relaxation."""
    radius=24.0*max(1,int(advance))
    pool=[]
    for c,s in list(local_opts)+list(global_opts):
        if float(np.linalg.norm(np.asarray(c)-np.asarray(prev_center))) > radius:
            continue
        if any(np.linalg.norm(np.asarray(c)-np.asarray(q[0])) < 8.0 for q in pool):
            continue
        pool.append((np.asarray(c,np.float32),float(s)))
    pool.sort(key=lambda z:z[1],reverse=True)
    return pool[:max(1,int(keep))]


def _safe_state(P, scores, initial_order, initial_x, dir_sign,
                reverse_cap, width, height):
    ys=P[:,1]
    if not np.array_equal(np.argsort(ys),initial_order): return None
    gaps=np.diff(ys[initial_order])
    if np.any(gaps<=4.0): return None
    if (np.any(P[:,0]<8) or np.any(P[:,0]>width-8) or
        np.any(P[:,1]<8) or np.any(P[:,1]>height-8)): return None
    for a in range(6):
        for b in range(a+1,6):
            if np.linalg.norm(P[a]-P[b])<20.0: return None
    motion_term=0.0
    for i in range(6):
        sign=float(dir_sign[i])
        if sign==0.0: continue
        progress=sign*float(P[i,0]-initial_x[i])
        if progress < -float(reverse_cap): return None
        if progress<0.0: motion_term -= 0.055*min(-progress,float(reverse_cap))
    appearance=float(np.sum(4.0*scores))
    weak_penalty=float(np.sum(np.maximum(0.0,0.62-scores)))*1.25
    return {'centers':P,'ncc':scores,'local_score':appearance+motion_term-weak_penalty,
            'min_sep':float(np.min(gaps))}


def _identity_distance(a,b):
    return float(np.max(np.linalg.norm(a['centers']-b['centers'],axis=1)))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('video',type=Path)
    ap.add_argument('--slit-sec',type=float,required=True)
    ap.add_argument('--seed-json',type=Path,required=True)
    ap.add_argument('--seed-meta',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=Path('exhibition_tracking_v19.json'))
    ap.add_argument('--stride',type=int,default=2)
    ap.add_argument('--template-w',type=int,default=54)
    ap.add_argument('--template-h',type=int,default=30)
    ap.add_argument('--min-ncc',type=float,default=.48)
    ap.add_argument('--strong-ncc',type=float,default=.80)
    ap.add_argument('--topk',type=int,default=6)
    ap.add_argument('--per-boat-keep',type=int,default=5)
    ap.add_argument('--per-path-keep',type=int,default=12)
    ap.add_argument('--beam-width',type=int,default=24)
    args=ap.parse_args()
    if args.stride<1: raise SystemExit('--stride must be >=1')
    t0=time.perf_counter()

    seed_obj=json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int,seed_obj)) != [1,2,3,4,5,6]: raise SystemExit('seed-json must contain 1..6')
    meta=json.loads(args.seed_meta.read_text(encoding='utf-8')); rows=meta.get('row_details') or {}
    dominant_dx=np.zeros(6,np.float32); dir_sign=np.zeros(6,np.float32)
    for boat in range(1,7):
        dx=float((rows.get(str(boat)) or {}).get('dominant_dx') or 0.0); dominant_dx[boat-1]=dx
        if abs(dx)>=4.0: dir_sign[boat-1]=1.0 if dx>0 else -1.0

    centers0=base.parse_seeds(seed_obj); initial_x=centers0[:,0].copy()
    initial_order=np.argsort(centers0[:,1]); entry_order=[int(i+1) for i in initial_order]
    cap=cv2.VideoCapture(str(args.video)); fps=cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC,args.slit_sec*1000.0); ok,slit=cap.read()
    if not ok: raise SystemExit('cannot read slit frame')
    slit_g=cv2.cvtColor(slit,cv2.COLOR_BGR2GRAY); H,W=slit_g.shape[:2]
    reverse_cap=max(48.0,0.05*float(W)); step_reverse_cap=max(12.0,0.0125*float(W))
    anchors=[]
    for cx,cy in centers0:
        a=base.crop_center(slit_g,float(cx),float(cy),args.template_w,args.template_h)
        if a is None: raise SystemExit('FAIL_CLOSED: cannot initialize boat template')
        anchors.append(a.copy())

    total_native=int(round(1.5*fps)); steps=int(np.ceil(total_native/args.stride))
    sample_native={int(round(o*fps)):o for o in OFFSETS[1:]}
    diagnostic={'last_completed_step':0,'last_native_frame':0,'predecessor_counts':[],
                'expanded_counts':[],'beam_sizes':[],'failure':None}
    samples={'0.0':{'centers':centers0.tolist()}}
    paths=[{'centers':centers0.copy(),'score':0.0,'last_step':None,'history':[],
            'ncc_history':[[] for _ in range(6)],'min_sep':1e9,'samples':dict(samples)}]
    native_done=0

    def fail(reason):
        diagnostic['failure']=reason; best=max(paths,key=lambda p:p['score']) if paths else None
        payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'stride':args.stride,
                 'method':'v19 result-blind predecessor-conditioned fleet beam tracker',
                 'entry_order':entry_order,'accepted':False,'reason':reason,'diagnostic':diagnostic,
                 'dominant_dx':{str(i+1):round(float(dominant_dx[i]),3) for i in range(6)},
                 'direction_sign':{str(i+1):int(dir_sign[i]) for i in range(6)},
                 'tracking_runtime_sec':round(time.perf_counter()-t0,3),'tracker_version':'v19'}
        if best is not None: payload['last_centers']=best['centers'].tolist(); payload['samples']=best['samples']
        args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(payload,ensure_ascii=False,indent=2)); raise SystemExit(2)

    for step in range(1,steps+1):
        advance=min(args.stride,total_native-native_done)
        if advance<=0: break
        for _ in range(advance-1):
            if not cap.grab(): fail('FAIL_CLOSED: video ended during stride grab')
        ok,cur=cap.read()
        if not ok: fail('FAIL_CLOSED: video ended during stride read')
        native_done+=advance; elapsed=native_done/fps; cur_g=cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY)
        cells=v17._fixed_seed_cells(centers0,initial_order,H,elapsed)
        if cells is None: fail('FAIL_CLOSED: invalid immutable seed lane bands')
        global_lists=[]
        for i in range(6):
            ylo,yhi=cells[i]; opts=v17._anchor_candidates(cur_g,anchors[i],ylo,yhi,args.topk,args.min_ncc)
            if not opts: fail(f'FAIL_CLOSED: no immutable-anchor candidate for boat {i+1}')
            global_lists.append(opts)

        expanded=[]; pred_with_expansion=0
        for p in paths:
            cand_lists=[]; viable=True
            for i in range(6):
                ylo,yhi=cells[i]; radius=24.0*max(1,int(advance))
                local=_local_anchor_candidates(cur_g,anchors[i],ylo,yhi,p['centers'][i],radius,args.topk,args.min_ncc)
                opts=_merge_candidates(global_lists[i],local,p['centers'][i],advance,args.per_boat_keep)
                if not opts: viable=False; break
                cand_lists.append(opts)
            if not viable: continue
            local_exp=[]
            for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
                P=np.asarray([cand_lists[i][j][0] for i,j in enumerate(idxs)],np.float32)
                scores=np.asarray([cand_lists[i][j][1] for i,j in enumerate(idxs)],float)
                s=_safe_state(P,scores,initial_order,initial_x,dir_sign,reverse_cap,W,H)
                if s is None: continue
                tr=v17._transition(p,s,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order)
                if tr is None: continue
                tr_score,step_vec=tr
                local_exp.append((float(tr_score),s,step_vec))
            if not local_exp: continue
            pred_with_expansion+=1; local_exp.sort(key=lambda z:z[0],reverse=True)
            for tr_score,s,step_vec in local_exp[:max(1,args.per_path_keep)]:
                npth={'centers':s['centers'].copy(),'score':float(p['score'])+tr_score,
                      'last_step':step_vec.copy(),'history':p['history']+[s['centers'].copy()],
                      'ncc_history':[list(x) for x in p['ncc_history']],
                      'min_sep':min(float(p['min_sep']),float(s['min_sep'])),
                      'samples':json.loads(json.dumps(p['samples']))}
                for i in range(6): npth['ncc_history'][i].append(float(s['ncc'][i]))
                for nf,off in sample_native.items():
                    key=f'{off:.1f}'
                    if key not in npth['samples'] and native_done>=nf:
                        vals=[round(float(x),3) for x in s['ncc']]
                        npth['samples'][key]={'centers':s['centers'].tolist(),'identity_ncc':vals,
                                             'anchor_ncc':vals,'adaptive_ncc':vals}
                expanded.append(npth)
        diagnostic['predecessor_counts'].append(pred_with_expansion); diagnostic['expanded_counts'].append(len(expanded))
        if not expanded: fail('FAIL_CLOSED: predecessor-conditioned beam exhausted; no feasible temporal expansion')
        expanded.sort(key=lambda p:p['score'],reverse=True); next_paths=[]
        for p in expanded:
            if any(_identity_distance(p,q)<5.0 for q in next_paths): continue
            next_paths.append(p)
            if len(next_paths)>=args.beam_width: break
        paths=next_paths or expanded[:1]
        diagnostic['last_completed_step']=step; diagnostic['last_native_frame']=native_done
        diagnostic['beam_sizes'].append(len(paths)); diagnostic['best_score']=round(float(paths[0]['score']),4)
        diagnostic['last_centers']=paths[0]['centers'].tolist()

    cap.release(); evaluated=[]
    for p in paths:
        med=np.asarray([float(np.median(x)) if x else 0.0 for x in p['ncc_history']],float)
        quality=['HIGH' if x>=args.strong_ncc else ('MEDIUM' if x>=args.min_ncc else 'LOW') for x in med]
        accepted=bool(np.all(med>=args.min_ncc) and all(q!='LOW' for q in quality))
        evaluated.append((accepted,p['score'],p,med,quality))
    evaluated.sort(key=lambda z:(z[0],z[1]),reverse=True); accepted,_score,best,med,quality=evaluated[0]
    payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'stride':args.stride,
             'effective_fps':fps/args.stride,'leakage_guard':'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER',
             'method':'v19 result-blind predecessor-conditioned fleet beam tracker','tracker_version':'v19',
             'entry_order':entry_order,'dominant_dx':{str(i+1):round(float(dominant_dx[i]),3) for i in range(6)},
             'direction_sign':{str(i+1):int(dir_sign[i]) for i in range(6)},
             'reverse_cap_px':round(float(reverse_cap),3),
             'step_reverse_cap_px_per_native_frame':round(float(step_reverse_cap),3),
             'min_lane_separation_px':None if best['min_sep']==1e9 else round(float(best['min_sep']),3),
             'template_fallbacks':{str(i+1):0 for i in range(6)},'fallback_fraction':{str(i+1):0.0 for i in range(6)},
             'median_identity_ncc':{str(i+1):round(float(med[i]),3) for i in range(6)},
             'median_anchor_ncc':{str(i+1):round(float(med[i]),3) for i in range(6)},
             'median_adaptive_ncc':{str(i+1):round(float(med[i]),3) for i in range(6)},
             'quality_tier':{str(i+1):quality[i] for i in range(6)},'samples':best['samples'],
             'diagnostic':diagnostic,'accepted':bool(accepted),'tracking_runtime_sec':round(time.perf_counter()-t0,3),
             'v19_changes':{'candidate_generation':'immutable anchor global peaks + predecessor-reachable immutable-anchor peaks',
                            'temporal_selection':'per-predecessor K-best joint expansions then identity-diverse fleet beam',
                            'future_frame_feedback':False,'quality_thresholds_relaxed':False,'result_blind':True}}
    if not accepted: payload['reason']='FAIL_CLOSED: confidence-aware tracking quality insufficient'
    else:
        horizons={}; y0=centers0[:,1]; final_res=None
        for off in OFFSETS[1:]:
            key=f'{off:.1f}'
            if key not in best['samples']:
                payload['accepted']=False; payload['reason']='FAIL_CLOSED: missing required horizon sample'; break
            c=np.asarray(best['samples'][key]['centers'],float); dx=c[:,0]-centers0[:,0]
            rel,trend=base.robust_linear_residual(y0,dx)
            horizons[key]={'dx_px':[round(float(x),3) for x in dx],'perspective_trend':trend,
                           'relative_forward_px':[round(float(x),3) for x in rel]}
            if off==1.5: final_res=rel
        if payload['accepted']:
            medr=np.median(final_res); mad=np.median(np.abs(final_res-medr)); scale=max(1.0,1.4826*mad)
            ses=np.clip(np.rint((final_res-medr)/scale),-3,3).astype(int)
            order=np.argsort(-final_res); ranks=np.empty(6,int); ranks[order]=np.arange(1,7)
            payload['horizons']=horizons
            payload['boats']={str(i+1):{'relative_forward_1_5px':round(float(final_res[i]),3),
                              'stretch_rank':int(ranks[i]),'ses_v19':int(ses[i]),'quality':quality[i]} for i in range(6)}
            payload['ses_scale_px']=round(float(scale),3)
            payload['warning']='EXPERIMENTAL live score; use only after multi-race blind validation.'
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))
    if not payload['accepted']: raise SystemExit(2)

if __name__=='__main__': main()
