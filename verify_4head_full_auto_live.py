#!/usr/bin/env python3
"""Contract/wiring checks for run_4head_full_auto_live.py."""
from __future__ import annotations

import csv
import inspect
import tempfile
from pathlib import Path

import run_4head_full_auto_live as m


def write_csv(path:Path,row:dict):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow(row)


def main():
    code='202609140102'
    pre={
        'race_code':code,'PRE':'0.31','pre_eligible':'1',
        'legacy_score4':'44','racer4':'.4','hist_st_edge_4v3':'.2','wall3_weak':'.7',
        'inner12_resistance':'.2','motor4_2ren':'33.3','motor4_hist':'.5',
        'turnfoot4_prior':'.6','past_win4':'.1',
    }
    card={'レースコード':code,'レース場コード':'01','艇1_選手名':'A','艇2_選手名':'B','艇3_選手名':'C','艇4_選手名':'D','艇5_選手名':'E','艇6_選手名':'F'}
    waku={'レースコード':code,'x':'1'}
    calls=[]
    originals=(m.load_artifact,m.build_post_features,m.score_post,m.build_exhibition,m.build_env_context,
               m.build_env_primitives,m.assemble_env,m.build_v93,m.build_player,m.assemble_source)
    try:
        m.load_artifact=lambda p:calls.append(('artifact',)) or {'A':1}
        m.build_post_features=lambda hd,jcd,rno,timeout: calls.append(('post_features',)) or {
            'features':{
                'ex_st_rank4':.8,'ex_st_4':.1,'ex_st_edge_4v3':.02,'orig_straight4':.7,
                'orig_lap4':.6,'orig_turn4':.5,'tilt4':0.0,
            },'result_or_payout_requested':False,
        }
        m.score_post=lambda row,a:calls.append(('post_score',len(row))) or .29
        m.build_exhibition=lambda hd,jcd,rno,timeout:calls.append(('exhibition',)) or {
            'race_code':code,'result_blind':True,'odds_used':False,
            'current_boats':{str(b):{} for b in range(1,7)},'st_flat':{}
        }
        m.build_env_context=lambda *args,**kwargs:calls.append(('env_context',)) or {
            'history_start':'2025-10-01','history_end':'2026-09-13','history_population_n':99,
            'weather_source_kind':'boatcast_bc_sui_prerace_only','weather_snapshot_hhmm':'1200',
            'entry_source_kind':'boatcast_bc_j_stt','tilt_source_kind':'boatcast_bc_j_tkz',
            'pinned_boatracecsv_commit':'563c69ccd28853b8b4953489c673877a9dfeb4e8'}
        m.build_env_primitives=lambda ex,ctx:calls.append(('env_primitives',)) or {'preview_comp':.5}
        m.assemble_env=lambda p,pre,post,a:calls.append(('env_assemble',pre,post)) or {'PRE':pre,'POST':post}
        import head4_v291_downstream_inference as inf
        orig_score_env=inf.score_env_entry
        inf.score_env_entry=lambda row,a:calls.append(('env_score',)) or .27
        m.build_v93=lambda c,w,e:calls.append(('v93',)) or {'race_code':code,'result_blind':True}
        m.build_player=lambda c,td,hs:calls.append(('player',td.isoformat(),hs.isoformat())) or {'race_code':code,'result_blind':True}
        m.assemble_source=lambda code_,pre_,post_,base,env,ex,v93,player: calls.append(('source',pre_,post_)) or {
            'race_code':code_,'PRE':pre_,'POST':post_,'env_primitives':{},'flat_row':{},'current_boats':{},'_source_meta':{'result_blind':True}
        }
        try:
            with tempfile.TemporaryDirectory() as td:
                td=Path(td);cp=td/'cards.csv';wp=td/'waku.csv';pp=td/'pre.csv'
                write_csv(cp,card);write_csv(wp,waku);write_csv(pp,pre)
                z=m.build_all('20260914',1,2,str(cp),str(wp),str(pp),'artifact.json','2025-10-01',20)
                assert z['race_code']==code and z['PRE']==.31 and z['POST']==.29 and z['ENV_ENTRY']==.27
                assert z['result_blind'] is True and z['target_day_results_used'] is False
                assert z['odds_used_upstream'] is False and z['payout_used'] is False
                names=[x[0] for x in calls]
                assert names==['artifact','post_features','post_score','exhibition','env_context','env_primitives','env_assemble','env_score','v93','player','source'],names
        finally:
            inf.score_env_entry=orig_score_env
    finally:
        (m.load_artifact,m.build_post_features,m.score_post,m.build_exhibition,m.build_env_context,
         m.build_env_primitives,m.assemble_env,m.build_v93,m.build_player,m.assemble_source)=originals

    src=inspect.getsource(m)
    assert 'build_post_features' in src and 'score_post' in src
    assert 'build_exhibition' in src and 'build_env_context' in src and 'build_env_primitives' in src
    assert 'build_v93' in src and 'build_player' in src and 'assemble_source' in src
    assert "run_4head_v291_varn_auto_live.py" in src
    # Final accepted runner, not this orchestrator, owns market acquisition.
    assert 'fetch_odds' not in src and 'data/results/realtime' not in src
    print('PASS verify_4head_full_auto_live')


if __name__=='__main__':main()
