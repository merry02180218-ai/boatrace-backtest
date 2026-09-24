#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
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

def pct(cond):
    a=pd.Series(cond).dropna()
    return float(a.mean()) if len(a) else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    x=pickle.load(a.prepared.open("rb")); rr=x["rows"]
    targets=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);month=code[:4]+"-"+code[4:6]
        if month not in DEV:continue
        if code[:8]>="20260901":raise RuntimeError("September entered")
        p=str(r.get("actual_combo","")).split("-")
        if len(p)==3 and p[0]=="1":
            targets.append((code,int(p[1]),int(p[2]),r))
    byday={};rows=[];missing=[]
    for code,sec,third,pr in targets:
        day=code[:8]
        if day not in byday:byday[day]=load_day(root,day)
        r=byday[day].get(code)
        if not r:missing.append(code);continue
        course_boat={c:ii(r.get(f"{c}コース_艇番")) for c in range(1,7)}
        course_st={c:ff(r.get(f"{c}コース_スタートタイミング")) for c in range(1,7)}
        boat_course={b:c for c,b in course_boat.items() if b is not None}
        boat_st={b:course_st[c] for c,b in course_boat.items() if b is not None}
        stvals={b:boat_st.get(b,np.nan) for b in BOATS}
        actual_order=[b for b in BOATS if np.isfinite(stvals[b])]
        actual_order=sorted(actual_order,key=lambda b:stvals[b])
        st_rank={b:i+1 for i,b in enumerate(actual_order)}
        inner_st=[stvals[b] for b in (2,3) if np.isfinite(stvals[b])]
        outer_st=[stvals[b] for b in (4,5,6) if np.isfinite(stvals[b])]
        if len(inner_st)<2 or not outer_st:continue
        best_inner=min(inner_st); worst_inner=max(inner_st); best_outer=min(outer_st)
        outer_best_boat=min((b for b in (4,5,6) if np.isfinite(stvals[b])),key=lambda b:stvals[b])
        exst={b:ff(pr.get(f"st{b}")) for b in BOATS}
        ex_order=sorted([b for b in BOATS if np.isfinite(exst[b])],key=lambda b:exst[b],reverse=True)
        ex_rank={b:i+1 for i,b in enumerate(ex_order)}
        secst=stvals.get(sec,np.nan)
        rows.append({
          "race_code":code,"month":code[:4]+"-"+code[4:6],"second":sec,"outer_second":int(sec>=4),
          "second_course":boat_course.get(sec),"second_actual_st":secst,"second_actual_st_rank":st_rank.get(sec),
          "second_ex_st_score":exst.get(sec),"second_ex_st_rank":ex_rank.get(sec),
          "course2_boat":course_boat.get(2),"course3_boat":course_boat.get(3),
          "course2_st":course_st.get(2),"course3_st":course_st.get(3),
          "best_inner_st":best_inner,"worst_inner_st":worst_inner,"best_outer_st":best_outer,
          "best_outer_boat":outer_best_boat,
          "best_outer_beats_best_inner":int(best_outer<best_inner),
          "best_outer_beats_one_inner":int(best_outer<worst_inner),
          "both_inner_st_ge_015":int(all(v>=.15 for v in inner_st)),
          "both_inner_st_ge_018":int(all(v>=.18 for v in inner_st)),
          "both_inner_st_ge_020":int(all(v>=.20 for v in inner_st)),
          "any_inner_st_ge_020":int(any(v>=.20 for v in inner_st)),
          "any_inner_st_ge_025":int(any(v>=.25 for v in inner_st)),
          "inner_st_spread":abs(inner_st[0]-inner_st[1]),
          "outer_vs_best_inner_gap":best_inner-best_outer,
          "outer_vs_worst_inner_gap":worst_inner-best_outer,
          "actual_second_is_fastest_outer":int(sec>=4 and sec==outer_best_boat),
          "actual_second_ex_st_top2":int(sec in ex_rank and ex_rank[sec]<=2),
          "actual_second_actual_st_top2":int(sec in st_rank and st_rank[sec]<=2),
          "ex_predicts_actual_st_top2":int(sec in ex_rank and sec in st_rank and ex_rank[sec]<=2 and st_rank[sec]<=2),
        })
    q=pd.DataFrame(rows);q.to_csv(OUT/"race_rows.csv",index=False)
    outer=q[q.outer_second.eq(1)];inner=q[q.outer_second.eq(0)]
    def group_summary(g):
        return {
          "R":int(len(g)),
          "best_outer_beats_best_inner":int(g.best_outer_beats_best_inner.sum()),"rate_best_outer_beats_best_inner":pct(g.best_outer_beats_best_inner),
          "best_outer_beats_one_inner":int(g.best_outer_beats_one_inner.sum()),"rate_best_outer_beats_one_inner":pct(g.best_outer_beats_one_inner),
          "both_inner_st_ge_015":int(g.both_inner_st_ge_015.sum()),"rate_both_inner_st_ge_015":pct(g.both_inner_st_ge_015),
          "both_inner_st_ge_018":int(g.both_inner_st_ge_018.sum()),"rate_both_inner_st_ge_018":pct(g.both_inner_st_ge_018),
          "both_inner_st_ge_020":int(g.both_inner_st_ge_020.sum()),"rate_both_inner_st_ge_020":pct(g.both_inner_st_ge_020),
          "any_inner_st_ge_020":int(g.any_inner_st_ge_020.sum()),"rate_any_inner_st_ge_020":pct(g.any_inner_st_ge_020),
          "any_inner_st_ge_025":int(g.any_inner_st_ge_025.sum()),"rate_any_inner_st_ge_025":pct(g.any_inner_st_ge_025),
          "mean_best_inner_st":float(g.best_inner_st.mean()),"mean_worst_inner_st":float(g.worst_inner_st.mean()),"mean_best_outer_st":float(g.best_outer_st.mean()),
          "mean_outer_vs_best_inner_gap":float(g.outer_vs_best_inner_gap.mean()),
          "actual_second_is_fastest_outer":int(g.actual_second_is_fastest_outer.sum()) if "actual_second_is_fastest_outer" in g else None,
          "actual_second_actual_st_top2":int(g.actual_second_actual_st_top2.sum()),
          "actual_second_ex_st_top2":int(g.actual_second_ex_st_top2.sum()),
          "ex_and_actual_st_top2":int(g.ex_predicts_actual_st_top2.sum()),
        }
    by_second={str(b):group_summary(g) for b,g in q.groupby("second")}
    # How predictive is exhibition ST of actual race ST rank for actual second?
    ctab=pd.crosstab(q.actual_second_ex_st_top2,q.actual_second_actual_st_top2).to_dict()
    result={
      "population":"DEV head1 wins with realtime ST and prepared exhibition ST",
      "R":int(len(q)),"target_R":len(targets),"missing_R":len(missing),"missing_codes":missing,
      "all":group_summary(q),"inner_second":group_summary(inner),"outer_second":group_summary(outer),
      "by_second":by_second,
      "exhibition_vs_actual_second_st_top2":{str(k):{str(kk):int(vv) for kk,vv in d.items()} for k,d in ctab.items()},
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False,
      "note":"Actual race ST is post-race explanatory only. Exhibition ST is pre-race."
    }
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_INNER_ST_WEAKNESS_V7",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
