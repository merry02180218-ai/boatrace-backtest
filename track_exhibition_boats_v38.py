#!/usr/bin/env python3
"""Result-blind v38: robust quadratic row-perspective camera field.

v37's continuous linear y-camera field still exhausted the beam on the unchanged
four-case matrix; artifacts show many feasible transitions but late candidate
exhaustion (e.g. Kiryu12 native frame 34). A perspective projection across the
full vertical span need not be linear, so v38 keeps v35 proposal generation and
all immutable NCC/appearance/fleet/reverse/motion thresholds while replacing only
the camera field with a robust degree-2 function of normalized image y.

For each displacement coordinate, fit all 3-point quadratic interpolants from the
six boats, discard numerically singular triples, and take the median predicted
value at each boat y. This is still fleet-only, same-frame, low-DOF geometry: no
future frame, race result, boat/race special case, offset, or threshold relaxation.
Residual cap remains 24 px/native-frame, relative-acceleration cap 18 px/native-
frame, absolute step cap 42 px/native-frame.
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v35 as v35

v34=v35.v34
DIAG38={k:0 for k in ["transition_calls","reject_relative_residual","reject_relative_acceleration","reject_absolute_speed","reject_reverse","accepts","camera_fallback_linear"]}

def _robust_quad(y,v):
    y=np.asarray(y,np.float64); v=np.asarray(v,np.float64)
    yc=float(np.median(y)); ys=max(32.0,float(np.ptp(y)))
    z=(y-yc)/ys; preds=[]
    for idx in itertools.combinations(range(len(y)),3):
        A=np.column_stack((np.ones(3),z[list(idx)],z[list(idx)]**2))
        if abs(float(np.linalg.det(A)))<1e-5: continue
        try: coef=np.linalg.solve(A,v[list(idx)])
        except np.linalg.LinAlgError: continue
        p=coef[0]+coef[1]*z+coef[2]*z*z
        # Reject explosive interpolants; this is a model-stability guard, not a
        # motion threshold. Physical motion gates are applied unchanged below.
        if np.all(np.isfinite(p)) and float(np.max(np.abs(p)))<250.0:
            preds.append(p)
    if preds:
        return np.median(np.asarray(preds),axis=0)
    DIAG38["camera_fallback_linear"]+=1
    A=np.column_stack((np.ones(len(z)),z))
    coef=np.linalg.lstsq(A,v,rcond=None)[0]
    return A@coef

def _camera(P0,vec):
    y=P0[:,1]
    return np.column_stack((_robust_quad(y,vec[:,0]),_robust_quad(y,vec[:,1])))

def _transition_v38(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order):
    DIAG38["transition_calls"]+=1
    P0=np.asarray(prev["centers"],np.float64); P1=np.asarray(cur["centers"],np.float64)
    steps=P1-P0; adv=max(1,int(advance)); cam=_camera(P0,steps)
    residual_vec=steps-cam; residual=np.linalg.norm(residual_vec,axis=1)
    if np.any(residual>24.0*adv): DIAG38["reject_relative_residual"]+=1; return None
    if np.any(np.linalg.norm(steps,axis=1)>42.0*adv): DIAG38["reject_absolute_speed"]+=1; return None
    score=float(cur["local_score"])-0.024*float(np.sum(residual))
    pv=prev.get("velocity")
    if prev.get("last_step") is not None and pv is not None:
        pv=np.asarray(pv,np.float64); prev_cam=_camera(P0-pv,pv); prev_residual=pv-prev_cam
        rel_acc=np.linalg.norm(residual_vec-prev_residual,axis=1)
        if np.any(rel_acc>18.0*adv): DIAG38["reject_relative_acceleration"]+=1; return None
        score-=0.014*float(np.sum(rel_acc))
    for i in range(6):
        sign=float(dir_sign[i]); sx=float(steps[i,0])
        if sign!=0.0:
            signed_step=sign*sx; progress=sign*float(P1[i,0]-initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap*adv:
                DIAG38["reject_reverse"]+=1; return None
            if signed_step<0.0: score-=0.18*min(-signed_step,step_reverse_cap*adv)
            else: score+=0.018*min(signed_step,24.0*adv)
            if progress<0.0: score-=0.055*min(-progress,reverse_cap)
    DIAG38["accepts"]+=1
    return score,steps.astype(np.float32)

def _out_path(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v38.json")

def main():
    old=v34._transition_v34; v34._transition_v34=_transition_v38
    try:
        try: v35.main()
        except SystemExit as exc: code=int(exc.code or 0) if isinstance(exc.code,(int,type(None))) else 2
    finally: v34._transition_v34=old
    p=_out_path(sys.argv)
    if p.exists():
        try:
            j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v38_robust_quadratic_row_camera"; j["diagnostics_v38"]={k:int(v) for k,v in DIAG38.items()}; p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as e: print(f"v38 diagnostics write warning: {e}",file=sys.stderr)
    print(json.dumps({"diagnostics_v38":DIAG38},ensure_ascii=False)); raise SystemExit(code)

if __name__=="__main__": main()
