#!/usr/bin/env python3
"""Result-blind v34: robust shared-translation compensation on every transition.

v33 fixed the first-transition degeneracy with a fleet-wide median translation,
but then handed later steps back to v31's affine fit. The v33 Kiryu3 artifact
failed at native frame 18 with 1,271 later-transition relative-residual rejects,
so v34 tests the narrower hypothesis that a short stride should use the same
robust shared camera translation throughout. This avoids a 3-point affine model
explaining or rejecting identity based on a flexible local warp.

For each transition, subtract the coordinate-wise median six-boat displacement.
Gate per-boat residual motion at the unchanged 24 px/native-frame cap and the
unchanged 42 px absolute ceiling. From the second transition onward, compare
camera-subtracted residual velocity with the previous transition's
camera-subtracted residual velocity and retain v31's 18 px/native-frame
relative-acceleration cap. Reverse corridor logic is unchanged. No future frame,
result, boat/race special case, offset, or confidence relaxation is used.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v25 as v25

DIAG34={k:0 for k in ["transition_calls","reject_relative_residual","reject_relative_acceleration","reject_absolute_speed","reject_reverse","accepts"]}

def _transition_v34(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order):
    DIAG34["transition_calls"]+=1
    P0=np.asarray(prev["centers"],np.float64); P1=np.asarray(cur["centers"],np.float64)
    steps=P1-P0; adv=max(1,int(advance))
    shared=np.median(steps,axis=0)
    residual_vec=steps-shared
    residual=np.linalg.norm(residual_vec,axis=1)
    if np.any(residual>24.0*adv):
        DIAG34["reject_relative_residual"]+=1; return None
    if np.any(np.linalg.norm(steps,axis=1)>42.0*adv):
        DIAG34["reject_absolute_speed"]+=1; return None
    score=float(cur["local_score"])-0.024*float(np.sum(residual))
    prev_vel=prev.get("velocity")
    if prev.get("last_step") is not None and prev_vel is not None:
        pv=np.asarray(prev_vel,np.float64)
        prev_shared=np.median(pv,axis=0)
        prev_residual=pv-prev_shared
        rel_acc=np.linalg.norm(residual_vec-prev_residual,axis=1)
        if np.any(rel_acc>18.0*adv):
            DIAG34["reject_relative_acceleration"]+=1; return None
        score-=0.014*float(np.sum(rel_acc))
    for i in range(6):
        sign=float(dir_sign[i]); sx=float(steps[i,0])
        if sign!=0.0:
            signed_step=sign*sx; progress=sign*float(P1[i,0]-initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap*adv:
                DIAG34["reject_reverse"]+=1; return None
            if signed_step<0.0: score-=0.18*min(-signed_step,step_reverse_cap*adv)
            else: score+=0.018*min(signed_step,24.0*adv)
            if progress<0.0: score-=0.055*min(-progress,reverse_cap)
    DIAG34["accepts"]+=1
    return score,steps.astype(np.float32)

def _out_path(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v34.json")

def main():
    old=v25._transition_v25
    v25._transition_v25=_transition_v34
    try:
        try: v25.main()
        except SystemExit as exc: code=int(exc.code or 0) if isinstance(exc.code,(int,type(None))) else 2
    finally:
        v25._transition_v25=old
    p=_out_path(sys.argv)
    if p.exists():
        try:
            j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v34_all_step_robust_translation"; j["diagnostics_v34"]={k:int(v) for k,v in DIAG34.items()}; p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as e: print(f"v34 diagnostics write warning: {e}",file=sys.stderr)
    print(json.dumps({"diagnostics_v34":DIAG34},ensure_ascii=False))
    raise SystemExit(code)

if __name__=="__main__": main()
