#!/usr/bin/env python3
"""Contract/parity checks for build_4head_env_v91_primitives_live.py."""
from __future__ import annotations

import math
from build_4head_env_v91_primitives_live import (
    PrimitiveBuildError, build, history_value, pct_rank_online,
    relative_deg, relative_wind_exact, tilt_band_exact,
    wind_adjust_points_v83_head4, wind_speed_bin_exact,
)


def close(a,b,eps=1e-10):
    assert math.isclose(float(a),float(b),rel_tol=0,abs_tol=eps),(a,b)


def fixture():
    current={
        'result_blind':True,
        'current_boats':{
            '4':{'cur_ex':0.8,'cur_orig_straight':0.6,'cur_orig_avg':0.7}
        },
        'st_flat':{'st_corr_strength_b4':0.9,'st_raw_strength_b4':0.5},
    }
    context={
        'history_prior1':0.4,'history_prior2':0.8,'history_has2':1,
        'history_population':[0.2,0.5,0.7,0.9],
        'tilt':0.5,'entry_course_preview':4,
        # Kiryu faces 90deg. wind code3=90 => tailwind; 3.4m => 3-4m => neutral.
        'venue_code':1,'wind_code':3,'wind_speed':3.4,
        'has_orig':1,'has_stt':1,'has_tkz':1,
    }
    return current,context


def main():
    # Exact v51 tilt-band boundaries.
    assert tilt_band_exact(-0.5)==-1
    assert tilt_band_exact(-0.49)==0
    assert tilt_band_exact(0.49)==0
    assert tilt_band_exact(0.5)==0.5
    assert tilt_band_exact(0.99)==0.5
    assert tilt_band_exact(1.0)==1

    # Exact v74 4-corner history semantics.
    close(history_value(.4,.8,1),.64)
    close(history_value(.4,.8,0),.4)
    close(pct_rank_online(.64,[.2,.5,.7,.9]),.5)
    close(pct_rank_online(.64,[]),.5)

    # Exact v83 relative wind and speed-bin boundaries.
    close(relative_deg(1,3),0)
    assert relative_wind_exact(0)=='追い'
    assert relative_wind_exact(44.999)=='追い'
    assert relative_wind_exact(45)=='右横'
    assert relative_wind_exact(135)=='向かい'
    assert relative_wind_exact(225)=='左横'
    assert relative_wind_exact(315)=='追い'
    assert wind_speed_bin_exact(2)=='0-2m'
    assert wind_speed_bin_exact(2.01)=='3-4m'
    assert wind_speed_bin_exact(4)=='3-4m'
    assert wind_speed_bin_exact(4.01)=='5m+'

    # Frozen v83 HEAD4 old-period mapping. Only these 3 cells are non-neutral.
    assert wind_adjust_points_v83_head4(0,2)==-2       # 追い_0-2m
    assert wind_adjust_points_v83_head4(180,2)==-2     # 向かい_0-2m
    assert wind_adjust_points_v83_head4(270,3)==2      # 左横_3-4m
    for deg,speed in [(0,3),(0,5),(90,1),(90,3),(90,5),(180,3),(180,5),(270,1),(270,5)]:
        assert wind_adjust_points_v83_head4(deg,speed)==0,(deg,speed)

    cur,ctx=fixture(); z=build(cur,ctx)
    preview=.28*.8+.30*.9+.22*.6+.15*.7+.05*.5
    corr20=.28*.8+.20*.9+.32*.6+.15*.7+.05*.5
    raw20=.28*.8+.20*.5+.32*.6+.15*.7+.05*.5
    hp=.5; hadj=2*(2*hp-1); tbonus=3.0
    base=100*preview+hadj+tbonus
    close(z['preview_comp'],preview)
    close(z['history_pct_online'],hp)
    close(z['history_adjust_online'],hadj)
    close(z['tilt_bonus'],tbonus)
    close(z['score_BASE_v91'],base)
    close(z['score_CORR20_v91'],base+100*(corr20-preview))
    close(z['score_RAW20_v91'],base+100*(raw20-preview))
    close(z['wind_adjust_points'],0)
    close(z['score_wind_v83'],base)
    assert z['entry_confirmed_same']==1
    assert len(z)==21

    # A live unfavorable cell derives -2 internally; no manual learned label is accepted/needed.
    badwind=dict(ctx); badwind['wind_speed']=2.0
    z2=build(cur,badwind)
    close(z2['wind_adjust_points'],-2)
    close(z2['score_wind_v83'],base-2)

    # Fail closed on result-blind bypass / invalid wind.
    badcur=dict(cur);badcur['result_blind']=False
    try: build(badcur,ctx)
    except PrimitiveBuildError: pass
    else: raise AssertionError('non-result-blind current exhibition must fail')
    bad=dict(ctx);bad['wind_speed']=-1
    try: build(cur,bad)
    except PrimitiveBuildError: pass
    else: raise AssertionError('negative wind speed must fail')

    print('PASS verify_4head_env_v91_primitives_live_v2')

if __name__=='__main__':main()
