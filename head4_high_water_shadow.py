#!/usr/bin/env python3
"""Shadow-only high-water signal for HEAD4 live output.

Research finding to preserve for forward validation:
water temperature >=30C AND Waku10 4-vs-3 SR >0 AND ST >0.
This flag never changes selected/decision/tickets/staking.
"""
from __future__ import annotations

def high_water_shadow(water_c, rel4_b3_sr, rel4_b3_st):
    try:
        w=float(water_c); sr=float(rel4_b3_sr); st=float(rel4_b3_st)
    except (TypeError,ValueError):
        return {"active":False,"label":None,"reason":"INPUT_NOT_READY","research_only":True,"production_applied":False}
    active=bool(w>=30.0 and sr>0.0 and st>0.0)
    return {
      "active":active,
      "label":"HIGH_WATER_30C_WAKU43_SR_ST" if active else None,
      "water_c":w,"rel4_b3_sr":sr,"rel4_b3_st":st,
      "research_only":True,"production_applied":False,
      "changes_bet_decision":False,
      "forward_validation":"2027 summer high-water season",
    }
