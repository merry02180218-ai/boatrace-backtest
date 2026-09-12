#!/usr/bin/env python3
"""Build one leakage-controlled historical day as if v288 were operated live for a month.

The month is frozen at its first day: head/pair models and PRE score thresholds use only
history strictly before --month-first. Target-day result/payout/exhibition are not used
while PRE/cache are built. Past days inside the evaluation month may be used only as
past information by the feature builders/bias calculation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import scan_20260911_3head_v288_pre as pre
import build_20260911_3head_v288_live_cache as cache
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v221_3head_scenario_pair as v221
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v224_3head_national_form_decompose as v224
import analyze_v234_3head_waku10_restored_replay as v234
from backtest import rows


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--date',required=True)
    ap.add_argument('--month-first',required=True)
    ap.add_argument('--month-next',required=True)
    ap.add_argument('--history-cutoff',required=True)
    ap.add_argument('--bias-start',required=True)
    a=ap.parse_args()

    day=datetime.strptime(a.date,'%Y-%m-%d').date()
    first=pd.Timestamp(a.month_first); nextm=pd.Timestamp(a.month_next)
    cutoff=pd.Timestamp(a.history_cutoff)
    bias_start=datetime.strptime(a.bias_start,'%Y-%m-%d').date()
    if not (first <= pd.Timestamp(day) < nextm):
        raise RuntimeError('target date outside frozen evaluation month')
    if cutoff != first-pd.Timedelta(days=1):
        raise RuntimeError('history cutoff must be exactly day before month-first')

    day8=day.strftime('%Y%m%d')
    inp=Path('current_input/v288')/day8
    cards_path=inp/'race_cards.csv'; waku_path=inp/'waku10.csv'
    if not cards_path.exists() or not waku_path.exists():
        raise RuntimeError(f'missing archived PRE inputs: {inp}')

    outdir=Path('live_outputs/v288_operational')/day8
    outdir.mkdir(parents=True,exist_ok=True)
    pre_csv=outdir/'pre_scan.csv'; pre_md=outdir/'pre_scan.md'; cache_path=outdir/'live_cache.joblib'

    pre.DAY=day; pre.FIRST=first; pre.NEXT=nextm
    pre.CUR_CARDS=cards_path; pre.CUR_WAKU=waku_path
    pre.OUT=pre_csv; pre.SUM=pre_md; cache.OUT=cache_path

    def target_bias(end=None,start=None):
        sums=defaultdict(list); allv=[]
        d=start or bias_start; e=end or (day-timedelta(days=1))
        while d<=e:
            for r in rows(f'data/previews/stt/{d:%Y/%m/%d}.csv'):
                for b in range(1,7):
                    try: v=float(r.get(f'艇{b}_スタート展示'))
                    except Exception: continue
                    if -.30<v<1.0: sums[b].append(v); allv.append(v)
            d=(pd.Timestamp(d)+pd.Timedelta(days=1)).date()
        g=float(np.mean(allv)) if allv else .15
        return {b:(float(np.mean(sums[b]))-g if sums[b] else 0.) for b in range(1,7)}

    def make_current_base():
        cards=pre.bycode(pre.local_csv(cards_path)); waku=pre.bycode(pre.local_csv(waku_path)); bias=target_bias(); out=[]
        for code,card in cards.items():
            if code not in waku: continue
            z=pre.v108.feature_row(day.isoformat(),card,waku[code],{}, {}, {}, bias)
            if z is None: continue
            z.update({'winner':0,'valid_result':0,'actual_combo':'','valid_payout':0,'payout100':0})
            for b in range(1,7):
                for key in (f'艇{b}_選手名',f'艇{b}_選手登番'):
                    if key in card: z[key]=card.get(key)
            out.append(z)
        if not out: raise RuntimeError(f'no current PRE rows built cards={len(cards)} waku={len(waku)}')
        return pd.DataFrame(out)

    def build_augmented_frozen():
        cov=pd.read_csv(pre.COV,dtype={'date':str,'source':str})
        if (cov.source=='missing').any(): raise RuntimeError('restored historical Waku10 has missing days')
        raw=pd.read_csv(v224.SRC,dtype={'race_code':str})
        dc0=v165.pc(raw,['date','race_date','ymd'])
        rd=pd.to_datetime(raw[dc0].astype(str),errors='coerce')
        raw=raw[rd < first].copy()
        cur=make_current_base(); raw=pd.concat([raw,cur],ignore_index=True,sort=False)
        dc=v165.pc(raw,['date','race_date','ymd']); vc=v165.pc(raw,['venue','jcd','stadium','place']); y,_=v165.target(raw); basefs=v165.feats(raw)
        raw['_date']=pd.to_datetime(raw[dc].astype(str),errors='coerce'); raw['_y']=y
        raw=raw[raw._date.notna() & ((raw._date<first) | (raw._date==pd.Timestamp(day)))].copy()

        v221.CONTAM=nextm; v221.END=day; old221=v221.day_fetch
        lc=pre.local_csv(cards_path); lw=pre.local_csv(waku_path)
        def safe221(d):
            if d==day: return d,{'cards':lc,'tkz':[],'orig':[],'res':[]}
            return old221(d)
        v221.day_fetch=safe221

        v222.CONTAM=nextm; v222.END=day; old222=v222.day_fetch
        def safe222(d):
            if d==day: return d,{'cards':lc,'waku':lw,'tkz':[],'stt':[],'orig':[]}
            dd,z=old222(d); z=dict(z)
            if d<=cutoff.date():
                rr=v234.local_rows(d)
                if rr: z['waku']=rr
            return dd,z
        v222.day_fetch=safe222
        v223.CONTAM=nextm; v224.CONTAM=nextm
        try:
            d=v221.build(raw,dc); d=v222.build_current(d,dc); d=v223.build_unused(d,dc); d=v224.add_decomp(d,dc)
        finally:
            v221.day_fetch=old221; v222.day_fetch=old222
        fs=[x for x in v234.full_features(d,basefs) if x in d.columns]
        return d,vc,basefs,fs

    original_grade=pre.operational_pre_grade
    def frozen_grade(hist,cur,cs):
        h=hist.copy(); hd=pd.to_datetime(h['date'].astype(str),errors='coerce')
        h=h[hd < first].copy()
        if h.empty: raise RuntimeError('no PRE score training rows before month-first')
        return original_grade(h,cur,cs)

    original_build=pre.build_augmented; original_bias=pre.learn_bias; original_base=pre.make_current_base
    pre.build_augmented=build_augmented_frozen; pre.learn_bias=target_bias; pre.make_current_base=make_current_base; pre.operational_pre_grade=frozen_grade
    try:
        bundle=build_augmented_frozen()
        pre.build_augmented=lambda:bundle
        pre.main()
        q=pd.read_csv(pre_csv,dtype={'race_code':str}) if pre_csv.exists() and pre_csv.stat().st_size else pd.DataFrame()
        if q.empty:
            d=bundle[0]
            today=d[d._date==pd.Timestamp(day)].copy()
            # A true production watcher would never enter the expensive LIVE scorer
            # when PRE has no candidate. Keep a minimal auditable cache so historical
            # replay records a clean NO_BET day without fitting unused models.
            joblib.dump({
                'current_rows':today,
                'pre_candidates':{},
                'st_bias':target_bias(),
                'date':day8,
                'history_cutoff':a.history_cutoff,
                'target_result_or_payout_used':False,
                'operational_pre_percentile_bridge':False,
                'operational_pre_training_quantile':True,
                'operational_month_replay':True,
                'zero_pre_fast_path':True,
            },cache_path,compress=3)
            print('CACHE_READY_ZERO_PRE',cache_path,'rows',len(today),flush=True)
        else:
            cache.main()
    finally:
        pre.build_augmented=original_build; pre.learn_bias=original_bias; pre.make_current_base=original_base; pre.operational_pre_grade=original_grade

    z=joblib.load(cache_path)
    z['date']=day8; z['history_cutoff']=a.history_cutoff
    z['production_daily_wrapper']=False; z['operational_month_replay']=True
    z['target_result_or_payout_used']=False
    joblib.dump(z,cache_path,compress=3)

    q=pd.read_csv(pre_csv,dtype={'race_code':str}) if pre_csv.exists() and pre_csv.stat().st_size else pd.DataFrame()
    candidates=[] if q.empty else q.race_code.astype(str).str.zfill(12).tolist()
    manifest={
      'policy':'3HEAD_V288_OPERATIONAL_MONTH_REPLAY','target_date':day.isoformat(),'target_date_yyyymmdd':day8,
      'month_first':str(first.date()),'month_next':str(nextm.date()),'history_cutoff':a.history_cutoff,
      'result_blind_target_day':True,'result_or_payout_used':False,'current_exhibition_used_for_pre':False,
      'operational_pre_training_quantile':True,'operational_pre_percentile_bridge':False,
      'pre_candidate_count':len(candidates),'pre_candidate_race_codes':candidates,
      'cards_sha256':sha256(cards_path),'waku_sha256':sha256(waku_path),'cache_sha256':sha256(cache_path),
      'evaluation_month_rows_removed_from_training_frame':True,
      'pre_score_training_filtered_before_month_first':True,
      'zero_pre_fast_path':len(candidates)==0,
      'rule_version':'v288-fixed-later; operational replay, not pristine model-selection evidence'
    }
    (outdir/'daily_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': main()
