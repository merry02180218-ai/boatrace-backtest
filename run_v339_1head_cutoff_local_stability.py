#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pandas as pd

import onehead_production_profile as prod
import run_v337_1head_head_cutoff_volume as v337

OUT = Path('/tmp/v339')
OUT.mkdir(parents=True, exist_ok=True)

CUTS = [0.7850, 0.7825, 0.7800, 0.7775, 0.7750]
CONTROL = 0.7800
EXPECTED_CONTROL = (prod.EXPECTED_PASS_R, prod.EXPECTED_HEAD, prod.EXPECTED_EXACT3)
EXPECTED_CONTROL_HASH = prod.EXPECTED_PASS_ID_SHA256


def identity_hash(df: pd.DataFrame) -> str:
    ids = sorted(df.race_code.astype(str).str.zfill(12).tolist())
    return hashlib.sha256('\n'.join(ids).encode('utf-8')).hexdigest()


def met(df: pd.DataFrame) -> dict:
    n = len(df)
    head = int(df.head_hit.sum()) if n else 0
    exact3 = int(df.hit.sum()) if n else 0
    return {
        'R': n,
        'head': head,
        'head_rate': 100.0 * head / n if n else None,
        'exact3': exact3,
        'exact3_rate': 100.0 * exact3 / n if n else None,
    }


def venue_stats(df: pd.DataFrame) -> tuple[float | None, float | None]:
    if df.empty:
        return None, None
    x = df.copy()
    x['place'] = x.race_code.astype(str).str.zfill(12).str[8:10]
    counts = x.groupby('place').size().astype(float)
    shares = counts / counts.sum()
    return float(100.0 * shares.max()), float((shares ** 2).sum())


def monthly_rows(cut: float, df: pd.DataFrame) -> list[dict]:
    out = []
    for month in v337.MONTHS:
        z = df[df.month.eq(month)]
        m = met(z)
        out.append({'cutoff': cut, 'month': month, **m})
    return out


def delta_metrics(selected: pd.DataFrame, control: pd.DataFrame) -> dict:
    ids = set(selected.race_code.astype(str))
    control_ids = set(control.race_code.astype(str))
    added = selected[~selected.race_code.astype(str).isin(control_ids)].copy()
    removed = control[~control.race_code.astype(str).isin(ids)].copy()
    return {
        'added_vs_078': met(added),
        'removed_vs_078': met(removed),
        'added_race_codes': sorted(added.race_code.astype(str).tolist()),
        'removed_race_codes': sorted(removed.race_code.astype(str).tolist()),
    }


