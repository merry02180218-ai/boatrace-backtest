#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v4"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan

def rank(vals):
    s=pd.Series(vals,dtype=float)
    return s.rank(method="average",ascending=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb")); rr=x["rows"]
    if len(rr["H078_M375"])!=236: raise RuntimeError("frozen universe drift")
    rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12); month=code[:4]+"-"+code[4:6]
        if month not in DEV: continue
        if code[:8]>="20260901": raise RuntimeError("September entered")
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1": continue
        try: sec=int(p[1])
        except: continue
        if sec not in BOATS: continue
        p2,pc=v365.formal_post_five6(r)
        p2rank=rank({b:ff(p2.get(b)) for b in BOATS})
        if ff(p2rank.get(sec))<=2: continue  # only MODEL_P2 misses
        vals={
          "score":{b:ff(r.get(f"score{b}")) for b in BOATS},
          "core":{b:ff(r.get(f"core{b}")) for b in BOATS},
          "ex":{b:ff(r.get(f"ex{b}")) for b in BOATS},
          "st":{b:ff(r.get(f"st{b}")) for b in BOATS},
          "straight":{b:ff(r.get(f"straight{b}")) for b in BOATS},
          "avg":{b:ff(r.get(f"avg{b}")) for b in BOATS},
        }
        rec={"race_code":code,"month":month,"actual_second":sec,"outer_second":int(sec>=4),
             "p2_rank":ff(p2rank.get(sec)),"opp_mass":ff(r.get("opp_mass")),
             "attack_ready":int(bool(r.get("attack_ready",False))),"attack_core":ff(r.get("attack_core"))}
        top2_flags=[]
        for name,d in vals.items():
            rk=rank(d); rrk=ff(rk.get(sec))
            rec[f"{name}_rank"]=rrk
            rec[f"{name}_top2"]=int(np.isfinite(rrk) and rrk<=2)
            top2_flags.append(rec[f"{name}_top2"])
        rec["any_feature_top2"]=int(any(top2_flags))
        rec["feature_top2_count"]=int(sum(top2_flags))
        if sec>=3:
            for name,d in vals.items():
                av,bv=ff(d.get(sec)),ff(d.get(sec-1))
                rec[f"{name}_beats_inner"]=int(np.isfinite(av) and np.isfinite(bv) and av>bv)
        else:
            for name in vals: rec[f"{name}_beats_inner"]=0
        rows.append(rec)
    q=pd.DataFrame(rows)
    q.to_csv(OUT/"p2_miss_rows.csv",index=False)
    if q.empty: raise RuntimeError("no P2 miss rows")
    features=["score","core","ex","st","straight","avg"]
    feat=[]
    for f in features:
        feat.append({"feature":f,"R":int(q[f"{f}_rank"].notna().sum()),
                     "top1":int((q[f"{f}_rank"]==1).sum()),
                     "top2":int(q[f"{f}_top2"].sum()),
                     "top2_rate":float(q[f"{f}_top2"].mean()),
                     "beats_inner":int(q[f"{f}_beats_inner"].sum()),
                     "beats_inner_rate":float(q[f"{f}_beats_inner"].mean())})
    lanes={str(k):int(v) for k,v in q.actual_second.value_counts().sort_index().items()}
    month=[]
    for m,g in q.groupby("month"):
        month.append({"month":m,"R":int(len(g)),"outer_R":int(g.outer_second.sum()),
                      "any_feature_top2":int(g.any_feature_top2.sum()),
                      "two_plus_features_top2":int((g.feature_top2_count>=2).sum())})
    outer=q[q.outer_second.eq(1)]
    inner=q[q.outer_second.eq(0)]
    summary={
      "population":"DEV head1 wins where actual SECOND is outside MODEL_P2 top2",
      "R":int(len(q)),"lane_counts":lanes,
      "outer_R":int(q.outer_second.sum()),"outer_rate":float(q.outer_second.mean()),
      "any_feature_top2_R":int(q.any_feature_top2.sum()),
      "any_feature_top2_rate":float(q.any_feature_top2.mean()),
      "two_plus_features_top2_R":int((q.feature_top2_count>=2).sum()),
      "two_plus_features_top2_rate":float((q.feature_top2_count>=2).mean()),
      "feature_summary":feat,"monthly":month,
      "outer_only":{"R":int(len(outer)),"any_feature_top2":int(outer.any_feature_top2.sum()),
                    "two_plus_features_top2":int((outer.feature_top2_count>=2).sum())},
      "inner_only":{"R":int(len(inner)),"any_feature_top2":int(inner.any_feature_top2.sum())},
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False
    }
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_P2_MISS_V4",json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":main()
