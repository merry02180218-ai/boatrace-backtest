#!/usr/bin/env python3
"""Result-blind multi-hypothesis beam fleet tracker for exhibition SES.

v13 is the first tracker in this line that keeps multiple six-boat identity paths
alive across frames instead of committing to one greedy fleet assignment every
frame. It preserves the v9/v11 safety principles: immutable seed-frame appearance,
dynamic lane cells, entry order and spacing checks, fallback/confidence caps,
frame-edge fail-closed behavior, and the result-blind slit-motion direction guard.

Each beam state owns centers, velocity/motion history, fallback counts and adaptive
templates. For every new frame it expands several feasible joint six-boat
assignments, scores them with appearance + LK prediction + recent motion + fleet
geometry, then keeps a small diverse beam. No future frame, race result,
boat-number special case, race-specific offset, or relaxed confidence threshold is
used.
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
from collections import deque
from pathlib import Path

import cv2
import numpy as np

import track_exhibition_boats_v6 as base
import track_exhibition_boats_v9 as v9

OFFSETS = (0.0, 0.5, 1.0, 1.5)


def _clone_state(h):
    return {
        'centers': h['centers'].copy(),
        'velocity': h['velocity'].copy(),
        'score': float(h['score']),
        'fallback': h['fallback'].copy(),
        'identity_hist': [list(x) for x in h['identity_hist']],
        'anchor_hist': [list(x) for x in h['anchor_hist']],
        'adaptive_hist': [list(x) for x in h['adaptive_hist']],
        'step_hist': [deque(list(x), maxlen=4) for x in h['step_hist']],
        'templates': [x.copy() for x in h['templates']],
        'samples': copy.deepcopy(h['samples']),
        'min_sep': float(h['min_sep']),
        'last_joint_score': float(h.get('last_joint_score', 0.0)),
    }


def _state_distance(a, b):
    return float(np.mean(np.linalg.norm(a['centers'] - b['centers'], axis=1)))


def _feasible_combos(cand_lists, centers, preds, cells, fleet, advance, min_ncc,
                     dir_sign, initial_x, reverse_cap, step_reverse_cap,
                     step_hist, initial_order, width, height, per_state_keep):
    """Return top feasible current-frame fleet assignments for one prior beam state."""
    adv = max(1, int(advance))
    ranked = []
    for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
        pts = []
        local_score = 0.0
        step_vecs = []
        frame_id = []
        frame_an = []
        frame_ad = []
        ok = True
        for i, j in enumerate(idxs):
            c, ad, an, is_fb = cand_lists[i][j]
            c = np.asarray(c, dtype=np.float32)
            ylo, yhi = cells[i]
            if not (ylo <= float(c[1]) <= yhi):
                ok = False
                break
            step_vec = c - centers[i]
            if np.linalg.norm(step_vec) > 24.0 * adv:
                ok = False
                break

            sign = float(dir_sign[i])
            if sign != 0.0:
                cumulative = sign * float(c[0] - initial_x[i])
                step_dir = sign * float(step_vec[0])
                if cumulative < -reverse_cap:
                    ok = False
                    break
                if step_dir < -step_reverse_cap * adv:
                    ok = False
                    break

            if not is_fb:
                identity = max(float(ad), float(an))
                if identity < min_ncc:
                    ok = False
                    break
                if abs(float(c[1] - preds[i][1])) > 10.0 * adv:
                    ok = False
                    break
                local_score += 1.8 * float(ad) + 1.8 * float(an) + 0.8 * identity
                local_score -= 0.010 * float(np.linalg.norm(c - preds[i]))
                local_score -= 0.004 * float(np.linalg.norm(step_vec - fleet))
                frame_id.append(identity)
                frame_an.append(float(an))
                frame_ad.append(float(ad))
            else:
                local_score -= 1.25
                frame_id.append(None)
                frame_an.append(None)
                frame_ad.append(None)

            hist = step_hist[i]
            if hist:
                arr = np.asarray(list(hist), dtype=np.float32)
                med = np.median(arr, axis=0)
                local_score -= 0.020 * float(np.linalg.norm(step_vec - med))
                if len(arr) >= 2:
                    local_score -= 0.012 * float(np.linalg.norm(step_vec - arr[-1]))
                    xmed = float(np.median(arr[:, 0]))
                    if abs(xmed) >= 3.0 and np.sign(xmed) * float(step_vec[0]) < -18.0 * adv:
                        ok = False
                        break
            pts.append(c)
            step_vecs.append(step_vec)
        if not ok:
            continue

        P = np.asarray(pts, dtype=np.float32)
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
                    dup = True
                    break
            if dup:
                break
        if dup:
            continue

        # Encourage coherent fleet evolution without forcing identical x motion.
        steps_arr = np.asarray(step_vecs, dtype=np.float32)
        robust_step = np.median(steps_arr, axis=0)
        local_score -= 0.003 * float(np.sum(np.linalg.norm(steps_arr - robust_step, axis=1)))
        ranked.append((local_score, idxs, P, step_vecs, frame_id, frame_an, frame_ad, gaps))

    ranked.sort(key=lambda z: z[0], reverse=True)
    return ranked[:max(1, int(per_state_keep))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--slit-sec', type=float, required=True)
    ap.add_argument('--seed-json', type=Path, required=True)
    ap.add_argument('--seed-meta', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=Path('exhibition_tracking_v13.json'))
    ap.add_argument('--stride', type=int, default=2)
    ap.add_argument('--template-w', type=int, default=54)
    ap.add_argument('--template-h', type=int, default=30)
    ap.add_argument('--min-ncc', type=float, default=.48)
    ap.add_argument('--strong-ncc', type=float, default=.80)
    ap.add_argument('--weak-fallback-frac', type=float, default=.35)
    ap.add_argument('--strong-fallback-frac', type=float, default=.50)
    ap.add_argument('--cell-margin', type=float, default=3.0)
    ap.add_argument('--topk', type=int, default=2)
    ap.add_argument('--beam-width', type=int, default=6)
    ap.add_argument('--per-state-keep', type=int, default=6)
    args = ap.parse_args()
    if args.stride < 1:
        raise SystemExit('--stride must be >=1')

    seed_obj = json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int, seed_obj)) != [1, 2, 3, 4, 5, 6]:
        raise SystemExit('seed-json must contain 1..6')
    meta = json.loads(args.seed_meta.read_text(encoding='utf-8'))
    rows = meta.get('row_details') or {}
    dir_sign = np.zeros(6, dtype=np.float32)
    dominant_dx = np.zeros(6, dtype=np.float32)
    for boat in range(1, 7):
        dx = float((rows.get(str(boat)) or {}).get('dominant_dx') or 0.0)
        dominant_dx[boat - 1] = dx
        if abs(dx) >= 4.0:
            dir_sign[boat - 1] = 1.0 if dx > 0 else -1.0

    centers0 = base.parse_seeds(seed_obj)
    initial_x = centers0[:, 0].copy()
    initial_order = np.argsort(centers0[:, 1])
    entry_order = [int(i + 1) for i in initial_order]

    cap = cv2.VideoCapture(str(args.video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.set(cv2.CAP_PROP_POS_MSEC, args.slit_sec * 1000.0)
    ok, prev = cap.read()
    if not ok:
        raise SystemExit('cannot read slit frame')
    prev_g = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    H, W = prev_g.shape[:2]
    reverse_cap = max(48.0, 0.05 * float(W))
    step_reverse_cap = max(12.0, 0.0125 * float(W))
    if base.dynamic_cells(centers0, initial_order, H, args.cell_margin) is None:
        raise SystemExit('FAIL_CLOSED: invalid initial lane cells')

    anchors = []
    for cx, cy in centers0:
        t = base.crop_center(prev_g, float(cx), float(cy), args.template_w, args.template_h)
        if t is None:
            raise SystemExit('FAIL_CLOSED: cannot initialize boat template')
        anchors.append(t.copy())

    total_native = int(round(1.5 * fps))
    steps = int(np.ceil(total_native / args.stride))
    sample_native = {int(round(o * fps)): o for o in OFFSETS[1:]}
    initial_samples = {'0.0': {'centers': centers0.tolist()}}
    beam = [{
        'centers': centers0.copy(),
        'velocity': np.zeros((6, 2), np.float32),
        'score': 0.0,
        'fallback': np.zeros(6, int),
        'identity_hist': [[] for _ in range(6)],
        'anchor_hist': [[] for _ in range(6)],
        'adaptive_hist': [[] for _ in range(6)],
        'step_hist': [deque(maxlen=4) for _ in range(6)],
        'templates': [x.copy() for x in anchors],
        'samples': initial_samples,
        'min_sep': 1e9,
        'last_joint_score': 0.0,
    }]
    native_done = 0
    diagnostic = {
        'last_completed_step': 0,
        'last_native_frame': 0,
        'beam_width_requested': int(args.beam_width),
        'beam_sizes': [],
        'failure': None,
    }

    def fail(reason):
        diagnostic['failure'] = reason
        best = max(beam, key=lambda h: h['score']) if beam else None
        payload = {
            'video': str(args.video), 'slit_sec': args.slit_sec, 'fps': fps, 'stride': args.stride,
            'method': 'v13 result-blind multi-hypothesis beam fleet tracker',
            'entry_order': entry_order, 'accepted': False, 'reason': reason,
            'diagnostic': diagnostic,
            'dominant_dx': {str(i + 1): round(float(dominant_dx[i]), 3) for i in range(6)},
            'direction_sign': {str(i + 1): int(dir_sign[i]) for i in range(6)},
        }
        if best is not None:
            payload['last_centers'] = best['centers'].tolist()
            payload['template_fallbacks'] = {str(i + 1): int(x) for i, x in enumerate(best['fallback'])}
            payload['samples'] = best['samples']
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    for step in range(1, steps + 1):
        advance = min(args.stride, total_native - native_done)
        if advance <= 0:
            break
        for _ in range(advance - 1):
            if not cap.grab():
                fail('FAIL_CLOSED: video ended during stride grab')
        ok, cur = cap.read()
        if not ok:
            fail('FAIL_CLOSED: video ended during stride read')
        native_done += advance
        cur_g = cv2.cvtColor(cur, cv2.COLOR_BGR2GRAY)

        expanded = []
        for h in beam:
            centers = h['centers']
            cells = base.dynamic_cells(centers, initial_order, H, args.cell_margin)
            if cells is None:
                continue
            lk = []
            ns = []
            spreads = []
            for cx, cy in centers:
                d, n, s = base.local_motion(prev_g, cur_g, float(cx), float(cy), max_mag=24 * advance)
                lk.append(d); ns.append(n); spreads.append(s)
            valid = np.array([d is not None for d in lk])
            if valid.any():
                Dv = np.array([d if d is not None else [np.nan, np.nan] for d in lk], np.float32)
                fleet = np.nanmedian(Dv, axis=0)
            else:
                fleet = np.median(h['velocity'], axis=0)

            preds = []
            cand_lists = []
            for i in range(6):
                ylo, yhi = cells[i]
                d = lk[i]
                if d is not None and np.linalg.norm(d - fleet) <= 24 * advance:
                    pred = centers[i] + d
                elif np.linalg.norm(h['velocity'][i]) > 0:
                    pred = centers[i] + h['velocity'][i]
                else:
                    pred = centers[i] + fleet
                pred = pred.astype(np.float32)
                if float(pred[1]) < ylo or float(pred[1]) > yhi:
                    pred = pred.copy(); pred[1] = np.clip(pred[1], ylo + 1.0, yhi - 1.0)
                preds.append(pred)
                opts = []
                for est, ad, an, _src in v9.dual_candidates(
                        cur_g, h['templates'][i], anchors[i], pred, ylo, yhi,
                        34 * advance, 10 * advance, args.topk):
                    opts.append((est, float(ad), float(an), False))
                opts.append((pred.astype(np.float32), None, None, True))
                cand_lists.append(opts)
            preds = np.asarray(preds, np.float32)
            trans = _feasible_combos(
                cand_lists, centers, preds, cells, np.asarray(fleet, np.float32), advance,
                args.min_ncc, dir_sign, initial_x, reverse_cap, step_reverse_cap,
                h['step_hist'], initial_order, W, H, args.per_state_keep)

            for local_score, idxs, P, step_vecs, frame_id, frame_an, frame_ad, gaps in trans:
                nh = _clone_state(h)
                nh['score'] += float(local_score)
                nh['last_joint_score'] = float(local_score)
                old_centers = nh['centers'].copy()
                nh['centers'] = P.copy()
                velocities = P - old_centers
                nh['velocity'] = .65 * nh['velocity'] + .35 * velocities
                nh['min_sep'] = min(nh['min_sep'], float(np.min(gaps)))
                for i, j in enumerate(idxs):
                    est, ad, an, is_fb = cand_lists[i][j]
                    nh['step_hist'][i].append(np.asarray(step_vecs[i], np.float32))
                    if is_fb:
                        nh['fallback'][i] += 1
                    else:
                        identity = max(float(ad), float(an))
                        nh['identity_hist'][i].append(identity)
                        nh['anchor_hist'][i].append(float(an))
                        nh['adaptive_hist'][i].append(float(ad))
                        if ad >= .72 and an >= .55:
                            nt = base.crop_center(cur_g, float(est[0]), float(est[1]), args.template_w, args.template_h)
                            if nt is not None and nt.shape == nh['templates'][i].shape:
                                nh['templates'][i] = cv2.addWeighted(nh['templates'][i], .90, nt, .10, 0)
                for nf, off in sample_native.items():
                    key = f'{off:.1f}'
                    if key not in nh['samples'] and native_done >= nf:
                        nh['samples'][key] = {
                            'centers': P.tolist(), 'features': ns, 'spread': spreads,
                            'identity_ncc': [None if x is None else round(float(x), 3) for x in frame_id],
                            'anchor_ncc': [None if x is None else round(float(x), 3) for x in frame_an],
                            'adaptive_ncc': [None if x is None else round(float(x), 3) for x in frame_ad],
                        }
                expanded.append(nh)

        if not expanded:
            fail('FAIL_CLOSED: beam exhausted; no feasible multi-frame fleet hypothesis')

        expanded.sort(key=lambda h: h['score'], reverse=True)
        next_beam = []
        for h in expanded:
            # Keep genuinely different fleet paths; near-identical hypotheses add no recovery value.
            if any(_state_distance(h, k) < 5.0 for k in next_beam):
                continue
            next_beam.append(h)
            if len(next_beam) >= args.beam_width:
                break
        if not next_beam:
            next_beam = expanded[:1]
        beam = next_beam
        diagnostic['last_completed_step'] = step
        diagnostic['last_native_frame'] = native_done
        diagnostic['beam_sizes'].append(len(beam))
        diagnostic['best_score'] = round(float(beam[0]['score']), 4)
        diagnostic['last_centers'] = beam[0]['centers'].tolist()
        prev_g = cur_g

    cap.release()

    # Prefer the highest-scoring path that passes the unchanged confidence gate.
    evaluated = []
    for h in beam:
        med_id = np.array([float(np.median(x)) if x else 0.0 for x in h['identity_hist']])
        med_an = np.array([float(np.median(x)) if x else 0.0 for x in h['anchor_hist']])
        med_ad = np.array([float(np.median(x)) if x else 0.0 for x in h['adaptive_hist']])
        fb_frac = h['fallback'] / max(1, steps)
        quality = []
        okboats = []
        for i in range(6):
            strong = med_id[i] >= args.strong_ncc
            lim = args.strong_fallback_frac if strong else args.weak_fallback_frac
            okb = bool(med_id[i] >= args.min_ncc and fb_frac[i] <= lim)
            okboats.append(okb)
            quality.append('HIGH' if strong and fb_frac[i] <= args.weak_fallback_frac else ('MEDIUM' if okb else 'LOW'))
        accepted = bool(all(okboats) and all(q != 'LOW' for q in quality))
        evaluated.append((accepted, h['score'], h, med_id, med_an, med_ad, fb_frac, quality))
    evaluated.sort(key=lambda z: (z[0], z[1]), reverse=True)
    accepted, _, best, med_id, med_an, med_ad, fb_frac, quality = evaluated[0]

    payload = {
        'video': str(args.video), 'slit_sec': args.slit_sec, 'fps': fps, 'stride': args.stride,
        'effective_fps': fps / args.stride,
        'leakage_guard': 'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER',
        'method': 'v13 result-blind multi-hypothesis beam fleet tracker',
        'beam': {'width': int(args.beam_width), 'per_state_keep': int(args.per_state_keep),
                 'final_hypotheses': len(beam), 'beam_sizes': diagnostic['beam_sizes']},
        'entry_order': entry_order,
        'dominant_dx': {str(i + 1): round(float(dominant_dx[i]), 3) for i in range(6)},
        'direction_sign': {str(i + 1): int(dir_sign[i]) for i in range(6)},
        'reverse_cap_px': round(float(reverse_cap), 3),
        'step_reverse_cap_px_per_native_frame': round(float(step_reverse_cap), 3),
        'min_lane_separation_px': None if best['min_sep'] == 1e9 else round(float(best['min_sep']), 3),
        'template_fallbacks': {str(i + 1): int(x) for i, x in enumerate(best['fallback'])},
        'fallback_fraction': {str(i + 1): round(float(x), 3) for i, x in enumerate(fb_frac)},
        'median_identity_ncc': {str(i + 1): round(float(x), 3) for i, x in enumerate(med_id)},
        'median_anchor_ncc': {str(i + 1): round(float(x), 3) for i, x in enumerate(med_an)},
        'median_adaptive_ncc': {str(i + 1): round(float(x), 3) for i, x in enumerate(med_ad)},
        'quality_tier': {str(i + 1): quality[i] for i in range(6)},
        'samples': best['samples'], 'diagnostic': diagnostic, 'accepted': bool(accepted),
    }
    if not accepted:
        payload['reason'] = 'FAIL_CLOSED: confidence-aware tracking quality insufficient'
    else:
        horizons = {}; y0 = centers0[:, 1]; final_res = None
        for off in OFFSETS[1:]:
            key = f'{off:.1f}'
            if key not in best['samples']:
                payload['accepted'] = False
                payload['reason'] = 'FAIL_CLOSED: missing required horizon sample'
                break
            c = np.array(best['samples'][key]['centers'], float)
            dx = c[:, 0] - centers0[:, 0]
            rel, trend = base.robust_linear_residual(y0, dx)
            horizons[key] = {'dx_px': [round(float(x), 3) for x in dx], 'perspective_trend': trend,
                             'relative_forward_px': [round(float(x), 3) for x in rel]}
            if off == 1.5:
                final_res = rel
        if payload['accepted']:
            med = np.median(final_res); mad = np.median(np.abs(final_res - med)); scale = max(1.0, 1.4826 * mad)
            ses = np.clip(np.rint((final_res - med) / scale), -3, 3).astype(int)
            order = np.argsort(-final_res); ranks = np.empty(6, int); ranks[order] = np.arange(1, 7)
            payload['horizons'] = horizons
            payload['boats'] = {str(i + 1): {'relative_forward_1_5px': round(float(final_res[i]), 3),
                'stretch_rank': int(ranks[i]), 'ses_v13': int(ses[i]), 'quality': quality[i]} for i in range(6)}
            payload['ses_scale_px'] = round(float(scale), 3)
            payload['warning'] = 'EXPERIMENTAL live score; use only after multi-race blind validation.'

    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload['accepted']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
