#!/usr/bin/env python3
"""Build exact current-day context for frozen HEAD4 v74/v83/v91 ENV primitives.

Result-blind current sources only:
- BOATCAST bc_j_tkz: current tilt/source-presence
- BOATCAST bc_j_stt: current exhibition entry course/source-presence
- BOATCAST bc_sui: current pre-race venue weather (wind direction/speed)
- accepted current-exhibition payload: proves original-exhibition availability

Historical context is replayed strictly before target_date using the exact v74
update order. Results, payouts and odds are never opened. Jul/Aug outcomes and
September outcomes are therefore not used.

Pinned parser lineage: BoatraceCSV commit
563c69ccd28853b8b4953489c673877a9dfeb4e8
- bc_j_stt row: [0]=entry course, [1]=boat number, [4]=ST, [5]=F/L
- bc_sui weather: [3]=wind direction text, [4]=wind speed
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict, deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from backtest import rows
from backtest_v3 import ingest_motor
from backtest_v4 import clean_name
from backtest_v74_ten_month_strict_flow import (
    PRELOAD, MODELS, bycode, raw_candidates, history_value,
    update_preview_states, hf, ps,
)
from build_4head_post_live import _fetch, BOATCAST
from fetch_4head_beforeinfo_live import validate_target
from historical_data_loader import waku10_rows

MODEL = '4カドまくり'
PINNED_BOATRACECSV = '563c69ccd28853b8b4953489c673877a9dfeb4e8'
WIND_DIRECTION_TO_CODE = [
    ('北西', 8), ('北東', 2), ('南西', 6), ('南東', 4),
    ('北', 1), ('東', 3), ('南', 5), ('西', 7),
]


class EnvContextBuildError(RuntimeError):
    pass


def _clean(v: Any) -> str:
    return ' '.join(str(v or '').replace('\u3000', ' ').split())


def _num(name: str, v: Any) -> float:
    s = _clean(v).replace('+', '')
    if s.startswith('.'):
        s = '0' + s
    if s.startswith('-.'):
        s = '-0' + s[1:]
    try:
        x = float(s)
    except Exception as e:
        raise EnvContextBuildError(f'invalid {name}') from e
    if not math.isfinite(x):
        raise EnvContextBuildError(f'non-finite {name}')
    return x


def race_code(hd: str, jcd: int, rno: int) -> str:
    hd, jcd, rno = validate_target(hd, jcd, rno)
    return f'{hd}{jcd:02d}{rno:02d}'


def boatcast_tkz_url(hd: str, jcd: int, rno: int) -> str:
    validate_target(hd, jcd, rno)
    return f'{BOATCAST}/hp_txt/{jcd:02d}/bc_j_tkz_{hd}_{jcd:02d}_{rno:02d}.txt'


def boatcast_stt_url(hd: str, jcd: int, rno: int) -> str:
    validate_target(hd, jcd, rno)
    return f'{BOATCAST}/hp_txt/{jcd:02d}/bc_j_stt_{hd}_{jcd:02d}_{rno:02d}.txt'


def boatcast_sui_url(hd: str, jcd: int) -> str:
    validate_target(hd, jcd, 1)
    return f'{BOATCAST}/m_txt/{jcd:02d}/bc_sui_{hd}_{jcd:02d}.txt'


def parse_tkz_tilt4(body: str) -> float:
    """Exact pinned bc_j_tkz layout: boat rows are 1..6, tilt is column 6."""
    lines = body.splitlines()
    if not lines or not lines[0].lstrip().startswith('data=') or len(lines) < 8:
        raise EnvContextBuildError('bc_j_tkz malformed/incomplete')
    status = lines[1].split('\t')[0].strip()
    if status != '1':
        raise EnvContextBuildError(f'bc_j_tkz not ready: status={status!r}')
    boat_rows = [x for x in lines[2:] if x.strip()][:6]
    if len(boat_rows) != 6:
        raise EnvContextBuildError('bc_j_tkz boat rows incomplete')
    cols = boat_rows[3].split('\t')
    if len(cols) <= 6:
        raise EnvContextBuildError('bc_j_tkz boat4 tilt missing')
    s = _clean(cols[6]).replace(' ', '').replace('度', '')
    return _num('tilt', s)


def parse_stt_courses(body: str) -> dict[int, int]:
    """Exact pinned bc_j_stt layout: [0]=course, [1]=boat number."""
    lines = body.splitlines()
    if not lines or not lines[0].lstrip().startswith('data='):
        raise EnvContextBuildError('bc_j_stt malformed')
    out: dict[int, int] = {}
    for raw in lines[2:]:
        if not raw.strip():
            continue
        cols = raw.split('\t')
        if len(cols) < 2:
            continue
        try:
            course = int(cols[0].strip())
            boat = int(cols[1].strip())
        except Exception:
            continue
        if 1 <= boat <= 6 and 1 <= course <= 6:
            out[boat] = course
    if set(out) != set(range(1, 7)) or len(set(out.values())) != 6:
        raise EnvContextBuildError(f'bc_j_stt course rows incomplete/invalid: {out}')
    return out


def _wind_code(text: str) -> int:
    s = _clean(text)
    for label, code in WIND_DIRECTION_TO_CODE:
        if label in s:
            return code
    raise EnvContextBuildError(f'unsupported/missing wind direction: {s!r}')


def parse_sui_weather(body: str) -> tuple[int, float, str]:
    """Use only pre-race bc_sui; never post-race bc_rs1_2.

    Pinned layout: [0]=HHMM, [3]=wind direction text, [4]=wind speed.
    Select the last valid weather row exactly as the source's latest snapshot.
    """
    valid: list[list[str]] = []
    for raw in body.splitlines():
        fields = raw.split('\t')
        if len(fields) >= 7 and re.fullmatch(r'\d{4}', fields[0].strip()):
            valid.append(fields)
    if not valid:
        raise EnvContextBuildError('bc_sui weather row missing')
    cols = valid[-1]
    wc = _wind_code(cols[3])
    ws = _num('wind_speed', cols[4])
    if ws < 0:
        raise EnvContextBuildError('negative wind_speed')
    return wc, ws, cols[0].strip()


def _read_csv(path: str) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        raise EnvContextBuildError(f'current card CSV missing: {path}')
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def _target_player(current_card_csv: str, code: str) -> tuple[str, str]:
    matches = [r for r in _read_csv(current_card_csv) if str(r.get('レースコード', '')).zfill(12) == code]
    if len(matches) != 1:
        raise EnvContextBuildError(f'target current card must match exactly once: {len(matches)}')
    card = matches[0]
    venue = str(card.get('レース場コード', '')).zfill(2)
    name = clean_name(card.get('艇4_選手名'))
    if not re.fullmatch(r'\d{2}', venue) or not name:
        raise EnvContextBuildError('target venue/player missing')
    return venue, name


def build_history_before(target: date, venue: str, player: str) -> dict[str, Any]:
    """Replay exact v74 candidate/history update order strictly before target."""
    if target <= PRELOAD:
        raise EnvContextBuildError('target must be after v74 PRELOAD')
    cache: dict[Any, Any] = {}
    mhist = defaultdict(list)
    seen: set[Any] = set()
    ph = defaultdict(lambda: deque(maxlen=2))
    histvals = {m: [] for m in MODELS}
    d = PRELOAD
    days = 0
    raw4 = 0
    while d < target:
        ds = str(d)
        ymd = d.strftime('%Y/%m/%d')
        cards = rows(f'data/programs/race_cards/{ymd}.csv')
        if cards:
            wrows, _ = waku10_rows(ds)
            w10 = bycode(wrows)
            tkzrows = rows(f'data/previews/tkz/{ymd}.csv')
            orows = rows(f'data/previews/original_exhibition/{ymd}.csv')
            raw, _ = raw_candidates(cards, w10, cache, mhist, ph)
            for r in raw:
                histvals[r['model']].append(history_value(r))
                if r['model'] == MODEL:
                    raw4 += 1
            # Exact v74 order: only after today's candidates are frozen does
            # today's preview/motor state become available for tomorrow.
            update_preview_states(cards, tkzrows, orows, cache, ph)
            ingest_motor(mhist, seen, d)
            days += 1
        d += timedelta(days=1)

    key = (venue, clean_name(player))
    q = ph.get(key, deque())
    p1 = ps(hf(ph, key, 1), MODEL)
    p2 = ps(hf(ph, key, 2), MODEL)
    has2 = int(len(q) >= 2)
    pop = [float(x) for x in histvals[MODEL]]
    if not pop:
        raise EnvContextBuildError('v74 4-head history population is empty')
    return {
        'history_prior1': float(p1),
        'history_prior2': float(p2),
        'history_has2': has2,
        'history_population': pop,
        'history_days_loaded': days,
        'history_population_n': len(pop),
        'history_raw4_seen': raw4,
        'history_start': PRELOAD.isoformat(),
        'history_end': (target - timedelta(days=1)).isoformat(),
    }


def build_from_sources(
    hd: str,
    jcd: int,
    rno: int,
    current_card_csv: str,
    current_exhibition: Mapping[str, Any],
    tkz_text: str,
    stt_text: str,
    sui_text: str,
) -> dict[str, Any]:
    code = race_code(hd, jcd, rno)
    if str(current_exhibition.get('race_code', '')).zfill(12) != code:
        raise EnvContextBuildError('current exhibition race_code mismatch')
    if current_exhibition.get('result_blind') is not True or current_exhibition.get('odds_used') is True:
        raise EnvContextBuildError('current exhibition is not result-blind')
    boats = current_exhibition.get('current_boats') or {}
    if not isinstance(boats, Mapping) or set(map(str, range(1, 7))) - set(boats):
        raise EnvContextBuildError('current exhibition boats incomplete')

    venue, player = _target_player(current_card_csv, code)
    if int(venue) != int(jcd):
        raise EnvContextBuildError('current card venue mismatch')
    target = datetime.strptime(hd, '%Y%m%d').date()
    hist = build_history_before(target, venue, player)
    course = parse_stt_courses(stt_text)[4]
    tilt = parse_tkz_tilt4(tkz_text)
    wc, ws, weather_hhmm = parse_sui_weather(sui_text)

    out: dict[str, Any] = {
        'schema': 'head4_env_context_live_v1',
        'race_code': code,
        'result_blind': True,
        'odds_used': False,
        'payout_used': False,
        'same_day_results_used': False,
        'jul_aug_outcomes_used': False,
        'september_outcomes_used': False,
        'v96_used': False,
        'pinned_boatracecsv_commit': PINNED_BOATRACECSV,
        'target_player4': player,
        'venue_code': int(jcd),
        'entry_course_preview': int(course),
        'wind_code': int(wc),
        'wind_speed': float(ws),
        'tilt': float(tilt),
        'has_orig': 1,
        'has_stt': 1,
        'has_tkz': 1,
        'weather_snapshot_hhmm': weather_hhmm,
        'weather_source_kind': 'boatcast_bc_sui_prerace_only',
        'entry_source_kind': 'boatcast_bc_j_stt',
        'tilt_source_kind': 'boatcast_bc_j_tkz',
    }
    out.update(hist)
    return out


def fetch_and_build(
    hd: str,
    jcd: int,
    rno: int,
    current_card_csv: str,
    current_exhibition: Mapping[str, Any],
    timeout: int = 20,
) -> dict[str, Any]:
    tu = boatcast_tkz_url(hd, jcd, rno)
    su = boatcast_stt_url(hd, jcd, rno)
    wu = boatcast_sui_url(hd, jcd)
    tkz = _fetch(tu, f'{BOATCAST}/hp_txt/{jcd:02d}/bc_j_tkz_', timeout)
    stt = _fetch(su, f'{BOATCAST}/hp_txt/{jcd:02d}/bc_j_stt_', timeout)
    # Important: current LIVE weather is bc_sui only. Do not consult bc_rs1_2.
    sui = _fetch(wu, f'{BOATCAST}/m_txt/{jcd:02d}/bc_sui_', timeout)
    return build_from_sources(hd, jcd, rno, current_card_csv, current_exhibition, tkz, stt, sui)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True, help='YYYYMMDD')
    ap.add_argument('--jcd', required=True, type=int)
    ap.add_argument('--race', required=True, type=int)
    ap.add_argument('--current-card-csv', required=True)
    ap.add_argument('--current-exhibition-json', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--timeout', type=int, default=20)
    a = ap.parse_args()
    exhibition = json.loads(Path(a.current_exhibition_json).read_text(encoding='utf-8'))
    z = fetch_and_build(a.date, a.jcd, a.race, a.current_card_csv, exhibition, a.timeout)
    Path(a.out).write_text(json.dumps(z, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({
        'status': 'READY', 'race_code': z['race_code'], 'out': a.out,
        'history_population_n': z['history_population_n'],
        'history_end': z['history_end'],
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
