#!/usr/bin/env python3
from __future__ import annotations
import math
from backtest_v3 import CORR
from backtest_v51_lane_corrected_tickets import rank_scores
from build_4head_v283_current_exhibition_live import build_from_sources,parse_display_times

def fixture():
    html='<html><body><table><tr><th>艇</th><th>展示タイム</th></tr>'+''.join(f'<tr><td>{b}</td><td>{6.80+.02*b:.2f}</td></tr>' for b in range(1,7))+'</table></body></html>'
    st='\n'.join(f'{b}\tx\tx\tx\t{0.04+0.02*b:.2f}\t' for b in range(1,7))
    # parser: data marker, status row, labels row, then boat + ignored column + metric values.
    orig='data=1\n1\tOK\n一周\tまわり足\t直線\n'+'\n'.join(f'{b}\tx\t{36.0+.1*b:.2f}\t{5.0+.03*b:.2f}\t{6.5+.02*b:.2f}' for b in range(1,7))
    bias={1:.01,2:.005,3:0.,4:-.005,5:-.01,6:-.015}
    return html,st,orig,bias

def main():
    html,st,orig,bias=fixture();z=build_from_sources('20260913',1,1,html,st,orig,bias)
    assert z['result_blind'] is True and z['odds_used'] is False
    assert z['race_code']=='202609130101' and set(z['current_boats'])==set(map(str,range(1,7)))
    d=parse_display_times(html);ex=rank_scores({b:d[b]+CORR[b]['展示'] for b in range(1,7)},True)
    for b in range(1,7):
        q=z['current_boats'][str(b)]
        assert abs(q['cur_ex']-ex[b])<1e-12
        assert set(q)=={'cur_ex','cur_st','cur_orig_lap','cur_orig_turn','cur_orig_straight','cur_orig_avg'}
        assert all(math.isfinite(float(v)) for v in q.values())
        assert all(0<=float(v)<=1 for v in q.values())
    # Faster corrected ST must never rank worse in this monotone fixture.
    assert z['current_boats']['1']['cur_st']>=z['current_boats']['6']['cur_st']
    print('PASS v283 six-boat current exhibition result-blind builder')
if __name__=='__main__':main()
