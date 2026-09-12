#!/usr/bin/env python3
"""Inference-only full pair order for HEAD4 v291 lineage.

This extends the already-frozen v283 TOP2XTOP2 ordering beyond the first four
pairs without changing those first four.  It does not train, calibrate, read
outcomes, or use v96.  The full 20-pair order is exactly v283.order_policy:
TOP2XTOP2 structural prefix followed by the remaining alpha2=.60 joint order.
"""
from __future__ import annotations
from typing import Mapping

import head4_v291_downstream_inference as h


def full_v283_order(p2: Mapping[int,float], pc: Mapping[tuple[int,int],float]):
    if set(p2)!=set(h.BOATS):
        raise h.FrozenInferenceError('SECOND probability boat universe mismatch')
    expected={(s,t) for s in h.BOATS for t in h.BOATS if s!=t}
    if set(pc)!=expected:
        raise h.FrozenInferenceError('conditional THIRD probability universe mismatch')
    base=h._joint_order(p2,pc)
    sr=sorted(h.BOATS,key=lambda s:(-float(p2[s]),s))
    cr={s:sorted((t for t in h.BOATS if t!=s),key=lambda t:(-float(pc[(s,t)]),t)) for s in h.BOATS}
    s1,s2=sr[:2]
    pool=[(s,cr[s][k]) for k in (0,1) for s in (s1,s2)]
    rank={pair:i for i,pair in enumerate(base)}
    prefix=sorted(pool,key=lambda pair:rank[pair])
    out=[];seen=set()
    for pair in prefix+base:
        if pair not in seen:
            seen.add(pair);out.append(pair)
    if len(out)!=20 or set(out)!=expected:
        raise h.FrozenInferenceError('full v283 order is not 20 unique pairs')
    if out[:4]!=h.v283_top4(p2,pc):
        raise h.FrozenInferenceError('full v283 order changed frozen Top4 prefix')
    return out


def add_full_pairs(inference: dict):
    """Attach full_pairs to an existing frozen inference result."""
    p2={int(k):float(v) for k,v in inference['p2'].items()}
    pc={}
    for k,v in inference['conditional_third'].items():
        s,t=k.split('>');pc[(int(s),int(t))]=float(v)
    order=full_v283_order(p2,pc)
    out=dict(inference)
    out['full_pairs']=[[4,s,t] for s,t in order]
    return out
