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

Opponent rows are emitted for every race so boat-1 losses remain available at inference
and settlement time. Training remains fail-closed: only valid 1-x-y outcomes produce a
positive SECOND label or a conditional THIRD training group; all other races are scored
for inference but ignored by the grouped listwise fit.
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


def second_long_all(d,sufs):
    """Emit all races for inference; only valid 1-x-y races have one positive label."""
    rec=[]
    for _,r in d.iterrows():
        a2,a3=v298.actual23(r.actual_combo)
        valid=int(r.head_hit)==1 and a2 in BOATS and a3 in BOATS
        for b in BOATS:
            z={'date':r.date,'month':r.month,'race_code':str(r.race_code).zfill(12),
               'y2':int(valid and b==a2),'actual2':a2,'actual3':a3}
            z.update(cand_record(r,b,sufs));rec.append(z)
    return pd.DataFrame(rec)


def conditional_long_all(d,sufs):
    """Emit all candidate pairs; invalid/non-1-head races are inference-only groups."""
    rec=[]
    for _,r in d.iterrows():
        a2,a3=v298.actual23(r.actual_combo)
        valid=int(r.head_hit)==1 and a2 in BOATS and a3 in BOATS
        for s in BOATS:
            sr=cand_record(r,s,sufs,'s_')
            for t in BOATS:
                if t==s:continue
                tr=cand_record(r,t,sufs,'t_')
                z={'date':r.date,'month':r.month,'race_code':str(r.race_code).zfill(12),
                   'group_id':f'{str(r.race_code).zfill(12)}|{s}',
                   'second_boat':s,'third_boat':t,
                   'train_group':int(valid and s==a2),
                   'ycond':int(valid and s==a2 and t==a3),
                   'actual2':a2,'actual3':a3,
                   'pair_same_side1':float((s<=3 and t<=3) or (s>=4 and t>=4)),
                   'pair_second_inner23':float(s in (2,3)),
                   'pair_second_outer456':float(s in (4,5,6)),
                   'pair_third_inner23':float(t in (2,3)),
                   'pair_third_outer456':float(t in (4,5,6)),
                   'pair_adjacent':float(abs(s-t)==1),'pair_distance':float(abs(s-t)),
                   'pair_third_minus_second':float(t-s),'pair_second_is2':float(s==2),
                   'pair_second_is3':float(s==3),'pair_second_is4':float(s==4),
                   'pair_second_is5':float(s==5),'pair_second_is6':float(s==6)}
                z.update(sr);z.update(tr)
                for k in sufs:
                    tv=z.get(f't_cand_{k}',np.nan);sv=z.get(f's_cand_{k}',np.nan)
                    z[f'diff_{k}']=tv-sv if pd.notna(tv) and pd.notna(sv) else np.nan
                    z[f'prod_{k}']=tv*sv if pd.notna(tv) and pd.notna(sv) else np.nan
                rec.append(z)
    return pd.DataFrame(rec)


if __name__=='__main__':
    v298.add_threat_original=v298.add_threat
    base.cand_record_original=base.cand_record
    base._cand_record_original=base.cand_record
    base.curated_suffixes=curated_suffixes
    base.cand_record=cand_record

    v298.add_threat=base.add_threat
    v298.suffixes=curated_suffixes
    v298.cand_record=cand_record
    v298.second_long=second_long_all
    v298.conditional_long=conditional_long_all
    v298.v279.ListwiseSoftmax=base.FastSecond
    v298.v282.ListwiseN=base.FastConditional
    settlement.AUDIT.clear()
    v298.v297.settle_full_after_freeze=settlement.settle_union_after_freeze
    print('v298 final audit runner: PLAYER_START pl_* fixed + within-race candidate relative signals + vectorized listwise + cached race context + all-race inference',flush=True)
    v298.main()
