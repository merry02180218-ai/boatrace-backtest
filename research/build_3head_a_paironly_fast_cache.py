#!/usr/bin/env python3
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import joblib,numpy as np,pandas as pd

import scan_20260911_3head_v288_pre as pre
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v224_3head_national_form_decompose as v224
from backtest import rows

def target_bias(day,bias_start):
    sums=defaultdict(list);allv=[];d=bias_start;e=day-timedelta(days=1)
    while d<=e:
        for r in rows(f'data/previews/stt/{d:%Y/%m/%d}.csv'):
            for b in range(1,7):
                try:v=float(r.get(f'艇{b}_スタート展示'))
                except Exception:continue
                if -.30<v<1.0:sums[b].append(v);allv.append(v)
        d=(pd.Timestamp(d)+pd.Timedelta(days=1)).date()
    g=float(np.mean(allv)) if allv else .15
    return {b:(float(np.mean(sums[b]))-g if sums[b] else 0.) for b in range(1,7)}

def finite_pair_fit(tr):
    bad=[];eligible=0
    for ix,r in tr.iterrows():
        if v222.ii(r.get('valid_result'))!=1:continue
        actual=v222.v166.combo(r.get('actual_combo'))
        if len(actual)!=3 or actual[0]!=3 or actual[1] not in v222.OPP or actual[2] not in v222.OPP or actual[1]==actual[2]:
            continue
        eligible+=1;ok=True
        for s in v222.OPP:
            for t in v222.OPP:
                if s==t:continue
                try:
                    vec=np.asarray(v222.pairvec(r,s,t,'V221'),float)
                    if not np.isfinite(vec).all():ok=False;break
                except Exception:
                    ok=False;break
            if not ok:break
        if not ok:bad.append(ix)
    clean=tr.drop(index=bad) if bad else tr
    return v222.fit_pair(clean,'V221'),{'eligible_pair_training_races':eligible,'dropped_nonfinite_pair_training_races':len(bad)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--date',required=True)
    ap.add_argument('--month-first',default='2026-03-01')
    ap.add_argument('--month-next',default='2026-04-01')
    ap.add_argument('--history-cutoff',default='2026-02-28')
    ap.add_argument('--bias-start',default='2026-02-01')
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    day=datetime.strptime(a.date,'%Y-%m-%d').date();day8=day.strftime('%Y%m%d')
    first=pd.Timestamp(a.month_first);nextm=pd.Timestamp(a.month_next)
    cutoff=pd.Timestamp(a.history_cutoff)
    if cutoff!=first-pd.Timedelta(days=1):raise RuntimeError('history cutoff mismatch')
    inp=Path('current_input/v288')/day8
    cards_path=inp/'race_cards.csv';waku_path=inp/'waku10.csv'
    cards=pre.bycode(pre.local_csv(cards_path));waku=pre.bycode(pre.local_csv(waku_path))
    bias=target_bias(day,datetime.strptime(a.bias_start,'%Y-%m-%d').date())
    cur=[]
    for code,card in cards.items():
        if code not in waku:continue
        z=pre.v108.feature_row(a.date,card,waku[code],{}, {}, {},bias)
        if z is None:continue
        z.update({'winner':0,'valid_result':0,'actual_combo':'','valid_payout':0,'payout100':0})
        for b in range(1,7):
            for key in (f'艇{b}_選手名',f'艇{b}_選手登番'):
                if key in card:z[key]=card.get(key)
        cur.append(z)
    if not cur:raise RuntimeError('no current base rows')

    raw=pd.read_csv(v224.SRC,dtype={'race_code':str})
    dc0=v165.pc(raw,['date','race_date','ymd'])
    rd=pd.to_datetime(raw[dc0].astype(str),errors='coerce')
    raw=raw[rd<first].copy()
    raw=pd.concat([raw,pd.DataFrame(cur)],ignore_index=True,sort=False)
    dc=v165.pc(raw,['date','race_date','ymd']);y,_=v165.target(raw)
    raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce');raw['_y']=y
    raw=raw[raw._date.notna()&((raw._date<first)|(raw._date==pd.Timestamp(day)))].copy()

    old_end,old_contam,old_fetch=v221.END,v221.CONTAM,v221.day_fetch
    v221.END=day;v221.CONTAM=nextm
    lc=pre.local_csv(cards_path)
    def safe221(d):
        if d==day:return d,{'cards':lc,'tkz':[],'orig':[],'res':[]}
        return old_fetch(d)
    v221.day_fetch=safe221
    try:d=v221.build(raw,dc)
    finally:
        v221.END=old_end;v221.CONTAM=old_contam;v221.day_fetch=old_fetch

    tr=d[d._date<first].copy();today=d[d._date==pd.Timestamp(day)].copy()
    if today.empty:raise RuntimeError('no pair current rows')
    pair,audit=finite_pair_fit(tr)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    joblib.dump({
      'policy':'3HEAD_A_PAIR_ONLY_FAST_CACHE',
      'date':day8,'history_cutoff':a.history_cutoff,
      'pair_model':pair,'current_rows':today,'st_bias':bias,
      'pair_training_audit':audit,
      'target_result_or_payout_used':False,
      'target_exhibition_used_in_cache':False,
    },out,compress=3)
    print('A_PAIR_ONLY_FAST_CACHE_READY',day8,'rows',len(today),audit,flush=True)
if __name__=='__main__':main()
