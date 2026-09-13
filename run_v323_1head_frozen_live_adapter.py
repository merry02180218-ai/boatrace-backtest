#!/usr/bin/env python3
"""v323: result-blind LIVE adapter for the frozen 1-head stack.

Frozen semantics
----------------
HEAD   : v308 absolute development q=.98 p_head cutoff + opponent mass >= .375.
SECOND : v317 OUTER_L2_1 with START family dropped.
THIRD  : v318 DROPSTART_T0.1.
TICKETS: v320 HYBRID alpha=.70, exactly three 1-x-y tickets.
ODDS   : official BOAT RACE odds3t only; 120-combination snapshot required.

This runner deliberately does not settle the target month and never asks for target-
month results/payouts.  Jul/Aug can be chronological training history, but they remain
NON-PRISTINE and never tune any frozen threshold/policy.  The current target row is
inference-only.  Because September outcomes remain unread, current player/prior-form
columns that cannot be reconstructed without September results are left missing and are
handled by the already-frozen model preprocessing; they are never future-backfilled.
"""
from __future__ import annotations

import argparse
import csv
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v300_1head_trifecta3_feature_upgrade as v300
import run_v303_1head_headmodel_transfer_ablation as v303
import run_v305_1head_leakage_audit as v305
import run_v307_1head_causal_turn_form as v307
import run_v310_1head_opponent_headrisk_second as v310
import run_v311_1head_opponent_second_family_autoresearch as v311
import run_v312_1head_opponent_outer_gate as v312
import run_v317_1head_opponent_error_features as v317
import run_v318_1head_opponent_third_rebuild as v318
import run_v299_1head_trifecta3_policy_search as v299
import run_v321_1head_julaug_nonpristine_validation as v321
import fetch_live_trifecta_odds as liveodds

ROOT = Path(__file__).resolve().parent
DEV_PRED = ROOT / 'analysis_v308_1head_volume_opponent_joint_pred.csv'
FROZEN_V320 = ROOT / 'analysis_v320_1head_exact3_ticket_policy_best_race.csv'
PREP_HEAD = ROOT / 'cache_v321_julaug_nonpristine_head_full.csv.gz'
PREP_SLIM = ROOT / 'cache_v321_julaug_nonpristine_slim.csv.gz'
Q = .98
OPP_MASS_CUT = .375
POLICY = 'HYBRID'
ALPHA = .70
TARGET_MONTH = '2026-09'

META_HEAD = {'date','month','race_code','venue','race','head_hit','actual_combo'}


def norm_code(x) -> str:
    s = str(x or '').strip()
    if s.endswith('.0') and s[:-2].isdigit():
        s = s[:-2]
    return s.zfill(12) if s.isdigit() else ''


def load_cards(path: Path) -> list[dict]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def assert_frozen_regression() -> dict:
    if not FROZEN_V320.exists():
        raise RuntimeError(f'missing frozen v320 artifact: {FROZEN_V320}')
    d = pd.read_csv(FROZEN_V320, dtype={'race_code': str})
    if len(d) != 345:
        raise RuntimeError(f'v323 regression drift: expected 345 rows, got {len(d)}')
    hh = int(pd.to_numeric(d.head_hit, errors='coerce').sum())
    hit = int(pd.to_numeric(d.hit, errors='coerce').sum())
    if hh != 290 or hit != 139:
        raise RuntimeError(f'v323 regression drift: head={hh} exact3={hit}, expected 290/139')
    if set(d.strategy.astype(str)) != {POLICY}:
        raise RuntimeError(f'v323 strategy drift: {sorted(set(d.strategy.astype(str)))}')
    if not np.allclose(pd.to_numeric(d.alpha, errors='coerce').to_numpy(float), ALPHA):
        raise RuntimeError('v323 alpha drift')
    for _, r in d.iterrows():
        ts = [x.strip() for x in str(r.tickets).split(';') if x.strip()]
        if len(ts) != 3 or len(set(ts)) != 3 or any(not x.startswith('1-') for x in ts):
            raise RuntimeError(f'v323 invalid frozen ticket set {r.race_code}: {ts}')
    return {'R': len(d), 'head_hits': hh, 'exact3_hits': hit}


def frozen_hcut() -> float:
    d = pd.read_csv(DEV_PRED, dtype={'race_code': str})
    if 'test_month' not in d or 'p_head' not in d:
        raise RuntimeError('v308 development prediction schema drift')
    bad = [m for m in d.test_month.astype(str).unique()
           if str(m).startswith(('2026-07','2026-08','2026-09'))]
    if bad:
        raise RuntimeError(f'v323 DEV_PRED contains forbidden months: {bad}')
    h = pd.to_numeric(d.p_head, errors='coerce').dropna()
    if h.empty:
        raise RuntimeError('v323 DEV_PRED has no p_head')
    return float(h.quantile(Q))


