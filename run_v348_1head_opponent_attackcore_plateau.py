#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v347_1head_opponent_attackcore as v347

OUT = Path('/tmp/v348')
OUT.mkdir(parents=True, exist_ok=True)
G2 = (0.25, 0.50, 0.75)
G3 = (0.75, 1.00, 1.25)
DEV_MONTHS = v347.DEV_MONTHS
SUPPORT_MONTHS = v347.SUPPORT_MONTHS


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')

    sel, pre_R = v347.current_selected()
    ids = set(sel.race_code.astype(str).str.zfill(12))
    p2dev, pcdev, p2ja, pcja = v347.opponent_maps()
    cores = v347.build_opponent_attackcore(ids)

    base_z, base, base_mon = v347.evaluate(sel, cores, p2dev, pcdev, p2ja, pcja, 0.0, 0.0)
    if (int(base['R']), int(base['head']), int(base['hits'])) != (276, 241, 121):
        raise AssertionError(f'baseline drift: {base}')

    rows = []
    monthly = []
    race_frames = []
    for g2 in G2:
        for g3 in G3:
            z, m, mon = v347.evaluate(sel, cores, p2dev, pcdev, p2ja, pcja, g2, g3)
            m['delta_hits'] = int(m['hits']) - int(base['hits'])
            m['delta_dev_hits'] = int(m['dev_hits']) - int(base['dev_hits'])
            m['delta_support_hits'] = int(m['support_hits']) - int(base['support_hits'])
            rows.append(m)
            mon['g2'] = g2
            mon['g3'] = g3
            monthly.append(mon)
            z['g2'] = g2
            z['g3'] = g3
            race_frames.append(z)

    grid = pd.DataFrame(rows).sort_values(['g2','g3']).reset_index(drop=True)
    monthly = pd.concat(monthly, ignore_index=True)
    races = pd.concat(race_frames, ignore_index=True)

    # Plateau diagnostics: central candidate and its eight immediate neighbors.
    center = grid[np.isclose(grid.g2, 0.5) & np.isclose(grid.g3, 1.0)].iloc[0]
    dev_ge_center_minus1 = int((grid.dev_hits >= int(center.dev_hits) - 1).sum())
    dev_positive = int((grid.delta_dev_hits > 0).sum())
    all_positive = int((grid.delta_hits > 0).sum())
    min_dev_delta = int(grid.delta_dev_hits.min())
    max_dev_delta = int(grid.delta_dev_hits.max())
    min_worst = float(grid.dev_worst_month.min())
    center_worst = float(center.dev_worst_month)

    # Robust ranking uses Feb-Jun only: dev_hits, then worst-month. Support is descriptive only.
    ranked = grid.sort_values(['dev_hits','dev_worst_month','support_hits','hits'], ascending=False).reset_index(drop=True)
    best = ranked.iloc[0]

    # Compare center to baseline at race level for stability details.
    cz = races[np.isclose(races.g2, 0.5) & np.isclose(races.g3, 1.0)].copy()
    cmp = base_z[['month','race_code','hit','tickets']].rename(columns={'hit':'base_hit','tickets':'base_tickets'}).merge(
        cz[['race_code','hit','tickets']].rename(columns={'hit':'center_hit','tickets':'center_tickets'}), on='race_code'
    )
    cmp['delta'] = cmp.center_hit - cmp.base_hit

    grid.to_csv(OUT/'v348_plateau_grid.csv', index=False)
    monthly.to_csv(OUT/'v348_plateau_monthly.csv', index=False)
    cmp.to_csv(OUT/'v348_center_race_delta.csv', index=False)

    result = {
        'profile': prod.PROFILE_NAME,
        'pre_R': pre_R,
        'pass_R': len(sel),
        'head': int(sel.head_hit.sum()),
        'baseline': base,
        'center_g2': 0.5,
        'center_g3': 1.0,
        'center': center.to_dict(),
        'best_neighborhood': best.to_dict(),
        'plateau': {
            'points': 9,
            'dev_positive_points': dev_positive,
            'all_positive_points': all_positive,
            'dev_within_1_hit_of_center_points': dev_ge_center_minus1,
            'min_dev_delta_hits': min_dev_delta,
            'max_dev_delta_hits': max_dev_delta,
            'min_dev_worst_month': min_worst,
            'center_dev_worst_month': center_worst,
        },
        'center_gain_R': int((cmp.delta == 1).sum()),
        'center_loss_R': int((cmp.delta == -1).sum()),
        'SEPTEMBER_OUTCOMES_READ': False,
        'JUL_AUG_STATUS': 'NON_PRISTINE_SUPPORT_ONLY',
        'PRODUCTION_CHANGED': False,
    }
    (OUT/'result_v348.json').write_text(json.dumps(result, indent=2, default=float), encoding='utf-8')

    lines = [
        '# v348 opponent attackCore local plateau audit', '',
        '- Production remains unchanged during this audit.',
        '- September outcomes remain unread; Jul/Aug are support-only.',
        f"- Baseline: {int(base['hits'])}/{int(base['R'])} all; Feb-Jun {int(base['dev_hits'])}/{int(base['dev_R'])}.",
        f"- Center g2=.50/g3=1.00: {int(center.hits)}/{int(center.R)} all; Feb-Jun {int(center.dev_hits)}/{int(center.dev_R)}; worst-month {100*center.dev_worst_month:.2f}%.",
        f"- Neighborhood best by pristine criterion: g2={best.g2:.2f}, g3={best.g3:.2f}, Feb-Jun {int(best.dev_hits)}/{int(best.dev_R)}, worst-month {100*best.dev_worst_month:.2f}%.",
        f"- Positive Feb-Jun improvement points: {dev_positive}/9; positive all-period improvement points: {all_positive}/9.",
        f"- Points within 1 dev hit of center: {dev_ge_center_minus1}/9.",
        f"- Neighborhood Feb-Jun delta range: {min_dev_delta:+d} to {max_dev_delta:+d} hits.",
        '', '## Grid',
        '|g2|g3|all hits|dev hits|dev delta|worst month|support hits|',
        '|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for _, r in grid.iterrows():
        lines.append(f"|{r.g2:.2f}|{r.g3:.2f}|{int(r.hits)}|{int(r.dev_hits)}|{int(r.delta_dev_hits):+d}|{100*r.dev_worst_month:.2f}%|{int(r.support_hits)}|")
    (OUT/'summary_v348.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print((OUT/'summary_v348.md').read_text(), flush=True)


if __name__ == '__main__':
    main()