def main() -> None:
    if not prod.SEPTEMBER_OUTCOMES_MUST_REMAIN_UNREAD:
        raise AssertionError('production profile permits September outcomes')
    if any(m >= '2026-09' for m in v337.MONTHS):
        raise AssertionError(f'v337 evaluation months unexpectedly include September: {v337.MONTHS}')

    base = v337.load_candidate_base()
    y, canon_pass, overlay_n = v337.build_exhibition(base)
    v337.validate_no_sep(y)

    # Recheck the frozen canonical v332 anchor before local-cutoff research.
    _, anchor, _, _ = v337.eval_cut(y, prod.ANCHOR_HEAD_CUTOFF)
    anchor_tuple = (len(anchor), int(anchor.head_hit.sum()), int(anchor.hit.sum()))
    anchor_hash = identity_hash(anchor)
    if anchor_tuple != (prod.ANCHOR_EXPECTED_PASS_R, prod.ANCHOR_EXPECTED_HEAD, prod.ANCHOR_EXPECTED_EXACT3):
        raise AssertionError(f'anchor metric drift: {anchor_tuple}')
    if anchor_hash != prod.ANCHOR_PASS_ID_SHA256:
        raise AssertionError(f'anchor identity drift: {anchor_hash}')
    if set(anchor.race_code.astype(str)) != set(canon_pass.race_code.astype(str)):
        raise AssertionError('anchor no longer equals canonical v332 PASS identity')

    selected_by_cut: dict[float, pd.DataFrame] = {}
    pre_by_cut: dict[float, pd.DataFrame] = {}
    for cut in CUTS:
        pre, selected, _, _ = v337.eval_cut(y, cut)
        pre_by_cut[cut] = pre
        selected_by_cut[cut] = selected

    control = selected_by_cut[CONTROL]
    control_tuple = (len(control), int(control.head_hit.sum()), int(control.hit.sum()))
    control_hash = identity_hash(control)
    if control_tuple != EXPECTED_CONTROL or control_hash != EXPECTED_CONTROL_HASH:
        raise AssertionError(
            f'production 0.78 control drift metrics={control_tuple} hash={control_hash} '
            f'expected={EXPECTED_CONTROL}/{EXPECTED_CONTROL_HASH}'
        )

    summary = []
    monthly = []
    deltas = {}
    for cut in CUTS:
        selected = selected_by_cut[cut]
        m = met(selected)
        top_share, hhi = venue_stats(selected)
        row = {
            'cutoff': cut,
            'pre_R': len(pre_by_cut[cut]),
            **m,
            'races_per_month': len(selected) / len(v337.MONTHS),
            'top_venue_share_pct': top_share,
            'venue_hhi': hhi,
            'pass_identity_sha256': identity_hash(selected),
        }
        summary.append(row)
        monthly.extend(monthly_rows(cut, selected))
        deltas[f'{cut:.4f}'] = delta_metrics(selected, control)

    pd.DataFrame(summary).to_csv(OUT/'analysis_v339_summary.csv', index=False)
    pd.DataFrame(monthly).to_csv(OUT/'analysis_v339_monthly.csv', index=False)
    control[['month','race_code','p_head','head_hit','hit']].sort_values('race_code').to_csv(
        OUT/'control_078_identity.csv', index=False
    )

    delta_rows = []
    for cut in CUTS:
        d = deltas[f'{cut:.4f}']
        for direction in ['added_vs_078', 'removed_vs_078']:
            delta_rows.append({'cutoff': cut, 'direction': direction, **d[direction]})
    pd.DataFrame(delta_rows).to_csv(OUT/'analysis_v339_delta_quality.csv', index=False)

    result = {
        'profile': prod.PROFILE_NAME,
        'production_unchanged': True,
        'production_head_cutoff': prod.HEAD_CUTOFF,
        'exhibition': {'family': 'ATTACK_ENV_SOFT', 'env_w': 0.1, 'q': 0.65},
        'canonical_overlay_rows': overlay_n,
        'anchor': {
            'metrics': {'R': anchor_tuple[0], 'head': anchor_tuple[1], 'exact3': anchor_tuple[2]},
            'sha256': anchor_hash,
        },
        'control_078': {
            'metrics': {'R': control_tuple[0], 'head': control_tuple[1], 'exact3': control_tuple[2]},
            'sha256': control_hash,
        },
        'summary': summary,
        'delta_vs_078': deltas,
        'SEPTEMBER_OUTCOMES_READ': False,
    }
    (OUT/'result_v339.json').write_text(json.dumps(result, indent=2), encoding='utf-8')

    lines = [
        '# v339 1-head cutoff local stability audit',
        '',
        f'- Formal production unchanged: HEAD cutoff {prod.HEAD_CUTOFF:.2f} / v332 q=.65.',
        '- September 2026 outcomes: UNREAD.',
        f'- canonical v332 overlay rows: {overlay_n}.',
        f'- 0.78 control identity: {control_tuple[0]}R / head {control_tuple[1]} / exact3 {control_tuple[2]} / sha256 {control_hash}.',
        '',
        '## Local cutoff sweep',
    ]
    for r in summary:
        lines.append(
            f"- {r['cutoff']:.4f}: PASS {r['R']} ({r['races_per_month']:.1f}/month), "
            f"head {r['head']}/{r['R']}={r['head_rate']:.2f}%, "
            f"exact3 {r['exact3']}/{r['R']}={r['exact3_rate']:.2f}%, "
            f"top venue {r['top_venue_share_pct']:.2f}%, HHI {r['venue_hhi']:.4f}"
        )
    lines += ['', '## Incremental quality versus 0.78']
    for cut in CUTS:
        if cut == CONTROL:
            continue
        d = deltas[f'{cut:.4f}']
        a, rm = d['added_vs_078'], d['removed_vs_078']
        if a['R']:
            lines.append(
                f"- {cut:.4f}: adds {a['R']} races; head {a['head']}/{a['R']}={a['head_rate']:.2f}%, "
                f"exact3 {a['exact3']}/{a['R']}={a['exact3_rate']:.2f}%"
            )
        if rm['R']:
            lines.append(
                f"- {cut:.4f}: removes {rm['R']} of 0.78 races; head {rm['head']}/{rm['R']}={rm['head_rate']:.2f}%, "
                f"exact3 {rm['exact3']}/{rm['R']}={rm['exact3_rate']:.2f}%"
            )
    (OUT/'summary_v339.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines), flush=True)


if __name__ == '__main__':
    main()
