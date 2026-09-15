#!/usr/bin/env python3
"""Result-blind v35: dual causal proposal centers + v34 transition gates.

v34 keeps hard transition/identity/geometry gates but the inherited v25 merge can
starve a predecessor because proposals are admitted only around one per-center
step hint. v35 does not widen the 24 px/native-frame proposal radius. Instead it
uses two causal centers when history exists: (1) the existing per-center hint and
(2) a robust fleet-wide median of already accepted step hints. A proposal is
admitted only if it is inside the unchanged radius of at least one causal center.
This expands hypothesis diversity without weakening NCC, reverse, geometry or
transition acceptance thresholds. No future frame or race result is used.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import track_exhibition_boats_v25 as v25
import track_exhibition_boats_v34 as v34

DIAG35={"merge_calls":0,"dual_center_calls":0,"shared_only_admits":0,"proposal_admits":0}


def _fleet_hint():
    vals=[]
    for seq in v25._STEP_HINTS.values():
        if seq:
            vals.append(np.asarray(seq[-1],np.float32))
    if not vals:
        return None
    return np.median(np.asarray(vals,np.float32),axis=0)


def _merge_v35(global_opts,local_opts,bank_opts,prev_center,advance,keep):
    DIAG35["merge_calls"]+=1
    adv=max(1,int(advance)); radius=24.0*adv
    prev=np.asarray(prev_center,np.float32)
    own=v25._step_hint(prev); shared=_fleet_hint()
    centers=[]
    if own is not None: centers.append(("own",prev+own))
    if shared is not None:
        centers.append(("shared",prev+shared)); DIAG35["dual_center_calls"]+=int(own is not None)
    if not centers: centers=[("static",prev)]
    raw=[(c,s,s,"immutable") for c,s in list(local_opts)+list(global_opts)] + list(bank_opts)
    raw.sort(key=lambda z:(0.72*float(z[1])+0.28*float(z[2])),reverse=True)
    pool=[]
    for c,imm,aux,source in raw:
        c=np.asarray(c,np.float32)
        hits=[name for name,pred in centers if float(np.linalg.norm(c-pred))<=radius]
        if not hits: continue
        if "shared" in hits and "own" not in hits and own is not None: DIAG35["shared_only_admits"]+=1
        if any(np.linalg.norm(c-q[0])<8.0 for q in pool): continue
        pool.append((c,float(imm),float(aux),source)); DIAG35["proposal_admits"]+=1
        if len(pool)>=max(1,int(keep)): break
    return pool


def _out_path(argv):
    if "--out" in argv:
        i=argv.index("--out")
        if i+1<len(argv): return Path(argv[i+1])
    return Path("exhibition_tracking_v35.json")


def main():
    old_merge=v25._merge_v25
    old_tr=v25._transition_v25
    v25._merge_v25=_merge_v35
    v25._transition_v25=v34._transition_v34
    code=0
    try:
        try: v25.main()
        except SystemExit as exc: code=int(exc.code or 0) if isinstance(exc.code,(int,type(None))) else 2
    finally:
        v25._merge_v25=old_merge; v25._transition_v25=old_tr
    p=_out_path(sys.argv)
    if p.exists():
        try:
            j=json.loads(p.read_text(encoding="utf-8")); j["tracker_version"]="v35_dual_causal_proposal_centers"; j["diagnostics_v35"]={k:int(v) for k,v in DIAG35.items()}; j["diagnostics_v34"]={k:int(v) for k,v in v34.DIAG34.items()}; p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        except Exception as e: print(f"v35 diagnostics write warning: {e}",file=sys.stderr)
    print(json.dumps({"diagnostics_v35":DIAG35,"diagnostics_v34":v34.DIAG34},ensure_ascii=False))
    raise SystemExit(code)

if __name__=="__main__": main()
