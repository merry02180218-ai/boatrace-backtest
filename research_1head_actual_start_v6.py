#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v6"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(str(x).strip())
        return v if np.isfinite(v) else np.nan
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
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    x=pickle.load(a.prepared.open("rb")); rr=x["rows"]
    targets=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);month=code[:4]+"-"+code[4:6]
        if month not in DEV:continue
        if code[:8]>="20260901":raise RuntimeError("September entered")
        p=str(r.get("actual_combo","")).split("-")
        if len(p)==3 and p[0]=="1":
            targets.append((code,int(p[1]),int(p[2])))
    byday={}
    rows=[]; missing=[]
    for code,sec,third in targets:
        day=code[:8]
        if day not in byday:byday[day]=load_day(root,day)
        r=byday[day].get(code)
        if not r:
            missing.append(code); continue
        course_boat={c:ii(r.get(f"{c}コース_艇番")) for c in range(1,7)}
        course_st={c:ff(r.get(f"{c}コース_スタートタイミング")) for c in range(1,7)}
        course_f={c:bool(str(r.get(f"{c}コース_F","")).strip()) for c in range(1,7)}
        boat_course={b:c for c,b in course_boat.items() if b is not None}
        boat_st={b:course_st[c] for c,b in course_boat.items() if b is not None}
        boat_f={b:course_f[c] for c,b in course_boat.items() if b is not None}
        sc=boat_course.get(sec); ss=boat_st.get(sec,np.nan)
        active=[b for b in range(2,7) if b in boat_st and not boat_f.get(b,False) and np.isfinite(boat_st[b])]
        st_sorted=sorted(active,key=lambda b:boat_st[b])
        st_rank=(st_sorted.index(sec)+1) if sec in st_sorted else None
        inner_course_boat=course_boat.get(sc-1) if sc and sc>1 else None
        inner_st=boat_st.get(inner_course_boat,np.nan) if inner_course_boat else np.nan
        beats_immediate_inner=int(np.isfinite(ss) and np.isfinite(inner_st) and ss<inner_st)
        c2b=course_boat.get(2);c3b=course_boat.get(3)
        c2st=boat_st.get(c2b,np.nan) if c2b else np.nan;c3st=boat_st.get(c3b,np.nan) if c3b else np.nan
        beats_c2=int(np.isfinite(ss) and np.isfinite(c2st) and ss<c2st)
        beats_c3=int(np.isfinite(ss) and np.isfinite(c3st) and ss<c3st)
        outer_frame=int(sec>=4)
        course_gain=int(outer_frame and sc is not None and sc<=3)
        fast_start=int(st_rank is not None and st_rank<=2)
        if outer_frame:
            if course_gain: mech="COURSE_GAIN"
            elif fast_start and beats_immediate_inner:mech="OUTER_FAST_START"
            elif fast_start:mech="FAST_START_NO_INNER_EDGE"
            elif beats_immediate_inner:mech="INNER_SLOW_EDGE"
            else:mech="NO_START_EDGE"
        else:
            mech="INNER_SECOND"
        rows.append({
          "race_code":code,"month":code[:4]+"-"+code[4:6],"second":sec,"third":third,
          "kimarite":str(r.get("決まり手","")).replace("　","").replace(" ",""),
          "winner_course":boat_course.get(1),"second_course":sc,"second_st":ss,"second_st_rank":st_rank,
          "outer_frame":outer_frame,"course_gain":course_gain,"fast_start":fast_start,
          "beats_immediate_inner_st":beats_immediate_inner,"beats_course2_st":beats_c2,"beats_course3_st":beats_c3,
          "mechanism":mech,
          "wind":ff(r.get("風速(m)")),"wave":ff(r.get("波の高さ(cm)")),"water_temp":ff(r.get("水温(℃)"))
        })
    q=pd.DataFrame(rows);q.to_csv(OUT/"race_rows.csv",index=False)
    if len(q)<int(len(targets)*.98):raise RuntimeError(f"realtime coverage too low {len(q)}/{len(targets)} missing={missing}")
    outer=q[q.outer_frame.eq(1)];inner=q[q.outer_frame.eq(0)]
    def sm(g):
        return {"R":int(len(g)),
                "st_top1":int((g.second_st_rank==1).sum()),"st_top1_rate":float((g.second_st_rank==1).mean()) if len(g) else None,
                "st_top2":int((g.second_st_rank<=2).sum()),"st_top2_rate":float((g.second_st_rank<=2).mean()) if len(g) else None,
                "beats_immediate_inner":int(g.beats_immediate_inner_st.sum()),"beats_immediate_inner_rate":float(g.beats_immediate_inner_st.mean()) if len(g) else None,
                "mean_second_st":float(g.second_st.mean()) if len(g) else None}
    by_second={}
    for b,g in q.groupby("second"):by_second[str(b)]=sm(g)
    mech={str(k):int(v) for k,v in outer.mechanism.value_counts().items()}
    by_kim=[]
    for k,g in q.groupby("kimarite"):
        by_kim.append({"kimarite":k,"R":int(len(g)),"outer_second":int(g.outer_frame.sum()),"outer_rate":float(g.outer_frame.mean())})
    course_cross=pd.crosstab(outer.second,outer.second_course).to_dict()
    result={
      "population":"DEV H078_M375 races where boat1 actually won; actual race ST/course mechanism",
      "R":int(len(q)),"target_R":int(len(targets)),"missing_R":int(len(missing)),"missing_codes":missing,
      "outer_R":int(len(outer)),"outer_rate":float(q.outer_frame.mean()),
      "all_second":sm(q),"inner_second":sm(inner),"outer_second":sm(outer),
      "outer_mechanisms":mech,
      "outer_course_gain_R":int(outer.course_gain.sum()),"outer_course_gain_rate":float(outer.course_gain.mean()) if len(outer) else None,
      "outer_fast_start_R":int(outer.fast_start.sum()),"outer_fast_start_rate":float(outer.fast_start.mean()) if len(outer) else None,
      "outer_beats_immediate_inner_R":int(outer.beats_immediate_inner_st.sum()),
      "outer_beats_immediate_inner_rate":float(outer.beats_immediate_inner_st.mean()) if len(outer) else None,
      "outer_beats_both_course2_3_R":int(((outer.beats_course2_st==1)&(outer.beats_course3_st==1)).sum()),
      "outer_beats_both_course2_3_rate":float(((outer.beats_course2_st==1)&(outer.beats_course3_st==1)).mean()) if len(outer) else None,
      "by_second":by_second,"by_kimarite":by_kim,
      "outer_second_frame_by_actual_course":{str(k):{str(kk):int(vv) for kk,vv in vv.items()} for k,vv in course_cross.items()},
      "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False,
      "note":"Actual race ST/course are post-race explanatory variables only, not LIVE prediction inputs."
    }
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_ACTUAL_START_V6",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
