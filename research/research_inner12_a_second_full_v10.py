#!/usr/bin/env python3
"""INNER12 V10: full A-only SECOND rerank with raw causal candidate features.
B and conditional THIRD stay frozen from V8. Sep1-24 diagnostic only.
"""
import json, math
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import research_inner12_ticket_roi_v6 as v6

BASE=Path("/tmp/v8x"); OUT=Path("/tmp/inner12_a_second_full_v10"); OUT.mkdir(parents=True,exist_ok=True)
detail=pd.read_csv(BASE/"sep_v8_detail.csv",dtype={"race_code":str})
cand=pd.read_csv(BASE/"sep_candidate_features.csv",dtype={"race_code":str})
train=pd.read_csv(BASE/"train_second_rows.csv")
FEATURES=["boat","head","pos_inside_head","pos_outside_head","pos_distance_head","motor","waku_wr","waku_st","waku_sr","nst",
"ex","st","orig_turn","orig_straight","orig_avg","opponent_core","pl_all_win","pl_all_p2","pl_frame_win","pl_frame_p2","pl_recent_p2",
"rel_core_head","rel_motor_head","rel_waku_st_head","rel_pl_p2_head"]
# 3HEAD route-inspired interactions, all pre-race.
for df in (train,cand):
    df["outer"]=pd.to_numeric(df["boat"],errors="coerce")>pd.to_numeric(df["head"],errors="coerce")
    df["inner"]=pd.to_numeric(df["boat"],errors="coerce")<pd.to_numeric(df["head"],errors="coerce")
    df["outer_ph"]=df.outer.astype(float)*pd.to_numeric(df.pl_frame_p2,errors="coerce")
    df["outer_motor"]=df.outer.astype(float)*pd.to_numeric(df.motor,errors="coerce")
    df["outer_core"]=df.outer.astype(float)*pd.to_numeric(df.opponent_core,errors="coerce")
    df["inner_ph"]=df.inner.astype(float)*pd.to_numeric(df.pl_frame_p2,errors="coerce")
    df["route32"]=((pd.to_numeric(df["head"],errors="coerce")==3)&(pd.to_numeric(df["boat"],errors="coerce")==2)).astype(float)*pd.to_numeric(df.pl_frame_p2,errors="coerce")
    df["route31"]=((pd.to_numeric(df.head)==3)&(pd.to_numeric(df["boat"],errors="coerce")==1)).astype(float)*pd.to_numeric(df.pl_frame_win,errors="coerce")
FEATURES += ["outer_ph","outer_motor","outer_core","inner_ph","route32","route31"]

def model(C):
 return Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(C=C,max_iter=3000,class_weight="balanced"))])
def softmax(x):
 x=np.asarray(x,float); e=np.exp(x-x.max()); return e/e.sum()
def reorder(old,p2,head):
 pairs=[tuple(map(int,x.split("-")[1:])) for x in old if x.startswith(f"{head}-")]
 bys={}
 for s,t in pairs:bys.setdefault(s,[]).append(t)
 secs=sorted(p2,key=lambda b:(-p2[b],b)); out=[]
 # preserve V8 six-ticket breadth but prioritize top2 SECOND.
 for s in secs[:2]:
  for t in bys.get(s,[])[:2]:
   k=f"{head}-{s}-{t}"
   if k not in out:out.append(k)
 for s in secs:
  for t in bys.get(s,[]):
   k=f"{head}-{s}-{t}"
   if k not in out:out.append(k)
 for k in old:
  if k.startswith(f"{head}-") and k not in out:out.append(k)
 return out[:6]

rows=[]; summaries={}
for C in [.05,.1,.2,.35,.5]:
 m=model(C); m.fit(train[FEATURES],train.y.astype(int))
 for _,r in detail.iterrows():
  old=str(r.tickets).split("|")
  if r.action!="A_DUAL_3_4":
   new=old[:]
  else:
   new=[]
   for head in [3,4]:
    q=cand[(cand.race_code.eq(str(r.race_code).zfill(12)))&(cand["head"].eq(head))].copy()
    sc=m.decision_function(q[FEATURES]); pp=softmax(sc)
    p2={int(b):float(p) for b,p in zip(q.boat,pp)}
    new.extend(reorder([x for x in old if x.startswith(f"{head}-")],p2,head))
  rows.append({"C":C,"race_code":r.race_code,"action":r.action,"actual":r.actual,"old_hit":int(r.ticket_hit),
               "new_hit":int(str(r.actual) in new),"tickets":"|".join(new),"points":len(new)})
z=pd.DataFrame(rows); z.to_csv(OUT/"compare.csv",index=False)
for C,g in z.groupby("C"):
 A=g[g.action.eq("A_DUAL_3_4")]; B=g[g.action.eq("B_3HEAD")]
 summaries[str(C)]={"total_hits":int(g.new_hit.sum()),"A_hits":int(A.new_hit.sum()),"A_old":int(A.old_hit.sum()),
                    "B_hits":int(B.new_hit.sum()),"B_unchanged":bool((B.new_hit==B.old_hit).all()),
                    "points_ok":bool(((A.points==12).all() and (B.points==6).all()))}
best=max(summaries,key=lambda k:(summaries[k]["A_hits"],summaries[k]["total_hits"],-float(k)))
meta={"model_id":"INNER12_A_SECOND_FULL_V10","status":"RESEARCH_SHADOW","sep_nonpristine":True,"production_changed":False,
"head_gate_changed":False,"B_changed":False,"third_model_changed":False,"features":FEATURES,"summary":summaries,"best_C":best}
(OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
print("INNER12_A_SECOND_FULL_V10_OK"); print("SUMMARY",json.dumps(summaries,ensure_ascii=False)); print("BEST_C",best); print("PRODUCTION_UNCHANGED")
