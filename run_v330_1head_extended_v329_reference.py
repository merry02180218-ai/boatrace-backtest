#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean
import json
import math

import numpy as np
import pandas as pd

from backtest import rows
import run_v326_1head_ticketaware_exhibition as v326
import run_v329_1head_multistage_exhibition as v329

ROOT = Path(__file__).resolve().parent
BASE_JA = ROOT / 'analysis_v321_1head_julaug_nonpristine_validation_race.csv'
OUT = Path('/tmp/v330')
OUT.mkdir(parents=True, exist_ok=True)
PRELOAD = date(2025, 10, 1)

# Frozen from v329 discovery. No retuning is allowed in v330.
CFG = {
    'attack_q': 0.55,
    'turn_q': 0.55,
    'env_q': 0.60,
    'bcore_q': 0.90,
    'benv_q': 0.40,
}
TH = {
    'attack': {'0.55': 0.6453333333333333},
    'turn': {'0.55': 0.5980000000000001},
    'env': {'0.6': -0.29666666666666663},
    'bcore': {'0.9': 0.8973333333333333},
    'benv': {'0.4': -0.37666666666666665},
}


def pct(n: int, d: int) -> float:
    return 100.0 * n / d if d else float('nan')


def wilson95(h: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float('nan'), float('nan'))
    z = 1.959963984540054
    p = h / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * math.sqrt((p*(1-p) + z*z/(4*n))/n) / den
    return (100*(center-half), 100*(center+half))


def metrics(df: pd.DataFrame) -> dict:
    n = len(df)
    h = int(pd.to_numeric(df['hit'], errors='coerce').fillna(0).sum()) if n else 0
    hh = int(pd.to_numeric(df['head_hit'], errors='coerce').fillna(0).sum()) if n else 0
    lo, hi = wilson95(h, n)
    hlo, hhi = wilson95(hh, n)
    return {
        'R': n,
        'H': h,
        'exact3_rate': pct(h, n),
        'exact3_wilson95_lo': lo,
        'exact3_wilson95_hi': hi,
        'head_H': hh,
        'head_rate': pct(hh, n),
        'head_wilson95_lo': hlo,
        'head_wilson95_hi': hhi,
    }


def validate_tickets(s: str) -> bool:
    ts = []
    for t in str(s).split(';'):
        p = t.strip().split('-')
        if len(p) != 3 or not all(x.isdigit() for x in p):
            return False
        tri = tuple(map(int, p))
        if tri[0] != 1:
            return False
        ts.append(tri)
    return len(ts) == 3


def load_reference() -> pd.DataFrame:
    x = pd.read_csv(BASE_JA, dtype={'race_code': str})
    x['race_code'] = x.race_code.astype(str).str.zfill(12)
    x['month'] = x.month.astype(str)
    x['hit'] = pd.to_numeric(x.hit, errors='coerce').fillna(0).astype(int)
    x['head_hit'] = pd.to_numeric(x.head_hit, errors='coerce').fillna(0).astype(int)
    if len(x) != 55 or int(x.head_hit.sum()) != 45 or int(x.hit.sum()) != 21:
        raise AssertionError(
            f'v321 identity mismatch R={len(x)} head={int(x.head_hit.sum())} hit={int(x.hit.sum())}'
        )
    if set(x.month) != {'2026-07', '2026-08'}:
        raise AssertionError(f'unexpected v321 months {sorted(set(x.month))}')
    bad = x[~x.tickets.map(validate_tickets)]
    if len(bad):
        raise AssertionError(f'invalid 3-ticket rows={len(bad)}')
    return x


