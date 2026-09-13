#!/usr/bin/env python3
from __future__ import annotations
from datetime import date
import build_4head_player_history_live as m

def card(code,names):
    z={'レースコード':code}
    for b,n in enumerate(names,1):z[f'艇{b}_選手名']=n
    return z

def main():
    target=card('202609120101',['B','C','D','A','E','F'])
    h1=card('202609100101',['A','B','X','Y','Z','Q'])
    h2=card('202609110101',['X','Y','Z','A','Q','B'])
    r1={'レースコード':'202609100101','1着_艇番':'1','2着_艇番':'2'}
    r2={'レースコード':'202609110101','1着_艇番':'6','2着_艇番':'4'}
    calls=[]
    def fake_rows(path):
        calls.append(path)
        if '2026/09/12' in path:raise AssertionError('target-day source accessed')
        if path.endswith('2026/09/10.csv') and 'race_cards' in path:return [h1]
        if path.endswith('2026/09/10.csv') and 'results' in path:return [r1]
        if path.endswith('2026/09/11.csv') and 'race_cards' in path:return [h2]
        if path.endswith('2026/09/11.csv') and 'results' in path:return [r2]
        return []
    old=m.rows;m.rows=fake_rows
    try:z=m.build(target,date(2026,9,12),date(2026,9,10))
    finally:m.rows=old
    f=z['player_flat']
    exp={
      'b4_pl_all_win':1/3,'b4_pl_all_p2':2/3,'b4_pl_frame_win':.09375,
      'b4_pl_frame_p2':.4375,'b4_pl_recent_p2':1.0,
    }
    for k,v in exp.items():
        if abs(f[k]-v)>1e-10:raise AssertionError((k,f[k],v))
    assert z['history_end']=='2026-09-11'
    assert z['same_day_results_used'] is False
    assert z['historical_outcomes_use']=='causal_feature_state_only'
    assert z['model_fitting_used'] is False and z['calibration_used'] is False and z['threshold_tuning_used'] is False
    assert z['odds_used'] is False and z['payout_used'] is False and z['v96_used'] is False
    assert all('2026/09/12' not in p for p in calls)
    print('HEAD4 player history live verification PASS')
if __name__=='__main__':main()
