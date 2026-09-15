#!/usr/bin/env python3
"""Result-blind v30 shared robust fleet-consensus affine-camera transition.

v29 proved that making the camera state shared across the fleet did not solve
beam exhaustion when the shared state was still restricted to a similarity
transform. Start-exhibition footage is oblique; pan/zoom plus first-order
perspective produces anisotropic scale/shear across the large y-span occupied
by six boats. v30 therefore changes ONLY the camera representation from shared
similarity to shared affine.

All v25/v29 proposal reachability, appearance bank/anchors, beam search, NCC,
immutable reverse-motion gates, fleet geometry, and numerical motion caps stay
unchanged. For each transition enumerate C(6,3)=20 three-boat affine fits,
score each on all six boats by 4th-smallest residual then trimmed mean of four
best residuals, select one shared fleet transform, and apply the unchanged
24 px/native-frame residual and 20 px/native-frame residual-acceleration caps.
No future frame, result, boat-number rule, race-specific offset, or threshold
relaxation is used.

Validation note: this source-only comment also provides a clean push-path
retrigger after the already-registered v29 bridge workflow has propagated.
"""
from __future__ import annotations
import itertools, json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v25 as v25
DIAG30={k:0 for k in ["transition_calls","transition_reject_initial_speed","transition_reject_consensus_fit","transition_reject_relative_residual","transition_reject_relative_acceleration","transition_reject_absolute_speed","transition_reject_reverse","transition_accepts","consensus_fit_calls","consensus_candidate_fits"]}
def _fit_affine(src,dst):
    src=np.asarray(src,np.float64); dst=np.asarray(dst,np.float64)
    if src.shape!=(3,2) or dst.shape!=(3,2): return None
    X=np.column_stack([src,np.ones(3)])
    if abs(float(np.linalg.det(X)))<1e-6: return None
    try: B=np.linalg.solve(X,dst)
    except np.linalg.LinAlgError: return None
    return B

def _apply_affine(B,pts):
    pts=np.asarray(pts,np.float64)
    return np.column_stack([pts,np.ones(len(pts))])@B

def _shared_affine(prev_pts,new_pts):
    DIAG30["consensus_fit_calls"]+=1
    best=None; best_key=None
    for idx in itertools.combinations(range(6),3):
        B=_fit_affine(prev_pts[list(idx)],new_pts[list(idx)])
        if B is None: continue
        DIAG30["consensus_candidate_fits"]+=1
        pred=_apply_affine(B,prev_pts)
        r=np.linalg.norm(new_pts-pred,axis=1)
        s=np.sort(r)
        key=(float(s[3]),float(np.mean(s[:4])))
        if best_key is None or key<best_key:
            best_key=key; best=(B,r)
    return best

def _transition_ok(prev_state,new_centers,frame_w):
    prev=np.asarray(prev_state["centers"],np.float64); new=np.asarray(new_centers,np.float64)
    if prev_state.get("prev_centers") is None:
        d=np.linalg.norm(new-prev,axis=1)
        if np.any(d>42.0): DIAG30["transition_reject_initial_speed"]+=1; return False,None
        return True,[None]*6
    fit=_shared_affine(prev,new)
    if fit is None: DIAG30["transition_reject_consensus_fit"]+=1; return False,None
    B,res=fit
    if np.any(res>24.0): DIAG30["transition_reject_relative_residual"]+=1; return False,None
    prevprev=np.asarray(prev_state["prev_centers"],np.float64)
    fit0=_shared_affine(prevprev,prev)
    if fit0 is not None:
        _,res0=fit0
        if np.any(np.abs(res-res0)>20.0): DIAG30["transition_reject_relative_acceleration"]+=1; return False,None
    d=np.linalg.norm(new-prev,axis=1)
    if np.any(d>42.0): DIAG30["transition_reject_absolute_speed"]+=1; return False,None
    dirs=prev_state.get("motion_dirs",[0]*6)
    anchors=np.asarray(prev_state.get("seed_centers",prev),np.float64)
    for i,sgn in enumerate(dirs):
        if not sgn: continue
        cumulative=(new[i,0]-anchors[i,0])*sgn
        step=(new[i,0]-prev[i,0])*sgn
        if cumulative < -0.05*frame_w or step < -0.0125*frame_w:
            DIAG30["transition_reject_reverse"]+=1; return False,None
    DIAG30["transition_accepts"]+=1
    return True,res.tolist()

def main():
    old=v25.transition_ok
    def wrapped(prev_state,new_centers,frame_w):
        DIAG30["transition_calls"]+=1
        return _transition_ok(prev_state,new_centers,frame_w)
    v25.transition_ok=wrapped
    try:
        rc=v25.main()
    finally:
        v25.transition_ok=old
    # v25 writes requested JSON; enrich it with v30 diagnostics if present.
    try:
        args=sys.argv[1:]
        if "--out" in args:
            p=Path(args[args.index("--out")+1])
            if p.exists():
                j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v30_shared_robust_affine_camera"; j["diagnostics_v30"]=DIAG30; p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding="utf-8")
    except Exception as e:
        print(f"v30 diagnostics write warning: {e}",file=sys.stderr)
    return rc
if __name__=="__main__": raise SystemExit(main())
