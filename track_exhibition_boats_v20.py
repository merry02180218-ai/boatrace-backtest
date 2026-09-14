#!/usr/bin/env python3
"""Result-blind predecessor beam with gated causal appearance rescue.

v19 kept a healthy predecessor-conditioned beam until a frame where every
predecessor produced zero feasible expansion.  v20 keeps the v19 immutable
anchor search and all v17 safety/final gates unchanged, but adds a *rescue-only*
proposal source when a predecessor has no standard expansion:

- each path carries one causal appearance template per boat;
- that template is updated only after a selected candidate has strong
  (>= strong_ncc) agreement with the immutable slit anchor;
- rescue searches the causal template only inside the predecessor-reachable
  window;
- every rescue proposal is re-checked at the exact center against the immutable
  slit anchor and must still satisfy min_ncc; therefore the .48 identity gate is
  not relaxed;
- adaptive appearance proposes locations only.  Fleet safety, temporal motion,
  reverse corridor, geometry/order, edge, duplicate and final confidence gates
  remain unchanged.

No future frame, race result, boat-number rule or race-specific offset is used.
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
import track_exhibition_boats_v19 as v19

OFFSETS = (0.0, 0.5, 1.0, 1.5)


def _ncc_same_size(a, b):
    if a is None or b is None or a.shape != b.shape:
        return -1.0
    r = cv2.matchTemplate(a, b, cv2.TM_CCOEFF_NORMED)
    v = float(r[0, 0])
    return v if np.isfinite(v) else -1.0


def _patch_at(cur_g, center, tw, th):
    return base.crop_center(cur_g, float(center[0]), float(center[1]), tw, th)


def _adaptive_local_candidates(cur_g, template, immutable_anchor, ylo, yhi,
                               prev_center, radius, topk, min_ncc):
    """Fast ROI-local causal-template proposals, immutable-anchor verified."""
    th, tw = template.shape[:2]
    px, py = map(float, prev_center)
    x0 = max(0, int(np.floor(px - radius - tw)))
    x1 = min(cur_g.shape[1], int(np.ceil(px + radius + tw)))
    y0 = max(0, int(np.floor(max(float(ylo), py - radius) - th)))
    y1 = min(cur_g.shape[0], int(np.ceil(min(float(yhi), py + radius) + th)))
    roi = cur_g[y0:y1, x0:x1]
    if roi.shape[0] < th or roi.shape[1] < tw:
        return []
    resp = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
    work = resp.copy()
    out = []
    nms_x = max(12, tw // 2)
    nms_y = max(8, th // 2)
    for _ in range(max(8, int(topk) * 4)):
        _mn, ad_score, _mnl, loc = cv2.minMaxLoc(work)
        if not np.isfinite(ad_score) or float(ad_score) < float(min_ncc):
            break
        c = np.asarray([x0 + loc[0] + tw / 2.0,
                        y0 + loc[1] + th / 2.0], np.float32)
        # Exact predecessor reachability and lane-band checks.
        if (float(np.linalg.norm(c - np.asarray(prev_center))) <= float(radius)
                and float(ylo) <= float(c[1]) <= float(yhi)):
            patch = _patch_at(cur_g, c, tw, th)
            imm = _ncc_same_size(patch, immutable_anchor)
            # Critical: rescue never bypasses the immutable .48 identity gate.
            if imm >= float(min_ncc):
                out.append((c, float(imm), float(ad_score)))
        yy0 = max(0, loc[1] - nms_y); yy1 = min(work.shape[0], loc[1] + nms_y + 1)
        xx0 = max(0, loc[0] - nms_x); xx1 = min(work.shape[1], loc[0] + nms_x + 1)
        work[yy0:yy1, xx0:xx1] = -2.0
        if len(out) >= int(topk):
            break
    return out


def _merge_v20(global_opts, local_opts, adaptive_opts, prev_center, advance,
               keep=5):
    """Merge proposal sources while retaining immutable NCC as identity score."""
    radius = 24.0 * max(1, int(advance))
    pool = []
    # immutable candidates: adaptive score equals immutable score
    raw = [(c, s, s, 'immutable') for c, s in list(local_opts) + list(global_opts)]
    raw += [(c, imm, ad, 'causal') for c, imm, ad in adaptive_opts]
    raw.sort(key=lambda z: (0.72 * float(z[1]) + 0.28 * float(z[2])), reverse=True)
    for c, imm, ad, source in raw:
        c = np.asarray(c, np.float32)
        if float(np.linalg.norm(c - np.asarray(prev_center))) > radius:
            continue
        if any(np.linalg.norm(c - q[0]) < 8.0 for q in pool):
            continue
        pool.append((c, float(imm), float(ad), source))
        if len(pool) >= max(1, int(keep)):
            break
    return pool


def _expand_predecessor(p, cand_lists, initial_order, initial_x, dir_sign,
                        reverse_cap, W, H, advance, step_reverse_cap,
                        per_path_keep):
    local_exp = []
    for idxs in itertools.product(*[range(len(x)) for x in cand_lists]):
        P = np.asarray([cand_lists[i][j][0] for i, j in enumerate(idxs)], np.float32)
        imm_scores = np.asarray([cand_lists[i][j][1] for i, j in enumerate(idxs)], float)
        adaptive_scores = np.asarray([cand_lists[i][j][2] for i, j in enumerate(idxs)], float)
        sources = [cand_lists[i][j][3] for i, j in enumerate(idxs)]
        s = v19._safe_state(P, imm_scores, initial_order, initial_x, dir_sign,
                            reverse_cap, W, H)
        if s is None:
            continue
        tr = v17._transition(p, s, advance, dir_sign, initial_x, reverse_cap,
                             step_reverse_cap, initial_order)
        if tr is None:
            continue
        tr_score, step_vec = tr
        # Tiny tie-break only: causal proposals do not replace immutable NCC score.
        tr_score += 0.035 * float(np.sum(np.maximum(0.0, adaptive_scores - imm_scores)))
        local_exp.append((float(tr_score), s, step_vec, adaptive_scores, sources))
    local_exp.sort(key=lambda z: z[0], reverse=True)
    return local_exp[:max(1, int(per_path_keep))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--slit-sec', type=float, required=True)
    ap.add_argument('--seed-json', type=Path, required=True)
    ap.add_argument('--seed-meta', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=Path('exhibition_tracking_v20.json'))
    ap.add_argument('--stride', type=int, default=2)
    ap.add_argument('--template-w', type=int, default=54)
    ap.add_argument('--template-h', type=int, default=30)
    ap.add_argument('--min-ncc', type=float, default=.48)
    ap.add_argument('--strong-ncc', type=float, default=.80)
    ap.add_argument('--topk', type=int, default=6)
    ap.add_argument('--per-boat-keep', type=int, default=5)
    ap.add_argument('--per-path-keep', type=int, default=12)
    ap.add_argument('--beam-width', type=int, default=24)
    args = ap.parse_args()
    if args.stride < 1:
        raise SystemExit('--stride must be >=1')
    t0 = time.perf_counter()

    seed_obj = json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int, seed_obj)) != [1, 2, 3, 4, 5, 6]:
        raise SystemExit('seed-json must contain 1..6')
    meta = json.loads(args.seed_meta.read_text(encoding='utf-8'))
    rows = meta.get('row_details') or {}
    dominant_dx = np.zeros(6, np.float32)
    dir_sign = np.zeros(6, np.float32)
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
    ok, slit = cap.read()
    if not ok:
        raise SystemExit('cannot read slit frame')
    slit_g = cv2.cvtColor(slit, cv2.COLOR_BGR2GRAY)
    H, W = slit_g.shape[:2]
    reverse_cap = max(48.0, 0.05 * float(W))
    step_reverse_cap = max(12.0, 0.0125 * float(W))
    anchors = []
    for cx, cy in centers0:
        a = base.crop_center(slit_g, float(cx), float(cy), args.template_w, args.template_h)
        if a is None:
            raise SystemExit('FAIL_CLOSED: cannot initialize boat template')
        anchors.append(a.copy())

    total_native = int(round(1.5 * fps))
    steps = int(np.ceil(total_native / args.stride))
    sample_native = {int(round(o * fps)): o for o in OFFSETS[1:]}
    diagnostic = {'last_completed_step': 0, 'last_native_frame': 0,
                  'predecessor_counts': [], 'expanded_counts': [], 'beam_sizes': [],
                  'rescue_attempts': [], 'rescue_predecessors_with_expansion': [],
                  'adaptive_proposals': [], 'failure': None}
    samples = {'0.0': {'centers': centers0.tolist()}}
    paths = [{'centers': centers0.copy(), 'score': 0.0, 'last_step': None,
              'history': [], 'ncc_history': [[] for _ in range(6)],
              'min_sep': 1e9, 'samples': dict(samples),
              'templates': [a.copy() for a in anchors]}]
    native_done = 0

    def fail(reason):
        diagnostic['failure'] = reason
        best = max(paths, key=lambda p: p['score']) if paths else None
        payload = {'video': str(args.video), 'slit_sec': args.slit_sec, 'fps': fps,
                   'stride': args.stride,
                   'method': 'v20 result-blind gated causal-appearance rescue beam tracker',
                   'entry_order': entry_order, 'accepted': False, 'reason': reason,
                   'diagnostic': diagnostic,
                   'dominant_dx': {str(i + 1): round(float(dominant_dx[i]), 3) for i in range(6)},
                   'direction_sign': {str(i + 1): int(dir_sign[i]) for i in range(6)},
                   'tracking_runtime_sec': round(time.perf_counter() - t0, 3),
                   'tracker_version': 'v20'}
        if best is not None:
            payload['last_centers'] = best['centers'].tolist()
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
        elapsed = native_done / fps
        cur_g = cv2.cvtColor(cur, cv2.COLOR_BGR2GRAY)
        cells = v17._fixed_seed_cells(centers0, initial_order, H, elapsed)
        if cells is None:
            fail('FAIL_CLOSED: invalid immutable seed lane bands')

        global_lists = []
        for i in range(6):
            ylo, yhi = cells[i]
            opts = v17._anchor_candidates(cur_g, anchors[i], ylo, yhi,
                                          args.topk, args.min_ncc)
            if not opts:
                fail(f'FAIL_CLOSED: no immutable-anchor candidate for boat {i + 1}')
            global_lists.append(opts)

        expanded = []
        pred_with_expansion = 0
        rescue_attempts = 0
        rescue_success = 0
        adaptive_count = 0
        for p in paths:
            standard_lists = []
            viable = True
            for i in range(6):
                ylo, yhi = cells[i]
                radius = 24.0 * max(1, int(advance))
                local = v19._local_anchor_candidates(cur_g, anchors[i], ylo, yhi,
                                                     p['centers'][i], radius,
                                                     args.topk, args.min_ncc)
                merged = _merge_v20(global_lists[i], local, [], p['centers'][i],
                                    advance, args.per_boat_keep)
                if not merged:
                    viable = False
                    break
                standard_lists.append(merged)
            local_exp = []
            if viable:
                local_exp = _expand_predecessor(
                    p, standard_lists, initial_order, initial_x, dir_sign,
                    reverse_cap, W, H, advance, step_reverse_cap, args.per_path_keep)

            # Rescue only when unchanged v19-style expansion is exhausted.
            if not local_exp:
                rescue_attempts += 1
                rescue_lists = []
                viable = True
                for i in range(6):
                    ylo, yhi = cells[i]
                    radius = 24.0 * max(1, int(advance))
                    local = v19._local_anchor_candidates(cur_g, anchors[i], ylo, yhi,
                                                         p['centers'][i], radius,
                                                         args.topk, args.min_ncc)
                    adaptive = _adaptive_local_candidates(
                        cur_g, p['templates'][i], anchors[i], ylo, yhi,
                        p['centers'][i], radius, args.topk, args.min_ncc)
                    adaptive_count += len(adaptive)
                    merged = _merge_v20(global_lists[i], local, adaptive,
                                        p['centers'][i], advance,
                                        args.per_boat_keep)
                    if not merged:
                        viable = False
                        break
                    rescue_lists.append(merged)
                if viable:
                    local_exp = _expand_predecessor(
                        p, rescue_lists, initial_order, initial_x, dir_sign,
                        reverse_cap, W, H, advance, step_reverse_cap,
                        args.per_path_keep)
                if local_exp:
                    rescue_success += 1

            if not local_exp:
                continue
            pred_with_expansion += 1
            for tr_score, s, step_vec, adaptive_scores, sources in local_exp:
                npth = {'centers': s['centers'].copy(),
                        'score': float(p['score']) + tr_score,
                        'last_step': step_vec.copy(),
                        'history': p['history'] + [s['centers'].copy()],
                        'ncc_history': [list(x) for x in p['ncc_history']],
                        'min_sep': min(float(p['min_sep']), float(s['min_sep'])),
                        'samples': json.loads(json.dumps(p['samples'])),
                        'templates': [x.copy() for x in p['templates']]}
                for i in range(6):
                    imm = float(s['ncc'][i])
                    npth['ncc_history'][i].append(imm)
                    # Causal update is allowed only under strong immutable agreement.
                    if imm >= float(args.strong_ncc):
                        patch = _patch_at(cur_g, s['centers'][i],
                                          args.template_w, args.template_h)
                        if patch is not None and patch.shape == npth['templates'][i].shape:
                            npth['templates'][i] = cv2.addWeighted(
                                npth['templates'][i], 0.70, patch, 0.30, 0.0)
                for nf, off in sample_native.items():
                    key = f'{off:.1f}'
                    if key not in npth['samples'] and native_done >= nf:
                        vals = [round(float(x), 3) for x in s['ncc']]
                        npth['samples'][key] = {
                            'centers': s['centers'].tolist(),
                            'identity_ncc': vals, 'anchor_ncc': vals,
                            'adaptive_ncc': [round(float(x), 3) for x in adaptive_scores],
                            'proposal_source': sources}
                expanded.append(npth)

        diagnostic['predecessor_counts'].append(pred_with_expansion)
        diagnostic['expanded_counts'].append(len(expanded))
        diagnostic['rescue_attempts'].append(rescue_attempts)
        diagnostic['rescue_predecessors_with_expansion'].append(rescue_success)
        diagnostic['adaptive_proposals'].append(adaptive_count)
        if not expanded:
            fail('FAIL_CLOSED: gated causal-appearance beam exhausted; no feasible temporal expansion')
        expanded.sort(key=lambda p: p['score'], reverse=True)
        next_paths = []
        for p in expanded:
            if any(v19._identity_distance(p, q) < 5.0 for q in next_paths):
                continue
            next_paths.append(p)
            if len(next_paths) >= args.beam_width:
                break
        paths = next_paths or expanded[:1]
        diagnostic['last_completed_step'] = step
        diagnostic['last_native_frame'] = native_done
        diagnostic['beam_sizes'].append(len(paths))
        diagnostic['best_score'] = round(float(paths[0]['score']), 4)
        diagnostic['last_centers'] = paths[0]['centers'].tolist()

    cap.release()
    evaluated = []
    for p in paths:
        med = np.asarray([float(np.median(x)) if x else 0.0
                          for x in p['ncc_history']], float)
        quality = ['HIGH' if x >= args.strong_ncc else
                   ('MEDIUM' if x >= args.min_ncc else 'LOW') for x in med]
        accepted = bool(np.all(med >= args.min_ncc) and all(q != 'LOW' for q in quality))
        evaluated.append((accepted, p['score'], p, med, quality))
    evaluated.sort(key=lambda z: (z[0], z[1]), reverse=True)
    accepted, _score, best, med, quality = evaluated[0]
    payload = {
        'video': str(args.video), 'slit_sec': args.slit_sec, 'fps': fps,
        'stride': args.stride, 'effective_fps': fps / args.stride,
        'leakage_guard': 'PRE_RACE_VIDEO_ONLY; JOIN_RESULTS_LATER',
        'method': 'v20 result-blind gated causal-appearance rescue beam tracker',
        'tracker_version': 'v20', 'entry_order': entry_order,
        'dominant_dx': {str(i + 1): round(float(dominant_dx[i]), 3) for i in range(6)},
        'direction_sign': {str(i + 1): int(dir_sign[i]) for i in range(6)},
        'reverse_cap_px': round(float(reverse_cap), 3),
        'step_reverse_cap_px_per_native_frame': round(float(step_reverse_cap), 3),
        'min_lane_separation_px': None if best['min_sep'] == 1e9 else round(float(best['min_sep']), 3),
        'template_fallbacks': {str(i + 1): 0 for i in range(6)},
        'fallback_fraction': {str(i + 1): 0.0 for i in range(6)},
        'median_identity_ncc': {str(i + 1): round(float(med[i]), 3) for i in range(6)},
        'median_anchor_ncc': {str(i + 1): round(float(med[i]), 3) for i in range(6)},
        'quality_tier': {str(i + 1): quality[i] for i in range(6)},
        'samples': best['samples'], 'diagnostic': diagnostic,
        'accepted': bool(accepted),
        'tracking_runtime_sec': round(time.perf_counter() - t0, 3),
        'v20_changes': {
            'standard_path': 'unchanged v19 immutable predecessor-conditioned search',
            'rescue': 'causal appearance ROI proposals only after standard predecessor expansion is empty',
            'immutable_rescue_gate': float(args.min_ncc),
            'template_update_gate': float(args.strong_ncc),
            'future_frame_feedback': False,
            'quality_thresholds_relaxed': False,
            'result_blind': True}}
    if not accepted:
        payload['reason'] = 'FAIL_CLOSED: confidence-aware tracking quality insufficient'
    else:
        horizons = {}
        y0 = centers0[:, 1]
        final_res = None
        for off in OFFSETS[1:]:
            key = f'{off:.1f}'
            if key not in best['samples']:
                payload['accepted'] = False
                payload['reason'] = 'FAIL_CLOSED: missing required horizon sample'
                break
            c = np.asarray(best['samples'][key]['centers'], float)
            dx = c[:, 0] - centers0[:, 0]
            rel, trend = base.robust_linear_residual(y0, dx)
            horizons[key] = {'dx_px': [round(float(x), 3) for x in dx],
                             'perspective_trend': trend,
                             'relative_forward_px': [round(float(x), 3) for x in rel]}
            if off == 1.5:
                final_res = rel
        if payload['accepted']:
            medr = np.median(final_res)
            mad = np.median(np.abs(final_res - medr))
            scale = max(1.0, 1.4826 * mad)
            ses = np.clip(np.rint((final_res - medr) / scale), -3, 3).astype(int)
            order = np.argsort(-final_res)
            ranks = np.empty(6, int); ranks[order] = np.arange(1, 7)
            payload['horizons'] = horizons
            payload['boats'] = {str(i + 1): {
                'relative_forward_1_5px': round(float(final_res[i]), 3),
                'stretch_rank': int(ranks[i]), 'ses_v20': int(ses[i]),
                'quality': quality[i]} for i in range(6)}
            payload['ses_scale_px'] = round(float(scale), 3)
            payload['warning'] = 'EXPERIMENTAL live score; use only after multi-race blind validation.'
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload['accepted']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
