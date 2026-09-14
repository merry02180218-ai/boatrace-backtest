#!/usr/bin/env python3
"""4-head focused study: boat4 minus boat3 motor win-rate / 2-ren-rate.

Research policy
---------------
* Production HEAD4_V291_COMP7 is untouched.
* April-June 2026 only chooses the motor-difference rule.
* July-August 2026 is holdout evaluation under the user's current policy.
* September outcomes are never read.
* Motor win-rate here is causal prior motor-history 1st-place rate, because the
  official race card exposes motor 2-ren / 3-ren rates but no motor win-rate.
* Motor 2-ren rate is the official pre-race race-card value.
* Current-day outcomes are joined only after all motor features are frozen.
* ROI uses archived historical odds as a retrospective proxy, never as a claim
  of immutable live/pre-deadline odds.
"""
from __future__ import annotations

import re
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
BANK=10000
COMP_TARGET=10.5
NS=tuple(range(2,21))
START=date(2026,1,1)
END=date(2026,8,31)
TRAIN_MONTHS=('2026-04','2026-05','2026-06')
HOLD_MONTHS=('2026-07','2026-08')
BASE_PRE=.18


def ff(x,d=np.nan):
    try:
        v=float(str(x).replace('%','').strip())
        return v if np.isfinite(v) else d
    except Exception:return d

def code(x):
    s=str(x).strip()
    if s.endswith('.0'):s=s[:-2]
    return s.zfill(12)

def motor_key(card,b):
    return str(card.get('レース場コード','')).zfill(2),str(card.get(f'艇{b}_モーター番号','')).strip()

def ingest_motor_win(hist,seen,day):
    """Ingest only rows available for `day`, called AFTER freezing that day's races."""
    ymd=day.strftime('%Y/%m/%d')
    for r in rows(f'data/programs/motor_history/{ymd}.csv'):
        venue=str(r.get('場コード','')).zfill(2); motor=str(r.get('モーター番号','')).strip()
        k=(venue,motor,r.get('使用開始日',''),r.get('使用終了日',''),r.get('使用者名',''))
        if not motor or k in seen:continue
        seen.add(k)
        digs=[int(x) for x in re.findall(r'[1-6１-６]',(r.get('着順列') or '').translate(str.maketrans('１２３４５６','123456')))]
        if digs:hist[(venue,motor)].extend(digs)

def prior_motor_win(hist,k):
    a=hist.get(k,[])
    return (sum(x==1 for x in a)/len(a)) if a else np.nan

def build_motor_features():
    hist=defaultdict(list);seen=set();d=START-timedelta(days=120)
    while d<START:
        ingest_motor_win(hist,seen,d);d+=timedelta(days=1)
    rec=[]
    while d<=END:
        ymd=d.strftime('%Y/%m/%d')
        cards=rows(f'data/programs/race_cards/{ymd}.csv')
        # Freeze all pre-race motor inputs before any same-day history ingestion.
        for r in cards:
            c=code(r.get('レースコード',''))
            k4=motor_key(r,4);k3=motor_key(r,3)
            w4=prior_motor_win(hist,k4);w3=prior_motor_win(hist,k3)
            p4=ff(r.get('艇4_モーター2連対率'));p3=ff(r.get('艇3_モーター2連対率'))
            rec.append({'date':str(d),'month':str(d)[:7],'race_code':c,
                        'motor4_win_prior':w4,'motor3_win_prior':w3,
                        'motor_win_diff_4v3':w4-w3 if np.isfinite(w4) and np.isfinite(w3) else np.nan,
                        'motor4_2ren':p4,'motor3_2ren':p3,
                        'motor_2ren_diff_4v3':p4-p3 if np.isfinite(p4) and np.isfinite(p3) else np.nan})
        ingest_motor_win(hist,seen,d);d+=timedelta(days=1)
    return pd.DataFrame(rec)