def current_static(cards: list[dict], target: date) -> pd.DataFrame:
    out = []
    for card in cards:
        code = norm_code(card.get('レースコード',''))
        if not code:
            continue
        if code[:8] != target.strftime('%Y%m%d'):
            raise RuntimeError(f'current card date mismatch: {code} vs {target}')
        q = {
            'date': target.isoformat(),
            'month': target.strftime('%Y-%m'),
            'race_code': code,
            'venue': str(card.get('レース場コード','') or code[8:10]).zfill(2),
            'race': int(code[10:12]),
        }
        for b in range(1,7):
            for k, v in v298.v294.raw_parts(card, b).items():
                q[f'b{b}_{k}'] = v
        out.append(q)
    if not out:
        raise RuntimeError('no usable current race cards')
    d = pd.DataFrame(out).drop_duplicates('race_code').copy()
    if d.race_code.duplicated().any():
        raise RuntimeError('duplicate current race codes')
    return d


def build_current_features(cur0: pd.DataFrame):
    """Build only result-blind transforms. No settlement call is allowed here."""
    d = cur0.copy()
    d = v298.v294.add_rel(d)
    d, threat = v298.add_threat(d)
    d, tf = v303.add_transfer_features(d)
    d, causal = v307.add_causal(d)
    safe = list(dict.fromkeys(
        v305.safe_transfer(tf['TURN_FORM']) +
        v305.safe_transfer(tf['STMOTOR']) + causal
    ))
    if any('meet_' in str(c).lower() for c in safe):
        raise RuntimeError('v323 unsafe meet_* current head feature')
    return d, threat, safe


def head_score(cur_feat: pd.DataFrame, hcut: float) -> pd.DataFrame:
    if not PREP_HEAD.exists():
        raise RuntimeError('v323 requires v321 full prepare head cache')
    hd = pd.read_csv(PREP_HEAD, dtype={'race_code': str})
    hd['race_code'] = hd.race_code.astype(str).str.zfill(12)
    if any(str(m).startswith('2026-09') for m in hd.month.astype(str).unique()):
        raise RuntimeError('v323 training head cache contains September')

    safe_static = set(v298.v296.SAFE)
    core = []
    for c in hd.columns:
        s = str(c)
        if s in META_HEAD:
            continue
        if s.startswith('v298_'):
            core.append(c); continue
        if '_pl_' in s or s.startswith('rel_pl_'):
            core.append(c); continue
        if any(s.startswith(f'b{b}_{k}') for b in range(1,7) for k in safe_static):
            core.append(c); continue
        if any(s.startswith(f'rel_{k}_') for k in safe_static):
            core.append(c); continue
        if any(s == f'attack23_{k}' for k in safe_static):
            core.append(c); continue
    core = list(dict.fromkeys(core))
    extras = [c for c in hd.columns if c not in META_HEAD and c not in core]
    extras = [c for c in extras if 'meet_' not in str(c).lower()]
    guard = [c for c in core if str(c).startswith(('b1_','b2_','b3_','b4_','rel_','attack23_','v298_'))]
    if any('meet_' in str(c).lower() for c in core + extras + guard):
        raise RuntimeError('v323 meet_* entered head fit')

    cur = cur_feat.copy()
    for c in hd.columns:
        if c not in cur.columns:
            cur[c] = np.nan
    cur['head_hit'] = 0
    cur['actual_combo'] = ''
    cur = cur[list(dict.fromkeys(list(hd.columns) + [c for c in cur.columns if c not in hd.columns]))]

    tr = hd.copy()
    te = cur.copy()
    bc = v298.v293.available(tr, core, .55)
    bg = v298.v293.available(tr, guard, .55)
    ex = v303.available(tr, extras)
    ph, _, _, _, _, _ = v298.head_fold(tr, te, list(dict.fromkeys(bc + ex)), bg)
    z = te[['date','month','race_code','venue','race']].copy()
    z['p_head'] = ph
    z['hcut'] = hcut
    return z


