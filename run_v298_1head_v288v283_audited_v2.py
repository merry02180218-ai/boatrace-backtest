#!/usr/bin/env python3
"""Final v298 audited runner: fix PLAYER_START player-history parity.

Builds on the vectorized v288/v283-aligned runner, but explicitly admits symmetric
`pl_*` prior-player fields (the previous `_pl_` string test missed names such as
`pl_all_win`) and adds candidate-within-race median/rank signals directly to both
SECOND and conditional THIRD candidate records.

The candidate feature constructor keeps exact v2 semantics while caching the six-boat
numeric context once per race row.  SECOND/THIRD construction calls cand_record many
times for the same row, so recomputing all six boats for every suffix on every call was
the dominant runtime/memory-allocation cost in CI.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v297_1head_guard_trifecta5_research as settlement
import run_v298_1head_v288v283_audited as base

BOATS=v298.BOATS
SAFE=base.SAFE

_LAST_ROW_TOKEN=None
_LAST_SUFS=None
_LAST_CTX=None


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


def _row_context(r,sufs):
    """Build exact numeric/relative candidate context once for the current race row."""
    global _LAST_ROW_TOKEN,_LAST_SUFS,_LAST_CTX
    token=(str(r.get('race_code','')),str(r.get('date','')),id(r))
    skey=tuple(sufs)
    if token==_LAST_ROW_TOKEN and skey==_LAST_SUFS and _LAST_CTX is not None:
        return _LAST_CTX
    ctx={}
    for k in sufs:
        vals=pd.to_numeric(pd.Series([r.get(f'b{b}_{k}',np.nan) for b in range(1,7)]),errors='coerce').to_numpy(float)
        opp=vals[1:]
        valid=opp[np.isfinite(opp)]
        rel={}
        for b in BOATS:
            cv=vals[b-1]
            if np.isfinite(cv) and valid.size:
                med=float(np.median(valid))
                less=int(np.sum(valid<cv));equal=int(np.sum(valid==cv))
                center=float(cv-med)
                pct=float((less+(equal+1)/2)/len(valid))
                gapmax=float(cv-np.max(valid))
            else:
                center=pct=gapmax=np.nan
            inner=vals[1:b-1]
            inner=inner[np.isfinite(inner)]
            if np.isfinite(cv):
                innerdiff=float(np.max(inner)-cv) if inner.size else (0.0 if b==2 else np.nan)
            else:
                innerdiff=np.nan
            h=vals[0]
            rel[b]=(float(cv) if np.isfinite(cv) else np.nan,
                    float(cv-h) if np.isfinite(cv) and np.isfinite(h) else np.nan,
                    innerdiff,center,pct,gapmax)
        ctx[k]=rel
    _LAST_ROW_TOKEN=token;_LAST_SUFS=skey;_LAST_CTX=ctx
    return ctx


def cand_record(r,b,sufs,prefix=''):
    ctx=_row_context(r,sufs)
    if prefix:
        z={f'{prefix}pos_boat':float(b),f'{prefix}pos_inner23':float(b in (2,3)),
           f'{prefix}pos_outer456':float(b in (4,5,6)),f'{prefix}pos_edge3':float(b==3),
           f'{prefix}pos_edge4':float(b==4),f'{prefix}pos_distance1':float(b-1)}
    else:
        z={'boat':int(b),'pos_boat':float(b),'pos_inner23':float(b in (2,3)),
           'pos_outer456':float(b in (4,5,6)),'pos_edge3':float(b==3),
           'pos_edge4':float(b==4),'pos_distance1':float(b-1)}
    for k in sufs:
        cv,diff1,innerdiff,center,pct,gapmax=ctx[k][b]
        z[f'{prefix}cand_{k}']=cv
        z[f'{prefix}diff1_{k}']=diff1
        z[f'{prefix}innermax_{k}_minus_cand']=innerdiff
        z[f'{prefix}cand_{k}__center']=center
        z[f'{prefix}cand_{k}__pct']=pct
        z[f'{prefix}cand_{k}__gapmax']=gapmax
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
    print('v298 final audit runner: PLAYER_START pl_* fixed + within-race candidate relative signals + vectorized listwise + cached race context',flush=True)
    v298.main()
