#!/usr/bin/env python3
"""Result-blind 2026-09-11 PRE scan for frozen HEAD4_V291_COMP7 S layer.

Reproduce the v250 PRE model recipe and score today's complete race universe.
The classifier is fitted only with labels through 2026-06-30.  July/August and
September outcomes are never loaded.  Prior-day Jul/Aug/Sep information may be
used only as contemporaneously available PRE feature state (motor history and
prior exhibitions), never for fitting, calibration, threshold selection, or
validation.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import csv
import hashlib
import json

import numpy as np
import pandas as pd

from backtest import rows, i, race_features
from backtest_v3 import ingest_motor
from backtest_v4 import add_features, score4v4, ingest_prior_day_preview
from analyze_v250_4head_rebuild_baseline import pre_features, make_model

DAY = date(2026, 9, 11)
TRAIN_START = date(2025, 12, 1)
TRAIN_END = date(2026, 6, 30)
PRELOAD_START = TRAIN_START - timedelta(days=120)
PRE_CUT = 0.28
CUR_CARDS = Path('current_input/race_cards.csv')
CUR_WAKU = Path('current_input/waku10.csv')
OUT = Path('scan_20260911_4head_v291_pre.csv')
SUM = Path('scan_20260911_4head_v291_pre.md')
AUDIT = Path('scan_20260911_4head_v291_pre_audit.json')
PRE_COLS = [
    'legacy_score4','racer4','hist_st_edge_4v3','wall3_weak',
    'inner12_resistance','motor4_2ren','motor4_hist','turnfoot4_prior','past_win4'
]


def local_rows(path: Path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def build_training_and_state():
    cache = {}
    hist = defaultdict(list)
    seen = set()
    d = PRELOAD_START
    while d < TRAIN_START:
        ingest_motor(hist, seen, d)
        if d >= TRAIN_START - timedelta(days=12):
            ingest_prior_day_preview(cache, d)
        d += timedelta(days=1)

    train = []
    d = TRAIN_START
    while d <= TRAIN_END:
        ymd = d.strftime('%Y/%m/%d')
        # PRE features are frozen before the same-day result is read.
        from backtest_v5_ev import process_features
        feats = process_features(d, cache, hist)
        frozen = []
        for r, x, s4, _s5, _dc in feats:
            z = {'date': str(d), 'race_code': str(r['レースコード']).zfill(12)}
            z.update(pre_features(x, s4))
            frozen.append(z)
        res = {r['レースコード']: r for r in rows(f'data/results/realtime/{ymd}.csv')}
        for z in frozen:
            rr = res.get(z['race_code'], {})
            z['y4head'] = int(i(rr.get('1着_艇番')) == 4)
            train.append(z)
        ingest_prior_day_preview(cache, d)
        ingest_motor(hist, seen, d)
        d += timedelta(days=1)

    # Advance only PRE feature state after the fitting cutoff.  No result or
    # payout file is touched for Jul/Aug/Sep.
    d = TRAIN_END + timedelta(days=1)
    while d < DAY:
        ingest_prior_day_preview(cache, d)
        ingest_motor(hist, seen, d)
        d += timedelta(days=1)
    return pd.DataFrame(train), cache, hist


def build_current(cache, hist):
    cards = local_rows(CUR_CARDS)
    waku = {str(r.get('レースコード','')).zfill(12): r for r in local_rows(CUR_WAKU)}
    out = []
    for r in cards:
        code = str(r.get('レースコード','')).zfill(12)
        if code not in waku:
            continue
        x = add_features(race_features(r, waku[code]), r, cache, hist)
        s4 = score4v4(x)
        z = {
            'date': str(DAY), 'race_code': code,
            'jcd': int(code[8:10]), 'rno': int(code[10:12]),
            'venue': str(r.get('レース場コード','')).zfill(2),
        }
        z.update(pre_features(x, s4))
        out.append(z)
    return pd.DataFrame(out), len(cards), len(waku)


def main():
    if DAY != date(2026, 9, 11):
        raise RuntimeError('frozen scanner date changed')
    if not CUR_CARDS.exists() or not CUR_WAKU.exists():
        raise RuntimeError('current PRE inputs missing')

    tr, cache, hist = build_training_and_state()
    cur, n_cards, n_waku = build_current(cache, hist)
    if tr.empty or cur.empty:
        raise RuntimeError(f'empty train/current train={len(tr)} current={len(cur)}')
    if tr.y4head.nunique() < 2:
        raise RuntimeError('training target has <2 classes')
    if len(cur) < 120:
        raise RuntimeError(f'insufficient current universe: {len(cur)}')

    model = make_model(PRE_COLS)
    model.fit(tr[PRE_COLS], tr.y4head.astype(int))
    cur['PRE'] = model.predict_proba(cur[PRE_COLS])[:, 1]
    cur['pre_eligible'] = (cur.PRE >= PRE_CUT).astype(int)
    cur = cur.sort_values(['PRE','race_code'], ascending=[False, True]).reset_index(drop=True)
    cur.to_csv(OUT, index=False)
    q = cur[cur.pre_eligible == 1].copy()

    coef = model.named_steps['m'].coef_[0].tolist()
    intercept = float(model.named_steps['m'].intercept_[0])
    audit = {
        'policy': 'HEAD4_V291_COMP7',
        'layer': 'S_PRE_STAGE_ONLY',
        'target_date': str(DAY),
        'result_blind_target_day': True,
        'pre_cut_inclusive': PRE_CUT,
        'model_recipe': 'analyze_v250_4head_rebuild_baseline.py::PRE',
        'fit_label_start': str(TRAIN_START),
        'fit_label_cutoff': str(TRAIN_END),
        'jul_aug_labels_used': False,
        'september_labels_used': False,
        'post_or_current_exhibition_used': False,
        'pre_features': PRE_COLS,
        'train_rows': int(len(tr)),
        'train_head4_rate': float(tr.y4head.mean()),
        'current_rows': int(len(cur)),
        'current_input_cards': n_cards,
        'current_input_waku': n_waku,
        'eligible_rows': int(len(q)),
        'cards_sha256': sha256(CUR_CARDS),
        'waku_sha256': sha256(CUR_WAKU),
        'logistic_C': 0.35,
        'coef_standardized_order': coef,
        'intercept': intercept,
        'note': 'Jul/Aug/Sep prior-day feature state is allowed as information known before 2026-09-11; labels after 2026-06-30 are not loaded.'
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    L = [
        '# 2026-09-11 4-head v291 PRE scan','',
        '- Formal result-blind PRE stage for frozen HEAD4_V291_COMP7 S layer.',
        '- Exact v250 PRE feature/model recipe; inclusive PRE >= 0.28.',
        '- Fit labels end 2026-06-30. Jul/Aug and September outcomes are not loaded.',
        '- Current-day exhibition/ST/original-exhibition are not used at this stage.',
        '- This is PRE eligibility only; final S still requires POST >= 0.25 and ENV_ENTRY >= 0.224790.',
        '',
        f'- Current complete race rows: {len(cur)}',
        f'- PRE >= {PRE_CUT:.2f}: {len(q)}',
        '',
        '|race|PRE|legacy4|racer4|motor4 hist|turnfoot4 prior|',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for _, r in q.iterrows():
        L.append(f"|JCD{int(r.jcd):02d} {int(r.rno)}R|{r.PRE:.6f}|{r.legacy_score4:.3f}|{r.racer4:.3f}|{r.motor4_hist:.3f}|{r.turnfoot4_prior:.3f}|")
    SUM.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
