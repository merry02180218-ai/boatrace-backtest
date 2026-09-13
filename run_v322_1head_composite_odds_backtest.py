#!/usr/bin/env python3
"""v322: composite-odds audit for the frozen 1-head exact-3 stack.

Selection/tickets are immutable inputs from v320. Historical closing odds are used only
for settlement diagnostics. This script intentionally does NOT compute Dutch stakes.

Frozen assertions:
- 345 races
- 290 boat-1 wins
- 139 exact-3 hits
- HYBRID alpha=.70
- exactly 3 unique 1-x-y tickets per race

Composite odds = 1 / sum(1 / odds_i) across the three frozen tickets.
For the user's backtest convention only, each evaluable race has notional cost 10,000;
if the frozen 3-ticket set hits, notional return is 10,000 * composite_odds, otherwise 0.
This is an evaluation convention, not a staking instruction.
"""
from __future__ import annotations

from pathlib import Path
import math
import numpy as np
import pandas as pd

import analyze_v205_3head_operational_replay as v205

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'analysis_v320_1head_exact3_ticket_policy_best_race.csv'
OUT = ROOT / 'analysis_v322_1head_composite_odds_backtest.csv'
MISSING = ROOT / 'analysis_v322_1head_composite_odds_missing.csv'
MONTHLY = ROOT / 'analysis_v322_1head_composite_odds_monthly.csv'
GRID = ROOT / 'analysis_v322_1head_composite_odds_threshold_grid.csv'
SUMMARY = ROOT / 'summary_v322_1head_composite_odds_backtest.md'
BANK = 10_000
THRESHOLDS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0]


def _ticket_list(x: str) -> list[str]:
    return [t.strip() for t in str(x).split(';') if t.strip()]


def _odds_row(oi: pd.DataFrame, code: str):
    if code not in oi.index:
        return None
    r = oi.loc[code]
    return r.iloc[-1] if isinstance(r, pd.DataFrame) else r


def _safe_odds(r, t: str):
    try:
        v = float(r[t])
    except Exception:
        return None
    return v if np.isfinite(v) and v > 0 else None


def composite(vals: list[float]) -> float:
    if len(vals) != 3 or any((not math.isfinite(x) or x <= 0) for x in vals):
        raise ValueError('composite requires three positive finite odds')
    return 1.0 / sum(1.0 / x for x in vals)


def metrics(g: pd.DataFrame) -> dict:
    R = len(g)
    hits = int(g.hit.sum()) if R else 0
    cost = float(R * BANK)
    ret = float(g.notional_return.sum()) if R else 0.0
    return {
        'R': R,
        'hits': hits,
        'hit_rate': hits / R if R else np.nan,
        'avg_composite_odds': float(g.composite_odds.mean()) if R else np.nan,
        'median_composite_odds': float(g.composite_odds.median()) if R else np.nan,
        'cost_yen': cost,
        'return_yen': ret,
        'profit_yen': ret - cost,
        'roi': ret / cost if cost else np.nan,
    }


