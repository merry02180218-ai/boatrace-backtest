#!/usr/bin/env python3
"""4-head focused study: boat4 minus boat3 motor win-rate / 2-ren-rate.

Policy:
- production HEAD4_V291_COMP7 untouched.
- Apr-Jun 2026 chooses rule; Jul-Aug 2026 is holdout.
- September outcomes are never read.
- motor win-rate = prior-only 1st-place rate for the same venue/motor, rebuilt
  causally from race cards + completed prior-day results.
- motor 2-ren rate = official pre-race race-card value.
- archived odds are a retrospective ROI proxy only.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from backtest import rows
from analyze_v205_3head_operational_replay import load_odds
import analyze_v96_4corner_monthly_walkforward_tiebreak as c4
import analyze_v251_4head_newroi_bridge as v251

ROOT=Path(__file__).resolve().parent
PRED=ROOT/'analysis_v250_4head_rebuild_baseline.csv'
OUT=ROOT/'analysis_4head_b4_minus_b3_motor_win_2ren_grid.csv'
DETAIL=ROOT/'analysis_4head_b4_minus_b3_motor_win_2ren_races.csv'
SUMMARY=ROOT/'summary_4head_b4_minus_b3_motor_win_2ren.md'
BANK=10000; COMP_TARGET=10.5; NS=tuple(range(2,21)); BASE_PRE=.18
HISTORY_START=date(2025,11,1); START=date(2026,1,1); END=date(2026,8,31)
TRAIN_MONTHS=('2026-04','2026-05','2026-06'); HOLD_MONTHS=('2026-07','2026-08')

def ff(x,d=np.nan):
    try:
        v=float(str(x).replace('%','').strip()); return v if np.isfinite(v) else d
    except Exception:return d

def ii(x,d=0):
    try:return int(float(str(x).strip()))
    except Exception:return d

def code(x):
    s=str(x).strip()
    if s.endswith('.0'):s=s[:-2]
    return s.zfill(12)

def bycode(rs):return {code(r.get('レースコード','')):r for r in rs if r.get('レースコード')}
def venue(card):return str(card.get('レース場コード','')).zfill(2)
def mkey(card,b):return venue(card),str(card.get(f'艇{b}_モーター番号','')).strip()

def prior_rate(hist,k):
    wins,total=hist.get(k,(0,0)); return wins/total if total else np.nan

def update_after_day(hist,cards,result_map):
    """Called only after all features for this day have been frozen."""
    for card in cards:
        c=code(card.get('レースコード','')); rr=result_map.get(c,{})
        winner=ii(rr.get('1着_艇番'),0)
        if winner not in range(1,7):continue
        for b in range(1,7):
            k=mkey(card,b)
            if not k[1]:continue
            w,n=hist.get(k,(0,0)); hist[k]=(w+(1 if b==winner else 0),n+1)

def build_motor_features():
    hist={}; rec=[]; d=HISTORY_START
    while d<=END:
        if d.month==9 and d.year==2026:raise RuntimeError('September outcome access blocked')
        ymd=d.strftime('%Y/%m/%d'); cards=rows(f'data/programs/race_cards/{ymd}.csv')
        if d>=START:
            for r in cards:
                c=code(r.get('レースコード','')); k4=mkey(r,4); k3=mkey(r,3)
                w4=prior_rate(hist,k4); w3=prior_rate(hist,k3)
                p4=ff(r.get('艇4_モーター2連対率')); p3=ff(r.get('艇3_モーター2連対率'))
                rec.append({'date':str(d),'month':str(d)[:7],'race_code':c,
                    'motor4_win_prior':w4,'motor3_win_prior':w3,
                    'motor_win_diff_4v3':w4-w3 if np.isfinite(w4) and np.isfinite(w3) else np.nan,
                    'motor4_2ren':p4,'motor3_2ren':p3,
                    'motor_2ren_diff_4v3':p4-p3 if np.isfinite(p4) and np.isfinite(p3) else np.nan})
        # result read occurs only after the entire day's features are frozen.
        result_map=bycode(rows(f'data/results/realtime/{ymd}.csv'))
        update_after_day(hist,cards,result_map); d+=timedelta(days=1)
    return pd.DataFrame(rec)

def settle_base():
    p=pd.read_csv(PRED,dtype={'race_code':str}); p['race_code']=p.race_code.map(code)
    p=p[(p.variant=='PRE') & (pd.to_numeric(p.p4head,errors='coerce')>=BASE_PRE) & p.month.isin(TRAIN_MONTHS+HOLD_MONTHS)].copy()
    rs=c4.read(); orders=v251.pair_orders(rs); actual=v251.actual_map(rs)
    od=load_odds()
    if od.empty:raise RuntimeError('archived odds unavailable')
    od=od.copy(); od['race_code']=od.race_code.map(code); oi=od.set_index('race_code',drop=False)
    out=[]
    for _,r in p.iterrows():
        c=code(r.race_code); ds=str(r.date); k=(ds,c); order=orders.get(k); a=actual.get(k)
        if not order or not a or a[3]!=1 or c not in oi.index:continue
        o=oi.loc[c]; o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
        choices=[]
        for n in NS:
            s=v251.settle(c,[f'4-{x}-{y}' for x,y in order[:n]],o,a)
            if s is not None:choices.append((n,int(s[0]),float(s[1]),float(s[2])))
        if not choices:continue
        n,hit,ret,comp=min(choices,key=lambda x:(abs(x[3]-COMP_TARGET),x[0]))
        out.append({'date':ds,'month':str(r.month),'race_code':c,'PRE':float(r.p4head),'n':n,'hit':hit,
                    'return_yen':ret,'comp_odds':comp,'actual_head4':int(a[0]==4)})
    z=pd.DataFrame(out)
    if z.empty:raise RuntimeError('no settled PRE>=0.18 rows')
    return z

def met(q):
    if q.empty:return {'R':0,'head4':0,'head4_rate':np.nan,'hits':0,'hit_rate':np.nan,'return_yen':0.0,'roi':np.nan}
    n=len(q); ret=float(q.return_yen.sum())
    return {'R':n,'head4':int(q.actual_head4.sum()),'head4_rate':float(q.actual_head4.mean()),'hits':int(q.hit.sum()),
            'hit_rate':float(q.hit.mean()),'return_yen':ret,'roi':ret/(n*BANK)}
def monthly_floor(q):
    a=[met(g)['roi'] for _,g in q.groupby('month') if len(g)]; return min(a) if a else np.nan

def main():
    z=settle_base().merge(build_motor_features(),on=['date','month','race_code'],how='left')
    z=z[z.motor_win_diff_4v3.notna() & z.motor_2ren_diff_4v3.notna()].copy()
    tr=z[z.month.isin(TRAIN_MONTHS)].copy(); ho=z[z.month.isin(HOLD_MONTHS)].copy()
    if len(tr)<30 or len(ho)<20:raise RuntimeError(f'insufficient train/holdout rows: {len(tr)}/{len(ho)}')
    qs=(.20,.30,.40,.50,.60,.70,.80)
    wt=sorted(set(float(tr.motor_win_diff_4v3.quantile(q)) for q in qs)); rt=sorted(set(float(tr.motor_2ren_diff_4v3.quantile(q)) for q in qs))
    base_tr=met(tr); min_r=max(30,int(np.ceil(.25*len(tr)))); defs=[]; rr=[]
    for a in wt:defs.append(('WIN_ONLY',a,np.nan))
    for b in rt:defs.append(('2REN_ONLY',np.nan,b))
    for a in wt:
        for b in rt:defs.extend([('AND',a,b),('OR',a,b)])
    def mask(df,typ,a,b):
        if typ=='WIN_ONLY':return df.motor_win_diff_4v3>=a
        if typ=='2REN_ONLY':return df.motor_2ren_diff_4v3>=b
        if typ=='AND':return (df.motor_win_diff_4v3>=a)&(df.motor_2ren_diff_4v3>=b)
        return (df.motor_win_diff_4v3>=a)|(df.motor_2ren_diff_4v3>=b)
    for typ,a,b in defs:
        q=tr[mask(tr,typ,a,b)]; mm=met(q)
        if mm['R']<min_r:continue
        rr.append({'rule':typ,'win_cut':a,'ren2_cut':b,**{f'train_{k}':v for k,v in mm.items()},'train_floor_roi':monthly_floor(q),'train_retention':len(q)/len(tr)})
    G=pd.DataFrame(rr)
    if G.empty:raise RuntimeError('no threshold cells passed minimum sample')
    G['beats_head']=G.train_head4_rate>=base_tr['head4_rate']; G['beats_roi']=G.train_roi>=base_tr['roi']; G['both_improve']=G.beats_head&G.beats_roi
    G=G.sort_values(['both_improve','train_floor_roi','train_roi','train_head4_rate','train_R'],ascending=[False,False,False,False,False]).reset_index(drop=True)
    best=G.iloc[0]; typ=best.rule; a=best.win_cut; b=best.ren2_cut
    chosen=lambda df:mask(df,typ,a,b)
    qtr=tr[chosen(tr)]; qh=ho[chosen(ho)]; base_ho=met(ho); hold=met(qh)
    G['selected']=False; G.loc[0,'selected']=True; G.to_csv(OUT,index=False)
    z['selected_frozen_rule']=chosen(z).astype(int); z.to_csv(DETAIL,index=False)
    def line(label,x):
        return f"- {label}: {x['R']}R / 4号艇1着 {x['head4']} ({100*x['head4_rate']:.2f}%) / 3連単 {x['hits']} ({100*x['hit_rate']:.2f}%) / ROI {100*x['roi']:.2f}% / return {x['return_yen']:.0f}円"
    chosen_text=f"- chosen: **{typ}**, win_diff>={a:.6f}"+(f", 2ren_diff>={b:.4f}pt" if np.isfinite(b) else '')
    L=['# 4号艇−3号艇 モーター勝率・2連対率 集中検証','',
       '- production `HEAD4_V291_COMP7` は変更しない検証専用。',
       '- モーター勝率 = 同場・同モーターの当日より前の全レース1着率。毎日の入力を先に固定し、その日の結果は翌日以降にだけ反映。',
       '- モーター2連対率 = 公式race-card事前値。差は双方とも `4号艇 - 3号艇`。',
       '- Apr-Junのみで条件選択。Jul-Augは固定holdout。September結果は未読。',
       '- 母集団=v250 PRE>=0.18。買い目=prior-only v96相手順位、N=2..20で合成オッズ10.5最接近、1R 10,000円Dutch。',
       '- ROIはarchived historical odds proxy。','',
       '## Apr-Jun',line('baseline',base_tr),chosen_text,line('chosen train',met(qtr)),f"- train monthly ROI floor: {100*monthly_floor(qtr):.2f}%",'',
       '## Jul-Aug holdout',line('baseline holdout',base_ho),line('chosen holdout',hold),f"- holdout retention: {len(qh)}/{len(ho)} ({100*len(qh)/len(ho):.1f}%)",'',
       '## Month breakdown (frozen chosen rule)','|month|R|4頭率|3連単率|ROI|','|---|---:|---:|---:|---:|']
    for mon,g in z[z.selected_frozen_rule==1].groupby('month'):
        x=met(g); L.append(f"|{mon}|{x['R']}|{100*x['head4_rate']:.2f}%|{100*x['hit_rate']:.2f}%|{100*x['roi']:.2f}%|")
    L+=['','## Guardrail','- この研究だけではproductionを変更しない。','- September outcomes / payouts / labels are not read.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8'); print('\n'.join(L))
if __name__=='__main__':main()
