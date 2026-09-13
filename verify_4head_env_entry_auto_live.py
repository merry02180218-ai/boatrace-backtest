#!/usr/bin/env python3
"""Wiring/guard checks for build_4head_env_entry_auto_live.py."""
from __future__ import annotations

import inspect
import build_4head_env_entry_auto_live as m


def main() -> None:
    calls = []
    originals = (m.build_exhibition, m.build_context, m.build_primitives,
                 m.load_artifact, m.assemble_env, m.score_env_entry)
    try:
        m.build_exhibition = lambda hd,jcd,rno,timeout: (
            calls.append(('exhibition',hd,jcd,rno)) or
            {'race_code':f'{hd}{jcd:02d}{rno:02d}','result_blind':True,'odds_used':False,
             'current_boats':{str(b):{} for b in range(1,7)}})
        m.build_context = lambda hd,jcd,rno,card,ex,timeout: (
            calls.append(('context',card)) or
            {'history_start':'2025-10-01','history_end':'2026-09-13','history_population_n':123,
             'weather_source_kind':'boatcast_bc_sui_prerace_only','weather_snapshot_hhmm':'1234',
             'entry_source_kind':'boatcast_bc_j_stt','tilt_source_kind':'boatcast_bc_j_tkz',
             'pinned_boatracecsv_commit':'563c69ccd28853b8b4953489c673877a9dfeb4e8'})
        m.build_primitives = lambda ex,ctx: calls.append(('primitives',)) or {'preview_comp':.5}
        m.load_artifact = lambda path: calls.append(('artifact',path)) or {'x':1}
        m.assemble_env = lambda primitives,pre,post,artifact: (
            calls.append(('env',pre,post)) or {'PRE':float(pre),'POST':float(post),'preview_comp':.5})
        m.score_env_entry = lambda row,artifact: calls.append(('score',)) or .33

        z = m.build('20260914',1,2,'cards.csv',.28,.25,'artifact.json',20)
        assert z['race_code']=='202609140102'
        assert z['result_blind'] is True and z['odds_used'] is False and z['payout_used'] is False
        assert z['same_day_results_used'] is False
        assert z['jul_aug_labels_used'] is False and z['september_labels_used'] is False
        assert z['ENV_ENTRY']==.33
        assert [x[0] for x in calls] == ['exhibition','context','primitives','artifact','env','score'], calls
        assert z['context_audit']['weather_source_kind']=='boatcast_bc_sui_prerace_only'
    finally:
        (m.build_exhibition, m.build_context, m.build_primitives,
         m.load_artifact, m.assemble_env, m.score_env_entry) = originals

    src = inspect.getsource(m)
    assert 'data/results' not in src
    assert 'bc_rs1_2' not in src
    assert 'fetch_odds' not in src
    assert 'build_exhibition' in src and 'build_context' in src and 'build_primitives' in src
    assert 'assemble_env' in src and 'score_env_entry' in src
    print('PASS verify_4head_env_entry_auto_live')


if __name__ == '__main__':
    main()
