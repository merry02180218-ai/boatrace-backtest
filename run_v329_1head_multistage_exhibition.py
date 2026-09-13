#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import itertools
import json
import numpy as np
import pandas as pd

import run_v326_1head_ticketaware_exhibition as v326

OUT = Path('/tmp/v329')
OUT.mkdir(parents=True, exist_ok=True)

CORE_Q = [0.55, 0.65, 0.75]
ENV_Q = [0.40, 0.50, 0.60]
B_CORE_Q = [0.80, 0.90]
B_ENV_Q = [0.40, 0.50]


def pct(n, d):
    return 100.0 * n / d if d else float('nan')


def metrics(df):
    n = len(df)
    h = int(df.hit.sum()) if n else 0
    hh = int(df.head_hit.sum()) if n else 0
    return {
        'R': n,
        'H': h,
        'exact3_rate': pct(h, n),
        'head_H': hh,
        'head_rate': pct(hh, n),
    }


def qval(s, q):
    x = pd.to_numeric(s, errors='coerce').dropna()
    if x.empty:
        raise RuntimeError(f'empty quantile source q={q}')
    return float(np.quantile(x.to_numpy(float), q))


def build_dataset():
    y = v326.build_dataset().copy()
    y['race_code'] = y.race_code.astype(str).str.zfill(12)
    y['hit'] = pd.to_numeric(y.hit, errors='coerce').fillna(0).astype(int)
    y['head_hit'] = pd.to_numeric(y.head_hit, errors='coerce').fillna(0).astype(int)
    if len(y) != 345 or int(y.hit.sum()) != 139 or int(y.head_hit.sum()) != 290:
        raise AssertionError('frozen v320 identity drift before v329')

    # Raw-source route readiness. Never infer availability from neutral rank=0.5.
    y['attack_ready'] = (
        y.tkz_all6.eq(1) & y.stt_all6.eq(1) &
        y.orig_straight_all6.eq(1) & y.orig_avg_all6.eq(1)
    )
    y['turn_ready'] = (
        y.tkz_all6.eq(1) & y.stt_all6.eq(1) &
        y.orig_turn_all6.eq(1) & y.orig_avg_all6.eq(1)
    )
    y['env_ready'] = (
        y.tkz_all6.eq(1) & y.stt_all6.eq(1) &
        y.orig_turn_all6.eq(1) & y.orig_straight_all6.eq(1)
    )

    y['attack_core'] = np.nan
    m = y.attack_ready
    y.loc[m, 'attack_core'] = (
        .30*y.loc[m, 'one_ex'] + .30*y.loc[m, 'one_st'] +
        .23*y.loc[m, 'one_straight'] + .17*y.loc[m, 'one_orig_avg']
    )

    y['turn_core'] = np.nan
    m = y.turn_ready
    y.loc[m, 'turn_core'] = (
        .21*y.loc[m, 'one_ex'] + .27*y.loc[m, 'one_st'] +
        .34*y.loc[m, 'one_turn'] + .18*y.loc[m, 'one_orig_avg']
    )

    y['env_pair'] = np.nan
    m = y.env_ready
    y.loc[m, 'env_pair'] = (
        .30*y.loc[m, 'sec_ex_mean_margin'] +
        .30*y.loc[m, 'sec_st_mean_margin'] +
        .20*y.loc[m, 'third_turn_mean_margin'] +
        .20*y.loc[m, 'third_straight_mean_margin']
    )

    y['best_core'] = y[['attack_core', 'turn_core']].max(axis=1, skipna=True)
    y['best_core_ready'] = y.attack_ready | y.turn_ready

    needed = ['attack_core','turn_core','env_pair','best_core']
    for c in needed:
        y[c] = pd.to_numeric(y[c], errors='coerce')

    y.to_csv(OUT/'analysis_v329_multistage_dataset.csv', index=False)
    return y