def settle_base():
    p=pd.read_csv(PRED,dtype={'race_code':str})
    p['race_code']=p.race_code.map(code)
    p=p[(p.variant=='PRE') & (pd.to_numeric(p.p4head,errors='coerce')>=BASE_PRE)].copy()
    p=p[p.month.isin(TRAIN_MONTHS+HOLD_MONTHS)].copy()
    rs=c4.read();orders=v251.pair_orders(rs);actual=v251.actual_map(rs)
    orders_by_code={code(k[1]):v for k,v in orders.items()}
    actual_by_code={code(k[1]):v for k,v in actual.items()}
    od=load_odds()
    if od.empty:raise RuntimeError('archived odds unavailable')
    od=od.copy();od['race_code']=od.race_code.map(code);oi=od.set_index('race_code',drop=False)
    out=[]
    for _,r in p.iterrows():
        c=code(r.race_code);ds=str(r.date);k=(ds,c)
        order=orders.get(k) or orders_by_code.get(c);a=actual.get(k) or actual_by_code.get(c)
        if not order or not a or a[3]!=1 or c not in oi.index:continue
        o=oi.loc[c];o=o.iloc[-1] if isinstance(o,pd.DataFrame) else o
        choices=[]
        for n in NS:
            ts=[f'4-{x}-{y}' for x,y in order[:n]]
            s=v251.settle(c,ts,o,a)
            if s is None:continue
            hit,ret,comp=s;choices.append((n,int(hit),float(ret),float(comp)))
        if not choices:continue
        n,hit,ret,comp=min(choices,key=lambda x:(abs(x[3]-COMP_TARGET),x[0]))
        out.append({'date':ds,'month':str(r.month),'race_code':c,'PRE':float(r.p4head),
                    'n':n,'hit':hit,'return_yen':ret,'comp_odds':comp,'actual_head4':int(a[0]==4)})
    z=pd.DataFrame(out)
    if z.empty:raise RuntimeError('no settled PRE>=0.18 rows')
    return z

def met(q):
    if q.empty:return {'R':0,'head4':0,'head4_rate':np.nan,'hits':0,'hit_rate':np.nan,'return_yen':0.0,'roi':np.nan}
    ret=float(q.return_yen.sum());n=len(q)
    return {'R':n,'head4':int(q.actual_head4.sum()),'head4_rate':float(q.actual_head4.mean()),
            'hits':int(q.hit.sum()),'hit_rate':float(q.hit.mean()),'return_yen':ret,'roi':ret/(n*BANK)}
def monthly_floor(q):
    vals=[]
    for _,g in q.groupby('month'):
        m=met(g)
        if m['R']:vals.append(m['roi'])
    return min(vals) if vals else np.nan

