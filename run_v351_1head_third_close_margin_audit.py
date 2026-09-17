#!/usr/bin/env python3
from __future__ import annotations

"""Audit exact-4 THIRD close-margin expansion on formal 1HEAD v351 276R.

The production three HYBRID tickets are never replaced.  For the SECOND branch
used by HYBRID tickets #1/#2, add conditional THIRD rank3 as exactly one extra
ticket when P(third rank2|second)-P(third rank3|second) <= threshold.

Thresholds .05/.10/.15 are evaluated on the identical frozen Feb-Aug 276R.
Historical payouts are joined only after the frozen selection/tickets are rebuilt.
2026-09-17 outcomes/payouts are never requested.
"""

from pathlib import Path
import json
import math

import pandas as pd

from backtest import rows, BOATRACECSV_REF
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v347_1head_opponent_attackcore as legacy
import run_v351_1head_production_regression as base

OUT = Path('/tmp/v351-third-close-margin-audit')
OUT.mkdir(parents=True, exist_ok=True)
BOATS = (2, 3, 4, 5, 6)
THRESHOLDS = (0.05, 0.10, 0.15)
DEV_MONTHS = ('2026-02', '2026-03', '2026-04', '2026-05', '2026-06')
SUPPORT_MONTHS = ('2026-07', '2026-08')
STAKE_PER_TICKET_YEN = 100


def _payout_map_for(code: str, cache: dict[str, dict[str, dict]]) -> dict[str, dict]:
    day = code[:8]
    if day >= '20260917':
        raise RuntimeError(f'forbidden result/payout date requested: {day}')
    if day not in cache:
        ymd = f'{day[:4]}/{day[4:6]}/{day[6:8]}'
        rs = rows(f'data/results/payouts/{ymd}.csv')
        cache[day] = {
            str(r.get('レースコード', '')).zfill(12): r
            for r in rs if r.get('レースコード')
        }
        if not cache[day]:
            raise RuntimeError(f'missing historical payout file/data for {ymd}')
    return cache[day]


def _payout(code: str, actual: str, cache: dict[str, dict[str, dict]]) -> tuple[str, int]:
    r = _payout_map_for(code, cache).get(code)
    if r is None:
        raise RuntimeError(f'missing payout row for {code}')
    combo = str(r.get('3連単_組番') or '').strip()
    try:
        payout = int(float(str(r.get('3連単_払戻金') or '0').replace(',', '')))
    except Exception as e:
        raise RuntimeError(f'invalid payout for {code}: {r.get("3連単_払戻金")}') from e
    if combo != actual:
        raise RuntimeError(f'payout/result combo mismatch {code}: payout={combo} actual={actual}')
    if payout <= 0:
        raise RuntimeError(f'non-positive payout for {code}: {payout}')
    return combo, payout


def _base_and_extra(p2, pc):
    pair = v299.pair_prob(p2, pc, prod.TICKET_ALPHA)
    top3 = v299.STRATEGIES['HYBRID'](p2, pc, pair)[:3]
    if len(top3) != 3 or len(set(top3)) != 3:
        raise RuntimeError(f'invalid HYBRID top3: {top3}')

    s = top3[0][0]
    if top3[1][0] != s or top3[2][0] == s:
        raise RuntimeError(f'HYBRID branch semantics drift: {top3}')
    thirds = sorted((t for t in BOATS if t != s), key=lambda t: (-float(pc[(s, t)]), t))
    if top3[0] != (s, thirds[0]) or top3[1] != (s, thirds[1]):
        raise RuntimeError(f'HYBRID conditional THIRD semantics drift: top3={top3} thirds={thirds}')

    gap23 = float(pc[(s, thirds[1])]) - float(pc[(s, thirds[2])])
    extra = (s, thirds[2])
    if extra in top3:
        raise RuntimeError(f'extra ticket already in baseline: {top3} extra={extra}')
    return top3, extra, gap23