def main():
    d = pd.read_csv(SRC, dtype={'race_code': str})
    d['race_code'] = d.race_code.astype(str).str.replace('.0', '', regex=False).str.zfill(12)

    # Fail closed if the frozen v320 cohort drifted.
    if len(d) != 345:
        raise RuntimeError(f'v320 cohort drift: expected 345 rows, got {len(d)}')
    if int(pd.to_numeric(d.head_hit, errors='coerce').sum()) != 290:
        raise RuntimeError('v320 head-hit drift: expected 290')
    if int(pd.to_numeric(d.hit, errors='coerce').sum()) != 139:
        raise RuntimeError('v320 exact3 drift: expected 139')
    if set(d.strategy.astype(str)) != {'HYBRID'}:
        raise RuntimeError(f'v320 strategy drift: {sorted(set(d.strategy.astype(str)))}')
    if not np.allclose(pd.to_numeric(d.alpha, errors='coerce').to_numpy(float), .70):
        raise RuntimeError('v320 alpha drift: expected .70')

    for _, r in d.iterrows():
        ts = _ticket_list(r.tickets)
        if len(ts) != 3 or len(set(ts)) != 3:
            raise RuntimeError(f'invalid frozen 3-ticket set {r.race_code}: {ts}')
        if any(not t.startswith('1-') for t in ts):
            raise RuntimeError(f'non-1-head ticket in frozen set {r.race_code}: {ts}')

    odds = v205.load_odds()
    if odds.empty:
        raise RuntimeError('historical trifecta odds source is empty')
    odds['race_code'] = odds.race_code.astype(str).str.replace('.0', '', regex=False).str.zfill(12)
    oi = odds.set_index('race_code', drop=False)

    rows = []
    missing = []
    for _, r in d.iterrows():
        code = str(r.race_code).zfill(12)
        ts = _ticket_list(r.tickets)
        o = _odds_row(oi, code)
        if o is None:
            missing.append({'month': r.month, 'race_code': code, 'tickets': r.tickets,
                            'reason': 'race_odds_missing'})
            continue
        vals = [_safe_odds(o, t) for t in ts]
        if any(v is None for v in vals):
            missing.append({'month': r.month, 'race_code': code, 'tickets': r.tickets,
                            'reason': 'one_or_more_ticket_odds_missing'})
            continue
        comp = composite([float(x) for x in vals])
        hit = int(r.hit)
        ret = BANK * comp if hit else 0.0
        rows.append({
            'month': r.month,
            'race_code': code,
            'head_hit': int(r.head_hit),
            'actual_combo': r.actual_combo,
            'ticket1': ts[0], 'odds1': vals[0],
            'ticket2': ts[1], 'odds2': vals[1],
            'ticket3': ts[2], 'odds3': vals[2],
            'composite_odds': comp,
            'hit': hit,
            'notional_cost': BANK,
            'notional_return': ret,
            'notional_profit': ret - BANK,
            'odds_source': str(o.get('odds_source', 'unknown')),
        })

    z = pd.DataFrame(rows)
    miss = pd.DataFrame(missing, columns=['month','race_code','tickets','reason'])
    if z.empty:
        raise RuntimeError('no v320 races have complete 3-ticket odds')
    z.to_csv(OUT, index=False)
    miss.to_csv(MISSING, index=False)

    monthly_rows = []
    for mo, g in z.groupby('month'):
        m = metrics(g)
        monthly_rows.append({'month': mo, **m})
    monthly = pd.DataFrame(monthly_rows)
    monthly.to_csv(MONTHLY, index=False)

    grid_rows = []
    for label, cut in [('ALL', None)] + [(f'>={x:g}', x) for x in THRESHOLDS]:
        g = z if cut is None else z[z.composite_odds >= cut]
        m = metrics(g)
        grid_rows.append({'rule': label, 'min_composite_odds': np.nan if cut is None else cut,
                          'coverage_of_evaluable': len(g) / len(z), **m})
    grid = pd.DataFrame(grid_rows)
    grid.to_csv(GRID, index=False)

    overall = metrics(z)
    coverage = len(z) / len(d)
    source_counts = z.odds_source.value_counts().to_dict()

    L = [
        '# v322 1HEAD frozen-3 composite-odds backtest', '',
        '- Frozen selection/tickets only: v308 cohort + v317 SECOND + v318 THIRD + v320 HYBRID alpha=.70.',
        '- Frozen cohort assertions passed: **345 races / 290 boat-1 wins / 139 exact3 hits**.',
        '- Closing odds are settlement diagnostics only; they never select races or tickets.',
        '- Composite odds = `1/(1/o1 + 1/o2 + 1/o3)` for the three frozen tickets.',
        '- No Dutch stakes are generated. 10,000 yen is used only as a notional backtest accounting unit.',
        '- Threshold rows below are descriptive development diagnostics, not an automatically promoted LIVE cutoff.', '',
        '## Odds coverage',
        f'- Complete 3-ticket odds: **{len(z)}/345 = {100*coverage:.2f}%**.',
        f'- Missing/incomplete odds rows: **{len(miss)}**.',
        f'- Odds sources: `{source_counts}`.', '',
        '## Overall evaluable result',
        f"- R **{overall['R']}**, hits **{overall['hits']} ({100*overall['hit_rate']:.2f}%)**.",
        f"- Average composite odds **{overall['avg_composite_odds']:.3f}**, median **{overall['median_composite_odds']:.3f}**.",
        f"- Notional return **{overall['return_yen']:.0f}** / cost **{overall['cost_yen']:.0f}**, ROI **{100*overall['roi']:.2f}%**, profit **{overall['profit_yen']:.0f}**.", '',
        '## Monthly',
        '|month|R|hits|hit rate|avg comp|median comp|ROI|',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for _, r in monthly.iterrows():
        L.append(f"|{r.month}|{int(r.R)}|{int(r.hits)}|{100*r.hit_rate:.2f}%|{r.avg_composite_odds:.3f}|{r.median_composite_odds:.3f}|{100*r.roi:.2f}%|")
    L += ['', '## Composite-odds threshold diagnostics',
          '|rule|R|coverage|hits|hit rate|avg comp|ROI|profit|',
          '|---|---:|---:|---:|---:|---:|---:|---:|']
    for _, r in grid.iterrows():
        L.append(f"|{r.rule}|{int(r.R)}|{100*r.coverage_of_evaluable:.2f}%|{int(r.hits)}|{100*r.hit_rate:.2f}%|{r.avg_composite_odds:.3f}|{100*r.roi:.2f}%|{r.profit_yen:.0f}|")
    L += ['', '## Guardrail',
          '- Do not choose a LIVE BUY cutoff solely from the best row above; Feb-Jun is reused development evidence.',
          '- Missing historical odds are reported separately and never allowed to redefine the frozen 345-race model cohort.']
    SUMMARY.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(SUMMARY.read_text(encoding='utf-8'), flush=True)


if __name__ == '__main__':
    main()