def freeze_threshold_tables(disc):
    a = disc[disc.attack_ready & disc.env_ready]
    t = disc[disc.turn_ready & disc.env_ready]
    b = disc[disc.best_core_ready & disc.env_ready]
    if len(a) < 20 or len(t) < 20 or len(b) < 20:
        raise RuntimeError(f'insufficient discovery readiness attack={len(a)} turn={len(t)} best={len(b)}')

    return {
        'attack': {str(q): qval(a.attack_core, q) for q in CORE_Q},
        'turn': {str(q): qval(t.turn_core, q) for q in CORE_Q},
        'env': {str(q): qval(disc.loc[disc.env_ready, 'env_pair'], q) for q in ENV_Q},
        'bcore': {str(q): qval(b.best_core, q) for q in B_CORE_Q},
        'benv': {str(q): qval(disc.loc[disc.env_ready, 'env_pair'], q) for q in B_ENV_Q},
    }


def apply_config(df, cfg, th):
    ta = th['attack'][str(cfg['attack_q'])]
    tt = th['turn'][str(cfg['turn_q'])]
    te = th['env'][str(cfg['env_q'])]
    tb = th['bcore'][str(cfg['bcore_q'])]
    tbe = th['benv'][str(cfg['benv_q'])]

    s = df.attack_ready & df.env_ready & (df.attack_core >= ta) & (df.env_pair >= te)
    a = (~s) & df.turn_ready & df.env_ready & (df.turn_core >= tt) & (df.env_pair >= te)
    b = (~s) & (~a) & df.best_core_ready & df.env_ready & (df.best_core >= tb) & (df.env_pair >= tbe)

    out = df[s | a | b].copy()
    if out.empty:
        out['v329_grade'] = pd.Series(dtype=str)
        return out
    out['v329_grade'] = np.where(s.loc[out.index], 'S', np.where(a.loc[out.index], 'A', 'B'))
    return out


def route_metrics(df):
    out = {'ALL': metrics(df)}
    if 'v329_grade' in df:
        for g in ['S','A','B']:
            out[g] = metrics(df[df.v329_grade.eq(g)])
    return out


def search_configs(disc, val, th):
    db = metrics(disc)
    vb = metrics(val)
    rows = []
    configs = []
    for aq,tq,eq,bq,beq in itertools.product(CORE_Q, CORE_Q, ENV_Q, B_CORE_Q, B_ENV_Q):
        cfg = {'attack_q':aq,'turn_q':tq,'env_q':eq,'bcore_q':bq,'benv_q':beq}
        dpass = apply_config(disc, cfg, th)
        vpass = apply_config(val, cfg, th)
        dm = metrics(dpass); vm = metrics(vpass)
        qualifies = (
            dm['R'] >= 25 and vm['R'] >= 15 and
            dm['exact3_rate'] >= db['exact3_rate'] and
            vm['exact3_rate'] >= vb['exact3_rate']
        )
        row = {**cfg, 'qualifies': int(qualifies),
               **{f'disc_{k}':v for k,v in dm.items()},
               **{f'val_{k}':v for k,v in vm.items()}}
        rows.append(row)
        if qualifies:
            configs.append((cfg, dm, vm))

    tab = pd.DataFrame(rows)
    tab.to_csv(OUT/'analysis_v329_route_grid.csv', index=False)
    if not configs:
        return tab, None

    # Predeclared preference: validation coverage, validation exact3, discovery exact3.
    configs.sort(key=lambda z:(z[2]['R'], z[2]['exact3_rate'], z[1]['exact3_rate']), reverse=True)
    return tab, configs[0][0]