def main():
    m=build_motor_features();z=settle_base().merge(m,on=['date','month','race_code'],how='left')
    usable=z.motor_win_diff_4v3.notna() & z.motor_2ren_diff_4v3.notna()
    z=z[usable].copy()
    if z.empty:raise RuntimeError('no races with both motor differences')
    tr=z[z.month.isin(TRAIN_MONTHS)].copy();ho=z[z.month.isin(HOLD_MONTHS)].copy()
    if len(tr)<30 or len(ho)<20:raise RuntimeError(f'insufficient train/holdout rows: {len(tr)}/{len(ho)}')

    # Coarse, data-derived thresholds only from Apr-Jun. Quantiles avoid arbitrary
    # unit mixing between prior win-rate (0-1) and official 2-ren percentage points.
    qs=(.20,.30,.40,.50,.60,.70,.80)
    wt=sorted(set(float(tr.motor_win_diff_4v3.quantile(q)) for q in qs))
    rt=sorted(set(float(tr.motor_2ren_diff_4v3.quantile(q)) for q in qs))
    rowsout=[]
    base_tr=met(tr);min_r=max(30,int(np.ceil(.25*len(tr))))
    defs=[]
    for a in wt:defs.append(('WIN_ONLY',a,np.nan))
    for b in rt:defs.append(('2REN_ONLY',np.nan,b))
    for a in wt:
      for b in rt:
        defs.append(('AND',a,b));defs.append(('OR',a,b))
    for typ,a,b in defs:
        if typ=='WIN_ONLY':mask=tr.motor_win_diff_4v3>=a
        elif typ=='2REN_ONLY':mask=tr.motor_2ren_diff_4v3>=b
        elif typ=='AND':mask=(tr.motor_win_diff_4v3>=a)&(tr.motor_2ren_diff_4v3>=b)
        else:mask=(tr.motor_win_diff_4v3>=a)|(tr.motor_2ren_diff_4v3>=b)
        q=tr[mask];mm=met(q)
        if mm['R']<min_r:continue
        rowsout.append({'rule':typ,'win_cut':a,'ren2_cut':b,**{f'train_{k}':v for k,v in mm.items()},
                        'train_floor_roi':monthly_floor(q),'train_retention':len(q)/len(tr)})
    G=pd.DataFrame(rowsout)
    if G.empty:raise RuntimeError('no threshold cells passed minimum sample')
    # Choose on Apr-Jun only. Prefer rules that improve both head rate and ROI over
    # the broad PRE baseline; otherwise choose best robust monthly ROI among cells.
    G['beats_head']=G.train_head4_rate>=base_tr['head4_rate']
    G['beats_roi']=G.train_roi>=base_tr['roi']
    G['both_improve']=G.beats_head&G.beats_roi
    G=G.sort_values(['both_improve','train_floor_roi','train_roi','train_head4_rate','train_R'],ascending=[False,False,False,False,False]).reset_index(drop=True)
    best=G.iloc[0]
    typ=best.rule;a=best.win_cut;b=best.ren2_cut
    def apply(df):
        if typ=='WIN_ONLY':return df.motor_win_diff_4v3>=a
        if typ=='2REN_ONLY':return df.motor_2ren_diff_4v3>=b
        if typ=='AND':return (df.motor_win_diff_4v3>=a)&(df.motor_2ren_diff_4v3>=b)
        return (df.motor_win_diff_4v3>=a)|(df.motor_2ren_diff_4v3>=b)
    qh=ho[apply(ho)].copy();hold=met(qh);base_ho=met(ho)
    G['selected']=False;G.loc[0,'selected']=True;G.to_csv(OUT,index=False)
    z['selected_frozen_rule']=apply(z).astype(int);z.to_csv(DETAIL,index=False)

    def line(label,x):
        return f"- {label}: {x['R']}R / 4号艇1着 {x['head4']} ({100*x['head4_rate']:.2f}%) / 3連単 {x['hits']} ({100*x['hit_rate']:.2f}%) / ROI {100*x['roi']:.2f}% / return {x['return_yen']:.0f}円"
    L=['# 4号艇−3号艇 モーター勝率・2連対率 集中検証','',
       '- production `HEAD4_V291_COMP7` は変更しない検証専用。',
       '- モーター勝率 = 当日より前に取得済みの同場・同モーター使用履歴における1着率。公式カードにモーター勝率列はないため、このprior-only定義を採用。',
       '- モーター2連対率 = 公式race-cardの事前値。',
       '- 差はどちらも `4号艇 - 3号艇`。',
       '- ルール選択はApr-Junだけ。Jul-Augは選択後に固定して後段検証。September結果は未読。',
       '- 母集団はv250 PRE>=0.18の4号艇候補。買い目はprior-only v96相手順位、N=2..20から合成オッズ10.5最接近、1R 10,000円Dutch。',
       '- ROIはarchived historical odds proxyであり、当時の不変LIVE締切前オッズとは扱わない。','',
       '## Apr-Jun baseline / chosen rule',line('baseline',base_tr),
       f"- chosen: **{typ}**, win_diff>={a:.6f}"+(f", 2ren_diff>={b:.4f}pt" if np.isfinite(b) else ''),
       line('chosen train',met(tr[apply(tr)])),
       f"- train monthly ROI floor: {100*monthly_floor(tr[apply(tr)]):.2f}%",'',
       '## Jul-Aug holdout',line('baseline holdout',base_ho),line('chosen holdout',hold),
       f"- holdout retention: {len(qh)}/{len(ho)} ({100*len(qh)/len(ho):.1f}%)",'',
       '## Month breakdown (frozen chosen rule)','|month|R|4頭率|3連単率|ROI|','|---|---:|---:|---:|---:|']
    for mon,g in z[z.selected_frozen_rule==1].groupby('month'):
        x=met(g);L.append(f"|{mon}|{x['R']}|{100*x['head4_rate']:.2f}%|{100*x['hit_rate']:.2f}%|{100*x['roi']:.2f}%|")
    L+=['','## Decision guardrail','- Jul-Augが良くても、この研究だけではproductionを変更しない。','- September outcomes / payouts / labels are not read by this script.']
    SUMMARY.write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))

if __name__=='__main__':main()
