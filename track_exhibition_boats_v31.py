#!/usr/bin/env python3
"""Result-blind v31 shared robust affine-camera transition, correctly wired into v25.

Audit of v30 found an integration defect before scientific validation: v30 tried
to monkey-patch ``v25.transition_ok``, but the retained v25 implementation exposes
``_transition_v25`` as the transition hook.  v31 keeps the intended v30 affine
camera science and unchanged safety caps, but installs it at the actual hook.

For every causal transition, enumerate C(6,3) exact affine fits from previous to
current six-boat centers and choose the fleet consensus by fourth-smallest
residual then trimmed mean of the best four.  With a previous accepted step,
reconstruct the previous-previous centers causally and compare affine residuals
to retain the unchanged 20 px/native-frame residual-acceleration gate.
No future frame, result, boat/race special case, or threshold relaxation is used.
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v25 as v25

DIAG31={k:0 for k in ["transition_calls","transition_reject_initial_speed","transition_reject_consensus_fit","transition_reject_relative_residual","transition_reject_relative_acceleration","transition_reject_absolute_speed","transition_reject_reverse","transition_accepts","consensus_fit_calls","consensus_candidate_fits"]}

def _fit_affine(src,dst):
    src=np.asarray(src,np.float64); dst=np.asarray(dst,np.float64)
    if src.shape!=(3,2) or dst.shape!=(3,2): return None
    X=np.column_stack([src,np.ones(3)])
    if abs(float(np.linalg.det(X)))<1e-6: return None
    try: return np.linalg.solve(X,dst)
    except np.linalg.LinAlgError: return None

def _apply_affine(B,pts):
    pts=np.asarray(pts,np.float64)
    return np.column_stack([pts,np.ones(len(pts))])@B

def _shared_affine(prev_pts,new_pts):
    prev_pts=np.asarray(prev_pts,np.float64); new_pts=np.asarray(new_pts,np.float64)
    DIAG31["consensus_fit_calls"]+=1
    best=None; best_key=None
    for idx in itertools.combinations(range(6),3):
        B=_fit_affine(prev_pts[list(idx)],new_pts[list(idx)])
        if B is None: continue
        DIAG31["consensus_candidate_fits"]+=1
        r=np.linalg.norm(new_pts-_apply_affine(B,prev_pts),axis=1)
        s=np.sort(r)
        key=(float(s[3]),float(np.mean(s[:4])))
        if best_key is None or key<best_key:
            best_key=key; best=(B,r)
    return best

def _transition_v31(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order):
    DIAG31["transition_calls"]+=1
    P0=np.asarray(prev["centers"],np.float64); P1=np.asarray(cur["centers"],np.float64)
    steps=P1-P0; adv=max(1,int(advance)); pv=prev.get("last_step")
    if pv is None:
        if np.any(np.linalg.norm(steps,axis=1)>24.0*adv):
            DIAG31["transition_reject_initial_speed"]+=1; return None
        residual=np.zeros(6,np.float64)
    else:
        fit=_shared_affine(P0,P1)
        if fit is None:
            DIAG31["transition_reject_consensus_fit"]+=1; return None
        _,residual=fit
        if np.any(residual>24.0*adv):
            DIAG31["transition_reject_relative_residual"]+=1; return None
        pv=np.asarray(pv,np.float64)
        Pm1=P0-pv
        fit0=_shared_affine(Pm1,P0)
        if fit0 is not None:
            _,res0=fit0
            if np.any(np.abs(residual-res0)>20.0*adv):
                DIAG31["transition_reject_relative_acceleration"]+=1; return None
        if np.any(np.linalg.norm(steps,axis=1)>42.0*adv):
            DIAG31["transition_reject_absolute_speed"]+=1; return None

    score=float(cur["local_score"])
    for i in range(6):
        sign=float(dir_sign[i]); sx=float(steps[i,0])
        if sign!=0.0:
            signed_step=sign*sx; progress=sign*float(P1[i,0]-initial_x[i])
            if progress < -reverse_cap or signed_step < -step_reverse_cap*adv:
                DIAG31["transition_reject_reverse"]+=1; return None
            if signed_step<0.0: score-=0.18*min(-signed_step,step_reverse_cap*adv)
            else: score+=0.018*min(signed_step,24.0*adv)
            if progress<0.0: score-=0.055*min(-progress,reverse_cap)
        if pv is not None:
            score-=0.024*float(residual[i])
    if pv is not None:
        score-=0.004*float(np.sum(residual))
    DIAG31["transition_accepts"]+=1
    return score,steps.astype(np.float32)

def _out_path(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v31.json")

def main():
    old=v25._transition_v25
    v25._transition_v25=_transition_v31
    try:
        try: v25.main()
        except SystemExit as exc: code=int(exc.code or 0) if isinstance(exc.code,(int,type(None))) else 2
    finally:
        v25._transition_v25=old
    p=_out_path(sys.argv)
    if p.exists():
        try:
            j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v31_shared_robust_affine_camera_fixed_hook"; j["diagnostics_v31"]={k:int(v) for k,v in DIAG31.items()}; p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as e: print(f"v31 diagnostics write warning: {e}",file=sys.stderr)
    print(json.dumps({"diagnostics_v31":DIAG31},ensure_ascii=False))
    raise SystemExit(code)

if __name__=="__main__": main()
