#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v10"; OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(str(x).strip());return v if np.isfinite(v) else np.nan
    except:return np.nan
def ii(x):
    try:return int(float(str(x).strip()))
    except:return None

def load_day(root,ymd):
    p=Path(root)/"data/results/realtime"/ymd[:4]/ymd[4:6]/f"{ymd[6:8]}.csv"
    if not p.is_file():return {}
    with p.open(encoding="utf-8-sig",newline="") as f:
        return {str(r.get("レースコード","")).zfill(12):r for r in csv.DictReader(f)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb"));root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    daycache={};rows=[];missing=[]
    for pr in x["rows"]["H078_M375"]:
        code=str(pr["race_code"]).zfill(12);month=code[:4]+"-"+code[4:6]
        if month not in DEV:continue
        p=str(pr.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1" or p[1]!="4":continue
        third=int(p[2]);day=code[:8]
        if day not in daycache:daycache[day]=load_day(root,day)
        rr=daycache[day].get(code)
        if not rr:missing.append(code);continue
        course_boat={c:ii(rr.get(f"{c}コース_艇番")) for c in range(1,7)}
        course_st={c:ff(rr.get(f"{c}コース_スタートタイミング")) for c in range(1,7)}
        boat_course={b:c for c,b in course_boat.items() if b is not None}
        boat_st={b:course_st[c] for c,b in course_boat.items() if b is not None}
        p2,_=v365.formal_post_five6(pr)
        z={"race_code":code,"month":month,"third":third,"third_group":"INNER2" if third==2 else "INNER3" if third==3 else "OUTER",
           "actual_st2":boat_st.get(2,np.nan),"actual_st3":boat_st.get(3,np.nan),"actual_st4":boat_st.get(4,np.nan),
           "course4":boat_course.get(4),"kimarite":str(rr.get("決まり手","")).replace("　","").replace(" ",""),
           "four_beats2_st":int(ff(boat_st.get(4))<ff(boat_st.get(2))) if np.isfinite(ff(boat_st.get(4))) and np.isfinite(ff(boat_st.get(2))) else 0,
           "four_beats3_st":int(ff(boat_st.get(4))<ff(boat_st.get(3))) if np.isfinite(ff(boat_st.get(4))) and np.isfinite(ff(boat_st.get(3))) else 0,
           "two_beats3_st":int(ff(boat_st.get(2))<ff(boat_st.get(3))) if np.isfinite(ff(boat_st.get(2))) and np.isfinite(ff(boat_st.get(3))) else 0,
           "p2_4":ff(p2.get(4)),"p2_rank4":None}
        order=sorted([2,3,4,5,6],key=lambda b:ff(p2.get(b)),reverse=True);z["p2_rank4"]=order.index(4)+1
        for metric in ("score","core","ex","st","straight","avg"):
            for b in (2,3,4):z[f"{metric}{b}"]=ff(pr.get(f"{metric}{b}"))
            z[f"{metric}4_minus2"]=ff(pr.get(f"{metric}4"))-ff(pr.get(f"{metric}2"))
            z[f"{metric}4_minus3"]=ff(pr.get(f"{metric}4"))-ff(pr.get(f"{metric}3"))
            z[f"{metric}4_beats2"]=int(z[f"{metric}4_minus2"]>0) if np.isfinite(z[f"{metric}4_minus2"]) else 0
            z[f"{metric}4_beats3"]=int(z[f"{metric}4_minus3"]>0) if np.isfinite(z[f"{metric}4_minus3"]) else 0
        rows.append(z)
    q=pd.DataFrame(rows);q.to_csv(OUT/"rows.csv",index=False)
    def sm(g):
        out={"R":int(len(g)),"third_counts":{str(k):int(v) for k,v in g.third.value_counts().sort_index().items()},
             "four_beats2_actual_st":int(g.four_beats2_st.sum()),"four_beats2_actual_st_rate":float(g.four_beats2_st.mean()) if len(g) else None,
             "four_beats3_actual_st":int(g.four_beats3_st.sum()),"four_beats3_actual_st_rate":float(g.four_beats3_st.mean()) if len(g) else None,
             "four_beats_both_actual_st":int(((g.four_beats2_st==1)&(g.four_beats3_st==1)).sum()),
             "four_beats_both_actual_st_rate":float(((g.four_beats2_st==1)&(g.four_beats3_st==1)).mean()) if len(g) else None,
             "mean_actual_st2":float(g.actual_st2.mean()),"mean_actual_st3":float(g.actual_st3.mean()),"mean_actual_st4":float(g.actual_st4.mean()),
             "p2_rank4_top1":int((g.p2_rank4==1).sum()),"p2_rank4_top2":int((g.p2_rank4<=2).sum())}
        for metric in ("score","core","ex","st","straight","avg"):
            out[f"{metric}_4_beats2"]=int(g[f"{metric}4_beats2"].sum())
            out[f"{metric}_4_beats3"]=int(g[f"{metric}4_beats3"].sum())
            out[f"{metric}_4_beats_both"]=int(((g[f"{metric}4_beats2"]==1)&(g[f"{metric}4_beats3"]==1)).sum())
        return out
    bygrp={k:sm(g) for k,g in q.groupby("third_group")}
    result={"population":"DEV head1 wins with boat4 second","R":int(len(q)),"missing":missing,
            "all":sm(q),"by_third_group":bygrp,
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False,
            "note":"actual ST is explanatory post-race only; score/core/ex/st/straight/avg are pre-race prepared."}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_FOUR_SECOND_V10",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
