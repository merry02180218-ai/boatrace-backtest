#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v337_1head_head_cutoff_volume as v337

OUT = Path('/tmp/v346')
OUT.mkdir(parents=True, exist_ok=True)

PRE_V345_EXPECTED = (276, 241, 119)
PRE_V345_SHA256 = '89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73'


def identity_hash(df: pd.DataFrame) -> str:
    ids = sorted(df.race_code.astype(str).str.zfill(12).tolist())
    return hashlib.sha256('\n'.join(ids).encode('utf-8')).hexdigest()


def metrics(df: pd.DataFrame) -> tuple[int, int, int]:
    return len(df), int(df.head_hit.sum()), int(df.hit.sum())


def apply_v345_attack_core(y: pd.DataFrame) -> pd.DataFrame:
    z = y.copy()
    m = z.attack_ready.fillna(False).astype(bool)
    z.loc[m, 'attack_core'] = (
        prod.ATTACK_CORE_W_ONE_EX * pd.to_numeric(z.loc[m, 'one_ex'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_ST * pd.to_numeric(z.loc[m, 'one_st'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_STRAIGHT * pd.to_numeric(z.loc[m, 'one_straight'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_ORIG_AVG * pd.to_numeric(z.loc[m, 'one_orig_avg'], errors='coerce')
    )
    z.loc[~m, 'attack_core'] = np.nan
    return z


def main() -> None:
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('production profile permits September outcomes')
    if prod.PROFILE_NAME != '1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE':
        raise AssertionError(f'unexpected profile {prod.PROFILE_NAME}')
    if prod.ATTACK_CORE_VERSION != 'v345':
        raise AssertionError(f'unexpected attack core {prod.ATTACK_CORE_VERSION}')
    weights = (
        prod.ATTACK_CORE_W_ONE_EX,
        prod.ATTACK_CORE_W_ONE_ST,
        prod.ATTACK_CORE_W_ONE_STRAIGHT,
        prod.ATTACK_CORE_W_ONE_ORIG_AVG,
    )
    if weights != (0.40, 0.25, 0.15, 0.20):
        raise AssertionError(f'unexpected v345 weights {weights}')
    if (prod.HEAD_CUTOFF, prod.OPPONENT_MASS_MIN, prod.EXHIBITION_ENV_W, prod.EXHIBITION_Q) != (0.78, 0.375, 0.10, 0.65):
        raise AssertionError('non-attack-core production parameter drift')

    base = v337.load_candidate_base()
    old_y, _, overlay_n = v337.build_exhibition(base)
    v337.validate_no_sep(old_y)

    # First prove the frozen pre-v345 route/data identity is still intact.
    old_pre, old_selected, _, _ = v337.eval_cut(old_y, prod.HEAD_CUTOFF)
    old_metrics = metrics(old_selected)
    old_hash = identity_hash(old_selected)
    if old_metrics != PRE_V345_EXPECTED or old_hash != PRE_V345_SHA256:
        raise AssertionError(
            f'pre-v345 sentinel drift metrics={old_metrics} hash={old_hash} '
            f'expected={PRE_V345_EXPECTED}/{PRE_V345_SHA256}'
        )

    # Production-only overlay: historical v332/v337 modules stay frozen.
    y = apply_v345_attack_core(old_y)
    v337.validate_no_sep(y)
    pre, selected, _, _ = v337.eval_cut(y, prod.HEAD_CUTOFF)
    got = metrics(selected)
    got_hash = identity_hash(selected)

    selected = selected.copy()
    selected['place'] = selected.race_code.astype(str).str.zfill(12).str[8:10]
    monthly = selected.groupby('month', as_index=False).agg(
        R=('race_code', 'size'), head=('head_hit', 'sum'), exact3=('hit', 'sum')
    )
    monthly['head_rate'] = 100.0 * monthly['head'] / monthly['R']
    monthly['exact3_rate'] = 100.0 * monthly['exact3'] / monthly['R']
    venue = selected.groupby('place', as_index=False).agg(
        R=('race_code', 'size'), head=('head_hit', 'sum'), exact3=('hit', 'sum')
    )
    venue['share_pct'] = 100.0 * venue['R'] / len(selected)
    venue['head_rate'] = 100.0 * venue['head'] / venue['R']
    venue['exact3_rate'] = 100.0 * venue['exact3'] / venue['R']
    venue = venue.sort_values(['R', 'place'], ascending=[False, True])

    old_ids = set(old_selected.race_code.astype(str))
    new_ids = set(selected.race_code.astype(str))
    added = selected[selected.race_code.astype(str).isin(new_ids - old_ids)].copy()
    removed = old_selected[old_selected.race_code.astype(str).isin(old_ids - new_ids)].copy()

    selected[['month', 'race_code', 'p_head', 'head_hit', 'hit', 'attack_core']].sort_values('race_code').to_csv(
        OUT / 'production_v345_pass_identity.csv', index=False
    )
    monthly.to_csv(OUT / 'production_v345_monthly.csv', index=False)
    venue.to_csv(OUT / 'production_v345_venue.csv', index=False)
    added.to_csv(OUT / 'production_v345_added_vs_prev345.csv', index=False)
    removed.to_csv(OUT / 'production_v345_removed_vs_prev345.csv', index=False)

    result = {
        'profile': prod.PROFILE_NAME,
        'attack_core_version': prod.ATTACK_CORE_VERSION,
        'attack_core_weights': {
            'one_ex': weights[0], 'one_st': weights[1],
            'one_straight': weights[2], 'one_orig_avg': weights[3],
        },
        'head_cutoff': prod.HEAD_CUTOFF,
        'pre_R': len(pre),
        'pass': {
            'R': got[0], 'head': got[1], 'head_rate': 100.0 * got[1] / got[0],
            'exact3': got[2], 'exact3_rate': 100.0 * got[2] / got[0],
        },
        'pass_identity_sha256': got_hash,
        'pre_v345_sentinel': {
            'pre_R': len(old_pre), 'R': old_metrics[0], 'head': old_metrics[1],
            'exact3': old_metrics[2], 'sha256': old_hash, 'verified': True,
        },
        'race_identity_delta': {
            'added_R': len(new_ids - old_ids), 'removed_R': len(old_ids - new_ids),
        },
        'canonical_overlay_rows': overlay_n,
        'top_venue_share_pct': float(venue.iloc[0].share_pct),
        'venue_hhi': float(((venue.R / len(selected)) ** 2).sum()),
        'SEPTEMBER_OUTCOMES_READ': False,
        'JUL_AUG_STATUS': 'NON_PRISTINE_SUPPORT_ONLY',
    }
    (OUT / 'result_v346.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
