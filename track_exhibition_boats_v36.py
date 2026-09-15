#!/usr/bin/env python3
"""Result-blind v36: perspective-band robust shared-translation compensation.

v35 added shared-motion proposal diversity but Kiryu3 still exhausted at native
frame 18; v34 diagnostics showed 990 transition rejects at the single global
translation residual gate. A single screen translation is too rigid under
perspective: upper and lower halves can have different apparent camera motion.

v36 keeps the exact 24 px/native-frame residual cap, 42 px absolute cap, 18 px
relative-acceleration cap, NCC/appearance/fleet/reverse gates and v35 proposal
logic. It only estimates shared camera motion separately for the upper and lower
three image rows (sorted by current y), using each band's coordinate-wise median.
This is geometry-derived, not boat-number/race-specific, and uses no future frame
or result information.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v35 as v35

v34=v35.v34
DIAG36={k:0 for k in ["transition_calls","reject_band_residual","reject_relative_acceleration","reject_absolute_speed","reject_reverse","accepts"]}

def _band_shared(P0, vec):
    order=np.argsort(P0[:,1])
    shared=np.zeros_like(vec,dtype=np.float64)
    for inds in (order[:3],order[3:]):
        med=np.median(vec[inds],axis=0)
        shared[inds]=med
    return shared

def _transition_v36(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order):
    DIAG36["transition_calls"]+=1
    P0=np.asarray(prev["centers"],np.float64); P1=np.asarray(cur["centers"],np.float64)
    steps=P1-P0; adv=max(1,int(advance))
    shared=_band_shared(P0,steps)
    residual_vec=steps-shared
    residual=np.linalg.norm(residual_vec,axis=1)
    if np.any(residual>24.0*adv):
        DIAG36["reject_band_residual"]+=1; return None
    if np.any(np.linalg.norm(steps,axis=1)>42.0*adv):
        DIAG36["reject_absolute_speed"]+=1; return None
    score=float(cur["local_score"])-0.024*float(np.sum(residual))
    prev_vel=prev.get("velocity")
    if prev.get("last_step") is not None and prev_vel is not None:
        pv=np.asarray(prev_vel,np.float64)
        prev_shared=_band_shared(P0,pv)
        prev_residual=pv-prev_shared
        rel_acc=np.linalg.norm(residual_vec-prev_residual,axis=1)
        if np.any(rel_acc>18.0*adv):
            DIAG36["reject_relative_acceleration"]+=1; return None
        score-=0.014*float(np.sum(rel_acc))
    for i in range(6):
        sign=float(dir_sign[i]); sx=float(steps[i,0])
        if sign!=0.0:
            signed_step=sign*sx; progress=sign*float(P1[i,0]-initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap*adv:
                DIAG36["reject_reverse"]+=1; return None
            if signed_step<0.0: score-=0.18*min(-signed_step,step_reverse_cap*adv)
            else: score+=0.018*min(signed_step,24.0*adv)
            if progress<0.0: score-=0.055*min(-progress,reverse_cap)
    DIAG36["accepts"]+=1
    return score,steps.astype(np.float32)

def _out_path(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v36.json")

def main():
    old=v34._transition_v34
    v34._transition_v34=_transition_v36
    try:
        try: v35.main()
        except SystemExit as exc: code=int(exc.code or 0) if isinstance(exc.code,(int,type(None))) else 2
    finally:
        v34._transition_v34=old
    p=_out_path(sys.argv)
    if p.exists():
        try:
            j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v36_perspective_band_translation"; j["diagnostics_v36"]={k:int(v) for k,v in DIAG36.items()}; p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as e: print(f"v36 diagnostics write warning: {e}",file=sys.stderr)
    print(json.dumps({"diagnostics_v36":DIAG36},ensure_ascii=False))
    raise SystemExit(code)

if __name__=="__main__": main()
