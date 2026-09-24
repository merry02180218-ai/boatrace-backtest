#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v7"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(str(x).strip()); return v if np.isfinite(v) else np.nan
    except:return np.nan
def ii(x):
    try:return int(float(str(x).strip()))
    except:return None
def load_day(root,ymd):
    p=Path(root)/"data/results/realtime"/ymd[:4]/ymd[4:6]/f"{ymd[6:8]}.csv"
    if not p.is_file():return {}
    with p.open(encoding="utf-8-sig",newline="") as f:
        return {str(r.get("レースコード","")).zfill(12):r for r in csv.DictReader(f)}
def start_maps(r):
    bc={};bs={}
    for c in range(1,7):
        b=ii(r.get(f"{c}コース_艇番"));st=ff(r.get(f"{c}コース_スタートタイミング"))
        if b is not None:bc[c]=b;bs[b]=st
    return bc,bs

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    x=pickle.load(a.prepared.open("rb")); rr=x["rows"]
    base_by={str(r["race_code"]).zfill(12):r for r in rr["H078_M375"]}
    days={};rows=[]
    for code,b in base_by.items():
        m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p=str(b.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        sec,third=int(p[1]),int(p[2])
        if sec<4:continue
        day=code[:8]
        if day not in days:days[day]=load_day(root,day)
        r=days[day].get(code)
        if not r:continue
        bc,bs=start_maps(r); sc=next((c for c,x in bc.items() if x==sec),None)
        inn=bc.get(sc-1) if sc and sc>1 else None
        secst=bs.get(sec,np.nan); innst=bs.get(inn,np.nan) if inn else np.nan
        active=[z for z in range(2,7) if np.isfinite(bs.get(z,np.nan))]
        sr=sorted(active,key=lambda z:bs[z]);st_rank=(sr.index(sec)+1) if sec in sr else None
        finish={}
        for k in range(1,7):
            z=ii(r.get(f"{k}着_艇番"))
            if z is not None:finish[z]=k
        inner_finish=finish.get(inn)
        # Strong start definition requires both a top-2 opponent ST and >=.02 edge over immediate inside.
        strong_start=int(st_rank is not None and st_rank<=2 and np.isfinite(innst) and (innst-secst)>=.02)
        lane_gain=int(sec>=4 and sc is not None and sc<=3)
        inner_collapse=int(inner_finish is not None and inner_finish>=4)
        # Pre-race strength of actual outer second, relative to immediate inside and boats 2/3.
        rec={"race_code":code,"month":m,"second":sec,"third":third,"second_course":sc,
             "inner_course_boat":inn,"inner_finish":inner_finish,
             "strong_start":strong_start,"lane_gain":lane_gain,"inner_collapse":inner_collapse,
             "second_st":secst,"inner_st":innst,"st_edge":innst-secst if np.isfinite(innst) and np.isfinite(secst) else np.nan}
        for metric in ("score","core","ex","st","straight","avg"):
            sv=ff(b.get(f"{metric}{sec}"));iv=ff(b.get(f"{metric}{inn}")) if inn else np.nan
            r2=ff(b.get(f"{metric}2"));r3=ff(b.get(f"{metric}3"))
            rec[f"{metric}_actual"]=sv
            rec[f"{metric}_vs_inner"]=sv-iv if np.isfinite(sv) and np.isfinite(iv) else np.nan
            q=[z for z in (r2,r3) if np.isfinite(z)]
            rec[f"{metric}_vs_inner23max"]=sv-max(q) if np.isfinite(sv) and q else np.nan
        # Primary descriptive route.
        if lane_gain:route="COURSE_GAIN"
        elif strong_start and inner_collapse:route="START_AND_INNER_COLLAPSE"
        elif strong_start:route="START_EDGE"
        elif inner_collapse:route="INNER_COLLAPSE_WITHOUT_START_EDGE"
        else:route="NON_START_POSITIONAL"
        rec["route"]=route;rows.append(rec)
    q=pd.DataFrame(rows);q.to_csv(OUT/"outer_second_routes.csv",index=False)
    if len(q)<38:raise RuntimeError(f"outer coverage low {len(q)}")
    byroute=[]
    for route,g in q.groupby("route"):
        row={"route":route,"R":int(len(g)),"share":float(len(g)/len(q)),
             "mean_st_edge":float(g.st_edge.mean()) if g.st_edge.notna().any() else None,
             "inner_collapse_rate":float(g.inner_collapse.mean())}
        for metric in ("score","core","ex","st","straight","avg"):
            s=pd.to_numeric(g[f"{metric}_vs_inner"],errors="coerce")
            row[f"{metric}_beats_inner_R"]=int((s>0).sum())
            row[f"{metric}_beats_inner_rate"]=float((s>0).mean())
            s23=pd.to_numeric(g[f"{metric}_vs_inner23max"],errors="coerce")
            row[f"{metric}_beats_inner23_R"]=int((s23>0).sum())
            row[f"{metric}_beats_inner23_rate"]=float((s23>0).mean())
        byroute.append(row)
    # Compare start-driven vs not.
    q["start_driven"]=((q.strong_start==1)|(q.lane_gain==1)).astype(int)
    compare={}
    for flag,g in q.groupby("start_driven"):
        key="start_or_course" if flag else "non_start"
        compare[key]={"R":int(len(g)),"inner_collapse":int(g.inner_collapse.sum()),"inner_collapse_rate":float(g.inner_collapse.mean())}
        for metric in ("score","core","ex","st","straight","avg"):
            s=pd.to_numeric(g[f"{metric}_vs_inner"],errors="coerce")
            compare[key][f"{metric}_beats_inner_rate"]=float((s>0).mean())
    result={"population":"DEV outer-second races; postrace route decomposition joined to pre-race foot/strength",
            "R":int(len(q)),"route_counts":{str(k):int(v) for k,v in q.route.value_counts().items()},
            "routes":byroute,"start_vs_nonstart":compare,
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False,
            "note":"Route labels use post-race actual ST/finish order for explanation only."}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_ROUTE_V7",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
