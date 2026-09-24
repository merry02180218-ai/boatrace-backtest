#!/usr/bin/env python3
from __future__ import annotations
import math

BOATS=(2,3,4,5,6)

def _int_p2(p2):
    return {int(k):float(v) for k,v in p2.items()}

def regime_meta(p2,local_edge_5_minus_4,straight_edge_5_minus_4,core_edge_5_minus_4,ratio_min=0.25):
    q=_int_p2(p2)
    order=sorted(BOATS,key=lambda b:(-q[b],b))
    denom=max(float(q[order[1]]),1e-12)
    ratio=float(q[5])/denom
    vals=[local_edge_5_minus_4,straight_edge_5_minus_4,core_edge_5_minus_4]
    finite=all(math.isfinite(float(v)) for v in vals)
    five_already_top2=5 in order[:2]
    applied=bool(
        finite and not five_already_top2
        and float(local_edge_5_minus_4)>0
        and float(straight_edge_5_minus_4)>0
        and float(core_edge_5_minus_4)>0
        and ratio>=float(ratio_min)-1e-12
    )
    return {
      'applied':applied,
      'five_already_p2_top2':bool(five_already_top2),
      'p2_order':order,
      'p2_second_boat':int(order[1]),
      'p2_ratio_5_to_second':float(ratio),
      'p2_ratio_min':float(ratio_min),
      'local_edge_5_minus_4':float(local_edge_5_minus_4),
      'straight_edge_5_minus_4':float(straight_edge_5_minus_4),
      'core_edge_5_minus_4':float(core_edge_5_minus_4),
    }

def extra_tickets(pc,formal_tickets,max_extra=3):
    formal=[str(x) for x in formal_tickets]
    fset=set(formal)
    def p(s,t):
        if (s,t) in pc:return float(pc[(s,t)])
        return float(pc[f'{s}-{t}'])
    thirds=sorted((t for t in BOATS if t!=5),key=lambda t:(-p(5,t),t))
    extras=[]
    for t in thirds:
        ticket=f'1-5-{t}'
        if ticket not in fset and ticket not in extras:
            extras.append(ticket)
        if len(extras)>=int(max_extra):break
    return extras
