#!/usr/bin/env python3
"""Build exact historical v93 opponent primitives from current causal inputs.

Inputs are current result-blind race_cards/waku10 plus the already-frozen current
exhibition object. Formula is copied from analyze_v93_4corner_second_third.py.
No outcomes, payouts or odds are read.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any
from backtest import rows,race_features,grade_score,clamp,pct_motor

BOATS=(1,2,3,5,6)
class V93BuildError(RuntimeError): pass

def bycode(rs):return {str(r.get('レースコード','')).zfill(12):r for r in rs if r.get('レースコード')}

def build(card:dict[str,Any],waku:dict[str,Any],exhibition:dict[str,Any])->dict[str,Any]:
    code=str(card.get('レースコード','')).zfill(12)
    if len(code)!=12 or not code.isdigit():raise V93BuildError('invalid race card code')
    if str(waku.get('レースコード','')).zfill(12)!=code:raise V93BuildError('waku race_code mismatch')
    if str(exhibition.get('race_code','')).zfill(12)!=code:raise V93BuildError('exhibition race_code mismatch')
    if not exhibition.get('result_blind') or exhibition.get('odds_used'):raise V93BuildError('exhibition not result-blind')
    x=race_features(card,waku)
    if not x:raise V93BuildError('race_features unavailable')
    cb=exhibition.get('current_boats') or {};stf=exhibition.get('st_flat') or {}
    out={}
    for b in BOATS:
        if b not in x or str(b) not in cb:raise V93BuildError(f'missing boat {b}')
        z=x[b];cur=cb[str(b)]
        motor=.62*pct_motor(z['motor2'])+.38*pct_motor(z['motor3'])
        q=clamp((z['wr']-3.0)/5.0);loc=clamp((z['local']-2.5)/5.5);ww=clamp(z['waku_wr']/8.0)
        nst=clamp((.24-z['nst'])/.14);gr=grade_score(z['grade'])
        st=float(stf[f'st_corr_strength_b{b}'])
        direct=.35*float(cur['cur_ex'])+.20*st+.25*float(cur['cur_orig_turn'])+.20*float(cur['cur_orig_avg'])
        total=.16*gr+.19*q+.08*loc+.17*motor+.13*ww+.09*nst+.18*direct
        parts={'grade':gr,'national':q,'local':loc,'motor':motor,'waku':ww,'nst':nst,'direct':direct}
        out[f'opp_score_b{b}_v93']=round(total,6)
        for k,v in parts.items():out[f'opp_{k}_b{b}_v93']=round(float(v),6)
    return {'schema':'head4_v93_primitives_live_v1','race_code':code,'v93_flat':out,'result_blind':True,'odds_used':False,'v96_used':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--race-cards',required=True);ap.add_argument('--waku10',required=True);ap.add_argument('--exhibition-json',required=True);ap.add_argument('--race-code',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    cards=bycode(rows(a.race_cards));waku=bycode(rows(a.waku10));code=str(a.race_code).zfill(12)
    if code not in cards or code not in waku:raise SystemExit(f'missing current PRE row {code}')
    ex=json.loads(Path(a.exhibition_json).read_text(encoding='utf-8'))
    z=build(cards[code],waku[code],ex);Path(a.out).write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'READY','race_code':code,'out':a.out},ensure_ascii=False))
if __name__=='__main__':main()