def main():
    y = build_dataset()
    disc = y[y.month.astype(str).isin(['2026-02','2026-03','2026-04'])].copy()
    val = y[y.month.astype(str).eq('2026-05')].copy()
    fwd = y[y.month.astype(str).eq('2026-06')].copy()

    if len(disc)+len(val)+len(fwd) != 345:
        raise AssertionError(f'unexpected month split {len(disc)}+{len(val)}+{len(fwd)}')

    th = freeze_threshold_tables(disc)
    (OUT/'v329_thresholds.json').write_text(json.dumps(th, indent=2, sort_keys=True), encoding='utf-8')
    grid, best = search_configs(disc, val, th)

    db, vb, fb = metrics(disc), metrics(val), metrics(fwd)
    readiness = {
        p: {
            'R': len(z),
            'attack_ready': int(z.attack_ready.sum()),
            'turn_ready': int(z.turn_ready.sum()),
            'env_ready': int(z.env_ready.sum()),
            'attack_env_ready': int((z.attack_ready & z.env_ready).sum()),
            'turn_env_ready': int((z.turn_ready & z.env_ready).sum()),
        }
        for p,z in [('FEB_APR',disc),('MAY',val),('JUNE',fwd)]
    }

    lines = [
        '# v329 1-head multistage exhibition judgement', '',
        '- frozen identity: 345 selected / 290 head / 139 exact3',
        '- tickets unchanged; v329 is downstream PASS/SKIP grading only.',
        '- Jul/Aug unopened for tuning/performance; September outcomes unread.',
        f'- readiness: `{json.dumps(readiness, ensure_ascii=False)}`',
        f'- discovery baseline: `{db}`',
        f'- May baseline: `{vb}`',
        f'- June baseline: `{fb}`',
        f'- frozen discovery thresholds: `{json.dumps(th, sort_keys=True)}`',
    ]

    if best is None:
        lines += [
            '- FROZEN_CONFIG: NONE (no predeclared S/A/B grid configuration passed Feb-Apr + May support constraints)',
            '- June PASS not searched/optimized.',
            '- FORWARD_SUPPORTED=False',
            '- PROMOTE=False',
        ]
        result = {
            'best': None, 'discovery_baseline': db, 'may_baseline': vb,
            'june_baseline': fb, 'readiness': readiness,
            'FORWARD_SUPPORTED': False, 'PROMOTE': False,
        }
    else:
        dpass = apply_config(disc, best, th)
        vpass = apply_config(val, best, th)
        jpass = apply_config(fwd, best, th)
        jskip = fwd[~fwd.race_code.isin(set(jpass.race_code))].copy()
        dm, vm, jm, jsm = metrics(dpass), metrics(vpass), metrics(jpass), metrics(jskip)
        forward = bool(
            jm['R'] >= 15 and
            jm['exact3_rate'] > fb['exact3_rate'] and
            jm['head_rate'] >= fb['head_rate'] - 5.0
        )
        promote = forward
        grades = {
            'FEB_APR': route_metrics(dpass),
            'MAY': route_metrics(vpass),
            'JUNE': route_metrics(jpass),
        }
        chosen = y.copy()
        chosen['v329_pass'] = 0
        chosen['v329_grade'] = ''
        for part in [dpass,vpass,jpass]:
            chosen.loc[chosen.race_code.isin(part.race_code), 'v329_pass'] = 1
            mp = dict(zip(part.race_code, part.v329_grade))
            chosen.loc[chosen.race_code.isin(mp), 'v329_grade'] = chosen.loc[chosen.race_code.isin(mp), 'race_code'].map(mp)
        chosen.to_csv(OUT/'analysis_v329_frozen_selection.csv', index=False)
        lines += [
            f'- FROZEN_CONFIG: `{json.dumps(best, sort_keys=True)}`',
            f'- Feb-Apr PASS: `{dm}`',
            f'- May PASS: `{vm}`',
            f'- June PASS: `{jm}`',
            f'- June SKIP: `{jsm}`',
            f'- grade breakdown: `{json.dumps(grades, sort_keys=True)}`',
            f'- FORWARD_SUPPORTED={forward}',
            f'- PROMOTE={promote}',
        ]
        result = {
            'best': best, 'thresholds': th,
            'discovery_baseline': db, 'may_baseline': vb, 'june_baseline': fb,
            'discovery_pass': dm, 'may_pass': vm, 'june_pass': jm, 'june_skip': jsm,
            'grade_breakdown': grades, 'readiness': readiness,
            'FORWARD_SUPPORTED': forward, 'PROMOTE': promote,
        }

    (OUT/'result_v329.json').write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')
    (OUT/'summary_v329.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines), flush=True)


if __name__ == '__main__':
    main()
