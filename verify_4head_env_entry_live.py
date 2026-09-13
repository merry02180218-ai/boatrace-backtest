#!/usr/bin/env python3
from __future__ import annotations
import copy
import math
from build_4head_env_entry_live import EXPECTED, PRIMITIVES, EnvEntryBuildError, assemble
from head4_v291_downstream_inference import load_artifact, score_env_entry


def main():
    a = load_artifact()
    assert a['ENV_ENTRY']['features'] == EXPECTED
    base = {k: 1.0 for k in PRIMITIVES}
    base.update({
        'preview_comp': .543, 'relative_deg': 90.0, 'wind_speed': 2.0,
        'wind_adjust_points': 0.0, 'entry_confirmed_same': 1.0,
        'entry_course_preview': 4.0, 'has_orig': 1.0, 'has_stt': 1.0,
        'has_tkz': 1.0, 'tilt': 0.0, 'tilt_bonus': -.04,
        'v91_ex': .6, 'v91_st_corr': .6, 'v91_st_raw': .6,
        'v91_straight': .5, 'score_BASE_v91': 54.1972,
        'score_CORR20_v91': 54.1553, 'score_RAW20_v91': 53.6362,
        'score_wind_v83': 53.7379, 'history_adjust_online': .6848,
        'history_pct_online': .6712,
    })
    pre, post = .31, .27
    row = assemble(base, pre, post, a)
    assert list(row) == EXPECTED
    assert abs(row['p4_joint'] - pre*post) < 1e-15
    assert abs(row['post_x_entry_same'] - post*base['entry_confirmed_same']) < 1e-15
    p = score_env_entry(row, a)
    assert math.isfinite(p) and 0.0 < p < 1.0

    for missing in PRIMITIVES:
        b = dict(base); b.pop(missing)
        try: assemble(b, pre, post, a)
        except EnvEntryBuildError: pass
        else: raise AssertionError(f'missing primitive did not fail closed: {missing}')
    b = dict(base); b['wind_speed'] = float('nan')
    try: assemble(b, pre, post, a)
    except EnvEntryBuildError: pass
    else: raise AssertionError('non-finite primitive did not fail closed')
    bad = copy.deepcopy(a); bad['ENV_ENTRY']['features'] = list(reversed(EXPECTED))
    try: assemble(base, pre, post, bad)
    except EnvEntryBuildError: pass
    else: raise AssertionError('schema mismatch did not fail closed')
    print('HEAD4 ENV_ENTRY live assembler contract PASS')

if __name__ == '__main__': main()
