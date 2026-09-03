"""v56 replay: 2026-08-20 using the current operational flow.

Protocol (as if run on 2026-08-20):
1) PRE candidates come from v46 pre-race candidate rows with result/target removed.
2) Current direct info is frame-corrected exhibition/original exhibition and training-only ST frame bias.
3) 3-makuri and 5-head are the current live rules: direct A (score>=55) + six tickets from v53.
4) 3-makurizashi and 4-corner remain observation/validation only; 4-corner also gets the v55 structure diagnostic.
5) PRE and DIRECT snapshots are written before the target-day result/payout is read.
6) Results/payouts are joined only after all decisions/tickets are frozen.

All v53 pair weights are learned/tuned only through 2026-07-15. v55 formula/threshold are also fixed only through 2026-07-15.
Actual entry and STT course/entry columns are not used.
"""
import csv
from collections import Counter

from backtest_v53_pair_and_0902_flow import (
    MODELS, HEAD, VENUE, learn_fit_priors, learn_st_frame_bias, tune_pair_weights,
    load_source, freeze, settle, write_csv
)
import backtest_v55_4corner_structure as v55

DAY='2026-08-20'
LIVE={'3まくり','5頭展開'}


def fmt(code):
    v=int(code[8:10]);r=int(code[10:12]);return f'{VENUE.get(v,v)}{r}R'


def pre_snapshot(src):
    out=[]
    for r in src:
        if r.get('date')!=DAY:continue
        code=r['race_code'];m=r['model'];v=int(code[8:10]);rn=int(code[10:12])
        out.append({
            'date':DAY,'race_code':code,'venue':VENUE.get(v,str(v)),'race_no':rn,
            'model':m,'head_boat':HEAD[m],
            'history_pct':r.get('history_pct',''),'history_adjust':r.get('history_adjust',''),
            'prior1':r.get('prior1',''),'prior2':r.get('prior2','')
        })
    return out


def v55_day_diagnostic():
    # Formula and threshold are selected only from FIT/TUNE windows ending 2026-07-15.
    frozen=v55.freeze()
    settled=v55.settle(frozen)
    chosen,_=v55.choose_formula(settled)
    _,th,_=v55.choose_threshold(settled,chosen)
    ans={}
    for z in frozen:
        if z['date']!=DAY:continue
        q=dict(z)
        q['v55_formula']=chosen;q['v55_threshold']=th
        q['v55_score']=q[f'score_{chosen}'];q['v55_selected']=int(q['v55_score']>=th)
        ans[q['race_code']]=q
    return ans,chosen,th


def main():
    pri,_=learn_fit_priors();stbias=learn_st_frame_bias();pairw,_=tune_pair_weights(pri,stbias)
    src=load_source()

    # 1. PRE snapshot (no current direct/result/payout).
    pre=pre_snapshot(src)
    write_csv('v56_20260820_pre.csv',pre)

    # 2. DIRECT decisions/tickets are frozen without reading target-day result/payout.
    frozen_all=freeze(src,stbias,pri,pairw)
    direct=[dict(z) for z in frozen_all if z['date']==DAY]
    diag4,form4,th4=v55_day_diagnostic()
    for z in direct:
        d4=diag4.get(z['race_code']) if z['model']=='4カドまくり' else None
        z['v55_formula']=form4 if d4 else ''
        z['v55_score']=d4.get('v55_score','') if d4 else ''
        z['v55_threshold']=th4 if d4 else ''
        z['v55_selected']=d4.get('v55_selected','') if d4 else ''
        z['live_action']='BUY' if z['model'] in LIVE and z['approved_A'] else 'OBSERVE'
        z['live_points']=6 if z['live_action']=='BUY' else 0
        z['live_tickets']=z['tickets_6'] if z['live_action']=='BUY' else ''
    write_csv('v56_20260820_direct.csv',direct)

    # 3. Only now join Aug 20 results/payouts.
    settled=settle(direct)
    for z in settled:
        if z['live_action']=='BUY':
            z['live_invest']=z['invest_6'];z['live_hit']=z['hit_6'];z['live_return']=z['return_6']
        else:
            z['live_invest']=0;z['live_hit']=0;z['live_return']=0
    write_csv('v56_20260820_settled.csv',settled)

    inv=sum(z['live_invest'] for z in settled);ret=sum(z['live_return'] for z in settled)
    roi=100*ret/inv if inv else 0
    buys=[z for z in settled if z['live_action']=='BUY']
    prec=Counter(r['model'] for r in pre);dirc=Counter(z['model'] for z in direct)

    L=['# v56 2026-08-20 一連フロー再現','',
       'PRE候補 → 枠補正済み直前情報 → BUY/OBSERVE固定 → その後に結果/払戻照合。',
       '実進入・ST展示コース欄は不使用。3まくり/5頭のみ現行主力の A以上・6点を実購入扱い。',
       '3まくり差し・4角は観察枠。4角にはv55事前構造診断も併記。','',
       '## 1. 前日/事前候補','|モデル|候補数|','|---|---:|']
    for m in MODELS:L.append(f'|{m}|{prec.get(m,0)}|')

    L += ['', '## 2. 直前判定（結果を見る前に固定）',
          '|レース|モデル|v53 score|A/S|v55 4角score|判定|6点買い目|',
          '|---|---|---:|---|---:|---|---|']
    for z in sorted(direct,key=lambda q:q['race_code']):
        band='S' if z['approved_S'] else 'A' if z['approved_A'] else '見送り'
        s55=f"{float(z['v55_score']):.1f}" if z.get('v55_score') not in ('',None) else '-'
        t=z['live_tickets'] if z['live_tickets'] else '-'
        L.append(f"|{fmt(z['race_code'])}|{z['model']}|{z['v53_score']:.1f}|{band}|{s55}|{z['live_action']}|{t}|")

    L += ['', '## 3. 結果照合',
          '|レース|モデル|判定|結果|決まり手|頭的中|狙い成立|買い目的中|払戻|',
          '|---|---|---|---|---|---:|---:|---:|---:|']
    for z in sorted(settled,key=lambda q:q['race_code']):
        L.append(f"|{fmt(z['race_code'])}|{z['model']}|{z['live_action']}|{z['actual_combo']}|{z['kimarite']}|{z['head_hit']}|{z['method_hit']}|{z['live_hit']}|{z['live_return']:,}円|")

    L += ['', '## 実購入扱い集計',
          f'- 購入: **{len(buys)}R**',f'- 投資: **{inv:,}円**',f'- 払戻: **{ret:,}円**',f'- ROI: **{roi:.1f}%**',
          f"- 的中: **{sum(z['live_hit'] for z in buys)}/{len(buys)}**" if buys else '- 的中: 0/0','',
          '## 4角検証メモ',f'- v55固定式: **{form4}** / 閾値 **{th4:.2f}**',
          '- 4角は実購入集計には含めず、当日の選別がどう働いたかだけ確認する。']

    with open('summary_v56_20260820_replay.md','w',encoding='utf-8') as f:f.write('\n'.join(L)+'\n')
    print('\n'.join(L))

if __name__=='__main__':main()
