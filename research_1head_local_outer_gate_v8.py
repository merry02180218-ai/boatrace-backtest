#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6); OUTER=(4,5,6)
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
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        actual2=int(p[1])
        p2,pc=v365.formal_post_five6(r)
        pv={b:ff(p2.get(b)) for b in BOATS}
        order=sorted(BOATS,key=lambda b:pv[b],reverse=True)
        cand=max(OUTER,key=lambda b:pv[b]); inner=cand-1
        z={"race_code":code,"month":m,"actual2":actual2,"cand":cand,"inner":inner,
           "baseline1":order[0],"baseline2":order[1],
           "baseline_hit":int(actual2 in order[:2]),
           "cand_is_actual":int(cand==actual2),
           "cand_already_top2":int(cand in order[:2]),
           "cand_p2":pv[cand],"inner_p2":pv.get(inner,np.nan),
           "base2_p2":pv[order[1]],"cand_vs_base2_ratio":pv[cand]/max(pv[order[1]],1e-12),
           "cand_vs_inner_ratio":pv[cand]/max(pv.get(inner,1e-12),1e-12)}
        cnt=0; cnt123=0
        for metric in ("score","core","ex","st","straight","avg"):
            cv=ff(r.get(f"{metric}{cand}"));iv=ff(r.get(f"{metric}{inner}"))
            e=cv-iv if np.isfinite(cv) and np.isfinite(iv) else np.nan
            z[f"{metric}_edge"]=e;z[f"{metric}_beat"]=int(np.isfinite(e) and e>0)
            cnt+=z[f"{metric}_beat"]
            if metric in ("core","straight","avg"):cnt123+=z[f"{metric}_beat"]
        z["all6_beat_count"]=cnt;z["foot3_beat_count"]=cnt123
        z["triple_foot"]=int(cnt123==3)
        z["straight_avg"]=int(z["straight_beat"] and z["avg_beat"])
        z["core_straight"]=int(z["core_beat"] and z["straight_beat"])
        z["core_avg"]=int(z["core_beat"] and z["avg_beat"])
        rows.append(z)
    q=pd.DataFrame(rows)
    if len(q)!=163:raise RuntimeError(f"sentinel {len(q)}")
    q.to_csv(OUT/"dev_rows.csv",index=False)
    rules=[]
    # deterministic interpretable gates; apply only when best outer is absent from baseline top2.
    specs=[]
    for n in (2,3,4,5):specs.append((f"ALL6_GE{n}",lambda d,n=n:d.all6_beat_count>=n))
    for n in (2,3):specs.append((f"FOOT3_GE{n}",lambda d,n=n:d.foot3_beat_count>=n))
    specs += [
      ("STRAIGHT_AVG",lambda d:d.straight_avg.eq(1)),
      ("CORE_STRAIGHT",lambda d:d.core_straight.eq(1)),
      ("CORE_AVG",lambda d:d.core_avg.eq(1)),
      ("TRIPLE_FOOT",lambda d:d.triple_foot.eq(1)),
    ]
    # Add modest P2-ratio floors to avoid elevating a tiny-probability outer candidate.
    for base_name,base_fn in list(specs):
        for ratio in (.35,.50,.65,.80):
            specs.append((f"{base_name}_R{ratio:.2f}",lambda d,fn=base_fn,ratio=ratio:fn(d)&(d.cand_vs_base2_ratio>=ratio)))
    seen=set()
    for name,fn in specs:
        if name in seen:continue
        seen.add(name)
        mask=fn(q) & q.cand_already_top2.eq(0)
        new_hits=[];resc=dam=0
        for i,r in q.iterrows():
            old=int(r.baseline_hit)
            if bool(mask.loc[i]):
                new_pair=(int(r.baseline1),int(r.cand))
                nh=int(int(r.actual2) in new_pair)
            else:nh=old
            new_hits.append(nh);resc+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
        fired=int(mask.sum());outer_true=int((mask&q.cand_is_actual.eq(1)).sum())
        precision=outer_true/fired if fired else None
        month={}
        for m,g in q.assign(fire=mask,new_hit=new_hits).groupby("month"):
            month[m]={"R":int(len(g)),"fired":int(g.fire.sum()),"rescued":int(((g.baseline_hit==0)&(g.new_hit==1)).sum()),
                      "damaged":int(((g.baseline_hit==1)&(g.new_hit==0)).sum()),"new_hits":int(g.new_hit.sum())}
        rules.append({"rule":name,"fired_R":fired,"actual_outer_candidate_R":outer_true,"precision":precision,
                      "rescued":resc,"damaged":dam,"net":resc-dam,"hits":int(sum(new_hits)),
                      "rate":float(np.mean(new_hits)),"monthly":month})
    rules.sort(key=lambda x:(x["hits"],x["net"],x["precision"] or -1,-x["fired_R"]),reverse=True)

    # Descriptive frequencies for the best-outer candidate, split by actual outcome.
    desc={}
    for label,mask in {
        "actual_best_outer_second":q.cand_is_actual.eq(1),
        "other_second":q.cand_is_actual.eq(0),
        "p2_miss_best_outer_actual":q.cand_is_actual.eq(1)&q.baseline_hit.eq(0),
    }.items():
        g=q[mask]
        desc[label]={"R":int(len(g))}
        for c in ("all6_beat_count","foot3_beat_count","straight_beat","avg_beat","core_beat","ex_beat","score_beat","st_beat"):
            if len(g):desc[label][c+"_mean"]=float(pd.to_numeric(g[c]).mean())
    result={"population":"DEV head1 wins; best-outer-P2 local edge gates",
            "baseline":{"R":163,"hits":int(q.baseline_hit.sum()),"rate":float(q.baseline_hit.mean())},
            "descriptive":desc,"top_rules":rules[:25],
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    pd.DataFrame([{k:v for k,v in z.items() if k!="monthly"} for z in rules]).to_csv(OUT/"rule_scan.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_LOCAL_OUTER_GATE_V8",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
