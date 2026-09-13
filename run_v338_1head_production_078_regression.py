#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pandas as pd

import onehead_production_profile as prod
import run_v337_1head_head_cutoff_volume as v337

OUT = Path('/tmp/v338')
OUT.mkdir(parents=True, exist_ok=True)


def identity_hash(df: pd.DataFrame) -> str:
    ids = sorted(df.race_code.astype(str).str.zfill(12).tolist())
    return hashlib.sha256('\n'.join(ids).encode('utf-8')).hexdigest()


def metrics(df: pd.DataFrame) -> tuple[int, int, int]:
    return len(df), int(df.head_hit.sum()), int(df.hit.sum())


def main() -> None:
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('production profile permits September outcomes')

    base = v337.load_candidate_base()
    y, canon_pass, overlay_n = v337.build_exhibition(base)
    v337.validate_no_sep(y)

    _, anchor, _, _ = v337.eval_cut(y, prod.ANCHOR_HEAD_CUTOFF)
    anchor_m = metrics(anchor)
    anchor_h = identity_hash(anchor)
    expected_anchor = (
        prod.ANCHOR_EXPECTED_PASS_R,
        prod.ANCHOR_EXPECTED_HEAD,
        prod.ANCHOR_EXPECTED_EXACT3,
    )
    if anchor_m != expected_anchor or anchor_h != prod.ANCHOR_PASS_ID_SHA256:
        raise AssertionError(
            f'anchor regression drift metrics={anchor_m} hash={anchor_h} '
            f'expected={expected_anchor}/{prod.ANCHOR_PASS_ID_SHA256}'
        )
    if set(anchor.race_code.astype(str)) != set(canon_pass.race_code.astype(str)):
        raise AssertionError('anchor no longer equals canonical v332 PASS identity')

    pre, selected, monthly_raw, summary = v337.eval_cut(y, prod.HEAD_CUTOFF)
    got = metrics(selected)
    expected = (prod.EXPECTED_PASS_R, prod.EXPECTED_HEAD, prod.EXPECTED_EXACT3)
    got_hash = identity_hash(selected)
    if got != expected or got_hash != prod.EXPECTED_PASS_ID_SHA256:
        raise AssertionError(
            f'production 0.78 regression drift metrics={got} hash={got_hash} '
            f'expected={expected}/{prod.EXPECTED_PASS_ID_SHA256}'
        )

    selected = selected.copy()
    selected['place'] = selected.race_code.astype(str).str.zfill(12).str[8:10]
    monthly = selected.groupby('month', as_index=False).agg(
        R=('race_code','size'), head=('head_hit','sum'), exact3=('hit','sum')
    )
    monthly['head_rate'] = 100.0 * monthly['head'] / monthly['R']
    monthly['exact3_rate'] = 100.0 * monthly['exact3'] / monthly['R']
    venue = selected.groupby('place', as_index=False).agg(
        R=('race_code','size'), head=('head_hit','sum'), exact3=('hit','sum')
    )
    venue['share_pct'] = 100.0 * venue['R'] / len(selected)
    venue['head_rate'] = 100.0 * venue['head'] / venue['R']
    venue['exact3_rate'] = 100.0 * venue['exact3'] / venue['R']
    venue = venue.sort_values(['R','place'], ascending=[False,True])

    anchor_ids = set(anchor.race_code.astype(str))
    added = selected[~selected.race_code.astype(str).isin(anchor_ids)].copy()
    added_metrics = {
        'R': len(added),
        'head': int(added.head_hit.sum()),
        'head_rate': 100.0 * added.head_hit.sum() / len(added),
        'exact3': int(added.hit.sum()),
        'exact3_rate': 100.0 * added.hit.sum() / len(added),
    }

    selected[['month','race_code','p_head','head_hit','hit']].sort_values('race_code').to_csv(
        OUT/'production_078_pass_identity.csv', index=False
    )
    monthly.to_csv(OUT/'production_078_monthly.csv', index=False)
    venue.to_csv(OUT/'production_078_venue.csv', index=False)
    result = {
        'profile': prod.PROFILE_NAME,
        'head_cutoff': prod.HEAD_CUTOFF,
        'pre_R': len(pre),
        'pass': {'R': got[0], 'head': got[1], 'exact3': got[2]},
        'pass_identity_sha256': got_hash,
        'anchor': {'R': anchor_m[0], 'head': anchor_m[1], 'exact3': anchor_m[2], 'sha256': anchor_h},
        'canonical_overlay_rows': overlay_n,
        'added_vs_anchor': added_metrics,
        'top_venue_share_pct': float(venue.iloc[0].share_pct),
        'venue_hhi': float(((venue.R / len(selected)) ** 2).sum()),
        'SEPTEMBER_OUTCOMES_READ': False,
    }
    (OUT/'result_v338.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
