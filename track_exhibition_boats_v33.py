#!/usr/bin/env python3
"""Result-blind v33: robust shared-translation compensation on the first transition.

v32 proved that an unconstrained 3-point affine fit is too flexible on the first
six-boat transition: it can explain wrong candidate geometry with near-zero
residual. At the slit the camera contribution over one stride is instead
modelled conservatively as a single fleet-wide translation, estimated by the
coordinate-wise median of all six displacements. Candidate identity is then
judged from each boat's residual motion after subtracting that shared camera
translation. Later transitions retain v31's robust affine model unchanged.

The existing 24 px/native-frame relative residual cap, 42 px absolute hard
ceiling, reverse corridor, appearance/geometry gates and fail-closed behavior
are retained. No future frame, result, boat-number special case, race-specific
offset or confidence-threshold relaxation is used.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v25 as v25
import track_exhibition_boats_v31 as v31

DIAG33={k:0 for k in ["transition_calls","initial_translation_calls","initial_reject_relative_residual","initial_reject_absolute_speed","initial_reject_reverse","later_calls","accepts"]}

def _transition_v33(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order):
    DIAG33["transition_calls"]+=1
    if prev.get("last_step") is not None:
        DIAG33["later_calls"]+=1
        out=v31._transition_v31(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order)
        if out is not None: DIAG33["accepts"]+=1
        return out
    DIAG33["initial_translation_calls"]+=1
    P0=np.asarray(prev["centers"],np.float64); P1=np.asarray(cur["centers"],np.float64)
    steps=P1-P0; adv=max(1,int(advance))
    shared=np.median(steps,axis=0)
    residual_vec=steps-shared
    residual=np.linalg.norm(residual_vec,axis=1)
    if np.any(residual>24.0*adv):
        DIAG33["initial_reject_relative_residual"]+=1; return None
    if np.any(np.linalg.norm(steps,axis=1)>42.0*adv):
        DIAG33["initial_reject_absolute_speed"]+=1; return None
    score=float(cur["local_score"])-0.024*float(np.sum(residual))
    for i in range(6):
        sign=float(dir_sign[i]); sx=float(steps[i,0])
        if sign!=0.0:
            signed_step=sign*sx; progress=sign*float(P1[i,0]-initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap*adv:
                DIAG33["initial_reject_reverse"]+=1; return None
            if signed_step<0.0: score-=0.18*min(-signed_step,step_reverse_cap*adv)
            else: score+=0.018*min(signed_step,24.0*adv)
            if progress<0.0: score-=0.055*min(-progress,reverse_cap)
    DIAG33["accepts"]+=1
    return score,steps.astype(np.float32)

def _out_path(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v33.json")

def main():
    old=v25._transition_v25
    v25._transition_v25=_transition_v33
    try:
        try: v25.main()
        except SystemExit as exc: code=int(exc.code or 0) if isinstance(exc.code,(int,type(None))) else 2
    finally:
        v25._transition_v25=old
    p=_out_path(sys.argv)
    if p.exists():
        try:
            j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v33_initial_robust_translation_later_affine"; j["diagnostics_v33"]={k:int(v) for k,v in DIAG33.items()}; j["diagnostics_v31"]={k:int(v) for k,v in v31.DIAG31.items()}; p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as e: print(f"v33 diagnostics write warning: {e}",file=sys.stderr)
    print(json.dumps({"diagnostics_v33":DIAG33,"diagnostics_v31":v31.DIAG31},ensure_ascii=False))
    raise SystemExit(code)

if __name__=="__main__": main()
