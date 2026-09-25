#!/usr/bin/env python3
"""V11 A-only SECOND route model: INNER vs OUTER (4/5/6), trained Jun-Aug only.
V4 head gate, B tickets and frozen V8 conditional THIRD are unchanged.
Sep1-24 is diagnostic only; no Sep label selects parameters.
"""
import json, math
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
BASE=Path("/tmp/v8x"); OUT=Path("/tmp/inner12_a_second_route_v11"); OUT.mkdir(parents=True,exist_ok=True)
train=pd.read_csv(BASE/"train_second_rows.csv"); cand=pd.read_csv(BASE/"sep_candidate_features.csv",dtype={"race_code":str})
pairs=pd.read_csv(BASE/"sep_pair_scores.csv",dtype={"race_code":str}); det=pd.read_csv(BASE/"sep_v8_detail.csv",dtype={"race_code":str})
F=["pl_frame_p2","pl_recent_p2","pl_all_p2","motor","opponent_core","st","orig_straight","waku_wr","waku_st"]
def num(s): return pd.to_numeric(s,errors="coerce")
def group_features(g):
 h=int(num(g["head"]).iloc[0]); inn=g[num(g["boat"])<h]; out=g[num(g["boat"])>h]
 def mx(z,k): return float(num(z[k]).max()) if len(z) else np.nan
 def mn(z,k): return float(num(z[k]).min()) if len(z) else np.nan
 r={"head":h,"n_outer":len(out)}
 for k in F:
  # ST/waku_st lower is faster; all others higher is stronger.
  if k in ("st","waku_st"):
   r["outer_"+k]=mn(out,k); r["inner_"+k]=mn(inn,k); r["gap_"+k]=r["inner_"+k]-r["outer_"+k]
  else:
   r["outer_"+k]=mx(out,k); r["inner_"+k]=mx(inn,k); r["gap_"+k]=r["outer_"+k]-r["inner_"+k]
 return r
# train rows are emitted in five-candidate race blocks.
tr=[]
for i in range(0,len(train),5):
 g=train.iloc[i:i+5].copy()
 if len(g)!=5 or int(num(g.y).sum())!=1: continue
 z=group_features(g); winner=int(num(g.loc[num(g.y)==1,"boat"]).iloc[0]); h=int(z["head"])
 z["y_outer"]=int(winner>h); tr.append(z)
tr=pd.DataFrame(tr)
RF=[c for c in tr.columns if c!="y_outer"]
route=Pipeline([("imp",SimpleImputer(strategy="median")),("sc",StandardScaler()),("lr",LogisticRegression(C=.25,max_iter=3000,class_weight="balanced"))])
route.fit(tr[RF],tr.y_outer)
rows=[]
for _,r in det.iterrows():
 old=str(r.tickets).split("|")
 if r.action!="A_DUAL_3_4":
  new=old[:]; probs={}
 else:
  new=[]; probs={}
  for h in (3,4):
   q=cand[(cand.race_code.eq(str(r.race_code).zfill(12)))&(num(cand["head"])==h)].copy()
   gf=pd.DataFrame([group_features(q)])
   po=float(route.predict_proba(gf[RF])[0,1]); probs[str(h)]=po
   pq=pairs[(pairs.race_code.eq(str(r.race_code).zfill(12)))&(num(pairs["head"])==h)].copy()
   # Full candidate universe. Route probability reweights SECOND side, frozen V8 p2 and conditional THIRD.
   pq["sidew"]=np.where(num(pq["second"])>h,po,1-po)
   pq["score"]=(num(pq.v8_p2).clip(lower=1e-12)**.70)*(num(pq.v8_pc).clip(lower=1e-12)**.30)*pq.sidew.clip(lower=.05)
   # guarantee breadth: best pair + second pair same SECOND + best different SECOND, then score order.
   pq=pq.sort_values(["score","second","third"],ascending=[False,True,True])
   order=list(zip(num(pq.second).astype(int),num(pq.third).astype(int)))
   first=order[0]; same=[x for x in order if x[0]==first[0] and x!=first]; other=[x for x in order if x[0]!=first[0]]
   seq=[first]+same[:1]+other[:1]+order; seen=[]
   for x in seq:
    if x not in seen: seen.append(x)
   new += [f"{h}-{s}-{t}" for s,t in seen[:6]]
 actual=str(r.actual); rows.append({"race_code":r.race_code,"action":r.action,"actual":actual,"old_hit":int(r.ticket_hit),"new_hit":int(actual in new),"tickets":"|".join(new),"points":len(new),"route_outer_prob":json.dumps(probs)})
z=pd.DataFrame(rows); z.to_csv(OUT/"compare.csv",index=False)
A=z[z.action.eq("A_DUAL_3_4")];B=z[z.action.eq("B_3HEAD")]
meta={"model_id":"INNER12_A_SECOND_ROUTE_V11","status":"RESEARCH_SHADOW","train_route_races":len(tr),"sep_used_for_fit":False,"sep_used_for_threshold":False,"fixed_C":.25,"fixed_route_threshold":.5,"head_gate_changed":False,"B_changed":False,"third_model_changed":False,"production_changed":False,
"summary":{"total_hits":int(z.new_hit.sum()),"old_total":int(z.old_hit.sum()),"A_hits":int(A.new_hit.sum()),"A_old":int(A.old_hit.sum()),"B_hits":int(B.new_hit.sum()),"B_unchanged":bool((B.new_hit==B.old_hit).all()),"points_ok":bool((A.points.eq(12).all() and B.points.eq(6).all()))}}
(OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
print("INNER12_A_SECOND_ROUTE_V11_OK");print(json.dumps(meta,ensure_ascii=False))
