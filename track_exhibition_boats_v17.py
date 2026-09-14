#!/usr/bin/env python3
"""Result-blind fixed-candidate fleet DP tracker for exhibition SES.

v17 removes the remaining prediction-feedback loop from candidate generation.
For each sampled frame and boat it builds an immutable-anchor NCC lattice from a
lane band derived only from the slit-frame seed geometry and elapsed time. These
per-frame candidates are independent of every prior tracking hypothesis. A
multi-frame fleet DP/beam then chooses a globally coherent path using unchanged
safety ideas: entry order, separation, edge checks, maximum step, immutable slit
motion direction, and confidence-aware fail closed behavior.

No race result, future frame look-ahead in candidate generation, boat-number
special case, race-specific offset, or relaxed NCC/fallback gate is used.
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

OFFSETS = (0.0, 0.5, 1.0, 1.5)


def _fixed_seed_cells(centers0, initial_order, height, elapsed, horizon=1.5):
    """Overlapping time-expanded cells derived only from immutable seed geometry."""
    ys = centers0[initial_order, 1].astype(float)
    bounds = [0.0]
    for a, b in zip(ys[:-1], ys[1:]):
        bounds.append((float(a) + float(b)) / 2.0)
    bounds.append(float(height))
    frac = min(1.0, max(0.0, float(elapsed) / max(0.1, float(horizon))))
    expand = 0.055 * float(height) + 0.045 * float(height) * frac
    cells = [None] * 6
    for rank, idx in enumerate(initial_order):
        lo = max(8.0, bounds[rank] - expand)
        hi = min(float(height) - 8.0, bounds[rank + 1] + expand)
        if hi - lo < 12.0:
            return None
        cells[int(idx)] = (lo, hi)
    return cells


def _anchor_candidates(cur_g, anchor, ylo, yhi, topk, min_ncc):
    """State-independent immutable-anchor peaks for one boat in one frame."""
    th, tw = anchor.shape[:2]
    if cur_g.shape[0] < th or cur_g.shape[1] < tw:
        return []
    resp = cv2.matchTemplate(cur_g, anchor, cv2.TM_CCOEFF_NORMED)
    rh, rw = resp.shape[:2]
    r0 = max(0, int(np.floor(float(ylo) - th / 2.0)))
    r1 = min(rh, int(np.ceil(float(yhi) - th / 2.0)) + 1)
    if r1 <= r0:
        return []
    work = resp[r0:r1].copy()
    out = []
    nms_x = max(12, tw // 2)
    nms_y = max(8, th // 2)
    attempts = max(12, int(topk) * 5)
    for _ in range(attempts):
        _mn, score, _mnl, loc = cv2.minMaxLoc(work)
        if not np.isfinite(score) or float(score) < float(min_ncc):
            break
        c = np.asarray([loc[0] + tw / 2.0, r0 + loc[1] + th / 2.0], np.float32)
        out.append((c, float(score)))
        yy0 = max(0, loc[1] - nms_y); yy1 = min(work.shape[0], loc[1] + nms_y + 1)
        xx0 = max(0, loc[0] - nms_x); xx1 = min(work.shape[1], loc[0] + nms_x + 1)
        work[yy0:yy1, xx0:xx1] = -2.0
        if len(out) >= int(topk):
            break
    return out


def _frame_fleet_states(cand_lists, initial_order, initial_x, dir_sign,
                        reverse_cap, width, height, keep):
    """Build current-frame fleet states without using any previous path state."""
    ranked = []
    for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
        pts = [cand_lists[i][j][0] for i, j in enumerate(idxs)]
        scores = np.asarray([cand_lists[i][j][1] for i, j in enumerate(idxs)], float)
        P = np.asarray(pts, np.float32)
        ys = P[:, 1]
        if not np.array_equal(np.argsort(ys), initial_order):
            continue
        gaps = np.diff(ys[initial_order])
        if np.any(gaps <= 4.0):
            continue
        if np.any(P[:, 0] < 8) or np.any(P[:, 0] > width - 8) or np.any(P[:, 1] < 8) or np.any(P[:, 1] > height - 8):
            continue
        dup = False
        for a in range(6):
            for b in range(a + 1, 6):
                if np.linalg.norm(P[a] - P[b]) < 20.0:
                    dup = True; break
            if dup:
                break
        if dup:
            continue
        ok = True
        motion_term = 0.0
        for i in range(6):
            sign = float(dir_sign[i])
            if sign == 0.0:
                continue
            progress = sign * float(P[i, 0] - initial_x[i])
            if progress < -float(reverse_cap):
                ok = False; break
            if progress < 0.0:
                motion_term -= 0.055 * min(-progress, float(reverse_cap))
        if not ok:
            continue
        appearance = float(np.sum(4.0 * scores))
        weak_penalty = float(np.sum(np.maximum(0.0, 0.62 - scores))) * 1.25
        local_score = appearance + motion_term - weak_penalty
        ranked.append({
            'centers': P,
            'ncc': scores,
            'local_score': local_score,
            'min_sep': float(np.min(gaps)),
        })
    ranked.sort(key=lambda s: s['local_score'], reverse=True)
    return ranked[:max(1, int(keep))]


def _transition(prev, cur, advance, dir_sign, initial_x, reverse_cap,
                step_reverse_cap, initial_order):
    P0 = prev['centers']; P1 = cur['centers']
    steps = P1 - P0
    adv = max(1, int(advance))
    if np.any(np.linalg.norm(steps, axis=1) > 24.0 * adv):
        return None
    score = float(cur['local_score'])
    for i in range(6):
        sign = float(dir_sign[i])
        sx = float(steps[i, 0])
        if sign != 0.0:
            signed_step = sign * sx
            progress = sign * float(P1[i, 0] - initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap * adv:
                return None
            if signed_step < 0.0:
                score -= 0.18 * min(-signed_step, step_reverse_cap * adv)
            else:
                score += 0.018 * min(signed_step, 24.0 * adv)
            if progress < 0.0:
                score -= 0.055 * min(-progress, reverse_cap)
        pv = prev.get('last_step')
        if pv is not None:
            score -= 0.024 * float(np.linalg.norm(steps[i] - pv[i]))
    robust = np.median(steps, axis=0)
    score -= 0.004 * float(np.sum(np.linalg.norm(steps - robust, axis=1)))
    return score, steps


def _state_distance(a, b):
    return float(np.mean(np.linalg.norm(a['centers'] - b['centers'], axis=1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--slit-sec', type=float, required=True)
    ap.add_argument('--seed-json', type=Path, required=True)
    ap.add_argument('--seed-meta', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=Path('exhibition_tracking_v17.json'))
    ap.add_argument('--stride', type=int, default=2)
    ap.add_argument('--template-w', type=int, default=54)
    ap.add_argument('--template-h', type=int, default=30)
    ap.add_argument('--min-ncc', type=float, default=.48)
    ap.add_argument('--strong-ncc', type=float, default=.80)
    ap.add_argument('--topk', type=int, default=6)
    ap.add_argument('--frame-state-keep', type=int, default=96)
    ap.add_argument('--beam-width', type=int, default=24)
    args = ap.parse_args()
    if args.stride < 1:
        raise SystemExit('--stride must be >=1')
    t0 = time.perf_counter()

    seed_obj = json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int, seed_obj)) != [1,2,3,4,5,6]:
        raise SystemExit('seed-json must contain 1..6')
    meta = json.loads(args.seed_meta.read_text(encoding='utf-8'))
    rows = meta.get('row_details') or {}
    dominant_dx = np.zeros(6, np.float32); dir_sign = np.zeros(6, np.float32)
    for boat in range(1,7):
        dx = float((rows.get(str(boat)) or {}).get('dominant_dx') or 0.0)
        dominant_dx[boat-1] = dx
        if abs(dx) >= 4.0:
            dir_sign[boat-1] = 1.0 if dx > 0 else -1.0

    centers0 = base.parse_seeds(seed_obj)
    initial_x = centers0[:,0].copy()
    initial_order = np.argsort(centers0[:,1])
    entry_order = [int(i+1) for i in initial_order]

    cap = cv2.VideoCapture(str(args.video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, args.slit_sec * 1000.0)
    ok, slit = cap.read()
    if not ok:
        raise SystemExit('cannot read slit frame')
    slit_g = cv2.cvtColor(slit, cv2.COLOR_BGR2GRAY)
    H,W = slit_g.shape[:2]
    reverse_cap = max(48.0, 0.05 * float(W))
    step_reverse_cap = max(12.0, 0.0125 * float(W))
    anchors=[]
    for cx,cy in centers0:
        a=base.crop_center(slit_g,float(cx),float(cy),args.template_w,args.template_h)
        if a is None:
            raise SystemExit('FAIL_CLOSED: cannot initialize boat template')
        anchors.append(a.copy())

    total_native=int(round(1.5*fps)); steps=int(np.ceil(total_native/args.stride))
    sample_native={int(round(o*fps)):o for o in OFFSETS[1:]}
    diagnostic={'last_completed_step':0,'last_native_frame':0,'frame_state_sizes':[],
                'beam_sizes':[],'failure':None}
    samples={'0.0':{'centers':centers0.tolist()}}
    paths=[{'centers':centers0.copy(),'score':0.0,'last_step':None,'history':[],
            'ncc_history':[[] for _ in range(6)],'min_sep':1e9,'samples':dict(samples)}]
    native_done=0

    def fail(reason):
        diagnostic['failure']=reason
        best=max(paths,key=lambda p:p['score']) if paths else None
        payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'stride':args.stride,
                 'method':'v17 result-blind fixed-candidate fleet DP tracker','entry_order':entry_order,
                 'accepted':False,'reason':reason,'diagnostic':diagnostic,
                 'dominant_dx':{str(i+1):round(float(dominant_dx[i]),3) for i in range(6)},
                 'direction_sign':{str(i+1):int(dir_sign[i]) for i in range(6)},
                 'tracking_runtime_sec':round(time.perf_counter()-t0,3),
                 'tracker_version':'v17'}
        if best is not None:
            payload['last_centers']=best['centers'].tolist(); payload['samples']=best['samples']
        args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(payload,ensure_ascii=False,indent=2)); raise SystemExit(2)

    for step in range(1,steps+1):
        advance=min(args.stride,total_native-native_done)
        if advance<=0: break
        for _ in range(advance-1):
            if not cap.grab(): fail('FAIL_CLOSED: video ended during stride grab')
        ok,cur=cap.read()
        if not ok: fail('FAIL_CLOSED: video ended during stride read')
        native_done += advance
        elapsed=native_done/fps
        cur_g=cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY)
        cells=_fixed_seed_cells(centers0,initial_order,H,elapsed)
        if cells is None: fail('FAIL_CLOSED: invalid immutable seed lane bands')
        cand_lists=[]
        for i in range(6):
            ylo,yhi=cells[i]
            opts=_anchor_candidates(cur_g,anchors[i],ylo,yhi,args.topk,args.min_ncc)
            if not opts:
                fail(f'FAIL_CLOSED: no state-independent anchor candidate for boat {i+1}')
            cand_lists.append(opts)
        states=_frame_fleet_states(cand_lists,initial_order,initial_x,dir_sign,
                                  reverse_cap,W,H,args.frame_state_keep)
        diagnostic['frame_state_sizes'].append(len(states))
        if not states: fail('FAIL_CLOSED: no feasible state-independent fleet state')

        expanded=[]
        for p in paths:
            for s in states:
                tr=_transition(p,s,advance,dir_sign,initial_x,reverse_cap,
                               step_reverse_cap,initial_order)
                if tr is None: continue
                tr_score,step_vec=tr
                npth={'centers':s['centers'].copy(),'score':float(p['score'])+float(tr_score),
                      'last_step':step_vec.copy(),'history':p['history']+[s['centers'].copy()],
                      'ncc_history':[list(x) for x in p['ncc_history']],
                      'min_sep':min(float(p['min_sep']),float(s['min_sep'])),
                      'samples':json.loads(json.dumps(p['samples']))}
                for i in range(6): npth['ncc_history'][i].append(float(s['ncc'][i]))
                for nf,off in sample_native.items():
                    key=f'{off:.1f}'
                    if key not in npth['samples'] and native_done>=nf:
                        vals=[round(float(x),3) for x in s['ncc']]
                        npth['samples'][key]={'centers':s['centers'].tolist(),
                                             'identity_ncc':vals,'anchor_ncc':vals,
                                             'adaptive_ncc':vals}
                expanded.append(npth)
        if not expanded: fail('FAIL_CLOSED: fixed-candidate DP exhausted; no feasible temporal path')
        expanded.sort(key=lambda p:p['score'],reverse=True)
        next_paths=[]
        for p in expanded:
            if any(_state_distance(p,q)<5.0 for q in next_paths): continue
            next_paths.append(p)
            if len(next_paths)>=args.beam_width: break
        paths=next_paths or expanded[:1]
        diagnostic['last_completed_step']=step; diagnostic['last_native_frame']=native_done
        diagnostic['beam_sizes'].append(len(paths)); diagnostic['best_score']=round(float(paths[0]['score']),4)
        diagnostic['last_centers']=paths[0]['centers'].tolist()

    cap.release()
    evaluated=[]
    for p in paths:
        med=np.asarray([float(np.median(x)) if x else 0.0 for x in p['ncc_history']],float)
        quality=['HIGH' if x>=args.strong_ncc else ('MEDIUM' if x>=args.min_ncc else 'LOW') for x in med]
        accepted=bool(np.all(med>=args.min_ncc) and all(q!='LOW' for q in quality))
        evaluated.append((accepted,p['score'],p,med,quality))
    evaluated.sort(key=lambda z:(z[0],z[1]),reverse=True)
    accepted,_score,best,med,quality=evaluated[0]
    payload={'video':str(args.video),'slit_sec':args.slit_sec,'fps':fps,'stride':args.stride,
             'effective_fps':fps/args.stride,'leakage_guard':'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER',
             'method':'v17 result-blind fixed-candidate fleet DP tracker','tracker_version':'v17',
             'entry_order':entry_order,'dominant_dx':{str(i+1):round(float(dominant_dx[i]),3) for i in range(6)},
             'direction_sign':{str(i+1):int(dir_sign[i]) for i in range(6)},
             'reverse_cap_px':round(float(reverse_cap),3),
             'step_reverse_cap_px_per_native_frame':round(float(step_reverse_cap),3),
             'min_lane_separation_px':None if best['min_sep']==1e9 else round(float(best['min_sep']),3),
             'template_fallbacks':{str(i+1):0 for i in range(6)},
             'fallback_fraction':{str(i+1):0.0 for i in range(6)},
             'median_identity_ncc':{str(i+1):round(float(med[i]),3) for i in range(6)},
             'median_anchor_ncc':{str(i+1):round(float(med[i]),3) for i in range(6)},
             'median_adaptive_ncc':{str(i+1):round(float(med[i]),3) for i in range(6)},
             'quality_tier':{str(i+1):quality[i] for i in range(6)},
             'samples':best['samples'],'diagnostic':diagnostic,'accepted':bool(accepted),
             'tracking_runtime_sec':round(time.perf_counter()-t0,3),
             'v17_changes':{'candidate_generation':'state-independent immutable-anchor lattice per frame',
                            'lane_bands':'immutable seed geometry + elapsed-time expansion only',
                            'temporal_selection':'fixed-candidate fleet DP/beam',
                            'prediction_feedback_in_candidates':False,
                            'fallbacks':'none; missing visual candidate fails closed',
                            'result_blind':True}}
    if not accepted:
        payload['reason']='FAIL_CLOSED: confidence-aware tracking quality insufficient'
    else:
        horizons={}; y0=centers0[:,1]; final_res=None
        for off in OFFSETS[1:]:
            key=f'{off:.1f}'
            if key not in best['samples']:
                payload['accepted']=False; payload['reason']='FAIL_CLOSED: missing required horizon sample'; break
            c=np.asarray(best['samples'][key]['centers'],float); dx=c[:,0]-centers0[:,0]
            rel,trend=base.robust_linear_residual(y0,dx)
            horizons[key]={'dx_px':[round(float(x),3) for x in dx], 'perspective_trend':trend,
                           'relative_forward_px':[round(float(x),3) for x in rel]}
            if off==1.5: final_res=rel
        if payload['accepted']:
            medr=np.median(final_res); mad=np.median(np.abs(final_res-medr)); scale=max(1.0,1.4826*mad)
            ses=np.clip(np.rint((final_res-medr)/scale),-3,3).astype(int)
            order=np.argsort(-final_res); ranks=np.empty(6,int); ranks[order]=np.arange(1,7)
            payload['horizons']=horizons
            payload['boats']={str(i+1):{'relative_forward_1_5px':round(float(final_res[i]),3),
                              'stretch_rank':int(ranks[i]),'ses_v17':int(ses[i]),'quality':quality[i]} for i in range(6)}
            payload['ses_scale_px']=round(float(scale),3)
            payload['warning']='EXPERIMENTAL live score; use only after multi-race blind validation.'
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))
    if not payload['accepted']: raise SystemExit(2)


if __name__=='__main__':
    main()
