#!/usr/bin/env python3
"""One-time cache builder for 2026-09-10 3-head LIVE smoke test.
Heavy history work belongs here, never in the deadline-time scorer.
"""
from __future__ import annotations
import joblib
import pandas as pd

import smoke_20260910_3head_fast_bridge as fast
import smoke_20260910_3head_live_bridge as slow
import analyze_v222_3head_broad_feature_audit as v222
import analyze_v223_3head_unused_feature_audit as v223
import analyze_v234_3head_waku10_restored_replay as v234
import analyze_v165_3head_monthly_walkforward as v165

OUT='cache_20260910_3head_live.joblib'
FIRST=pd.Timestamp('2026-09-01')
NEXT=pd.Timestamp('2026-10-01')


def main():
    # Reuse canonical restored-Waku10 artifact and optimized historical decomposition.
    v234.reconstruct=fast.cached_reconstruct
    slow.v234.reconstruct=fast.cached_reconstruct
    slow.v224.add_decomp=fast.fast_add_decomp

    d,vc,basefs,fs=slow.build_augmented()
    tr=d[d._date<FIRST].copy()
    pair=v222.fit_pair(tr,'V221')

    # Freeze the exact September head model instead of refitting it during LIVE.
    hfs=v223.numeric_ok(d,fs)
    htr=d[d._date<FIRST].copy()
    for c in hfs:
        htr[c]=pd.to_numeric(htr[c],errors='coerce')
    cats=[vc] if vc and vc not in hfs else []
    head=v165.model(hfs,cats)
    head.fit(htr[hfs+cats],htr._y.astype(int))

    codes={'202609101605','202609101407'}
    cur=d[d.race_code.astype(str).str.zfill(12).isin(codes)].copy()
    if len(cur)!=2:
        raise RuntimeError(f'expected 2 current rows, got {len(cur)}')

    joblib.dump({
        'head_model':head,
        'head_features':hfs,
        'head_cats':cats,
        'pair_model':pair,
        'current_rows':cur,
        'built_for':'2026-09-10',
        'history_cutoff':'2026-08-31',
        'result_blind_target_day':True,
    },OUT,compress=3)
    print('CACHE_READY',OUT,'rows',len(cur),'head_features',len(hfs),flush=True)

if __name__=='__main__':
    main()
