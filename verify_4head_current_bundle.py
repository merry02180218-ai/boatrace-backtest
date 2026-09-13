#!/usr/bin/env python3
from __future__ import annotations
from build_4head_current_bundle import build,BundleBuildError
from assemble_4head_v291_varn_live_input import assemble

def fixture():
    r={
      'v91_ex':.6,'score_CORR20_v91':54.1,'score_wind_v83':53.7,'score_RAW20_v91':53.6,'score_BASE_v91':54.2,'preview_comp':.54,
      'opp_score_b1_v93':.45,
    }
    for b in range(1,7):
        r[f'b{b}_pl_all_p2']=.20+.01*b;r[f'b{b}_pl_all_win']=.07+.01*b;r[f'b{b}_pl_frame_p2']=.16+.01*b
        r[f'b{b}_pl_recent_p2']=.22+.01*b;r[f'b{b}_pl_frame_win']=.05+.005*b
        if b!=4:
            for k,v in [('grade',.4),('national',.35),('local',.33),('motor',.55),('nst',.5)]:r[f'opp_{k}_b{b}_v93']=v+.001*b
            for k,v in [('raw',.08),('raw_strength',.5),('raw_rank',3.),('corr_strength',.5),('corr_rank',3.)]:r[f'st_{k}_b{b}']=v+.001*b
    cur={str(b):{'cur_ex':.4+.01*b,'cur_st':.5-.01*b,'cur_orig_lap':.48,'cur_orig_turn':.52,'cur_orig_straight':.51,'cur_orig_avg':.503333} for b in range(1,7)}
    env={
      'preview_comp':.54,'relative_deg':90,'wind_speed':2,'wind_adjust_points':0,'entry_confirmed_same':1,'entry_course_preview':4,
      'has_orig':1,'has_stt':1,'has_tkz':1,'tilt':0,'tilt_bonus':-.04,'v91_ex':.6,'v91_st_corr':.6,'v91_st_raw':.6,'v91_straight':.5,
      'score_BASE_v91':54.2,'score_CORR20_v91':54.1,'score_RAW20_v91':53.6,'score_wind_v83':53.7,'history_adjust_online':.68,'history_pct_online':.67,
    }
    return {'race_code':'202609130101','PRE':.29,'POST':.26,'env_primitives':env,'flat_row':r,'current_boats':cur}

def main():
    src=fixture();b=build(src)
    assert b['_source_meta']['result_blind'] and not b['_source_meta']['odds_used']
    assert abs(b['a_features']['rel_pl_all_win_4v1']-(src['flat_row']['b4_pl_all_win']-src['flat_row']['b1_pl_all_win']))<1e-12
    assert abs(b['a_features']['rel_pl_recent_p2_4v3']-(src['flat_row']['b4_pl_recent_p2']-src['flat_row']['b3_pl_recent_p2']))<1e-12
    assert b['boats']['1']['v93_grade']==src['flat_row']['opp_grade_b1_v93']
    assert b['boats']['5']['pref_pl_recent_p2']==src['flat_row']['b5_pl_recent_p2']
    out=assemble(b)
    assert out['_auto_meta']['policy']=='HEAD4_V291_COMP7_VARN_F4_N16'
    assert len(out['p2'])==5 and len(out['cond'])==20
    bad=fixture();bad['flat_row']['winner']=4
    try:build(bad);raise AssertionError('result leakage must fail closed')
    except BundleBuildError:pass
    bad=fixture();del bad['flat_row']['b3_pl_recent_p2']
    try:build(bad);raise AssertionError('missing causal primitive must fail closed')
    except BundleBuildError:pass
    print('PASS current bundle -> frozen HEAD4 V291 VARN assembler; result/market leakage guards PASS')
if __name__=='__main__':main()
