#!/usr/bin/env python3
"""Contract/parser/source-allow-list checks for build_4head_env_context_live.py."""
from __future__ import annotations

import csv
import inspect
import tempfile
from pathlib import Path

import build_4head_env_context_live as m


def stt_fixture() -> str:
    return 'data=1\n1\n' + '\n'.join([
        '2\t1\tA\t.15\t.08\t\t1',
        '1\t2\tB\t.16\t.09\t\t2',
        '3\t3\tC\t.17\t.10\t\t3',
        '4\t4\tD\t.18\t.11\t\t4',
        '5\t5\tE\t.19\t.12\t\t5',
        '6\t6\tF\t.20\t.13\t\t6',
    ]) + '\n'


def tkz_fixture() -> str:
    rows = []
    for b in range(1, 7):
        tilt = '+ 0.5' if b == 4 else '+ 0.0'
        rows.append(f'P{b}\t6.7{b}\t0\t000\t52.0\t0\t{tilt}')
    return 'data=1\n1\n' + '\n'.join(rows) + '\n'


def sui_fixture() -> str:
    return '0900\t1\t2\t北西 (追い)\t3.5\t+24.0\t+22.0\n0930\t1\t2\t南東 (向い)\t4.0\t+25.0\t+22.5\n'


def write_card(path: Path) -> None:
    fields = ['レースコード', 'レース場コード', '艇4_選手名']
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerow({'レースコード':'202609140101','レース場コード':'01','艇4_選手名':'選手　四'})


def main() -> None:
    c = m.parse_stt_courses(stt_fixture())
    assert c[1] == 2 and c[2] == 1 and c[4] == 4, c
    assert m.parse_tkz_tilt4(tkz_fixture()) == 0.5
    wc, ws, hhmm = m.parse_sui_weather(sui_fixture())
    assert wc == 4 and ws == 4.0 and hhmm == '0930', (wc, ws, hhmm)

    # Exact pinned source URL families. Fetch code must actually call only the
    # current pre-race TKZ/STT/SUI URLs; explanatory comments are irrelevant.
    assert '/bc_j_tkz_' in m.boatcast_tkz_url('20260914', 1, 1)
    assert '/bc_j_stt_' in m.boatcast_stt_url('20260914', 1, 1)
    assert '/bc_sui_' in m.boatcast_sui_url('20260914', 1)
    src = inspect.getsource(m.fetch_and_build)
    assert 'boatcast_tkz_url' in src and 'boatcast_stt_url' in src and 'boatcast_sui_url' in src
    assert "_fetch(wu, f'{BOATCAST}/m_txt/{jcd:02d}/bc_sui_'" in src
    assert 'results/' not in inspect.getsource(m)
    assert 'payout' not in src.lower()
    assert 'odds' not in src.lower()

    # Build contract without expensive history replay; history replay has its own
    # exact v74 imports/update order and is checked statically below.
    original = m.build_history_before
    m.build_history_before = lambda target, venue, player: {
        'history_prior1':.4, 'history_prior2':.8, 'history_has2':1,
        'history_population':[.2,.5,.7,.9], 'history_days_loaded':10,
        'history_population_n':4, 'history_raw4_seen':4,
        'history_start':'2025-10-01', 'history_end':'2026-09-13',
    }
    try:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'cards.csv'; write_card(p)
            exhibition = {
                'race_code':'202609140101', 'result_blind':True, 'odds_used':False,
                'current_boats':{str(b):{'cur_ex':.5} for b in range(1,7)},
            }
            z = m.build_from_sources('20260914', 1, 1, str(p), exhibition,
                                     tkz_fixture(), stt_fixture(), sui_fixture())
            assert z['result_blind'] is True
            assert z['same_day_results_used'] is False
            assert z['jul_aug_outcomes_used'] is False
            assert z['september_outcomes_used'] is False
            assert z['entry_course_preview'] == 4
            assert z['wind_code'] == 4 and z['wind_speed'] == 4.0
            assert z['tilt'] == .5
            assert z['has_orig'] == z['has_stt'] == z['has_tkz'] == 1
            assert z['history_end'] == '2026-09-13'
    finally:
        m.build_history_before = original

    hsrc = inspect.getsource(m.build_history_before)
    assert 'while d < target' in hsrc
    assert 'raw_candidates(cards, w10, cache, mhist, ph)' in hsrc
    assert "histvals[r['model']].append(history_value(r))" in hsrc
    assert 'update_preview_states(cards, tkzrows, orows, cache, ph)' in hsrc
    assert 'ingest_motor(mhist, seen, d)' in hsrc
    assert 'data/results' not in hsrc and 'payout' not in hsrc and 'odds' not in hsrc

    for bad in ('', 'data=1\n1\n'):
        try: m.parse_stt_courses(bad)
        except m.EnvContextBuildError: pass
        else: raise AssertionError('malformed STT must fail closed')
    try: m.parse_sui_weather('bad\n')
    except m.EnvContextBuildError: pass
    else: raise AssertionError('missing weather must fail closed')

    print('PASS verify_4head_env_context_live')


if __name__ == '__main__':
    main()
