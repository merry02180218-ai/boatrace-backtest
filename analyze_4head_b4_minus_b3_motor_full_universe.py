#!/usr/bin/env python3
"""Validate the already-frozen boat4-vs-boat3 motor rule on the full race universe.
No PRE/p4head gate is used. September 2026 outcomes are never read.
"""
from pathlib import Path
import numpy as np, pandas as pd
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v251_4head_newroi_bridge as v251
from analyze_v205_3head_operational_replay import load_odds
from analyze_4head_b4_minus_b3_motor_win_2ren import build_motor_features, code, met, BANK, COMP_TARGET, NS

ROOT=Path(__file__).resolve().parent
DETAIL=ROOT/'analysis_4head_b4_minus_b3_motor_full_universe_races.csv'
SUMMARY=ROOT/'summary_4head_b4_minus_b3_motor_full_universe.md'
MONTHS=('2026-04','2026-05','2026-06','2026-07','2026-08')
TRAIN=('2026-04','2026-05','2026-06')
HOLD=('2026-07','2026-08')
WIN_CUT=0.010782
REN2_CUT=0.4000

def settle_all():
    rs=c4.read(); orders=v251.pair_orders(rs); actual=v251.actual_map(rs)
    od=load_odds()
    if od.empty: raise RuntimeError('archived odds unavailable')
    od=od.copy(); od['race_code']=od.race_code.map(code); oi=od.set_index('race_code',drop=False)
    out=[]
    for r in rs:
        ds=str(r.get('date','')); mon=ds[:7]
        if mon not in MONTHS: continue
        c=code(r.get('race_code','')); k=(ds,c); order=orders.get(k); a=actual.get(k)
        if not order or not a or a[3]!=1 or c not in oi.index: continue
        o=oi.loc[c]; o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
        choices=[]
        for n in NS:
            s=v251.settle(c,[f'4-{x}-{y}' for x,y in order[:n]],o,a)
            if s is not None: choices.append((n,int(s[0]),float(s[1]),float(s[2])))
        if not choices: continue
        n,hit,ret,comp=min(choices,key=lambda x:(abs(x[3]-COMP_TARGET),x[0]))
        out.append({'date':ds,'month':mon,'race_code':c,'n':n,'hit':hit,'return_yen':ret,'comp_odds':comp,'actual_head4':int(a[0]==4)})
    z=pd.DataFrame(out)
    if z.empty: raise RuntimeError('no full-universe settled rows')
    return z

def fmt(label,q):
    x=met(q)
    return f"- {label}: {x['R']}R / 4号艇1着 {x['head4']} ({100*x['head4_rate']:.2f}%) / 3連単 {x['hits']} ({100*x['hit_rate']:.2f}%) / ROI {100*x['roi']:.2f}% / return {x['return_yen']:.0f}円"

def main():
    z=settle_all().merge(build_motor_features(),on=['date','month','race_code'],how='left')
    z=z[z.motor_win_diff_4v3.notna() & z.motor_2ren_diff_4v3.notna()].copy()
    z['selected_fixed_motor_rule']=((z.motor_win_diff_4v3>=WIN_CUT)&(z.motor_2ren_diff_4v3>=REN2_CUT)).astype(int)
    z.to_csv(DETAIL,index=False)
    L=['# 4号艇−3号艇 モーター差 — 全レース母集団 固定条件検証','',
       '- v250 PRE/p4head gateは使用しない。対象期間でsettle可能な全レースが母集団。',
       f'- fixed rule: `motor_win_diff_4v3 >= {WIN_CUT:.6f} AND motor_2ren_diff_4v3 >= {REN2_CUT:.4f}pt`。再最適化なし。',
       '- 相手順位・Dutch・archived odds proxyの処理は直前研究と同一。',
       '- production `HEAD4_V291_COMP7` は変更しない。September outcomes are UNREAD.','']
    for title,mons in [('Apr-Jun',TRAIN),('Jul-Aug holdout',HOLD),('Apr-Aug total',MONTHS)]:
        b=z[z.month.isin(mons)]; q=b[b.selected_fixed_motor_rule==1]
        L += [f'## {title}',fmt('full universe',b),fmt('fixed motor rule',q),f'- retention: {len(q)}/{len(b)} ({100*len(q)/len(b):.2f}%)','']
    L += ['## Month breakdown','|month|全R|条件R|4頭率|3連単率|ROI|','|---|---:|---:|---:|---:|---:|']
    for mon,g in z.groupby('month'):
        q=g[g.selected_fixed_motor_rule==1]; x=met(q)
        L.append(f"|{mon}|{len(g)}|{len(q)}|{100*x['head4_rate']:.2f}%|{100*x['hit_rate']:.2f}%|{100*x['roi']:.2f}%|")
    L += ['','## Guardrail','- fixed rule only; no threshold retuning on Jul-Aug.','- September result/payout/label files are not read.','- This validation does not authorize production promotion.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__': main()