def opponent_score(cur_feat: pd.DataFrame, head: pd.DataFrame):
    if not PREP_SLIM.exists():
        raise RuntimeError('v323 requires v321 prepare opponent slim cache')
    slim = pd.read_csv(PREP_SLIM, dtype={'race_code': str})
    slim.race_code = slim.race_code.astype(str).str.zfill(12)
    if any(str(m).startswith('2026-09') for m in slim.month.astype(str).unique()):
        raise RuntimeError('v323 opponent cache contains September')

    v300.setup_v298()
    sufs = v298.suffixes(slim)
    if any('meet_' in str(x).lower() for x in sufs):
        raise RuntimeError('v323 forbidden meet_* opponent suffix')

    cur = cur_feat.copy()
    cur['head_hit'] = 0
    cur['actual_combo'] = ''
    need = list(slim.columns)
    for c in need:
        if c not in cur.columns:
            cur[c] = np.nan
    cur = cur[need]
    full = pd.concat([slim, cur], ignore_index=True)
    full['race_code'] = full.race_code.astype(str).str.zfill(12)
    if set(full.loc[full.month.astype(str)==TARGET_MONTH, 'race_code']) != set(cur.race_code):
        raise RuntimeError('v323 target inference cohort mismatch')

    sl = v300.augment_second(v298.second_long(full, sufs))
    base_p2, _ = v300.p2_predict(sl, TARGET_MONTH, 10.0, False)
    _, p3, p4 = v312.load_cache()
    sl_hr = v310.add_headrisk(sl, p3, p4)
    sx, _ = v317.add_engineered(sl_hr, 'OUTER')
    p2, _ = v311.p2_predict_explicit(sx, TARGET_MONTH, 1.0, None, {'START'})

    cl = v300.augment_third(v321._third_fold_long(full, sufs, TARGET_MONTH))
    base_pc, _ = v300.pc_predict(cl, TARGET_MONTH, .3, False)
    pc, _ = v318.pc_predict(cl, TARGET_MONTH, .1, 'DROP_START')

    masses = {}
    for code in cur.race_code.astype(str):
        if code not in base_p2 or code not in base_pc:
            raise RuntimeError(f'v323 base opponent prediction missing {code}')
        masses[code] = v300.base5(base_p2[code], base_pc[code])[1]

    out = head.copy()
    out['opp_mass'] = [masses.get(str(x).zfill(12), np.nan) for x in out.race_code]
    out['selected'] = ((pd.to_numeric(out.p_head, errors='coerce') >= pd.to_numeric(out.hcut, errors='coerce')) &
                       (pd.to_numeric(out.opp_mass, errors='coerce') >= OPP_MASS_CUT)).astype(int)

    fn = v299.STRATEGIES[POLICY]
    ticket_map = {}
    for code in out.loc[out.selected==1, 'race_code'].astype(str):
        if code not in p2 or code not in pc:
            raise RuntimeError(f'v323 frozen opponent prediction missing {code}')
        probs = v299.pair_prob(p2[code], pc[code], ALPHA)
        top3 = fn(p2[code], pc[code], probs)[:3]
        tickets = [f'1-{s}-{t}' for s,t in top3]
        if len(tickets) != 3 or len(set(tickets)) != 3 or any(not t.startswith('1-') for t in tickets):
            raise RuntimeError(f'v323 invalid live tickets {code}: {tickets}')
        ticket_map[code] = tickets
    out['tickets'] = [';'.join(ticket_map.get(str(c), [])) for c in out.race_code]
    return out, ticket_map


def composite(vals: list[float]) -> float:
    if len(vals) != 3 or any((not math.isfinite(x) or x <= 0) for x in vals):
        raise ValueError('v323 composite requires 3 positive finite odds')
    return 1.0 / sum(1.0/x for x in vals)


