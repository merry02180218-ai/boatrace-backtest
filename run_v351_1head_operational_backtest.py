#!/usr/bin/env python3
from __future__ import annotations

"""Operational-style backtest for the formal 1-head v351 production profile.

Replays the frozen Feb-Aug production selections one race at a time, applies the
formal opponentCore coefficients, generates exactly three trifecta tickets,
settles historical payouts, and measures the local post-exhibition decision
calculation latency. September outcomes are never read.
"""

from pathlib import Path
import json
import math
import statistics
import time

import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v347_1head_opponent_attackcore as legacy

OUT = Path('/tmp/v351-operational-backtest')
OUT.mkdir(parents=True, exist_ok=True)
BOATS = (2, 3, 4, 5, 6)
DEV_MONTHS = ('2026-02', '2026-03', '2026-04', '2026-05', '2026-06')
SUPPORT_MONTHS = ('2026-07', '2026-08')
STAKE_PER_TICKET_YEN = 100
TICKETS_PER_RACE = 3


def _norm(values):
    total = sum(max(float(v), 0.0) for v in values.values())
    if total <= 0:
        return {k: 1.0 / len(values) for k in values}
    return {k: max(float(v), 0.0) / total for k, v in values.items()}


def _adjust_second(p2, core):
    g2 = float(prod.OPPONENT_CORE_SECOND_G2)
    return _norm({b: float(p2[b]) * math.exp(g2 * (float(core[b]) - 0.5)) for b in BOATS})


def _adjust_third(pc, core):
    g3 = float(prod.OPPONENT_CORE_THIRD_G3)
    out = {}
    for s in BOATS:
        raw = {t: float(pc[(s, t)]) * math.exp(g3 * (float(core[t]) - 0.5)) for t in BOATS if t != s}
        for t, p in _norm(raw).items():
            out[(s, t)] = p
    return out


def _tickets(p2, pc):
    pair = v299.pair_prob(p2, pc, prod.TICKET_ALPHA)
    top3 = v299.STRATEGIES['HYBRID'](p2, pc, pair)[:3]
    return ';'.join(f'1-{s}-{t}' for s, t in top3)


def _payout_value(race):
    for key in ('payout100', 'payout', 'trifecta_payout'):
        if key in race.index:
            try:
                v = float(race[key])
                if math.isfinite(v) and v >= 0:
                    return v
            except Exception:
                pass
    return 0.0


def _metrics(df):
    n = len(df)
    hits = int(df.hit.sum()) if n else 0
    stake = int(n * TICKETS_PER_RACE * STAKE_PER_TICKET_YEN)
    ret = float(df.return_yen.sum()) if n else 0.0
    return {
        'R': n,
        'HEAD': int(df.head_hit.sum()) if n else 0,
        'EXACT3': hits,
        'exact3_rate': hits / n if n else 0.0,
        'stake_yen': stake,
        'return_yen': ret,
        'roi': ret / stake if stake else 0.0,
    }


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')
    if prod.OPPONENT_CORE_VERSION != 'v351_OPPONENTCORE_G2_045_G3_100':
        raise AssertionError('not v351 production')

    selected, pre_R = legacy.current_selected()
    selected = selected.copy()
    selected['race_code'] = selected.race_code.astype(str).str.zfill(12)
    selected = selected[selected.month.isin(DEV_MONTHS + SUPPORT_MONTHS)].sort_values('race_code').reset_index(drop=True)
    if len(selected) != prod.PRODUCTION_EXPECTED_PASS_R:
        raise AssertionError(f'PASS drift: {len(selected)}')

    ids = set(selected.race_code)
    prep_t0 = time.perf_counter()
    p2dev, pcdev, p2ja, pcja = legacy.opponent_maps()
    cores = legacy.build_opponent_attackcore(ids)
    prep_ms = (time.perf_counter() - prep_t0) * 1000.0

    rec = []
    for _, race in selected.iterrows():
        month = str(race.month)
        code = str(race.race_code).zfill(12)
        t0 = time.perf_counter()
        p2, pc = legacy.get_dist(month, code, p2dev, pcdev, p2ja, pcja)
        core = cores.get(code)
        if core is None:
            p2a = {int(k): float(v) for k, v in p2.items()}
            pca = {(int(s), int(t)): float(v) for (s, t), v in pc.items()}
            ready = 0
        else:
            p2a = _adjust_second(p2, core)
            pca = _adjust_third(pc, core)
            ready = 1
        tickets = _tickets(p2a, pca)
        decision_ms = (time.perf_counter() - t0) * 1000.0

        actual = str(race.actual_combo)
        parts = actual.split('-')
        head_hit = int(len(parts) == 3 and parts[0].isdigit() and int(parts[0]) == 1)
        hit = int(actual in tickets.split(';'))
        payout = _payout_value(race)
        rec.append({
            'month': month,
            'race_code': code,
            'tickets': tickets,
            'actual_combo': actual,
            'head_hit': head_hit,
            'hit': hit,
            'payout100': payout,
            'return_yen': payout if hit else 0.0,
            'core_ready': ready,
            'decision_ms': decision_ms,
        })

    z = pd.DataFrame(rec)
    overall = _metrics(z)
    dev = _metrics(z[z.month.isin(DEV_MONTHS)])
    support = _metrics(z[z.month.isin(SUPPORT_MONTHS)])
    if overall['EXACT3'] != prod.PRODUCTION_EXPECTED_EXACT3:
        raise AssertionError(f'EXACT3 drift: {overall["EXACT3"]}')
    if dev['EXACT3'] != 107 or support['EXACT3'] != 24:
        raise AssertionError('segment hit drift')

    lat = z.decision_ms.tolist()
    monthly = []
    for mo, g in z.groupby('month', sort=True):
        m = _metrics(g)
        m['month'] = mo
        monthly.append(m)

    result = {
        'profile': prod.PROFILE_NAME,
        'second_g2': prod.OPPONENT_CORE_SECOND_G2,
        'third_g3': prod.OPPONENT_CORE_THIRD_G3,
        'pre_R': pre_R,
        'overall': overall,
        'Feb-Jun_pristine': dev,
        'Jul-Aug_support_only': support,
        'monthly': monthly,
        'post_exhibition_compute_timing_ms': {
            'shared_prepare_ms': prep_ms,
            'mean_per_race': statistics.mean(lat),
            'median_per_race': statistics.median(lat),
            'p95_per_race': float(pd.Series(lat).quantile(0.95)),
            'max_per_race': max(lat),
        },
        'core_ready_R': int(z.core_ready.sum()),
        'SEPTEMBER_OUTCOMES_READ': False,
        'JUL_AUG_STATUS': prod.JUL_AUG_STATUS,
        'NOTE': 'Timing measures local decision computation after inputs are available; network exhibition-fetch latency is separate.',
    }
    (OUT/'result_v351_operational_backtest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    z.to_csv(OUT/'v351_operational_backtest_races.csv', index=False)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
