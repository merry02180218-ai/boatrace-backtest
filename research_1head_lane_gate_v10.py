#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v10"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x);return v if np.isfinite(v) else np.nan
    except:return np.nan

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb"));rr=x["rows"];rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p=str(r.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        actual2=int(p[1]);p2,pc=v365.formal_post_five6(r)
        pv={b:ff(p2.get(b)) for b in BOATS};order=sorted(BOATS,key=lambda b:pv[b],reverse=True)
        z={"race_code":code,"month":m,"actual2":actual2,"base1":order[0],"base2":order[1],
           "baseline_hit":int(actual2 in order[:2])}
        for cand,inner in ((4,3),(5,4)):
            z[f"c{cand}_already"]=int(cand in order[:2])
            z[f"c{cand}_ratio2"]=pv[cand]/max(pv[order[1]],1e-12)
            cnt=0
            for met in ("score","core","ex","st","straight","avg"):
                cv=ff(r.get(f"{met}{cand}"));iv=ff(r.get(f"{met}{inner}"))
                e=cv-iv if np.isfinite(cv) and np.isfinite(iv) else np.nan
                z[f"c{cand}_{met}_edge"]=e;z[f"c{cand}_{met}_beat"]=int(np.isfinite(e) and e>0)
                if met in ("core","straight","avg"):cnt+=z[f"c{cand}_{met}_beat"]
            z[f"c{cand}_foot3"]=cnt
        rows.append(z)
    q=pd.DataFrame(rows)
    if len(q)!=163:raise RuntimeError(f"sentinel {len(q)}")
    q.to_csv(OUT/"dev_rows.csv",index=False)

    specs=[]
    for cand in (4,5):
        for n in (2,3):
            for ratio in (.25,.35,.50,.65,.80):
                specs.append((cand,f"C{cand}_FOOT{n}_R{ratio:.2f}",
                              lambda d,c=cand,n=n,ratio=ratio:(d[f"c{c}_foot3"]>=n)&(d[f"c{c}_ratio2"]>=ratio)))
        for combo in (("straight","avg"),("core","straight"),("core","avg")):
            for ratio in (.35,.50,.65):
                a,b=combo
                specs.append((cand,f"C{cand}_{a}_{b}_R{ratio:.2f}",
                              lambda d,c=cand,a=a,b=b,ratio=ratio:(d[f"c{c}_{a}_beat"]==1)&(d[f"c{c}_{b}_beat"]==1)&(d[f"c{c}_ratio2"]>=ratio)))
    single=[]
    for cand,name,fn in specs:
        fire=fn(q)&q[f"c{cand}_already"].eq(0)
        new=[];res=dam=0
        for i,r in q.iterrows():
            old=int(r.baseline_hit)
            nh=int(int(r.actual2) in (int(r.base1),cand)) if bool(fire.loc[i]) else old
            new.append(nh);res+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
        single.append({"candidate":cand,"rule":name,"fired_R":int(fire.sum()),
                       "rescued":res,"damaged":dam,"net":res-dam,"hits":int(sum(new)),"rate":float(np.mean(new))})
    single.sort(key=lambda x:(x["hits"],x["net"],-x["fired_R"]),reverse=True)

    # Combine top independent candidate-4 and candidate-5 rules in all pairings.
    r4=[x for x in single if x["candidate"]==4][:8];r5=[x for x in single if x["candidate"]==5][:8]
    lookup={name:(cand,fn) for cand,name,fn in specs}
    combos=[]
    for a4 in r4:
      for a5 in r5:
        _,f4=lookup[a4["rule"]];_,f5=lookup[a5["rule"]]
        m4=f4(q)&q.c4_already.eq(0);m5=f5(q)&q.c5_already.eq(0)
        new=[];res=dam=0;both=0
        for i,r in q.iterrows():
            old=int(r.baseline_hit);pair=[int(r.base1),int(r.base2)]
            fire4=bool(m4.loc[i]);fire5=bool(m5.loc[i])
            if fire4 and fire5:
                both+=1
                # Prefer candidate with higher P2 relative to current second.
                chosen=4 if r.c4_ratio2>=r.c5_ratio2 else 5
                pair=[int(r.base1),chosen]
            elif fire4:pair=[int(r.base1),4]
            elif fire5:pair=[int(r.base1),5]
            nh=int(int(r.actual2) in pair)
            new.append(nh);res+=int(old==0 and nh==1);dam+=int(old==1 and nh==0)
        combos.append({"rule4":a4["rule"],"rule5":a5["rule"],"fired4":int(m4.sum()),"fired5":int(m5.sum()),"both":both,
                       "rescued":res,"damaged":dam,"net":res-dam,"hits":int(sum(new)),"rate":float(np.mean(new))})
    combos.sort(key=lambda x:(x["hits"],x["net"],-(x["fired4"]+x["fired5"])),reverse=True)
    result={"population":"DEV head1 wins; lane-specific 4/5 second gates",
            "baseline":{"R":163,"hits":int(q.baseline_hit.sum()),"rate":float(q.baseline_hit.mean())},
            "single_top":single[:30],"combined_top":combos[:20],
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    pd.DataFrame(single).to_csv(OUT/"single_rules.csv",index=False);pd.DataFrame(combos).to_csv(OUT/"combined_rules.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_LANE_GATE_V10",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
