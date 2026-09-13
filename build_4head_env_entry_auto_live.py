#!/usr/bin/env python3
"""One-command result-blind HEAD4 ENV_ENTRY live pipeline.

Inputs: target race, current race-card CSV, frozen PRE and POST probabilities.
Pipeline:
  current six-boat exhibition -> exact ENV context -> v74/v83/v91 21 primitives
  -> frozen 25-field ENV_ENTRY + score

No results, payouts or odds are requested. All missing current inputs fail closed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from head4_v291_downstream_inference import load_artifact, score_env_entry
from build_4head_env_entry_live import assemble as assemble_env
from build_4head_env_v91_primitives_live import build as build_primitives
from build_4head_env_context_live import fetch_and_build as build_context
from build_4head_v283_current_exhibition_live import fetch_and_build as build_exhibition


class EnvAutoBuildError(RuntimeError):
    pass


def build(
    hd: str,
    jcd: int,
    rno: int,
    current_card_csv: str,
    pre: float,
    post: float,
    artifact_path: str = 'artifacts/head4_v291_downstream_20260630.json',
    timeout: int = 20,
) -> dict[str, Any]:
    exhibition = build_exhibition(hd, jcd, rno, timeout)
    context = build_context(hd, jcd, rno, current_card_csv, exhibition, timeout)
    primitives = build_primitives(exhibition, context)
    artifact = load_artifact(artifact_path)
    row = assemble_env(primitives, pre, post, artifact)
    env_score = score_env_entry(row, artifact)
    code = f'{hd}{int(jcd):02d}{int(rno):02d}'
    return {
        'schema': 'head4_env_entry_auto_live_v1',
        'race_code': code,
        'policy': 'HEAD4_V291_COMP7',
        'frozen_training_cutoff': '2026-06-30',
        'result_blind': True,
        'odds_used': False,
        'payout_used': False,
        'same_day_results_used': False,
        'jul_aug_labels_used': False,
        'september_labels_used': False,
        'v96_used': False,
        'PRE': float(pre),
        'POST': float(post),
        'features': row,
        'ENV_ENTRY': float(env_score),
        'context_audit': {
            'history_start': context.get('history_start'),
            'history_end': context.get('history_end'),
            'history_population_n': context.get('history_population_n'),
            'weather_source_kind': context.get('weather_source_kind'),
            'weather_snapshot_hhmm': context.get('weather_snapshot_hhmm'),
            'entry_source_kind': context.get('entry_source_kind'),
            'tilt_source_kind': context.get('tilt_source_kind'),
            'pinned_boatracecsv_commit': context.get('pinned_boatracecsv_commit'),
        },
        'current_exhibition': exhibition,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='YYYYMMDD')
    ap.add_argument('--jcd', required=True, type=int)
    ap.add_argument('--race', required=True, type=int)
    ap.add_argument('--current-card-csv', required=True)
    ap.add_argument('--pre', required=True, type=float)
    ap.add_argument('--post', required=True, type=float)
    ap.add_argument('--artifact', default='artifacts/head4_v291_downstream_20260630.json')
    ap.add_argument('--out', required=True)
    ap.add_argument('--timeout', type=int, default=20)
    a = ap.parse_args()
    z = build(a.date, a.jcd, a.race, a.current_card_csv, a.pre, a.post, a.artifact, a.timeout)
    Path(a.out).write_text(json.dumps(z, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'status':'READY', 'race_code':z['race_code'], 'ENV_ENTRY':z['ENV_ENTRY'], 'out':a.out
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
