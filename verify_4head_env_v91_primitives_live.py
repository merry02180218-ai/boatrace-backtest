#!/usr/bin/env python3
"""Contract/parity checks for build_4head_env_v91_primitives_live.py."""
from __future__ import annotations

import math
from build_4head_env_v91_primitives_live import (
    PrimitiveBuildError, build, history_value, pct_rank_online,
    relative_deg, tilt_band_exact,
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
        'venue_code':1,'wind_code':3,'wind_speed':3.4,'wind_adjust_points':2,
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

    # v83 relative wind: Kiryu facing 90 deg and wind code 3 = 90 deg.
    close(relative_deg(1,3),0)

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
    close(z['score_wind_v83'],base+2)
    assert z['entry_confirmed_same']==1
    assert len(z)==21

    # Fail closed: no learned wind default, no result-blind bypass.
    bad=dict(ctx); bad.pop('wind_adjust_points')
    try: build(cur,bad)
    except PrimitiveBuildError: pass
    else: raise AssertionError('missing wind adjustment must fail closed')
    badcur=dict(cur);badcur['result_blind']=False
    try: build(badcur,ctx)
    except PrimitiveBuildError: pass
    else: raise AssertionError('non-result-blind current exhibition must fail')

    print('PASS verify_4head_env_v91_primitives_live')

if __name__=='__main__':main()
