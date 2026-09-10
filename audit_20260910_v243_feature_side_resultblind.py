#!/usr/bin/env python3
"""Compute only v243 exhibition-side features for 2026-09-10 two PRE candidates.
Loads programs/previews only. NEVER loads results/payouts/odds.
"""
from datetime import date,timedelta
from collections import defaultdict
import pandas as pd
from backtest import rows,race_features,pct_motor
from analyze_v23_20260902_daypreview import by_code
from backtest_v51_lane_corrected_tickets import corrected_direct,ff

TARGETS=[('児島',16,5),('鳴門',14,7)]
KEEP=-0.1999999999999999
RESCUE=0.5672342857142857

def learn_bias_until(end=date(2026,9,9),start=date(2026,8,1)):
    sums=defaultdict(list); allv=[]; d=start
    while d<=end:
        for r in rows(f'data/previews/stt/{d:%Y/%m/%d}.csv'):
            for b in range(1,7):
                v=ff(r.get(f'艇{b}_スタート展示'))
                if v is not None and -.30<v<1.0:
                    sums[b].append(v);allv.append(v)
        d+=timedelta(days=1)
    g=sum(allv)/len(allv)
    return {b:(sum(sums[b])/len(sums[b])-g if sums[b] else 0.) for b in range(1,7)}

def main():
    ymd='2026/09/10'
    cards=by_code(f'data/programs/race_cards/{ymd}.csv')
    waku=by_code(f'data/programs/waku10/{ymd}.csv')
    tkz=by_code(f'data/previews/tkz/{ymd}.csv')
    stt=by_code(f'data/previews/stt/{ymd}.csv')
    orig=by_code(f'data/previews/original_exhibition/{ymd}.csv')
    bias=learn_bias_until()
    print('BIAS',bias)
    print('SOURCE_COUNTS',len(cards),len(waku),len(tkz),len(stt),len(orig))
    for name,jcd,rno in TARGETS:
        code=f'20260910{jcd:02d}{rno:02d}'
        print('\nTARGET',name,rno,'code',code)
        card=cards.get(code,{}); ww=waku.get(code,{})
        print('PRESENT',bool(card),bool(tkz.get(code)),bool(stt.get(code)),bool(orig.get(code)))
        if not card: continue
        x=race_features(card,ww)
        ex,st,os=corrected_direct(code,tkz,stt,orig,bias)
        motor=.62*pct_motor(x[3]['motor2'])+.38*pct_motor(x[3]['motor3'])
        minus=st[3]-st[5]
        attack=.28*ex[3]+.28*st[3]+.24*os[3]['straight']+.20*motor
        print('EX',ex)
        print('ST',st)
        print('OS3',os[3])
        print('MOTOR3',motor,'motor2',x[3]['motor2'],'motor3',x[3]['motor3'])
        print('f__c_b3_minus_b5_st',repr(minus),'KEEP_PASS',minus>=KEEP,'KEEP_THR',repr(KEEP))
        print('f__c_attack3_stretch',repr(attack),'RESCUE_PASS',attack<=RESCUE,'RESCUE_THR',repr(RESCUE))
if __name__=='__main__':main()
