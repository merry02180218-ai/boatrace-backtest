#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v332_1head_attack_first_redesign as v332

OUT = Path('/tmp/v347')
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = ['2026-02','2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
PRISTINE = set(MONTHS[:5])
CFG = {'family':'ATTACK_ENV_SOFT','env_w':0.1,'q':0.65}


def parse_combo(s):
    p = str(s).split('-')
    return tuple(int(x) for x in p) if len(p) == 3 else (None, None, None)


def parse_boats(s):
    if pd.isna(s):
        return set()
    return {int(x) for x in str(s).split('-') if x.isdigit()}


def select_v345(y: pd.DataFrame) -> pd.DataFrame:
    z = y.copy()
    z['race_code'] = z.race_code.astype(str).str.zfill(12)
    z['month'] = z.month.astype(str)
    if any(x.startswith('2026-09') for x in z.month.unique()):
        raise AssertionError('September entered source')
    if not set(z.month).issubset(set(MONTHS)):
        raise AssertionError(f'unexpected months {sorted(set(z.month))}')
    ready = z.attack_ready.astype(bool)
    z.loc[ready, 'attack_core'] = (
        prod.ATTACK_CORE_W_ONE_EX * pd.to_numeric(z.loc[ready, 'one_ex'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_ST * pd.to_numeric(z.loc[ready, 'one_st'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_STRAIGHT * pd.to_numeric(z.loc[ready, 'one_straight'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_ORIG_AVG * pd.to_numeric(z.loc[ready, 'one_orig_avg'], errors='coerce')
    )
    z.loc[~ready, 'attack_core'] = np.nan
    z = z[pd.to_numeric(z.p_head, errors='coerce').ge(prod.HEAD_CUTOFF)].copy()
    out = []
    for month in MONTHS:
        if month == '2026-08':
            train = z[z.month.isin(MONTHS[:-1])].copy()
        else:
            train = z[z.month.isin([m for m in MONTHS[:-1] if m != month])].copy()
        test = z[z.month.eq(month)].copy()
        p, _ = v332.fit_apply(train, test, CFG)
        out.append(p)
    return pd.concat(out, ignore_index=True)


def main() -> None:
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')
    src = Path(sys.argv[1])
    y = pd.read_csv(src, dtype={'race_code': str})
    sel = select_v345(y)
    identity = (len(sel), int(sel.head_hit.sum()), int(sel.hit.sum()))
    expected = (prod.CURRENT_EXPECTED_PASS_R, prod.CURRENT_EXPECTED_HEAD, prod.CURRENT_EXPECTED_EXACT3)
    if identity != expected:
        raise AssertionError(f'v345 identity drift {identity} != {expected}')

    total_miss = sel[sel.hit.eq(0)].copy()
    hm = sel[sel.head_hit.eq(1) & sel.hit.eq(0)].copy()
    combos = hm.actual_combo.map(parse_combo)
    hm['actual_second'] = [x[1] for x in combos]
    hm['actual_third'] = [x[2] for x in combos]
    hm['second_candidate_hit'] = hm.apply(lambda r: r.actual_second in parse_boats(r.second_boats), axis=1)
    hm['third_candidate_hit'] = hm.apply(lambda r: r.actual_third in parse_boats(r.third_boats), axis=1)
    hm['second_covered'] = hm.apply(lambda r: r.actual_second in parse_boats(r.covered_boats), axis=1)
    hm['third_covered'] = hm.apply(lambda r: r.actual_third in parse_boats(r.covered_boats), axis=1)
    hm['both_covered'] = hm.second_covered & hm.third_covered
    hm['both_slot_candidates'] = hm.second_candidate_hit & hm.third_candidate_hit
    hm['failure_class'] = np.select(
        [~hm.both_covered, hm.both_slot_candidates],
        ['coverage_miss', 'ticket_layout_miss'],
        default='slot_rank_miss',
    )
    hm['segment'] = np.where(hm.month.isin(PRISTINE), 'FEB_JUN_PRISTINE', 'JUL_AUG_NON_PRISTINE')

    monthly = hm.groupby(['month','failure_class'], as_index=False).size().rename(columns={'size':'R'})
    segment = hm.groupby(['segment','failure_class'], as_index=False).size().rename(columns={'size':'R'})
    overall = hm.groupby('failure_class', as_index=False).size().rename(columns={'size':'R'})
    overall['share_pct'] = 100.0 * overall.R / len(hm)

    # Among head-hit races, opponent mass is a useful descriptive diagnostic only.
    hh = sel[sel.head_hit.eq(1)].copy()
    hh['opp_mass_bin'] = pd.qcut(pd.to_numeric(hh.opp_mass, errors='coerce'), 5, duplicates='drop')
    opp_bins = hh.groupby('opp_mass_bin', observed=True, as_index=False).agg(
        R=('race_code','size'), exact3=('hit','sum'), opp_min=('opp_mass','min'), opp_max=('opp_mass','max')
    )
    opp_bins['exact3_rate'] = 100.0 * opp_bins.exact3 / opp_bins.R
    opp_bins['opp_mass_bin'] = opp_bins.opp_mass_bin.astype(str)

    hm.to_csv(OUT/'v347_headhit_exact3_misses.csv', index=False)
    monthly.to_csv(OUT/'v347_failure_monthly.csv', index=False)
    segment.to_csv(OUT/'v347_failure_segment.csv', index=False)
    overall.to_csv(OUT/'v347_failure_overall.csv', index=False)
    opp_bins.to_csv(OUT/'v347_opponent_mass_quintiles.csv', index=False)

    counts = dict(zip(overall.failure_class, overall.R.astype(int)))
    pristine_counts = dict(zip(
        segment.loc[segment.segment.eq('FEB_JUN_PRISTINE'),'failure_class'],
        segment.loc[segment.segment.eq('FEB_JUN_PRISTINE'),'R'].astype(int)
    ))
    support_counts = dict(zip(
        segment.loc[segment.segment.eq('JUL_AUG_NON_PRISTINE'),'failure_class'],
        segment.loc[segment.segment.eq('JUL_AUG_NON_PRISTINE'),'R'].astype(int)
    ))
    result = {
        'profile': prod.PROFILE_NAME,
        'identity': {'R': identity[0], 'head': identity[1], 'exact3': identity[2]},
        'exact3_miss_R': int(len(total_miss)),
        'head_hit_exact3_miss_R': int(len(hm)),
        'head_miss_R': int((sel.head_hit == 0).sum()),
        'head_hit_exact3_miss_share_of_all_exact3_miss_pct': 100.0 * len(hm) / len(total_miss),
        'failure_classes_all': counts,
        'failure_classes_feb_jun_pristine': pristine_counts,
        'failure_classes_jul_aug_non_pristine': support_counts,
        'coverage_miss_share_pct': 100.0 * counts.get('coverage_miss',0) / len(hm),
        'slot_rank_miss_share_pct': 100.0 * counts.get('slot_rank_miss',0) / len(hm),
        'ticket_layout_miss_share_pct': 100.0 * counts.get('ticket_layout_miss',0) / len(hm),
        'SEPTEMBER_OUTCOMES_READ': False,
        'JUL_AUG_STATUS': 'NON_PRISTINE_SUPPORT_ONLY',
        'PRODUCTION_CHANGED': False,
    }
    (OUT/'result_v347.json').write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
