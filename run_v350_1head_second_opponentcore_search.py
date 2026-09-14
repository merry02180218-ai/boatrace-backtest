#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v347_1head_opponent_attackcore as legacy

OUT = Path('/tmp/v350')
OUT.mkdir(parents=True, exist_ok=True)
G3_FIXED = 1.00
G2_VALUES = tuple(round(x * 0.05, 2) for x in range(41))
DEV_MONTHS = legacy.DEV_MONTHS
SUPPORT_MONTHS = legacy.SUPPORT_MONTHS


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')

    sel, pre_R = legacy.current_selected()
    ids = set(sel.race_code.astype(str).str.zfill(12))
    p2dev, pcdev, p2ja, pcja = legacy.opponent_maps()
    cores = legacy.build_opponent_attackcore(ids)

    rows = []
    monthly_frames = []
    race_frames = []
    for g2 in G2_VALUES:
        z, m, mon = legacy.evaluate(sel, cores, p2dev, pcdev, p2ja, pcja, g2, G3_FIXED)
        rows.append(m)
        mon['g2'] = g2
        monthly_frames.append(mon)
        z['g2'] = g2
        race_frames.append(z)

    grid = pd.DataFrame(rows).sort_values('g2').reset_index(drop=True)
    monthly = pd.concat(monthly_frames, ignore_index=True)
    races = pd.concat(race_frames, ignore_index=True)

    current = grid[np.isclose(grid.g2, 0.50)].iloc[0]
    grid['delta_vs_current_hits'] = grid.hits - int(current.hits)
    grid['delta_vs_current_dev_hits'] = grid.dev_hits - int(current.dev_hits)
    grid['delta_vs_current_support_hits'] = grid.support_hits - int(current.support_hits)
    grid['distance_from_current'] = (grid.g2 - 0.50).abs()

    # Selection uses pristine data only. Jul-Aug never influence ranking or tie-breaking.
    # If pristine metrics tie, prefer the smaller change from the current production value.
    ranked = grid.sort_values(
        ['dev_hits', 'dev_worst_month', 'distance_from_current'],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    best = ranked.iloc[0]

    best_g2 = float(best.g2)
    near = grid[(grid.g2 >= max(0.0, best_g2 - 0.15) - 1e-9) & (grid.g2 <= min(2.0, best_g2 + 0.15) + 1e-9)].copy()
    plateau = grid[grid.dev_hits >= int(best.dev_hits) - 1].copy()

    cur_r = races[np.isclose(races.g2, 0.50)][['race_code','month','hit','tickets']].rename(
        columns={'hit':'current_hit','tickets':'current_tickets'}
    )
    best_r = races[np.isclose(races.g2, best_g2)][['race_code','hit','tickets']].rename(
        columns={'hit':'best_hit','tickets':'best_tickets'}
    )
    cmp = cur_r.merge(best_r, on='race_code')
    cmp['delta'] = cmp.best_hit - cmp.current_hit

    grid.to_csv(OUT/'v350_second_g2_grid.csv', index=False)
    monthly.to_csv(OUT/'v350_second_g2_monthly.csv', index=False)
    cmp.to_csv(OUT/'v350_best_vs_current_race_delta.csv', index=False)

    result = {
        'profile': prod.PROFILE_NAME,
        'pre_R': pre_R,
        'pass_R': len(sel),
        'head': int(sel.head_hit.sum()),
        'g3_fixed': G3_FIXED,
        'g2_start': min(G2_VALUES),
        'g2_end': max(G2_VALUES),
        'g2_step': 0.05,
        'points': len(G2_VALUES),
        'ranking_rule': 'Feb-Jun dev_hits desc, Feb-Jun worst-month desc, distance from current .50 asc',
        'current': current.to_dict(),
        'best_pristine': best.to_dict(),
        'best_gain_R_vs_current': int((cmp.delta == 1).sum()),
        'best_loss_R_vs_current': int((cmp.delta == -1).sum()),
        'near_best': near.to_dict(orient='records'),
        'plateau_dev_within_1_hit': {
            'count': int(len(plateau)),
            'g2_min': float(plateau.g2.min()),
            'g2_max': float(plateau.g2.max()),
        },
        'SEPTEMBER_OUTCOMES_READ': False,
        'JUL_AUG_STATUS': 'NON_PRISTINE_SUPPORT_ONLY',
        'PRODUCTION_CHANGED': False,
    }
    (OUT/'result_v350.json').write_text(json.dumps(result, indent=2, default=float), encoding='utf-8')

    lines = [
        '# v350 second opponentCore coefficient search', '',
        '- Third-side coefficient is fixed at g3=1.00.',
        '- Second-side g2 is scanned from 0.00 to 2.00 in 0.05 steps.',
        '- Ranking uses Feb-Jun pristine data only: dev hits, then pristine worst-month, then distance from current .50.',
        '- Jul-Aug are support-only and are not used in ranking or tie-breaking.',
        '- September outcomes remain unread.',
        '',
        f"- Current g2=.50: all {int(current.hits)}/{int(current.R)}, Feb-Jun {int(current.dev_hits)}/{int(current.dev_R)}, worst-month {100*current.dev_worst_month:.2f}%.",
        f"- Best pristine g2={best_g2:.2f}: all {int(best.hits)}/{int(best.R)}, Feb-Jun {int(best.dev_hits)}/{int(best.dev_R)}, worst-month {100*best.dev_worst_month:.2f}%.",
        f"- Best vs current race swaps: +hit {int((cmp.delta == 1).sum())} / -hit {int((cmp.delta == -1).sum())}.",
        f"- Within one pristine hit of best: {len(plateau)} points, g2 {float(plateau.g2.min()):.2f} to {float(plateau.g2.max()):.2f}.",
        '', '## Local neighborhood',
        '|g2|all hits|dev hits|dev delta vs .50|worst month|support hits|',
        '|---:|---:|---:|---:|---:|---:|',
    ]
    for _, r in near.iterrows():
        lines.append(f"|{r.g2:.2f}|{int(r.hits)}|{int(r.dev_hits)}|{int(r.delta_vs_current_dev_hits):+d}|{100*r.dev_worst_month:.2f}%|{int(r.support_hits)}|")
    (OUT/'summary_v350.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print((OUT/'summary_v350.md').read_text(), flush=True)


if __name__ == '__main__':
    main()
