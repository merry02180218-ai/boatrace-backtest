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
    try: M=np.linalg.solve(X,dst)
    except np.linalg.LinAlgError: return None
    return M if np.all(np.isfinite(M)) else None
def _apply(pt,M): return np.asarray([float(pt[0]),float(pt[1]),1.0])@M
def _fleet_affine_residual(src,dst):
    src=np.asarray(src,np.float32); dst=np.asarray(dst,np.float32)
    if src.shape!=(6,2) or dst.shape!=(6,2): return None
    DIAG30["consensus_fit_calls"]+=1; best=None
    for fit in itertools.combinations(range(6),3):
        M=_fit_affine(src[list(fit)],dst[list(fit)])
        if M is None: continue
        DIAG30["consensus_candidate_fits"]+=1; es=[]
        for j in range(6):
            r=dst[j]-_apply(src[j],M); e=float(np.linalg.norm(r))
            if not np.isfinite(e): break
            es.append(e)
        if len(es)!=6: continue
        se=sorted(es); key=(se[3],float(np.mean(se[:4])),tuple(fit))
        if best is None or key<best[0]: best=(key,M)
    if best is None: return None
    return np.asarray([dst[j]-_apply(src[j],best[1]) for j in range(6)],np.float32)
def _transition(prev,cur,advance,dir_sign,initial_x,reverse_cap,step_reverse_cap,initial_order):
    DIAG30["transition_calls"]+=1; P0=np.asarray(prev["centers"],np.float32); P1=np.asarray(cur["centers"],np.float32); steps=P1-P0; adv=max(1,int(advance)); pv=prev.get("last_step")
    if pv is None:
        if np.any(np.linalg.norm(steps,axis=1)>24.0*adv): DIAG30["transition_reject_initial_speed"]+=1; return None
        rel_cur=steps-np.median(steps,axis=0); rel_prev=None
    else:
        pv=np.asarray(pv,np.float32); rel_cur=_fleet_affine_residual(P0,P1); rel_prev=_fleet_affine_residual(P0-pv,P0)
        if rel_cur is None or rel_prev is None: DIAG30["transition_reject_consensus_fit"]+=1; return None
        acc=rel_cur-rel_prev
        if np.any(np.linalg.norm(rel_cur,axis=1)>24.0*adv): DIAG30["transition_reject_relative_residual"]+=1; return None
        if np.any(np.linalg.norm(acc,axis=1)>20.0*adv): DIAG30["transition_reject_relative_acceleration"]+=1; return None
        if np.any(np.linalg.norm(steps,axis=1)>42.0*adv): DIAG30["transition_reject_absolute_speed"]+=1; return None
    score=float(cur["local_score"])
    for i in range(6):
        sign=float(dir_sign[i]); sx=float(steps[i,0])
        if sign!=0.0:
            ss=sign*sx; progress=sign*float(P1[i,0]-initial_x[i])
            if progress < -reverse_cap or ss < -step_reverse_cap*adv: DIAG30["transition_reject_reverse"]+=1; return None
            score += (0.018*min(ss,24.0*adv)) if ss>=0 else (-0.18*min(-ss,step_reverse_cap*adv))
            if progress<0: score-=0.055*min(-progress,reverse_cap)
        if rel_prev is not None: score-=0.024*float(np.linalg.norm(rel_cur[i]-rel_prev[i]))
    score-=0.004*float(np.sum(np.linalg.norm(rel_cur,axis=1))); DIAG30["transition_accepts"]+=1; return score,steps
def _out(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v30.json")
def _annotate(p):
    if not p.exists(): return
    try:o=json.loads(p.read_text(encoding="utf-8"))
    except Exception:return
    o["tracker_version"]="v30"; o["method"]="v30 causal trajectory + shared robust four-of-six fleet-consensus affine-camera transition"; o["v30_changes"]={"proposal_reachability":"unchanged v25 causal predecessor prediction","camera_model":"one shared robust fleet affine transform selected from C(6,3) fits","camera_fit_selection":"minimize 4th-smallest six-boat residual then mean of four best residuals","relative_residual_cap_px_per_native_frame":24.0,"relative_acceleration_cap_px_per_native_frame":20.0,"absolute_screen_step_cap_px_per_native_frame":42.0,"immutable_ncc_threshold_changed":False,"reverse_motion_gate_changed":False,"fleet_geometry_gate_changed":False,"future_frame_feedback":False,"result_blind":True}; o["v30_diagnostic"]={k:int(v) for k,v in DIAG30.items()}
    for b in (o.get("boats") or {}).values():
        if "ses_v25" in b and "ses_v30" not in b:b["ses_v30"]=b["ses_v25"]
        elif "ses_v21" in b and "ses_v30" not in b:b["ses_v30"]=b["ses_v21"]
    p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
    v25._transition_v25=_transition; code=0
    try:v25.main()
    except SystemExit as e: code=int(e.code or 0) if isinstance(e.code,(int,type(None))) else 2
    finally:_annotate(_out(sys.argv))
    print(json.dumps({"v30_diagnostic":DIAG30},ensure_ascii=False)); raise SystemExit(code)
if __name__=="__main__":main()
# Regression trigger: unchanged four-video result-blind technical matrix.
