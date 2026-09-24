#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v8"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb"));rr=x["rows"]
    rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);month=code[:4]+"-"+code[4:6]
        if month not in DEV:continue
        if code[:8]>="20260901":raise RuntimeError("September entered")
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        s,t=int(p[1]),int(p[2])
        if s not in BOATS or t not in BOATS or s==t:continue
        p2,pc=v365.formal_post_five6(r)
        cand=[b for b in BOATS if b!=s]
        cond={b:ff(pc.get((s,b))) for b in cand}
        cr=sorted(cand,key=lambda b:cond[b],reverse=True)
        third_rank=cr.index(t)+1
        rows.append({
          "race_code":code,"month":month,"second":s,"third":t,
          "second_inner":int(s in (2,3)),"third_inner23":int(t in (2,3)),
          "third_inside_second":int(t<s),"third_outside_second":int(t>s),
          "third_adjacent":int(abs(t-s)==1),
          "cond_rank":third_rank,"cond_top1":int(third_rank==1),"cond_top2":int(third_rank<=2),
          "cond_top3":int(third_rank<=3),"cond_p":cond[t],
          "third_score":ff(r.get(f"score{t}")),"third_st":ff(r.get(f"st{t}")),
          "third_core":ff(r.get(f"core{t}")),"third_straight":ff(r.get(f"straight{t}")),
          "third_avg":ff(r.get(f"avg{t}"))
        })
    q=pd.DataFrame(rows);q.to_csv(OUT/"rows.csv",index=False)
    by_second={}
    for s,g in q.groupby("second"):
        counts={str(k):int(v) for k,v in g.third.value_counts().sort_index().items()}
        by_second[str(s)]={
          "R":int(len(g)),"third_counts":counts,
          "third_inner23":int(g.third_inner23.sum()),"third_inner23_rate":float(g.third_inner23.mean()),
          "third_inside_second":int(g.third_inside_second.sum()),"third_inside_second_rate":float(g.third_inside_second.mean()),
          "third_adjacent":int(g.third_adjacent.sum()),"third_adjacent_rate":float(g.third_adjacent.mean()),
          "cond_top1":int(g.cond_top1.sum()),"cond_top1_rate":float(g.cond_top1.mean()),
          "cond_top2":int(g.cond_top2.sum()),"cond_top2_rate":float(g.cond_top2.mean()),
          "cond_top3":int(g.cond_top3.sum()),"cond_top3_rate":float(g.cond_top3.mean()),
        }
    normal=q[q.second_inner.eq(1)];outer=q[q.second_inner.eq(0)]
    def sm(g):
        return {"R":int(len(g)),
                "third_inner23":int(g.third_inner23.sum()),"third_inner23_rate":float(g.third_inner23.mean()) if len(g) else None,
                "third_inside_second":int(g.third_inside_second.sum()),"third_inside_second_rate":float(g.third_inside_second.mean()) if len(g) else None,
                "third_adjacent":int(g.third_adjacent.sum()),"third_adjacent_rate":float(g.third_adjacent.mean()) if len(g) else None,
                "cond_top1":int(g.cond_top1.sum()),"cond_top1_rate":float(g.cond_top1.mean()) if len(g) else None,
                "cond_top2":int(g.cond_top2.sum()),"cond_top2_rate":float(g.cond_top2.mean()) if len(g) else None,
                "cond_top3":int(g.cond_top3.sum()),"cond_top3_rate":float(g.cond_top3.mean()) if len(g) else None}
    result={
      "population":"DEV head1 wins, third-place mechanism conditional on actual second",
      "R":int(len(q)),"by_second":by_second,
      "inner_second":sm(normal),"outer_second":sm(outer),
      "outer_second_third_counts":{str(k):int(v) for k,v in outer.third.value_counts().sort_index().items()},
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False,
      "note":"actual second is post-race mechanism conditioning, not a LIVE input."
    }
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_THIRD_BY_SECOND_V8",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
