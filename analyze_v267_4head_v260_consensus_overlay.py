#!/usr/bin/env python3
"""v267: does the v264/v265 consensus improve the v260 4-head selector?

Freeze the existing v260 selector and ticket policy first:
  PRE >= 0.28, POST >= 0.25, composite-odds target = 10.5.
Then apply only a small set of consensus ranking overlays from v265 and measure
exact current new ROI.  2026-07/08 are explicitly excluded.

This is development/model-selection evidence. Historical odds are the archived
proxy used by v251/v260, not a complete contemporaneous LIVE pre-deadline
snapshot archive. Formal OOS ROI must be measured prospectively in September.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

import analyze_v251_4head_newroi_bridge as v251
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
from analyze_v205_3head_operational_replay import load_odds

ROOT = Path(__file__).resolve().parent
P4 = ROOT / 'analysis_v250_4head_rebuild_baseline.csv'
F4 = ROOT / 'analysis_v264_4head_feature_exhaustive.csv'
OUT = ROOT / 'analysis_v267_4head_v260_consensus_overlay.csv'
SUM = ROOT / 'summary_v267_4head_v260_consensus_overlay.md'
BANK = 10000
PRE_CUT = 0.28
POST_CUT = 0.25
COMP_TARGET = 10.5
NS = tuple(range(2, 21))
KEEP_FRACS = (1.00, 0.90, 0.80, 0.70, 0.60, 0.50)

CONSENSUS = {
    'V265_200_TOP_SCORE': (('ENV_ENTRY','OPP_CONTEXT','ALL_SAFE_HGB'), (0.50,0.20,0.30)),
    'V265_150_TOP_SCORE': (('ENV_ENTRY','OPP_CONTEXT','ALL_SAFE_HGB'), (0.40,0.40,0.20)),
    'V265_200_SIMPLE_SCORE': (('ENV_ENTRY','OPP_CONTEXT'), (0.30,0.70)),
    'ENV_ENTRY_ONLY': (('ENV_ENTRY',), (1.0,)),
    'OPP_CONTEXT_ONLY': (('OPP_CONTEXT',), (1.0,)),
}


def selector_frame():
    p = pd.read_csv(P4, dtype={'race_code': str})
    p['race_code'] = p.race_code.astype(str).str.zfill(12)
    w = p.pivot_table(index=['date','month','race_code'], columns='variant', values='p4head', aggfunc='last').reset_index()
    w = w[(w.month <= '2026-06') & (~w.month.isin(['2026-07','2026-08']))].copy()
    w = w[(w.PRE >= PRE_CUT) & (w.POST >= POST_CUT)].copy()

    f = pd.read_csv(F4, dtype={'race_code': str})
    f['race_code'] = f.race_code.astype(str).str.zfill(12)
    f = f[(f.month <= '2026-06') & (~f.month.isin(['2026-07','2026-08']))].copy()
    fw = f.pivot_table(index=['date','month','race_code','y4'], columns='variant', values='p', aggfunc='last').reset_index()
    z = w.merge(fw, on=['date','month','race_code'], how='inner')
    return z


def settle_rows(z):
    rs = c4.read()
    orders = v251.pair_orders(rs)
    actual = v251.actual_map(rs)
    od = load_odds()
    oi = od.set_index('race_code', drop=False) if not od.empty else pd.DataFrame()
    rows = []
    for _, r in z.iterrows():
        code = str(r.race_code).zfill(12)
        order = orders.get((str(r.date), code))
        a = actual.get((str(r.date), code))
        if not order or not a or a[3] != 1 or code not in oi.index:
            continue
        o = oi.loc[code]
        o = o.iloc[-1] if isinstance(o, pd.DataFrame) else o
        ch = []
        for n in NS:
            tickets = [f'4-{x}-{y}' for x, y in order[:n]]
            s = v251.settle(code, tickets, o, a)
            if s is not None:
                hit, ret, comp = s
                ch.append((n, int(hit), float(ret), float(comp)))
        if not ch:
            continue
        n, hit, ret, comp = min(ch, key=lambda x: (abs(x[3] - COMP_TARGET), x[0]))
        rec = {
            'date': r.date, 'month': r.month, 'race_code': code,
            'PRE': float(r.PRE), 'POST': float(r.POST), 'y4': int(r.y4),
            'n': n, 'hit': hit, 'return_yen': ret, 'comp_odds': comp,
        }
        for name, (members, weights) in CONSENSUS.items():
            if all(m in r.index and pd.notna(r[m]) for m in members):
                rec[name] = float(sum(float(r[m])*w for m, w in zip(members, weights)))
            else:
                rec[name] = np.nan
        rows.append(rec)
    return pd.DataFrame(rows)


def summarize(q, overlay, keep_frac, base_r):
    if q.empty:
        return None
    cost = len(q)*BANK
    ret = float(q.return_yen.sum())
    mm = []
    for mon, g in q.groupby('month'):
        c = len(g)*BANK; rr = float(g.return_yen.sum())
        mm.append((mon, len(g), 100*rr/c if c else np.nan, 100*g.hit.mean(), 100*g.y4.mean()))
    return {
        'overlay': overlay, 'keep_frac': keep_frac,
        'base_settled_R': int(base_r), 'R': int(len(q)),
        'head4_rate_pct': 100*q.y4.mean(), 'trifecta_hit_pct': 100*q.hit.mean(),
        'avg_n': q.n.mean(), 'avg_comp_odds': q.comp_odds.mean(),
        'cost_yen': int(cost), 'return_yen': ret, 'profit_yen': ret-cost,
        'new_roi_pct': 100*ret/cost,
        'min_month_roi_pct': min(x[2] for x in mm) if mm else np.nan,
        'month_detail': ';'.join(f'{m}:{n}R ROI{roi:.2f}% hit{hit:.2f}% head{head:.2f}%' for m,n,roi,hit,head in mm),
    }


def main():
    z = selector_frame()
    settled = settle_rows(z)
    if settled.empty:
        raise RuntimeError('no settled v260-base rows')
    rows = []

    # Frozen v260 benchmark: no new overlay.
    b = summarize(settled.copy(), 'NONE_V260_BASE', 1.0, len(settled))
    rows.append(b)

    for name in CONSENSUS:
        q = settled[settled[name].notna()].sort_values([name,'race_code'], ascending=[False,True]).copy()
        if q.empty:
            continue
        for frac in KEEP_FRACS:
            n = max(1, int(np.ceil(len(q)*frac)))
            s = q.head(n).copy()
            rec = summarize(s, name, frac, len(settled))
            if rec:
                rec['score_cut'] = float(s[name].min())
                rows.append(rec)

    o = pd.DataFrame(rows)
    if 'score_cut' not in o:
        o['score_cut'] = np.nan
    o['robust_roi'] = np.minimum(o.new_roi_pct, o.min_month_roi_pct)
    o = o.sort_values(['robust_roi','new_roi_pct','R'], ascending=False)
    o.to_csv(OUT, index=False)

    L = [
        '# v267 4-head: v260 selector + v265 consensus overlay', '',
        f'- Frozen base selector: PRE>={PRE_CUT:.2f}, POST>={POST_CUT:.2f}.',
        f'- Frozen ticket policy: 4-x-y prior-only v96 pair rank; N chosen only by composite odds nearest {COMP_TARGET:.1f}.',
        '- Exact new ROI settlement: 10,000 yen/race inverse-odds Dutch, 100-yen Hamilton rounding, misses return 0.',
        '- Jul/Aug explicitly excluded. Consensus inputs are v264 walk-forward predictions.',
        '- Archived historical odds proxy only; retrospective/model-selection evidence, NOT formal pristine/live OOS ROI.', '',
        '## Benchmark and overlays',
        '|overlay|keep|score cut|R|4-head|3連単 hit|avgN|avg comp|return|profit|new ROI|min month ROI|month detail|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|',
    ]
    for _, r in o.iterrows():
        cut = '--' if pd.isna(r.get('score_cut')) else f'{r.score_cut:.6f}'
        L.append(
            f'|{r.overlay}|{100*r.keep_frac:.0f}%|{cut}|{int(r.R)}|{r.head4_rate_pct:.2f}%|'
            f'{r.trifecta_hit_pct:.2f}%|{r.avg_n:.2f}|{r.avg_comp_odds:.3f}|{r.return_yen:.0f}|'
            f'{r.profit_yen:+.0f}|{r.new_roi_pct:.2f}%|{r.min_month_roi_pct:.2f}%|{r.month_detail}|'
        )
    base = o[o.overlay == 'NONE_V260_BASE'].iloc[0]
    better = o[(o.overlay != 'NONE_V260_BASE') & (o.R >= 50) & (o.robust_roi > base.robust_roi)]
    L += ['', '## Decision']
    if len(better):
        r = better.iloc[0]
        L.append(f'- A consensus overlay improves robust development ROI versus frozen v260 base: {r.overlay}, keep {100*r.keep_frac:.0f}%, {int(r.R)}R, ROI {r.new_roi_pct:.2f}%, monthly floor {r.min_month_roi_pct:.2f}%.')
    else:
        L.append('- No >=50R consensus overlay improves robust development ROI versus the frozen v260 base. Keep v260 signal separate from v265 head-rate research.')
    L += ['- Do not adopt from this retrospective overlay search; any chosen rule must be frozen before September prospective/live-odds validation.', '']
    SUM.write_text('\n'.join(L), encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
