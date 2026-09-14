#!/usr/bin/env python3
from __future__ import annotations

"""Independent production regression for 1-head v351 opponentCore.

This verifier rebuilds the fixed Feb-Aug selection from the frozen pipeline,
recomputes opponentCore from preview inputs, applies the formally adopted v351
SECOND/THIRD coefficients, regenerates three tickets, and checks production
sentinels. September outcomes must remain unread.
"""

from pathlib import Path
import hashlib
import json
import math

import pandas as pd

import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v347_1head_opponent_attackcore as legacy

OUT = Path('/tmp/v351-production-audit')
OUT.mkdir(parents=True, exist_ok=True)
BOATS = (2, 3, 4, 5, 6)
DEV_MONTHS = ('2026-02', '2026-03', '2026-04', '2026-05', '2026-06')
SUPPORT_MONTHS = ('2026-07', '2026-08')


def _norm(values):
    total = sum(max(float(v), 0.0) for v in values.values())
    if total <= 0.0:
        return {k: 1.0 / len(values) for k in values}
    return {k: max(float(v), 0.0) / total for k, v in values.items()}


def _second_adjust(p2, core):
    g2 = float(prod.OPPONENT_CORE_SECOND_G2)
    raw = {
        b: float(p2[b]) * math.exp(g2 * (float(core[b]) - 0.5))
        for b in BOATS
    }
    return _norm(raw)


def _third_adjust(pc, core):
    g3 = float(prod.OPPONENT_CORE_THIRD_G3)
    out = {}
    for second in BOATS:
        raw = {
            third: float(pc[(second, third)])
            * math.exp(g3 * (float(core[third]) - 0.5))
            for third in BOATS
            if third != second
        }
        for third, value in _norm(raw).items():
            out[(second, third)] = value
    return out


def _tickets(p2, pc):
    pair_prob = v299.pair_prob(p2, pc, prod.TICKET_ALPHA)
    top3 = v299.STRATEGIES['HYBRID'](p2, pc, pair_prob)[:3]
    return ';'.join(f'1-{second}-{third}' for second, third in top3)


def _sha(lines):
    return hashlib.sha256('\n'.join(lines).encode('utf-8')).hexdigest()


def main():
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')
    if prod.JUL_AUG_STATUS != 'NON_PRISTINE_SUPPORT_ONLY':
        raise AssertionError(f'Jul/Aug status drift: {prod.JUL_AUG_STATUS}')
    if prod.OPPONENT_CORE_VERSION != 'v351_OPPONENTCORE_G2_045_G3_100':
        raise AssertionError(f'wrong opponentCore version: {prod.OPPONENT_CORE_VERSION}')
    if float(prod.OPPONENT_CORE_SECOND_G2) != 0.45:
        raise AssertionError('SECOND g2 drift')
    if float(prod.OPPONENT_CORE_THIRD_G3) != 1.00:
        raise AssertionError('THIRD g3 drift')

    selected, pre_R = legacy.current_selected()
    selected = selected.copy()
    selected['race_code'] = selected.race_code.astype(str).str.zfill(12)
    ids = set(selected.race_code)

    p2dev, pcdev, p2ja, pcja = legacy.opponent_maps()
    cores = legacy.build_opponent_attackcore(ids)

    records = []
    for _, race in selected.sort_values('race_code').iterrows():
        month = str(race.month)
        code = str(race.race_code).zfill(12)
        if month not in DEV_MONTHS + SUPPORT_MONTHS:
            raise AssertionError(f'unexpected month in frozen selection: {month}')

        p2, pc = legacy.get_dist(month, code, p2dev, pcdev, p2ja, pcja)
        core = cores.get(code)
        if core is None:
            p2_adj = {int(k): float(v) for k, v in p2.items()}
            pc_adj = {(int(s), int(t)): float(v) for (s, t), v in pc.items()}
            core_ready = 0
        else:
            p2_adj = _second_adjust(p2, core)
            pc_adj = _third_adjust(pc, core)
            core_ready = 1

        tickets = _tickets(p2_adj, pc_adj)
        actual = str(race.actual_combo)
        parts = actual.split('-')
        head_hit = int(len(parts) == 3 and parts[0].isdigit() and int(parts[0]) == 1)
        hit = int(actual in tickets.split(';'))
        records.append({
            'month': month,
            'race_code': code,
            'actual_combo': actual,
            'tickets': tickets,
            'head_hit': head_hit,
            'hit': hit,
            'core_ready': core_ready,
        })

    z = pd.DataFrame(records).sort_values('race_code').reset_index(drop=True)
    pass_R = len(z)
    head = int(z.head_hit.sum())
    exact3 = int(z.hit.sum())
    race_sha = _sha(z.race_code.tolist())
    ticket_sha = _sha((z.race_code + ':' + z.tickets).tolist())

    got = (pass_R, head, exact3, race_sha, ticket_sha)
    expected = (
        prod.PRODUCTION_EXPECTED_PASS_R,
        prod.PRODUCTION_EXPECTED_HEAD,
        prod.PRODUCTION_EXPECTED_EXACT3,
        prod.PRODUCTION_EXPECTED_PASS_ID_SHA256,
        prod.PRODUCTION_EXPECTED_TICKET_ID_SHA256,
    )
    if got != expected:
        raise AssertionError(f'v351 production sentinel drift: {got} != {expected}')

    dev = z[z.month.isin(DEV_MONTHS)]
    support = z[z.month.isin(SUPPORT_MONTHS)]
    if (len(dev), int(dev.hit.sum())) != (220, 107):
        raise AssertionError('Feb-Jun pristine sentinel drift')
    if (len(support), int(support.hit.sum())) != (56, 24):
        raise AssertionError('Jul-Aug support-only sentinel drift')

    result = {
        'profile': prod.PROFILE_NAME,
        'opponentCore_version': prod.OPPONENT_CORE_VERSION,
        'second_g2': prod.OPPONENT_CORE_SECOND_G2,
        'third_g3': prod.OPPONENT_CORE_THIRD_G3,
        'pre_R': pre_R,
        'PASS': pass_R,
        'HEAD': head,
        'EXACT3': exact3,
        'exact3_rate': exact3 / pass_R,
        'race_identity_sha256': race_sha,
        'ticket_identity_sha256': ticket_sha,
        'core_ready_R': int(z.core_ready.sum()),
        'Feb-Jun': {'R': len(dev), 'EXACT3': int(dev.hit.sum())},
        'Jul-Aug': {'R': len(support), 'EXACT3': int(support.hit.sum())},
        'SEPTEMBER_OUTCOMES_READ': False,
        'JUL_AUG_STATUS': prod.JUL_AUG_STATUS,
        'AUDIT_SOURCE': 'raw/frozen pipeline regeneration; no v350 search artifact read',
        'AUDIT_OK': True,
    }
    (OUT / 'result_v351_production_regression.json').write_text(
        json.dumps(result, indent=2), encoding='utf-8'
    )
    z[['month', 'race_code', 'tickets', 'head_hit', 'hit', 'core_ready']].to_csv(
        OUT / 'v351_production_races.csv', index=False
    )
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
