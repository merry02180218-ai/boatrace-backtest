#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

import onehead_production_profile as prod
import run_v332_1head_attack_first_redesign as v332

OUT = Path('/tmp/v346fast')
OUT.mkdir(parents=True, exist_ok=True)
MONTHS = ['2026-02','2026-03','2026-04','2026-05','2026-06','2026-07','2026-08']
CFG = {'family':'ATTACK_ENV_SOFT','env_w':0.1,'q':0.65}
PRE_V345 = (276, 241, 119)
PRE_V345_SHA = '89e0b32c3ffbed6212f98f0a9b2e230717b8e41010019e3321fb49e70148ba73'


def ident(df: pd.DataFrame) -> str:
    ids = sorted(df.race_code.astype(str).str.zfill(12).tolist())
    return hashlib.sha256('\n'.join(ids).encode()).hexdigest()


def met(df: pd.DataFrame):
    return len(df), int(df.head_hit.sum()), int(df.hit.sum())


def eval_cut(df: pd.DataFrame):
    y = df[pd.to_numeric(df.p_head, errors='coerce').ge(prod.HEAD_CUTOFF)].copy()
    selected = []
    for m in MONTHS:
        if m == '2026-08':
            tr = y[y.month.isin(MONTHS[:-1])].copy()
        else:
            tr = y[y.month.isin([x for x in MONTHS[:-1] if x != m])].copy()
        te = y[y.month.eq(m)].copy()
        p, _ = v332.fit_apply(tr, te, CFG)
        selected.append(p)
    return y, pd.concat(selected, ignore_index=True)


def main() -> None:
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('September guard disabled')
    if prod.PROFILE_NAME != '1HEAD_PRODUCTION_20260914_HEAD078_V345_ATTACKCORE':
        raise AssertionError(prod.PROFILE_NAME)
    src = Path(sys.argv[1])
    y = pd.read_csv(src, dtype={'race_code':str})
    y.race_code = y.race_code.astype(str).str.zfill(12)
    y.month = y.month.astype(str)
    if any(x.startswith('2026-09') for x in y.month.unique()):
        raise AssertionError('September entered artifact')
    if not set(y.month).issubset(set(MONTHS)):
        raise AssertionError(f'unexpected months {sorted(set(y.month))}')

    old_pre, old = eval_cut(y)
    if met(old) != PRE_V345 or ident(old) != PRE_V345_SHA:
        raise AssertionError(f'old sentinel drift {met(old)} {ident(old)}')

    z = y.copy()
    m = z.attack_ready.astype(bool)
    z.loc[m, 'attack_core'] = (
        prod.ATTACK_CORE_W_ONE_EX * pd.to_numeric(z.loc[m, 'one_ex'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_ST * pd.to_numeric(z.loc[m, 'one_st'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_STRAIGHT * pd.to_numeric(z.loc[m, 'one_straight'], errors='coerce')
        + prod.ATTACK_CORE_W_ONE_ORIG_AVG * pd.to_numeric(z.loc[m, 'one_orig_avg'], errors='coerce')
    )
    z.loc[~m, 'attack_core'] = np.nan
    pre, selected = eval_cut(z)
    got = met(selected); h = ident(selected)
    expected = (prod.CURRENT_EXPECTED_PASS_R, prod.CURRENT_EXPECTED_HEAD, prod.CURRENT_EXPECTED_EXACT3)
    if got != expected or h != prod.CURRENT_EXPECTED_PASS_ID_SHA256:
        raise AssertionError(
            f'current v345 identity drift got={got}/{h} '
            f'expected={expected}/{prod.CURRENT_EXPECTED_PASS_ID_SHA256}'
        )

    selected = selected.copy()
    selected['place'] = selected.race_code.str[8:10]
    monthly = selected.groupby('month', as_index=False).agg(R=('race_code','size'), head=('head_hit','sum'), exact3=('hit','sum'))
    monthly['head_rate'] = 100 * monthly['head'] / monthly['R']
    monthly['exact3_rate'] = 100 * monthly['exact3'] / monthly['R']
    venue = selected.groupby('place', as_index=False).agg(R=('race_code','size'), head=('head_hit','sum'), exact3=('hit','sum'))
    venue['share_pct'] = 100 * venue['R'] / len(selected)
    venue['head_rate'] = 100 * venue['head'] / venue['R']
    venue['exact3_rate'] = 100 * venue['exact3'] / venue['R']
    venue = venue.sort_values(['R','place'], ascending=[False,True])

    old_ids = set(old.race_code); new_ids = set(selected.race_code)
    result = {
        'profile': prod.PROFILE_NAME,
        'source': 'v337 repaired canonical artifact',
        'pre_R': len(pre),
        'pass': {'R': got[0], 'head': got[1], 'head_rate': 100*got[1]/got[0], 'exact3': got[2], 'exact3_rate': 100*got[2]/got[0]},
        'pass_identity_sha256': h,
        'current_profile_identity_verified': True,
        'pre_v345_sentinel_verified': True,
        'pre_v345': {'pre_R':len(old_pre), 'R':PRE_V345[0], 'head':PRE_V345[1], 'exact3':PRE_V345[2], 'sha256':PRE_V345_SHA},
        'race_identity_delta': {'added_R':len(new_ids-old_ids), 'removed_R':len(old_ids-new_ids)},
        'top_venue_share_pct': float(venue.iloc[0].share_pct),
        'venue_hhi': float(((venue.R/len(selected))**2).sum()),
        'SEPTEMBER_OUTCOMES_READ': False,
        'JUL_AUG_STATUS': 'NON_PRISTINE_SUPPORT_ONLY',
    }
    selected[['month','race_code','p_head','head_hit','hit','attack_core']].sort_values('race_code').to_csv(OUT/'production_v345_pass_identity.csv', index=False)
    monthly.to_csv(OUT/'production_v345_monthly.csv', index=False)
    venue.to_csv(OUT/'production_v345_venue.csv', index=False)
    (OUT/'result_v346_fast.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__': main()
