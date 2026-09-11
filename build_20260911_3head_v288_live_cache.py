#!/usr/bin/env python3
"""Build the frozen 2026-09-11 3-head v288 live cache before race deadlines.
Heavy historical reconstruction/model fitting happens here, never in the deadline scorer.
Target-day results/payouts are intentionally unavailable.
"""
from __future__ import annotations
import joblib
import numpy as np
import pandas as pd

import scan_20260911_3head_v288_pre as pre
import analyze_v165_3head_monthly_walkforward as v165
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v249_3head_pre_rolling_sab_optimize as v249

OUT='cache_20260911_3head_v288_live.joblib'


def main():
    d,vc,basefs,fs=pre.build_augmented()

    # Freeze the September pair model and head model from data strictly before Sep-1.
    tr=d[d._date<pre.FIRST].copy()
    pair=v222.fit_pair(tr,'V221')
    hfs=v223.numeric_ok(d,fs)
    htr=d[d._date<pre.FIRST].copy()
    for c in hfs:
        htr[c]=pd.to_numeric(htr[c],errors='coerce')
    cats=[vc] if vc and vc not in hfs else []
    head=v165.model(hfs,cats)
    head.fit(htr[hfs+cats],htr._y.astype(int))

    # Reproduce the operational PRE universe/grade bridge used by today's scan.
    base_te,_=v223.fit_head(d,list(basefs),vc,pre.FIRST,pre.NEXT)
    k=max(1,int((base_te._p>=.30).sum()))
    te,_=v223.fit_head(d,fs,vc,pre.FIRST,pre.NEXT)
    te=te[te._date==pd.Timestamp(pre.DAY)].copy()
    sel=te.nlargest(min(k,len(te)),'_p').copy()
    if sel.empty:
        raise RuntimeError('no v243 head candidates')

    hist=pd.read_csv('analysis_v243_3head_expand_feature_audit.csv',dtype={'race_code':str})
    hist.date=hist.date.astype(str)
    hist['_target']=v249.target(hist).astype(int)
    cs=v249.cols(hist)
    cur=pd.DataFrame(index=sel.index)
    for c in cs:
        rawc=c[3:] if c.startswith('f__') else c
        cur[c]=pd.to_numeric(sel.get(rawc,np.nan),errors='coerce')
    cur['_score']=v249.fit_score(hist,cur,cs)
    cur['_pct']=cur['_score'].rank(pct=True,method='first',ascending=True)
    cur['grade']=np.where(cur._pct>=.70,'S',np.where(cur._pct>=.20,'A','B'))

    candidates={}
    for idx,r in sel.iterrows():
        c=cur.loc[idx]
        if c.grade not in ('S','A'):
            continue
        code=str(r.race_code).zfill(12)
        candidates[code]={
            'pre_grade':str(c.grade),
            'pre_score':float(c._score),
            'pre_pct':float(c._pct),
            'pre_p3':float(r._p),
        }

    today=d[d._date==pd.Timestamp(pre.DAY)].copy()
    joblib.dump({
        'head_model':head,
        'head_features':hfs,
        'head_cats':cats,
        'pair_model':pair,
        'current_rows':today,
        'pre_candidates':candidates,
        'st_bias':pre.learn_bias(),
        'date':'20260911',
        'history_cutoff':'2026-08-31',
        'target_result_or_payout_used':False,
        'operational_pre_percentile_bridge':True,
    },OUT,compress=3)
    print('CACHE_READY',OUT,'rows',len(today),'candidates',candidates,flush=True)

if __name__=='__main__':
    main()