def build_reference_features(base: pd.DataFrame) -> pd.DataFrame:
    wanted = set(base.race_code)
    selected_days = sorted({date(int(c[:4]), int(c[4:6]), int(c[6:8])) for c in wanted})
    selected_day_set = set(selected_days)
    last = max(selected_days)
    sums = defaultdict(list)
    allv: list[float] = []
    features: dict[str, dict] = {}

    d = PRELOAD
    while d <= last:
        ymd = d.strftime('%Y/%m/%d')
        strows = rows(f'data/previews/stt/{ymd}.csv')
        bias = v326.st_bias(sums, allv)
        if d in selected_day_set:
            tkz = v326.bycode(rows(f'data/previews/tkz/{ymd}.csv'))
            stt = v326.bycode(strows)
            orig = v326.bycode(rows(f'data/previews/original_exhibition/{ymd}.csv'))
            prefix = d.strftime('%Y%m%d')
            for code in sorted(c for c in wanted if c.startswith(prefix)):
                tr = tkz.get(code, {})
                sr = stt.get(code, {})
                orr = orig.get(code, {})
                audit = {
                    'has_tkz': int(code in tkz),
                    'has_stt': int(code in stt),
                    'has_orig': int(code in orig),
                    **v326.raw_completeness(tr, sr, orr),
                }
                audit['source_complete'] = int(all(audit[k] for k in [
                    'tkz_all6', 'stt_all6', 'orig_turn_all6',
                    'orig_straight_all6', 'orig_avg_all6'
                ]))
                ex, st, os = v326.corrected_direct(code, tkz, stt, orig, bias)
                b = base.loc[base.race_code.eq(code)].iloc[0]
                z = v326.partial_feature_row(b, ex, st, os, audit)
                z.update(audit)
                features[code] = z
        # Critical causality: ingest day-D ST only after scoring day D.
        v326.update_st(strows, sums, allv)
        d += timedelta(days=1)

    feat = pd.DataFrame.from_dict(features, orient='index')
    feat.index.name = 'race_code'
    feat = feat.reset_index()
    y = base.merge(feat, on='race_code', how='left', validate='one_to_one')

    readiness_cols = [
        'tkz_all6','stt_all6','orig_turn_all6','orig_straight_all6','orig_avg_all6'
    ]
    for c in readiness_cols:
        y[c] = pd.to_numeric(y.get(c), errors='coerce').fillna(0).astype(int)

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

    for c in [
        'one_ex','one_st','one_straight','one_orig_avg','one_turn',
        'sec_ex_mean_margin','sec_st_mean_margin',
        'third_turn_mean_margin','third_straight_mean_margin'
    ]:
        y[c] = pd.to_numeric(y.get(c), errors='coerce')

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
        .30*y.loc[m, 'sec_ex_mean_margin'] + .30*y.loc[m, 'sec_st_mean_margin'] +
        .20*y.loc[m, 'third_turn_mean_margin'] + .20*y.loc[m, 'third_straight_mean_margin']
    )
    y['best_core'] = y[['attack_core','turn_core']].max(axis=1, skipna=True)
    y['best_core_ready'] = y.attack_ready | y.turn_ready
    return y


def fixed_apply(df: pd.DataFrame) -> pd.DataFrame:
    ta = TH['attack']['0.55']
    tt = TH['turn']['0.55']
    te = TH['env']['0.6']
    tb = TH['bcore']['0.9']
    tbe = TH['benv']['0.4']
    s = df.attack_ready & df.env_ready & (df.attack_core >= ta) & (df.env_pair >= te)
    a = (~s) & df.turn_ready & df.env_ready & (df.turn_core >= tt) & (df.env_pair >= te)
    b = (~s) & (~a) & df.best_core_ready & df.env_ready & (df.best_core >= tb) & (df.env_pair >= tbe)
    out = df[s | a | b].copy()
    out['v329_grade'] = np.where(s.loc[out.index], 'S', np.where(a.loc[out.index], 'A', 'B'))
    return out


def period_report(df: pd.DataFrame, label: str) -> dict:
    p = fixed_apply(df)
    skip = df[~df.race_code.isin(set(p.race_code))].copy()
    selected_days = int(df.race_code.str[:8].nunique())
    pass_days = int(p.race_code.str[:8].nunique()) if len(p) else 0
    return {
        'label': label,
        'baseline': metrics(df),
        'readiness': {
            'attack_ready': int(df.attack_ready.sum()),
            'turn_ready': int(df.turn_ready.sum()),
            'env_ready': int(df.env_ready.sum()),
            'attack_env_ready': int((df.attack_ready & df.env_ready).sum()),
            'turn_env_ready': int((df.turn_ready & df.env_ready).sum()),
        },
        'pass': metrics(p),
        'skip': metrics(skip),
        'pass_fraction_pct': pct(len(p), len(df)),
        'selected_days': selected_days,
        'pass_days': pass_days,
        'pass_per_selected_day': (len(p)/selected_days if selected_days else float('nan')),
        'grades': {g: metrics(p[p.v329_grade.eq(g)]) for g in ['S','A','B']},
    }