def attach_live_odds(out: pd.DataFrame, ticket_map: dict[str,list[str]], target: date) -> pd.DataFrame:
    z = out.copy()
    for c in ['odds1','odds2','odds3','composite_odds','odds_complete','bet_status']:
        z[c] = np.nan if c != 'bet_status' else 'SKIP_NOT_SELECTED'
    for i, r in z[z.selected==1].iterrows():
        code = str(r.race_code).zfill(12)
        tickets = ticket_map[code]
        jcd = code[8:10]
        rno = int(code[10:12])
        status = 'SKIP_ODDS_UNAVAILABLE'
        try:
            resp = liveodds.safe_get(liveodds.BASE, {'rno':rno,'jcd':jcd,'hd':target.strftime('%Y%m%d')})
            odds = liveodds.parse_odds(resp.text)
            if set(odds) != liveodds.expected_combos() or len(odds) != 120:
                z.at[i,'odds_complete'] = 0
                z.at[i,'bet_status'] = 'SKIP_INCOMPLETE_ODDS'
                continue
            vals = []
            for t in tickets:
                a,b,c = map(int,t.split('-'))
                v = float(odds[(a,b,c)])
                if not math.isfinite(v) or v <= 0:
                    raise ValueError(f'invalid odds {t}={v}')
                vals.append(v)
            z.at[i,'odds1'],z.at[i,'odds2'],z.at[i,'odds3'] = vals
            z.at[i,'composite_odds'] = composite(vals)
            z.at[i,'odds_complete'] = 1
            status = 'SKIP_NO_FROZEN_ODDS_CUTOFF'
        except Exception as e:
            print(f'v323 odds unavailable {code}: {type(e).__name__}: {e}', flush=True)
            z.at[i,'odds_complete'] = 0
        z.at[i,'bet_status'] = status
    return z


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='YYYY-MM-DD')
    ap.add_argument('--cards', required=True, type=Path)
    ap.add_argument('--out', default='v323_live', type=Path)
    ap.add_argument('--skip-odds', action='store_true')
    args = ap.parse_args()
    target = date.fromisoformat(args.date)
    if target.strftime('%Y-%m') != TARGET_MONTH:
        raise RuntimeError(f'v323 currently frozen for target month {TARGET_MONTH}, got {target}')
    if not args.cards.exists():
        raise RuntimeError(f'current cards missing: {args.cards}')

    reg = assert_frozen_regression()
    hcut = frozen_hcut()
    print(f"v323 regression OK R={reg['R']} head={reg['head_hits']} exact3={reg['exact3_hits']} hcut={hcut:.10f}", flush=True)

    cards = load_cards(args.cards)
    cur0 = current_static(cards, target)
    cur_feat, _, _ = build_current_features(cur0)
    head = head_score(cur_feat, hcut)
    scored, ticket_map = opponent_score(cur_feat, head)
    scored['policy'] = POLICY
    scored['alpha'] = ALPHA
    scored['opp_mass_cut'] = OPP_MASS_CUT
    if args.skip_odds:
        scored['odds1'] = np.nan; scored['odds2'] = np.nan; scored['odds3'] = np.nan
        scored['composite_odds'] = np.nan; scored['odds_complete'] = 0
        scored['bet_status'] = np.where(scored.selected.eq(1),'SKIP_ODDS_NOT_REQUESTED','SKIP_NOT_SELECTED')
    else:
        scored = attach_live_odds(scored, ticket_map, target)

    args.out.mkdir(parents=True, exist_ok=True)
    csvp = args.out / f'v323_1head_live_{target.strftime("%Y%m%d")}.csv'
    mdp = args.out / f'v323_1head_live_{target.strftime("%Y%m%d")}.md'
    scored.to_csv(csvp, index=False)
    sel = scored[scored.selected==1].copy()
    lines = [
        '# v323 frozen 1-head LIVE adapter', '',
        f'- Date: **{target.isoformat()}**',
        f'- Historical regression: **345R / 290 head wins / 139 exact3** (asserted before current scoring).',
        f'- Frozen head cutoff: **{hcut:.10f}** (v308 development q=.98); opponent mass >= **{OPP_MASS_CUT:.3f}**.',
        f'- Frozen opponent/tickets: **v317 OUTER_L2_1 / v318 DROPSTART_T0.1 / {POLICY} alpha={ALPHA:.2f} / exactly 3 tickets**.',
        '- September outcomes/payouts are not used. Target rows are inference-only; `meet_*` is forbidden.',
        '- BUY cutoff is not frozen; complete odds therefore remain fail-safe `SKIP_NO_FROZEN_ODDS_CUTOFF`.', '',
        f'## Current scan\n- Usable scheduled races: **{len(scored)}**; v308-qualified: **{len(sel)}**.', '',
        '|race_code|venue|R|p_head|hcut|opp_mass|tickets|odds1|odds2|odds3|composite|status|',
        '|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|'
    ]
    for _, r in scored.iterrows():
        def fnum(x, n=3):
            return '-' if pd.isna(x) else f'{float(x):.{n}f}'
        lines.append(f"|{r.race_code}|{r.venue}|{int(r.race)}|{fnum(r.p_head,6)}|{fnum(r.hcut,6)}|{fnum(r.opp_mass,3)}|{r.tickets or '-'}|{fnum(r.odds1,1)}|{fnum(r.odds2,1)}|{fnum(r.odds3,1)}|{fnum(r.composite_odds,3)}|{r.bet_status}|")
    mdp.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(mdp.read_text(encoding='utf-8'), flush=True)
    print(f'v323 wrote {csvp} and {mdp}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
