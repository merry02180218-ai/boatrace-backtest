#!/usr/bin/env python3
from __future__ import annotations
import copy,math
from build_4head_v283_rows_live import V283RowBuildError,derive
from head4_v291_downstream_inference import BOATS,load_artifact,score_second,score_conditional_third,v283_top4

def main():
    a=load_artifact();fs=a['v283_SECOND']['features'];med=a['v283_SECOND']['imputer_median']
    base=dict(zip(fs,med));boats={str(b):dict(base) for b in BOATS}
    # Head boat 4 only needs current exhibition context.
    boats['4']={c:.5 for c in ('cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg')}
    # Make current values deterministic and boat-specific so vs4/pair formulas are testable.
    for b in BOATS:
        for c in ('cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg'):
            boats[str(b)][c]=.40+.01*b
    second,cond=derive({'boats':boats},a)
    assert len(second)==5 and [r['boat'] for r in second]==list(BOATS)
    assert len(cond)==20 and len({(r['second_boat'],r['third_boat']) for r in cond})==20
    assert all(list({k:r[k] for k in a['v283_SECOND']['features']})==a['v283_SECOND']['features'] for r in second)
    fs3=a['v283_COND_THIRD']['features']
    assert all(all(k in r for k in fs3) for r in cond)
    r=next(x for x in cond if x['second_boat']==1 and x['third_boat']==3)
    assert r['pair_second_inner']==1.0 and r['pair_third_inner']==1.0 and r['pair_distance']==2.0 and r['pair_third_minus_second']==2.0
    assert abs(r['t_cur_ex__vs4']-(.43-.5))<1e-15
    assert abs(r['t_cur_ex__abs4']-.07)<1e-15
    assert r['t_is_boat3']==1.0 and r['t_is_inner_edge3']==1.0
    p2=score_second(second,a);pc=score_conditional_third(cond,a);top=v283_top4(p2,pc)
    assert set(p2)==set(BOATS) and abs(sum(p2.values())-1)<1e-12
    for s in BOATS: assert abs(sum(v for (ss,_),v in pc.items() if ss==s)-1)<1e-12
    assert len(top)==4 and len(set(top))==4
    # Missing a frozen SECOND primitive must fail closed before scoring.
    bad=copy.deepcopy(boats);bad['1'].pop(fs[0])
    try: derive({'boats':bad},a)
    except V283RowBuildError: pass
    else: raise AssertionError('missing SECOND primitive did not fail closed')
    assert a['jul_aug_labels_used'] is False and a['september_labels_used'] is False and a['v96_production_signal_used'] is False
    print('HEAD4 v283 current-day row derivation contract PASS')
if __name__=='__main__':main()
