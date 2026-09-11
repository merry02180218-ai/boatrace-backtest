#!/usr/bin/env python3
"""Final v298 audited runner: fix PLAYER_START player-history parity.

Builds on the vectorized v288/v283-aligned runner, but explicitly admits symmetric
`pl_*` prior-player fields (the previous `_pl_` string test missed names such as
`pl_all_win`) and adds candidate-within-race median/rank signals directly to both
SECOND and conditional THIRD candidate records.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v297_1head_guard_trifecta5_research as settlement
import run_v298_1head_v288v283_audited as base

BOATS=v298.BOATS
SAFE=base.SAFE


def curated_suffixes(d):
    out=[]
    for k in SAFE:
        if all(f'b{b}_{k}' in d for b in range(1,7)):
            out.append(k)
    for c in d.columns:
        if not c.startswith('b1_'):
            continue
        k=c[3:]
        if 'meet_' in k:
            continue
        if k.startswith('pl_') and all(f'b{b}_{k}' in d for b in range(1,7)):
            out.append(k)
    out=sorted(set(out))
    if any('meet_' in k for k in out):
        raise RuntimeError('forbidden meet_* opponent feature')
    if not any(k.startswith('pl_') for k in out):
        raise RuntimeError('PLAYER_START parity failed: no symmetric pl_* history fields')
    return out


def cand_record(r,b,sufs,prefix=''):
    z=base.cand_record_original(r,b,sufs,prefix) if hasattr(base,'cand_record_original') else base._cand_record_original(r,b,sufs,prefix)
    # v279 add_relative-style within-race signals.  For 1-head opponents the
    # candidate universe is boats 2..6.  These are PRE-only and symmetric.
    for k in sufs:
        cv=base._scalar(r.get(f'b{b}_{k}',np.nan))
        vals=[]
        for j in BOATS:
            vv=base._scalar(r.get(f'b{j}_{k}',np.nan))
            if pd.notna(vv): vals.append((j,float(vv)))
        if pd.notna(cv) and vals:
            arr=np.asarray([v for _,v in vals],float)
            z[f'{prefix}cand_{k}__center']=float(cv-np.median(arr))
            less=sum(v<float(cv) for _,v in vals); equal=sum(v==float(cv) for _,v in vals)
            z[f'{prefix}cand_{k}__pct']=(less+(equal+1)/2)/len(vals)
            z[f'{prefix}cand_{k}__gapmax']=float(cv-np.max(arr))
        else:
            z[f'{prefix}cand_{k}__center']=np.nan
            z[f'{prefix}cand_{k}__pct']=np.nan
            z[f'{prefix}cand_{k}__gapmax']=np.nan
    return z


if __name__=='__main__':
    v298.add_threat_original=v298.add_threat
    base.cand_record_original=base.cand_record
    base._cand_record_original=base.cand_record
    base.curated_suffixes=curated_suffixes
    base.cand_record=cand_record

    v298.add_threat=base.add_threat
    v298.suffixes=curated_suffixes
    v298.cand_record=cand_record
    v298.second_long=base.second_long
    v298.conditional_long=base.conditional_long
    v298.v279.ListwiseSoftmax=base.FastSecond
    v298.v282.ListwiseN=base.FastConditional
    settlement.AUDIT.clear()
    v298.v297.settle_full_after_freeze=settlement.settle_union_after_freeze
    print('v298 final audit runner: PLAYER_START pl_* fixed + within-race candidate relative signals + vectorized listwise',flush=True)
    v298.main()