def main() -> None:
    # Rebuild pristine-development/fwd cohort only to verify that fixed v329 behavior has not drifted.
    old = v329.build_dataset().copy()
    oldpass = fixed_apply(old)
    if len(old) != 345 or int(old.hit.sum()) != 139 or int(old.head_hit.sum()) != 290:
        raise AssertionError('v329 base drift')
    if len(oldpass) != 66 or int(oldpass.hit.sum()) != 30 or int(oldpass.head_hit.sum()) != 59:
        raise AssertionError(
            f'v329 fixed-pass drift R={len(oldpass)} H={int(oldpass.hit.sum())} head={int(oldpass.head_hit.sum())}'
        )

    base = load_reference()
    ext = build_reference_features(base)
    if len(ext) != 55 or int(ext.hit.sum()) != 21 or int(ext.head_hit.sum()) != 45:
        raise AssertionError('extended cohort drift after feature merge')
    ext.to_csv(OUT/'analysis_v330_julaug_features.csv', index=False)

    reports = {}
    for month in ['2026-07','2026-08']:
        reports[month] = period_report(ext[ext.month.eq(month)].copy(), month)
    reports['JUL_AUG'] = period_report(ext.copy(), 'JUL_AUG')

    # Per-month fixed-v329 descriptive table for the full Feb-Aug view.
    monthly_rows = []
    for month in ['2026-02','2026-03','2026-04','2026-05','2026-06']:
        z = old[old.month.astype(str).eq(month)].copy()
        r = period_report(z, month)
        monthly_rows.append({
            'month': month, 'pristine_status': 'PRE_JUL',
            'base_R': r['baseline']['R'], 'base_exact3': r['baseline']['H'],
            'base_exact3_rate': r['baseline']['exact3_rate'],
            'base_head': r['baseline']['head_H'], 'base_head_rate': r['baseline']['head_rate'],
            'pass_R': r['pass']['R'], 'pass_fraction_pct': r['pass_fraction_pct'],
            'pass_exact3': r['pass']['H'], 'pass_exact3_rate': r['pass']['exact3_rate'],
            'pass_head': r['pass']['head_H'], 'pass_head_rate': r['pass']['head_rate'],
            'S_R': r['grades']['S']['R'], 'A_R': r['grades']['A']['R'], 'B_R': r['grades']['B']['R'],
        })
    for month in ['2026-07','2026-08']:
        r = reports[month]
        monthly_rows.append({
            'month': month, 'pristine_status': 'NON_PRISTINE_REFERENCE',
            'base_R': r['baseline']['R'], 'base_exact3': r['baseline']['H'],
            'base_exact3_rate': r['baseline']['exact3_rate'],
            'base_head': r['baseline']['head_H'], 'base_head_rate': r['baseline']['head_rate'],
            'pass_R': r['pass']['R'], 'pass_fraction_pct': r['pass_fraction_pct'],
            'pass_exact3': r['pass']['H'], 'pass_exact3_rate': r['pass']['exact3_rate'],
            'pass_head': r['pass']['head_H'], 'pass_head_rate': r['pass']['head_rate'],
            'S_R': r['grades']['S']['R'], 'A_R': r['grades']['A']['R'], 'B_R': r['grades']['B']['R'],
        })
    monthly = pd.DataFrame(monthly_rows)
    monthly.to_csv(OUT/'analysis_v330_monthly.csv', index=False)

    extpass = fixed_apply(ext)
    combined_base_R = len(old) + len(ext)
    combined_base_H = int(old.hit.sum()) + int(ext.hit.sum())
    combined_base_head = int(old.head_hit.sum()) + int(ext.head_hit.sum())
    combined_pass_R = len(oldpass) + len(extpass)
    combined_pass_H = int(oldpass.hit.sum()) + int(extpass.hit.sum())
    combined_pass_head = int(oldpass.head_hit.sum()) + int(extpass.head_hit.sum())

    aggregate = {
        'FEB_JUN': {
            'baseline': metrics(old),
            'pass': metrics(oldpass),
            'pass_fraction_pct': pct(len(oldpass), len(old)),
        },
        'JUL_AUG_NON_PRISTINE_REFERENCE': reports['JUL_AUG'],
        'FEB_AUG_DESCRIPTIVE_ONLY': {
            'baseline': {
                'R': combined_base_R, 'H': combined_base_H,
                'exact3_rate': pct(combined_base_H, combined_base_R),
                'head_H': combined_base_head, 'head_rate': pct(combined_base_head, combined_base_R),
            },
            'pass': {
                'R': combined_pass_R, 'H': combined_pass_H,
                'exact3_rate': pct(combined_pass_H, combined_pass_R),
                'head_H': combined_pass_head, 'head_rate': pct(combined_pass_head, combined_pass_R),
            },
            'pass_fraction_pct': pct(combined_pass_R, combined_base_R),
            'warning': 'Contains NON-PRISTINE Jul/Aug; descriptive only, never promotion evidence.',
        },
    }

    result = {
        'fixed_config': CFG,
        'fixed_thresholds': TH,
        'reference_identity': {'R':55,'head':45,'exact3':21},
        'reports': reports,
        'aggregate': aggregate,
        'september_outcomes': 'UNREAD',
        'promotion_eligible': False,
        'reason': 'v330 is a fixed-rule NON-PRISTINE Jul/Aug robustness/volume stress test only.',
    }
    (OUT/'result_v330.json').write_text(json.dumps(result, indent=2, sort_keys=True), encoding='utf-8')

    lines = [
        '# v330 extended v329 robustness / volume audit', '',
        '- v329 formulas/config/thresholds are frozen; no retuning occurred.',
        '- Jul/Aug are NON-PRISTINE reference only and cannot promote or tune the model.',
        '- September outcomes remain UNREAD.',
        '- Reconciled Jul/Aug base: **55R / head45 / exact3 21**.',
        '- Reconciled Feb-Jun fixed v329 PASS: **66R / head59 / exact3 30**.', '',
    ]
    for key in ['2026-07','2026-08','JUL_AUG']:
        r = reports[key]
        b = r['baseline']; p = r['pass']; s = r['skip']
        lines += [
            f'## {key}',
            f"- baseline: R={b['R']} exact3={b['H']} ({b['exact3_rate']:.2f}%) head={b['head_H']} ({b['head_rate']:.2f}%)",
            f"- readiness attack/turn/env={r['readiness']['attack_ready']}/{r['readiness']['turn_ready']}/{r['readiness']['env_ready']}",
            f"- PASS: R={p['R']} ({r['pass_fraction_pct']:.2f}% of base) exact3={p['H']} ({p['exact3_rate']:.2f}%, Wilson95 {p['exact3_wilson95_lo']:.2f}-{p['exact3_wilson95_hi']:.2f}%) head={p['head_H']} ({p['head_rate']:.2f}%)",
            f"- SKIP: R={s['R']} exact3={s['H']} ({s['exact3_rate']:.2f}%) head={s['head_H']} ({s['head_rate']:.2f}%)",
            f"- grades S/A/B={r['grades']['S']['R']}/{r['grades']['A']['R']}/{r['grades']['B']['R']}",
            f"- selected days={r['selected_days']}, PASS days={r['pass_days']}, PASS/selected-day={r['pass_per_selected_day']:.3f}", '',
        ]
    a = aggregate['FEB_JUN']; e = aggregate['JUL_AUG_NON_PRISTINE_REFERENCE']; c = aggregate['FEB_AUG_DESCRIPTIVE_ONLY']
    lines += [
        '## Volume comparison',
        f"- Feb-Jun: PASS {a['pass']['R']}/{a['baseline']['R']} = {a['pass_fraction_pct']:.2f}%; exact3 {a['pass']['H']}/{a['pass']['R']} = {a['pass']['exact3_rate']:.2f}%; head {a['pass']['head_H']}/{a['pass']['R']} = {a['pass']['head_rate']:.2f}%.",
        f"- Jul-Aug NON-PRISTINE: PASS {e['pass']['R']}/{e['baseline']['R']} = {e['pass_fraction_pct']:.2f}%; exact3 {e['pass']['H']}/{e['pass']['R']} = {e['pass']['exact3_rate']:.2f}%; head {e['pass']['head_H']}/{e['pass']['R']} = {e['pass']['head_rate']:.2f}%.",
        f"- Feb-Aug descriptive: PASS {c['pass']['R']}/{c['baseline']['R']} = {c['pass_fraction_pct']:.2f}%; exact3 {c['pass']['H']}/{c['pass']['R']} = {c['pass']['exact3_rate']:.2f}%; head {c['pass']['head_H']}/{c['pass']['R']} = {c['pass']['head_rate']:.2f}%.",
        '- Do not use the combined line for promotion because it includes NON-PRISTINE Jul/Aug.',
    ]
    (OUT/'summary_v330.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines), flush=True)


if __name__ == '__main__':
    main()
