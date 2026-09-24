#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
UNIVERSES=("H078_M375","H0775_M375","H0775_M350","PROD276","LIVE165")
BOATS=(2,3,4,5,6)

def rank_pc(pc,s,actual):
    cand=[t for t in BOATS if t!=s]
    cand=sorted(cand,key=lambda t:(-float(pc[(s,t)]),t))
    return cand.index(actual)+1,cand

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb"))
    out={}
    for name in UNIVERSES:
        rows=x["rows"].get(name,[])
        rec=[]
        for r in rows:
            code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
            if m not in DEV:continue
            parts=str(r.get("actual_combo","")).split("-")
            if len(parts)!=3 or parts[0]!="1":continue
            try:s=int(parts[1]);t=int(parts[2])
            except:continue
            if s!=5:continue
            p2,pc=v365.formal_post_five6(r)
            rk,order=rank_pc(pc,5,t)
            rec.append({"race_code":code,"month":m,"third":t,"pc_rank":rk,
                        "pc1":order[0],"pc2":order[1],"pc3":order[2],
                        "top1":int(rk==1),"top2":int(rk<=2),"top3":int(rk<=3),
                        "third_inner23":int(t in (2,3)),"third4":int(t==4),"third6":int(t==6)})
        q=pd.DataFrame(rec)
        if q.empty:
            out[name]={"R":0};continue
        monthly={str(k):{"R":int(len(g)),"top1":int(g.top1.sum()),"top2":int(g.top2.sum())} for k,g in q.groupby("month")}
        out[name]={
          "R":int(len(q)),
          "third_counts":{str(k):int(v) for k,v in q.third.value_counts().sort_index().items()},
          "pc_top1":int(q.top1.sum()),"pc_top1_rate":float(q.top1.mean()),
          "pc_top2":int(q.top2.sum()),"pc_top2_rate":float(q.top2.mean()),
          "pc_top3":int(q.top3.sum()),"pc_top3_rate":float(q.top3.mean()),
          "inner23_rate":float(q.third_inner23.mean()),"third4_rate":float(q.third4.mean()),"third6_rate":float(q.third6.mean()),
          "monthly":monthly
        }
        q.to_csv(f"/tmp/1head-five-third-{name}.csv",index=False)
    result={"population":"DEV boat1 wins with boat5 second; conditional-third robustness across universes",
            "universes":out,"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    print("DEV_1HEAD_FIVE_THIRD_V16",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
