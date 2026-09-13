#!/usr/bin/env python3
from __future__ import annotations
from backtest import grade_score,clamp,pct_motor,race_features
from build_4head_v93_primitives_live import build

def fixture():
    code='202609130101';card={'レースコード':code};waku={'レースコード':code}
    for b in range(1,7):
        p=f'艇{b}_';card.update({p+'選手名':f'P{b}',p+'級別':['A1','A2','B1','B2','A1','A2'][b-1],p+'全国平均ST':.12+.01*b,
          p+'全国勝率':5.0+.2*b,p+'当地勝率':4.5+.1*b,p+'モーター2連対率':30+b,p+'モーター3連対率':45+b})
        waku.update({p+'枠番別平均ST':.13+.01*b,p+'枠番別勝率':4.0+.2*b,p+'枠番別平均スタート順':3.0})
    boats={};stflat={}
    for b in range(1,7):
        boats[str(b)]={'cur_ex':1-(b-1)/5,'cur_st':1-(b-1)/5,'cur_orig_lap':.5,'cur_orig_turn':.6,'cur_orig_straight':.55,'cur_orig_avg':.55}
        stflat[f'st_corr_strength_b{b}']=1-(b-1)/5
    ex={'race_code':code,'current_boats':boats,'st_flat':stflat,'result_blind':True,'odds_used':False}
    return card,waku,ex

def main():
    card,waku,ex=fixture();z=build(card,waku,ex);assert z['result_blind'] and not z['odds_used'] and not z['v96_used']
    flat=z['v93_flat'];x=race_features(card,waku);b=1;a=x[b]
    motor=.62*pct_motor(a['motor2'])+.38*pct_motor(a['motor3']);q=clamp((a['wr']-3)/5);loc=clamp((a['local']-2.5)/5.5);ww=clamp(a['waku_wr']/8);nst=clamp((.24-a['nst'])/.14);gr=grade_score(a['grade'])
    direct=.35*ex['current_boats']['1']['cur_ex']+.20*ex['st_flat']['st_corr_strength_b1']+.25*.6+.20*.55
    score=.16*gr+.19*q+.08*loc+.17*motor+.13*ww+.09*nst+.18*direct
    assert flat['opp_grade_b1_v93']==round(gr,6);assert flat['opp_national_b1_v93']==round(q,6);assert flat['opp_score_b1_v93']==round(score,6)
    for b in (1,2,3,5,6):
        for k in ('grade','national','local','motor','waku','nst','direct'):assert f'opp_{k}_b{b}_v93' in flat
        assert f'opp_score_b{b}_v93' in flat
    print('PASS exact v93 current opponent primitive formula')
if __name__=='__main__':main()
