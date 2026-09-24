#!/usr/bin/env python3
"""INNER12 A SECOND reranker V9.

Research-only comparison against frozen V8. Head gate, B branch and THIRD are untouched.
For A rows only, add a 3HEAD-inspired route-aware prior to V8 SECOND probabilities:
- inner route strength: boat1 frame-win / boat2 frame-p2 PLAYERHistory;
- outer route strength: boats4-6 PLAYERHistory recent/frame p2 + motor + opponentCore;
- apply only as a soft rerank, then use the unchanged V8 conditional THIRD and HYBRID pair construction.

Training remains Jun-Aug only. Sep1-24 is diagnostic/non-pristine; production unchanged.
"""
from __future__ import annotations
import json, math, runpy
from pathlib import Path
import numpy as np, pandas as pd

BASE=Path("/tmp/inner12_onehead_opponent_v8")
OUT=Path("/tmp/inner12_a_second_reranker_v9"); OUT.mkdir(parents=True,exist_ok=True)

# V8 is executed first by workflow; reuse its exact frozen train rows and September detail.
v8=pd.read_csv(BASE/"sep_v8_detail.csv",dtype={"race_code":str})
s2=pd.read_csv(BASE/"train_second_rows.csv")
# This experiment is deliberately conservative: learn only generic lane-role priors from V8 causal train rows.
# Candidate rows contain one positive per head-race. Fit smoothed per-boat SECOND prior and PH/core effects.
eps=1e-9
boat_prior=s2.groupby("boat").y.agg(["sum","count"])
boat_prior["p"]=(boat_prior["sum"]+2)/(boat_prior["count"]+10)
global_p=float((s2.y.sum()+2)/(len(s2)+10))
lane_log={int(b):math.log(float(r.p)/global_p) for b,r in boat_prior.iterrows()}

# Estimate monotone train-only feature effects via positive-vs-negative standardized mean differences.
features=["pl_frame_p2","pl_recent_p2","pl_all_p2","motor","opponent_core","pos_outside_head"]
effects={}
for c in features:
    z=pd.to_numeric(s2[c],errors="coerce")
    sd=float(z.std()) or 1.0
    effects[c]=float((z[s2.y.eq(1)].mean()-z[s2.y.eq(0)].mean())/sd)

# Candidate reranking is reconstructed from V8 diag p2. We intentionally do not touch THIRD.
# Since V8 detail does not persist raw Sep candidate features, V9 is a lane-role route ablation first:
# inner boats receive learned lane priors; outer boats receive learned outer lane priors.
# This directly tests whether 3HEAD-style route/outer emphasis fixes SECOND misses without changing point count.
def rerank_p2(p2,head,strength):
    q={}
    for b,p in p2.items():
        boost=lane_log.get(int(b),0.0)
        # route-aware: when head is 3/4, preserve inner/outer distinction rather than global score only.
        if int(b)>int(head): boost*=1.25
        elif int(b)<int(head): boost*=0.85
        q[int(b)]=max(float(p),eps)*math.exp(strength*boost)
    den=sum(q.values()); return {b:v/den for b,v in q.items()}

def hybrid_from_existing_tickets(tickets,newp,head):
    # Preserve V8 THIRD ordering within each SECOND from its existing pair order.
    pairs=[tuple(map(int,t.split("-")[1:])) for t in tickets if t.startswith(f"{head}-")]
    bys={}
    for s,t in pairs: bys.setdefault(s,[]).append(t)
    seconds=sorted(newp,key=lambda b:(-newp[b],b))
    out=[]
    # same HYBRID intent: best second twice, then another second, then fill.
    if seconds:
        s=seconds[0]
        for t in bys.get(s,[])[:2]: out.append(f"{head}-{s}-{t}")
    if len(seconds)>1:
        s=seconds[1]
        if bys.get(s): out.append(f"{head}-{s}-{bys[s][0]}")
    for s in seconds:
        for t in bys.get(s,[]):
            k=f"{head}-{s}-{t}"
            if k not in out: out.append(k)
    # Existing V8 top6 may not contain every second; fill from original unchanged ordering.
    for k in tickets:
        if k.startswith(f"{head}-") and k not in out: out.append(k)
    return out[:6]

rows=[]
for strength in [0.25,0.5,0.75,1.0,1.25]:
  for _,r in v8.iterrows():
    diag=json.loads(r.diag); orig=str(r.tickets).split("|"); new=[]
    if r.action=="A_DUAL_3_4":
      for hs in ["3","4"]:
        d=diag[hs]; p2={int(k):float(v) for k,v in d["p2"].items()}
        rp=rerank_p2(p2,int(hs),strength)
        oldh=[x for x in orig if x.startswith(hs+"-")]
        new.extend(hybrid_from_existing_tickets(oldh,rp,int(hs)))
    else:
      new=orig[:]  # B frozen exactly.
    act=str(r.actual); hit=int(act in new)
    rows.append({"strength":strength,"race_code":r.race_code,"action":r.action,"actual":act,
                 "old_hit":int(r.ticket_hit),"new_hit":hit,"tickets":"|".join(new),
                 "point_count":len(new)})
z=pd.DataFrame(rows); z.to_csv(OUT/"v9_compare.csv",index=False)

summary={}
for st,g in z.groupby("strength"):
    A=g[g.action.eq("A_DUAL_3_4")]; B=g[g.action.ne("A_DUAL_3_4")]
    summary[str(st)]={"R":len(g),"hits":int(g.new_hit.sum()),"old_hits":int(g.old_hit.sum()),
      "A_R":len(A),"A_hits":int(A.new_hit.sum()),"A_old_hits":int(A.old_hit.sum()),
      "B_unchanged":bool((B.new_hit==B.old_hit).all()),"points_ok":bool((g.point_count==np.where(g.action.eq("A_DUAL_3_4"),12,6)).all())}
best=max(summary,key=lambda k:(summary[k]["A_hits"],-abs(float(k)-0.5)))
meta={"model_id":"INNER12_A_SECOND_RERANKER_V9","status":"RESEARCH_SHADOW",
 "source":"V8 + 3HEAD-inspired inner/outer SECOND route prior",
 "train_period":"Jun-Aug only via V8 train_second_rows","sep_nonpristine":True,
 "production_changed":False,"third_changed":False,"B_changed":False,
 "lane_prior":lane_log,"feature_effect_diagnostics":effects,"summary":summary,"best_strength_by_A_hits":best,
 "warning":"V9 is an ablation using train-only lane-role priors because V8 did not persist raw Sep candidate features. If positive, next version should persist raw Sep features and test full PLAYERHistory/motor route rerank."}
(OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
print("INNER12_A_SECOND_RERANKER_V9_OK")
print("SUMMARY",json.dumps(summary,ensure_ascii=False))
print("BEST",best)
print("B_UNCHANGED_ALL",all(v["B_unchanged"] for v in summary.values()))
print("PRODUCTION_UNCHANGED")
