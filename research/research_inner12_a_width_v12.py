#!/usr/bin/env python3
"""V12 ticket-width diagnostic. Frozen V8 scores; no refit and no Sep selection.
Compare A-only 12/16/20/24 total tickets while B remains V8 6.
"""
import json, math
from pathlib import Path
import pandas as pd, numpy as np
import research_inner12_ticket_roi_v6 as v6
B=Path("/tmp/v8x"); O=Path("/tmp/inner12_a_width_v12");O.mkdir(parents=True,exist_ok=True)
d=pd.read_csv(B/"sep_v8_detail.csv",dtype={"race_code":str}); p=pd.read_csv(B/"sep_pair_scores.csv",dtype={"race_code":str})
WIDTHS=[12,16,20,24]
def order(q,h):
 q=q.copy()
 q["score"]=(pd.to_numeric(q.v8_p2).clip(lower=1e-12)**.70)*(pd.to_numeric(q.v8_pc).clip(lower=1e-12)**.30)
 q=q.sort_values(["score","second","third"],ascending=[False,True,True])
 a=[(int(x.second),int(x.third)) for x in q.itertuples()]
 f=a[0]; same=[x for x in a if x[0]==f[0] and x!=f]; other=[x for x in a if x[0]!=f[0]]
 out=[]
 for x in [f]+same[:1]+other[:1]+a:
  if x not in out:out.append(x)
 return out
rows=[]
for _,r in d.iterrows():
 code=str(r.race_code).zfill(12); actual=str(r.actual)
 for w in WIDTHS:
  if r.action!="A_DUAL_3_4":
   ts=str(r.tickets).split("|")
  else:
   per=w//2;ts=[]
   for h in (3,4):
    q=p[(p.race_code.eq(code))&(pd.to_numeric(p["head"])==h)]
    ts += [f"{h}-{s}-{t}" for s,t in order(q,h)[:per]]
  rows.append({"width":w,"race_code":code,"action":r.action,"actual":actual,"hit":int(actual in ts),"points":len(ts),"tickets":"|".join(ts)})
z=pd.DataFrame(rows);z.to_csv(O/"compare.csv",index=False)
summary={}
for w,g in z.groupby("width"):
 A=g[g.action.eq("A_DUAL_3_4")];B3=g[g.action.eq("B_3HEAD")]
 summary[str(w)]={"R":len(g),"hits":int(g.hit.sum()),"hit_rate":float(g.hit.mean()),"A_hits":int(A.hit.sum()),"A_rate":float(A.hit.mean()),"B_hits":int(B3.hit.sum()),"A_points":sorted(A.points.unique().tolist()),"B_points":sorted(B3.points.unique().tolist())}
meta={"model_id":"INNER12_A_WIDTH_V12","status":"RESEARCH_DIAGNOSTIC","source":"frozen V8 probabilities","sep_used_for_fit":False,"sep_used_for_selection":False,"production_changed":False,"summary":summary}
(O/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
print("INNER12_A_WIDTH_V12_OK");print(json.dumps(meta,ensure_ascii=False))
