#!/usr/bin/env python3
"""v265: compact consensus ensemble audit for 4-head.

Input is ONLY the walk-forward predictions produced by v264.  No Jul/Aug rows are
used.  This is retrospective/model-selection evidence, not pristine validation.
The primary research target remains >=200 selected races with >=40% realized
boat-4 head rate.  We report the best attainable value even when the target is
not reached; no NON-PRISTINE month is used to rescue a rule.
"""
from __future__ import annotations
from pathlib import Path
import itertools
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'analysis_v264_4head_feature_exhaustive.csv'
OUT = ROOT / 'analysis_v265_4head_ensemble_consensus.csv'
SUM = ROOT / 'summary_v265_4head_ensemble_consensus.md'

VARIANTS = [
    'ENV_ENTRY', 'OPP_CONTEXT', 'PLAYER_COURSE', 'ST_3HEAD_ANALOG',
    'ALL_SAFE_HGB', 'ALL_SAFE_LINEAR', 'PRIOR_FOOT',
]
MIN_NS = (100, 150, 200)
PAIR_WEIGHTS = np.round(np.arange(0.0, 1.0001, 0.05), 2)
TRIPLE_WEIGHTS = [
    (round(a, 2), round(b, 2), round(1.0-a-b, 2))
    for a in np.arange(0.0, 1.0001, 0.10)
    for b in np.arange(0.0, 1.0001-a, 0.10)
    if 1.0-a-b >= -1e-9
]


def best_prefix(base: pd.DataFrame, score: np.ndarray, min_n: int):
    q = base[['month', 'date', 'race_code', 'y4']].copy()
    q['score'] = score
    q = q[np.isfinite(q.score)].sort_values(['score', 'race_code'], ascending=[False, True]).reset_index(drop=True)
    if len(q) < min_n:
        return None
    cs = q.y4.cumsum().to_numpy()
    ns = np.arange(1, len(q)+1)
    rate = cs / ns
    # Search score-prefix thresholds with enough volume.  Since scores are
    # continuous, ties are rare; when present, settle the full tied block.
    best = None
    for n in range(min_n, len(q)+1):
        if n < len(q) and q.loc[n-1, 'score'] == q.loc[n, 'score']:
            continue
        z = q.iloc[:n]
        mm = z.groupby('month').y4.agg(['count', 'mean'])
        rec = {
            'R': int(n), 'heads': int(cs[n-1]), 'head_rate': float(rate[n-1]),
            'cut': float(q.loc[n-1, 'score']),
            'monthly_floor': float(mm['mean'].min()),
            'months': int(len(mm)),
            'month_detail': ';'.join(f'{m}:{int(r["count"])}R/{100*r["mean"]:.2f}%' for m, r in mm.iterrows()),
        }
        key = (rec['head_rate'], rec['monthly_floor'], rec['R'])
        if best is None or key > best[0]:
            best = (key, rec)
    return best[1] if best else None


def add_rows(rows, base, name, members, weights, score):
    for min_n in MIN_NS:
        r = best_prefix(base, score, min_n)
        if not r:
            continue
        rows.append({
            'ensemble': name,
            'members': '+'.join(members),
            'weights': '+'.join(f'{x:.2f}' for x in weights),
            'min_n': min_n,
            **r,
            'pass_40': bool(r['head_rate'] >= 0.40),
        })


def main():
    d = pd.read_csv(SRC, dtype={'race_code': str})
    d['race_code'] = d.race_code.astype(str).str.zfill(12)
    d = d[d.month <= '2026-06'].copy()
    # Explicitly reject NON-PRISTINE months even if the upstream file changes.
    d = d[~d.month.isin(['2026-07', '2026-08'])].copy()
    w = d.pivot_table(index=['month', 'date', 'race_code', 'y4'], columns='variant', values='p', aggfunc='last').reset_index()
    common = [v for v in VARIANTS if v in w.columns]
    base = w.dropna(subset=common).copy()
    if len(base) < 200:
        raise RuntimeError(f'need >=200 common v264 OOF rows, got {len(base)}')

    rows = []
    for v in common:
        add_rows(rows, base, f'SINGLE:{v}', [v], [1.0], base[v].to_numpy(float))

    for a, b in itertools.combinations(common, 2):
        for wa in PAIR_WEIGHTS:
            wb = round(1.0-wa, 2)
            if wa == 0 or wb == 0:
                continue
            score = wa*base[a].to_numpy(float) + wb*base[b].to_numpy(float)
            add_rows(rows, base, f'PAIR:{a}+{b}', [a, b], [wa, wb], score)

    for a, b, c in itertools.combinations(common, 3):
        for wa, wb, wc in TRIPLE_WEIGHTS:
            if min(wa, wb, wc) <= 0:
                continue
            score = wa*base[a].to_numpy(float) + wb*base[b].to_numpy(float) + wc*base[c].to_numpy(float)
            add_rows(rows, base, f'TRIPLE:{a}+{b}+{c}', [a, b, c], [wa, wb, wc], score)

    o = pd.DataFrame(rows)
    o = o.sort_values(['min_n', 'pass_40', 'head_rate', 'monthly_floor', 'R'], ascending=[False, False, False, False, False])
    o.to_csv(OUT, index=False)

    months = ', '.join(sorted(base.month.unique()))
    L = [
        '# v265 4-head compact consensus ensemble', '',
        '- Source: v264 walk-forward prediction outputs only.',
        f'- Actual common OOF evaluation months available here: {months}; common races={len(base)}.',
        '- 2026-07/08 are explicitly excluded and cannot affect model selection.',
        '- Pair weights use 0.05 steps; triple weights use 0.10 steps.',
        '- Primary target: >=200 selected races and >=40% realized boat-4 head rate.',
        '- Retrospective/model-selection evidence only; not pristine validation.', '',
    ]
    for mn in (200, 150, 100):
        z = o[o.min_n == mn].sort_values(['pass_40', 'head_rate', 'monthly_floor', 'R'], ascending=[False, False, False, False]).head(20)
        L += [f'## Best rules with at least {mn} races',
              '|members|weights|R|heads|head rate|cut|monthly floor|40% pass|month detail|',
              '|---|---|---:|---:|---:|---:|---:|---|---|']
        for _, r in z.iterrows():
            L.append(f'|{r.members}|{r.weights}|{int(r.R)}|{int(r.heads)}|{100*r.head_rate:.2f}%|{r.cut:.6f}|{100*r.monthly_floor:.2f}%|{"YES" if r.pass_40 else "NO"}|{r.month_detail}|')
        L.append('')
    p200 = o[(o.min_n == 200) & (o.pass_40)]
    L += ['## Decision',
          '- >=200R / >=40% target: ' + ('ACHIEVED in this retrospective search.' if len(p200) else 'NOT achieved; do not weaken the target with Jul/Aug NON-PRISTINE data.'),
          '- Use the strongest simple/robust consensus candidate as the next new-ROI bridge input; do not adopt it as production until frozen and prospectively tested.', '']
    SUM.write_text('\n'.join(L), encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
