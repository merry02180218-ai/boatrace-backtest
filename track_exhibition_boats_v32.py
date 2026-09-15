#!/usr/bin/env python3
"""Result-blind v32: robust affine camera compensation from the first transition.

v31's fixed-hook audit showed Kiryu3 rejecting every first transition at the raw
24 px/native-frame speed gate. That gate is inconsistent with the later robust
affine camera model: shared camera pan/zoom can make raw first-step screen motion
large even when fleet-relative motion is sane. v32 applies the same six-boat
robust affine consensus at the initial transition, while retaining the existing
24 px relative-residual cap, 42 px absolute hard ceiling, reverse corridor,
appearance/geometry gates, and all later-step v31 logic.

This is a coordinate-model consistency fix, not a threshold relaxation. No
future frame, result, boat-number special case, or race-specific offset is used.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v25 as v25
import track_exhibition_boats_v31 as v31

DIAG32={k:0 for k in ["transition_calls","initial_affine_calls","initial_reject_consensus_fit","initial_reject_relative_residual","initial_reject_absolute_speed","later_calls","accepts"]}

def _transition_v32(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order):
    DIAG32["transition_calls"]+=1
    if prev.get("last_step") is not None:
        DIAG32["later_calls"]+=1
        out=v31._transition_v31(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order)
        if out is not None: DIAG32["accepts"]+=1
        return out
    DIAG32["initial_affine_calls"]+=1
    P0=np.asarray(prev["centers"],np.float64); P1=np.asarray(cur["centers"],np.float64)
    steps=P1-P0; adv=max(1,int(advance))
    fit=v31._shared_affine(P0,P1)
    if fit is None:
        DIAG32["initial_reject_consensus_fit"]+=1; return None
    _,residual=fit
    if np.any(residual>24.0*adv):
        DIAG32["initial_reject_relative_residual"]+=1; return None
    if np.any(np.linalg.norm(steps,axis=1)>42.0*adv):
        DIAG32["initial_reject_absolute_speed"]+=1; return None
    score=float(cur["local_score"])-0.024*float(np.sum(residual))
    for i in range(6):
        sign=float(dir_sign[i]); sx=float(steps[i,0])
        if sign!=0.0:
            signed_step=sign*sx; progress=sign*float(P1[i,0]-initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap*adv:
                return None
            if signed_step<0.0: score-=0.18*min(-signed_step,step_reverse_cap*adv)
            else: score+=0.018*min(signed_step,24.0*adv)
            if progress<0.0: score-=0.055*min(-progress,reverse_cap)
    DIAG32["accepts"]+=1
    return score,steps.astype(np.float32)

def _out_path(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v32.json")

def main():
    old=v25._transition_v25
    v25._transition_v25=_transition_v32
    try:
        try: v25.main()
        except SystemExit as exc: code=int(exc.code or 0) if isinstance(exc.code,(int,type(None))) else 2
    finally:
        v25._transition_v25=old
    p=_out_path(sys.argv)
    if p.exists():
        try:
            j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v32_initial_and_later_robust_affine_camera"; j["diagnostics_v32"]={k:int(v) for k,v in DIAG32.items()}; j["diagnostics_v31"]={k:int(v) for k,v in v31.DIAG31.items()}; p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as e: print(f"v32 diagnostics write warning: {e}",file=sys.stderr)
    print(json.dumps({"diagnostics_v32":DIAG32,"diagnostics_v31":v31.DIAG31},ensure_ascii=False))
    raise SystemExit(code)

if __name__=="__main__": main()
