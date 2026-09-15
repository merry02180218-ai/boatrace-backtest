#!/usr/bin/env python3
"""Result-blind v37: robust continuous row-perspective camera field.

v36 split the six boats into two 3-row bands. The unchanged four-case matrix still
failed closed, so a hard band boundary is not sufficient. v37 keeps v35 proposal
generation and every immutable NCC/appearance/fleet/reverse/motion threshold, but
models short-stride camera displacement as a continuous robust linear function of
image y. Each displacement coordinate uses a Theil-Sen median pairwise slope plus
median intercept, evaluated at each boat's previous y. This is a low-DOF,
geometry-derived camera model; it is less flexible than the rejected affine model
and avoids v36's discontinuous upper/lower split.

Residual cap remains 24 px/native-frame, relative-acceleration cap 18 px/native-
frame, absolute step cap 42 px/native-frame. No future frame, result, boat/race
special case, offset, or confidence relaxation.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v35 as v35

v34=v35.v34
DIAG37={k:0 for k in ["transition_calls","reject_relative_residual","reject_relative_acceleration","reject_absolute_speed","reject_reverse","accepts"]}

def _robust_line(y,v):
    y=np.asarray(y,np.float64); v=np.asarray(v,np.float64); slopes=[]
    for i in range(len(y)):
        for j in range(i+1,len(y)):
            dy=float(y[j]-y[i])
            if abs(dy)>=8.0: slopes.append(float((v[j]-v[i])/dy))
    slope=float(np.median(slopes)) if slopes else 0.0
    intercept=float(np.median(v-slope*y))
    return intercept+slope*y

def _camera(P0,vec):
    y=P0[:,1]
    return np.column_stack((_robust_line(y,vec[:,0]),_robust_line(y,vec[:,1])))

def _transition_v37(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order):
    DIAG37["transition_calls"]+=1
    P0=np.asarray(prev["centers"],np.float64); P1=np.asarray(cur["centers"],np.float64)
    steps=P1-P0; adv=max(1,int(advance)); cam=_camera(P0,steps)
    residual_vec=steps-cam; residual=np.linalg.norm(residual_vec,axis=1)
    if np.any(residual>24.0*adv): DIAG37["reject_relative_residual"]+=1; return None
    if np.any(np.linalg.norm(steps,axis=1)>42.0*adv): DIAG37["reject_absolute_speed"]+=1; return None
    score=float(cur["local_score"])-0.024*float(np.sum(residual))
    pv=prev.get("velocity")
    if prev.get("last_step") is not None and pv is not None:
        pv=np.asarray(pv,np.float64); prev_cam=_camera(P0-pv,pv); prev_residual=pv-prev_cam
        rel_acc=np.linalg.norm(residual_vec-prev_residual,axis=1)
        if np.any(rel_acc>18.0*adv): DIAG37["reject_relative_acceleration"]+=1; return None
        score-=0.014*float(np.sum(rel_acc))
    for i in range(6):
        sign=float(dir_sign[i]); sx=float(steps[i,0])
        if sign!=0.0:
            signed_step=sign*sx; progress=sign*float(P1[i,0]-initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap*adv:
                DIAG37["reject_reverse"]+=1; return None
            if signed_step<0.0: score-=0.18*min(-signed_step,step_reverse_cap*adv)
            else: score+=0.018*min(signed_step,24.0*adv)
            if progress<0.0: score-=0.055*min(-progress,reverse_cap)
    DIAG37["accepts"]+=1
    return score,steps.astype(np.float32)

def _out_path(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v37.json")

def main():
    old=v34._transition_v34; v34._transition_v34=_transition_v37
    try:
        try: v35.main()
        except SystemExit as exc: code=int(exc.code or 0) if isinstance(exc.code,(int,type(None))) else 2
    finally: v34._transition_v34=old
    p=_out_path(sys.argv)
    if p.exists():
        try:
            j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v37_robust_linear_row_camera"; j["diagnostics_v37"]={k:int(v) for k,v in DIAG37.items()}; p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as e: print(f"v37 diagnostics write warning: {e}",file=sys.stderr)
    print(json.dumps({"diagnostics_v37":DIAG37},ensure_ascii=False)); raise SystemExit(code)

if __name__=="__main__": main()
