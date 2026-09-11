#!/usr/bin/env python3
"""Result-blind calibration helper for boat-1 seed localization.

Starting from an existing six-boat seed JSON, vary only boat 1 around its base
position, run tracker v5, and rank candidates only by tracking quality.
No race-result endpoint is accessed.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path


def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr


def parse_vals(s):
    return [float(x) for x in s.split(',') if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video', type=Path)
    ap.add_argument('--slit-sec', type=float, required=True)
    ap.add_argument('--seed-json', type=Path, required=True)
    ap.add_argument('--x-offsets', default='-180,-150,-120,-90,-60,-30,0,30,60,90,120,150,180')
    ap.add_argument('--y-offsets', default='-18,0,18')
    ap.add_argument('--out', type=Path, default=Path('boat1_seed_sweep_v1.json'))
    args = ap.parse_args()

    root = Path(__file__).resolve().parent
    base = json.loads(args.seed_json.read_text(encoding='utf-8'))
    if sorted(map(int, base)) != [1,2,3,4,5,6]:
        raise SystemExit('seed-json must contain boats 1..6')
    bx, by = map(float, base['1'][:2])
    rows = []

    for dx in parse_vals(args.x_offsets):
        for dy in parse_vals(args.y_offsets):
            seeds = json.loads(json.dumps(base))
            seeds['1'] = [bx + dx, by + dy]
            tag = f"x{int(dx):+d}_y{int(dy):+d}".replace('+','p').replace('-','m')
            sj = Path(f'_b1_seed_{tag}.json')
            tj = Path(f'_b1_track_{tag}.json')
            sj.write_text(json.dumps(seeds, indent=2) + '\n', encoding='utf-8')
            rc, so, se = run([
                sys.executable, str(root / 'track_exhibition_boats_v5.py'), str(args.video),
                '--slit-sec', str(args.slit_sec), '--seed-json', str(sj),
                '--out', str(tj), '--stride', '2'
            ])
            rec = {'dx':dx,'dy':dy,'seed':[round(bx+dx,2),round(by+dy,2)],
                   'process_ok':rc==0,'result_blind':True,'race_results_read':False}
            if tj.exists():
                tr = json.loads(tj.read_text(encoding='utf-8'))
                q = tr.get('quality_tier',{})
                fb = tr.get('fallback_fraction',{})
                ncc = tr.get('median_template_ncc',{})
                rec.update({
                    'accepted': bool(tr.get('accepted')),
                    'boat1_quality': q.get('1'),
                    'boat1_fallback': fb.get('1'),
                    'boat1_ncc': ncc.get('1'),
                    'low_count': sum(v=='LOW' for v in q.values()),
                    'fallback_sum': round(sum(float(v) for v in fb.values()),3),
                })
            else:
                rec['error'] = (se or so).strip()[-400:]
            rows.append(rec)

    viable = [r for r in rows if 'boat1_fallback' in r]
    best = None
    if viable:
        best = min(viable, key=lambda r:(
            0 if r.get('accepted') else 1,
            r.get('low_count',99),
            float(r.get('boat1_fallback',9)),
            -float(r.get('boat1_ncc',0)),
            abs(r['dx']) + 0.5*abs(r['dy'])
        ))
    payload = {
        'result_blind':True,
        'race_results_read':False,
        'method':'boat1-only x/y seed offset sweep + tracker v5 quality ranking',
        'slit_sec':args.slit_sec,
        'base_boat1_seed':[bx,by],
        'candidate_count':len(rows),
        'best_tracking_quality_candidate':best,
        'candidates':rows,
        'warning':'Calibration helper only; ranking uses tracking quality, never race result.'
    }
    args.out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