def _metrics(df: pd.DataFrame, threshold: float | None):
    if threshold is None:
        expanded = pd.Series(False, index=df.index)
        hit = df.base_hit.astype(bool)
        tickets = pd.Series(3, index=df.index)
    else:
        expanded = df.gap23 <= threshold + 1e-12
        hit = df.base_hit.astype(bool) | (expanded & df.extra_hit.astype(bool))
        tickets = 3 + expanded.astype(int)
        if not tickets.isin([3, 4]).all():
            raise RuntimeError('ticket-count invariant failed')

    stake = int((tickets * STAKE_PER_TICKET_YEN).sum())
    ret = int(df.loc[hit, 'payout100'].sum())
    exact = int(hit.sum())
    base_exact = int(df.base_hit.sum())
    return {
        'threshold': 'BASE' if threshold is None else f'{threshold:.2f}',
        'R': len(df),
        'expanded_R': int(expanded.sum()),
        'added_tickets': int(expanded.sum()),
        'exact3_hits': exact,
        'exact3_rate': exact / len(df),
        'gain_hits': exact - base_exact,
        'stake_yen': stake,
        'return_yen': ret,
        'profit_yen': ret - stake,
        'roi': ret / stake if stake else None,
    }


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')
    if prod.JUL_AUG_STATUS != 'NON_PRISTINE_SUPPORT_ONLY':
        raise AssertionError(f'Jul/Aug status drift: {prod.JUL_AUG_STATUS}')
    if prod.OPPONENT_CORE_VERSION != 'v351_OPPONENTCORE_G2_045_G3_100':
        raise AssertionError(f'wrong production version: {prod.OPPONENT_CORE_VERSION}')
    if prod.TICKET_POLICY != 'v320_HYBRID' or float(prod.TICKET_ALPHA) != 0.70:
        raise AssertionError('ticket policy drift')

    # Rebuild the exact formal production population before reading payout files.
    selected, pre_R = legacy.current_selected()
    selected = selected.copy()
    selected['race_code'] = selected.race_code.astype(str).str.zfill(12)
    selected = selected.sort_values('race_code').reset_index(drop=True)
    if any(str(c).startswith('20260917') for c in selected.race_code):
        raise AssertionError('forbidden 2026-09-17 race in formal population')
    if any(str(m) not in DEV_MONTHS + SUPPORT_MONTHS for m in selected.month):
        raise AssertionError('formal population contains unexpected month')

    ids = set(selected.race_code)
    p2dev, pcdev, p2ja, pcja = legacy.opponent_maps()
    cores = legacy.build_opponent_attackcore(ids)

    rec = []
    for _, race in selected.iterrows():
        month = str(race.month)
        code = str(race.race_code).zfill(12)
        p2, pc = legacy.get_dist(month, code, p2dev, pcdev, p2ja, pcja)
        core = cores.get(code)
        if core is None:
            p2a = {int(k): float(v) for k, v in p2.items()}
            pca = {(int(s), int(t)): float(v) for (s, t), v in pc.items()}
            ready = 0
        else:
            p2a = base._second_adjust(p2, core)
            pca = base._third_adjust(pc, core)
            ready = 1

        top3, extra, gap23 = _base_and_extra(p2a, pca)
        tickets = ';'.join(f'1-{s}-{t}' for s, t in top3)
        extra_ticket = f'1-{extra[0]}-{extra[1]}'
        actual = str(race.actual_combo)
        parts = actual.split('-')
        rec.append({
            'month': month,
            'race_code': code,
            'actual_combo': actual,
            'head_hit': int(len(parts) == 3 and parts[0].isdigit() and int(parts[0]) == 1),
            'base_tickets': tickets,
            'base_hit': int(actual in tickets.split(';')),
            'first_second': int(top3[0][0]),
            'extra_ticket': extra_ticket,
            'extra_hit': int(actual == extra_ticket),
            'gap23': gap23,
            'core_ready': ready,
        })

    z = pd.DataFrame(rec).sort_values('race_code').reset_index(drop=True)
    got = (
        len(z),
        int(z.head_hit.sum()),
        int(z.base_hit.sum()),
        base._sha(z.race_code.tolist()),
        base._sha((z.race_code + ':' + z.base_tickets).tolist()),
    )
    expected = (
        prod.PRODUCTION_EXPECTED_PASS_R,
        prod.PRODUCTION_EXPECTED_HEAD,
        prod.PRODUCTION_EXPECTED_EXACT3,
        prod.PRODUCTION_EXPECTED_PASS_ID_SHA256,
        prod.PRODUCTION_EXPECTED_TICKET_ID_SHA256,
    )
    if got != expected:
        raise AssertionError(f'formal v351 sentinel drift: {got} != {expected}')
    dev = z[z.month.isin(DEV_MONTHS)]
    support = z[z.month.isin(SUPPORT_MONTHS)]
    if (len(dev), int(dev.base_hit.sum())) != (220, 107):
        raise AssertionError('Feb-Jun pristine sentinel drift')
    if (len(support), int(support.base_hit.sum())) != (56, 24):
        raise AssertionError('Jul-Aug support-only sentinel drift')

    # Historical payout join is deliberately after selection/ticket regeneration.
    payout_cache: dict[str, dict[str, dict]] = {}
    payouts = []
    combos = []
    for _, r in z.iterrows():
        combo, payout = _payout(str(r.race_code), str(r.actual_combo), payout_cache)
        combos.append(combo)
        payouts.append(payout)
    z['payout_combo'] = combos
    z['payout100'] = payouts
    if len(payout_cache) == 0:
        raise AssertionError('no payout files joined')

    summary_rows = [_metrics(z, None)] + [_metrics(z, t) for t in THRESHOLDS]
    summary = pd.DataFrame(summary_rows)

    monthly_rows = []
    for threshold in (None,) + THRESHOLDS:
        for month, g in z.groupby('month', sort=True):
            m = _metrics(g, threshold)
            m['month'] = month
            monthly_rows.append(m)
    monthly = pd.DataFrame(monthly_rows)

    # Verify exact-four semantics for every threshold.
    for threshold in THRESHOLDS:
        mask = z.gap23 <= threshold + 1e-12
        for _, r in z[mask].iterrows():
            ts = str(r.base_tickets).split(';') + [str(r.extra_ticket)]
            if len(ts) != 4 or len(set(ts)) != 4:
                raise AssertionError(f'exact-4 invariant failed {r.race_code} {threshold}: {ts}')

    result = {
        'profile': prod.PROFILE_NAME,
        'definition': 'Preserve v351 HYBRID top3; on first HYBRID SECOND branch add conditional THIRD rank3 iff pc(rank2)-pc(rank3) <= threshold; exactly 4 tickets on expanded races.',
        'thresholds': list(THRESHOLDS),
        'baseline': summary_rows[0],
        'candidates': summary_rows[1:],
        'formal_sentinel': {
            'PASS': len(z),
            'HEAD': int(z.head_hit.sum()),
            'EXACT3': int(z.base_hit.sum()),
            'race_identity_sha256': got[3],
            'ticket_identity_sha256': got[4],
            'Feb-Jun': {'R': len(dev), 'EXACT3': int(dev.base_hit.sum())},
            'Jul-Aug': {'R': len(support), 'EXACT3': int(support.base_hit.sum())},
        },
        'payout_source': f'BoatraceCSV/{BOATRACECSV_REF} data/results/payouts/YYYY/MM/DD.csv',
        'payout_days_joined': len(payout_cache),
        'stake_per_ticket_yen': STAKE_PER_TICKET_YEN,
        'pre_R': pre_R,
        'core_ready_R': int(z.core_ready.sum()),
        'JUL_AUG_STATUS': prod.JUL_AUG_STATUS,
        'SEPTEMBER_OUTCOMES_READ': False,
        'TODAY_20260917_RESULT_OR_PAYOUT_USED': False,
        'AUDIT_OK': True,
    }

    z.to_csv(OUT / 'rows.csv', index=False, encoding='utf-8-sig')
    summary.to_csv(OUT / 'summary.csv', index=False, encoding='utf-8-sig')
    monthly.to_csv(OUT / 'monthly.csv', index=False, encoding='utf-8-sig')
    (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
