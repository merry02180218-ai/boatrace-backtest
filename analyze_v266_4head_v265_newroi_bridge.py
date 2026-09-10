#!/usr/bin/env python3
"""v266: v265 4-head consensus selectors -> exact 10k Dutch new-ROI bridge.

Selector rules are frozen from the v265 retrospective Apr-Jun audit before this
script evaluates trifecta settlement. Jul/Aug are excluded. Ticket opponents
use the existing prior-only v96-lineage pair rank. We compare fixed Top-N and a
single composite-odds target policy; no result is used to choose a ticket.

IMPORTANT: Apr-Jun does not have a complete contemporaneous LIVE odds-snapshot
archive. load_odds() is therefore an archived-odds development proxy. The
settlement math is the current new ROI definition (10,000 yen total per race,
inverse-odds Dutch, 100-yen Hamilton rounding, misses return 0), but the result
is NOT formal pristine/live OOS ROI.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'analysis_v264_4head_feature_exhaustive.csv'
OUT = ROOT / 'analysis_v266_4head_v265_newroi_bridge.csv'
DETAIL = ROOT / 'analysis_v266_4head_v265_newroi_detail.csv'
SUM = ROOT / 'summary_v266_4head_v265_newroi_bridge.md'
BANK = 10000
NS = tuple(range(2, 21))
TARGETS = np.arange(7.0, 14.01, 0.5)

# Frozen directly from v265 output; all were selected without Jul/Aug.
SELECTORS = {
    'V265_200_TOP': {
        'members': ('ENV_ENTRY', 'OPP_CONTEXT', 'ALL_SAFE_HGB'),
        'weights': (0.50, 0.20, 0.30), 'cut': 0.204598,
    },
    'V265_150_TOP': {
        'members': ('ENV_ENTRY', 'OPP_CONTEXT', 'ALL_SAFE_HGB'),
        'weights': (0.40, 0.40, 0.20), 'cut': 0.241513,
    },
    'V265_150_FLOOR': {
        'members': ('ENV_ENTRY', 'OPP_CONTEXT', 'ST_3HEAD_ANALOG'),
        'weights': (0.40, 0.40, 0.20), 'cut': 0.258712,
    },
    'V265_200_SIMPLE': {
        'members': ('ENV_ENTRY', 'OPP_CONTEXT'),
        'weights': (0.30, 0.70), 'cut': 0.214622,
    },
}


def load_selectors():
    d = pd.read_csv(SRC, dtype={'race_code': str})
    d['race_code'] = d.race_code.astype(str).str.zfill(12)
    d = d[(d.month <= '2026-06') & (~d.month.isin(['2026-07', '2026-08']))].copy()
    w = d.pivot_table(
        index=['month', 'date', 'race_code', 'y4'], columns='variant', values='p', aggfunc='last'
    ).reset_index()
    out = []
    for name, cfg in SELECTORS.items():
        z = w.dropna(subset=list(cfg['members'])).copy()
        score = np.zeros(len(z), dtype=float)
        for member, weight in zip(cfg['members'], cfg['weights']):
            score += weight * z[member].to_numpy(float)
        z['selector'] = name
        z['score'] = score
        z = z[z.score >= cfg['cut']].copy()
        out.append(z[['selector', 'month', 'date', 'race_code', 'y4', 'score']])
    return pd.concat(out, ignore_index=True)


def precompute(selected):
    rs = c4.read()
    orders = v251.pair_orders(rs)
    actual = v251.actual_map(rs)
    od = load_odds()
    oi = od.set_index('race_code', drop=False) if not od.empty else pd.DataFrame()
    rows = []
    for _, r in selected.iterrows():
        code = str(r.race_code).zfill(12)
        order = orders.get((str(r.date), code))
        a = actual.get((str(r.date), code))
        if not order or not a or a[3] != 1 or code not in oi.index:
            continue
        o = oi.loc[code]
        o = o.iloc[-1] if isinstance(o, pd.DataFrame) else o
        choices = []
        for n in NS:
            tickets = [f'4-{x}-{y}' for x, y in order[:n]]
            s = v251.settle(code, tickets, o, a)
            if s is None:
                continue
            hit, ret, comp = s
            choices.append((n, int(hit), float(ret), float(comp)))
        if not choices:
            continue
        rows.append({
            'selector': r.selector, 'month': r.month, 'date': r.date,
            'race_code': code, 'score': float(r.score), 'y4': int(r.y4),
            'choices': choices,
        })
    return rows


def aggregate(vals, selector, policy, selected_r):
    q = pd.DataFrame(vals)
    if q.empty:
        return None
    cost = len(q) * BANK
    ret = q.return_yen.sum()
    mm = []
    for mon, g in q.groupby('month'):
        c = len(g) * BANK
        rr = g.return_yen.sum()
        mm.append((mon, len(g), 100 * rr / c if c else np.nan))
    min_month_roi = min(x[2] for x in mm) if mm else np.nan
    return {
        'selector': selector, 'policy': policy,
        'selected_R': int(selected_r), 'settled_R': int(len(q)),
        'coverage_pct': 100 * len(q) / selected_r if selected_r else np.nan,
        'head4_rate_pct': 100 * q.y4.mean(),
        'trifecta_hits': int(q.hit.sum()),
        'trifecta_hit_rate_pct': 100 * q.hit.mean(),
        'avg_n': q.n.mean(), 'avg_comp_odds': q.comp.mean(),
        'cost_yen': int(cost), 'return_yen': float(ret),
        'profit_yen': float(ret - cost), 'new_roi_pct': 100 * ret / cost,
        'min_month_roi_pct': float(min_month_roi),
        'month_roi': ';'.join(f'{m}:{n}R/{roi:.2f}%' for m, n, roi in mm),
    }


def main():
    selected = load_selectors()
    pre = precompute(selected)
    selected_counts = selected.groupby('selector').size().to_dict()
    rows = []
    details = []

    for selector in SELECTORS:
        rr = [x for x in pre if x['selector'] == selector]
        # Fixed Top-N policies. Skip only races lacking the complete odds needed
        # for that N; coverage is reported so missing archived odds stay visible.
        for n in NS:
            vals = []
            for r in rr:
                choice = next(((h, rt, c) for nn, h, rt, c in r['choices'] if nn == n), None)
                if choice is None:
                    continue
                hit, ret, comp = choice
                vals.append({'month': r['month'], 'race_code': r['race_code'], 'y4': r['y4'],
                             'n': n, 'hit': hit, 'return_yen': ret, 'comp': comp})
            a = aggregate(vals, selector, f'FIXED_N={n}', selected_counts.get(selector, 0))
            if a:
                rows.append(a)

        # Composite-odds target chooses N from available odds only, never from result.
        for target in TARGETS:
            vals = []
            for r in rr:
                n, hit, ret, comp = min(r['choices'], key=lambda x: (abs(x[3] - target), x[0]))
                vals.append({'month': r['month'], 'race_code': r['race_code'], 'y4': r['y4'],
                             'n': n, 'hit': hit, 'return_yen': ret, 'comp': comp})
                details.append({'selector': selector, 'target': target, 'month': r['month'],
                                'race_code': r['race_code'], 'score': r['score'], 'n': n,
                                'hit': hit, 'return_yen': ret, 'comp_odds': comp, 'y4': r['y4']})
            a = aggregate(vals, selector, f'COMP_TARGET={target:.1f}', selected_counts.get(selector, 0))
            if a:
                rows.append(a)

    o = pd.DataFrame(rows)
    o['robust_roi'] = np.minimum(o.new_roi_pct, o.min_month_roi_pct)
    o = o.sort_values(['robust_roi', 'new_roi_pct', 'settled_R'], ascending=False)
    o.to_csv(OUT, index=False)
    pd.DataFrame(details).to_csv(DETAIL, index=False)

    L = [
        '# v266 4-head v265 selector -> new ROI bridge', '',
        '- Selectors: frozen from v265 Apr-Jun consensus audit; Jul/Aug excluded.',
        '- Settlement: exactly 10,000 yen per betting race, inverse-odds Dutch, 100-yen Hamilton rounding; misses return 0.',
        '- Opponent order: prior-only v96-lineage 4-x-y pair ranking.',
        '- Odds: archived historical odds proxy, not a complete contemporaneous pre-deadline LIVE snapshot archive.',
        '- Therefore these are development/model-selection ROI numbers, NOT formal pristine/live OOS ROI.', '',
        '## Best policies by minimum(overall ROI, monthly-floor ROI)',
        '|selector|policy|selected|settled|coverage|4-head|3連単 hit|avgN|avg comp|return|profit|new ROI|min month ROI|month ROI|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for _, r in o.head(40).iterrows():
        L.append(
            f'|{r.selector}|{r.policy}|{int(r.selected_R)}|{int(r.settled_R)}|{r.coverage_pct:.1f}%|'
            f'{r.head4_rate_pct:.2f}%|{r.trifecta_hit_rate_pct:.2f}%|{r.avg_n:.2f}|{r.avg_comp_odds:.3f}|'
            f'{r.return_yen:.0f}|{r.profit_yen:+.0f}|{r.new_roi_pct:.2f}%|{r.min_month_roi_pct:.2f}%|{r.month_roi}|'
        )
    L += ['', '## Per-selector best robust policy']
    for selector, g in o.groupby('selector'):
        r = g.sort_values(['robust_roi', 'new_roi_pct'], ascending=False).iloc[0]
        L.append(
            f'- {selector}: {r.policy}, {int(r.settled_R)}R, 3連単hit {r.trifecta_hit_rate_pct:.2f}%, '
            f'new ROI {r.new_roi_pct:.2f}%, monthly floor {r.min_month_roi_pct:.2f}%.'
        )
    L += ['', '## Decision',
          '- Do not treat the best retrospective ROI as the live model ROI.',
          '- Freeze a selector + ticket policy only after checking robustness; formal ROI starts on unseen September races with pre-deadline odds snapshots.', '']
    SUM.write_text('\n'.join(L), encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
