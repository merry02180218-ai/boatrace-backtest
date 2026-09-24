#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v9"
OUT.mkdir(parents=True,exist_ok=True)

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
def maps(r):
    bc={};bs={}
    for c in range(1,7):
        b=ii(r.get(f"{c}コース_艇番"));st=ff(r.get(f"{c}コース_スタートタイミング"))
        if b is not None:bc[c]=b;bs[b]=st
    fin={}
    for k in range(1,7):
        b=ii(r.get(f"{k}着_艇番"))
        if b is not None:fin[b]=k
    return bc,bs,fin

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    x=pickle.load(a.prepared.open("rb"));rr=x["rows"];cache={};rows=[]
    for b in rr["H078_M375"]:
        code=str(b["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p=str(b.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        sec,third=int(p[1]),int(p[2]);day=code[:8]
        if day not in cache:cache[day]=load_day(root,day)
        r=cache[day].get(code)
        if not r:continue
        bc,bs,fin=maps(r);course={boat:c for c,boat in bc.items()}
        p2,pc=v365.formal_post_five6(b);pv={z:ff(p2.get(z)) for z in BOATS}
        p2order=sorted(BOATS,key=lambda z:pv[z],reverse=True)
        st_active=[z for z in BOATS if np.isfinite(bs.get(z,np.nan))]
        storder=sorted(st_active,key=lambda z:bs[z])
        sc=course.get(sec);inner=bc.get(sc-1) if sc and sc>1 else None
        rec={"race_code":code,"month":m,"second":sec,"third":third,
             "p2_rank":p2order.index(sec)+1,"p2_top2":int(sec in p2order[:2]),
             "st_rank":storder.index(sec)+1 if sec in storder else np.nan,
             "st_top2":int(sec in storder[:2]),"second_course":sc,
             "course_shift":sc-sec if sc else np.nan,
             "immediate_inner":inner,"inner_finish":fin.get(inner,np.nan) if inner else np.nan,
             "inner_collapse":int(inner is not None and fin.get(inner,9)>=4),
             "inner_st_edge":(bs.get(inner,np.nan)-bs.get(sec,np.nan)) if inner else np.nan,
             "beats_inner_st":int(inner is not None and np.isfinite(bs.get(inner,np.nan)) and np.isfinite(bs.get(sec,np.nan)) and bs[sec]<bs[inner]),
             "third_is_inside_neighbor":int(third==sec-1),
             "third_is_outside_neighbor":int(third==sec+1),
             "kimarite":str(r.get("決まり手","")).replace("　","").replace(" ","")}
        for met in ("score","core","ex","st","straight","avg"):
            sv=ff(b.get(f"{met}{sec}"));iv=ff(b.get(f"{met}{inner}")) if inner else np.nan
            rec[f"{met}_beats_inner"]=int(np.isfinite(sv) and np.isfinite(iv) and sv>iv)
        if sec>=4:
            rec["foot3_all"]=int(rec["core_beats_inner"] and rec["straight_beats_inner"] and rec["avg_beats_inner"])
        else:rec["foot3_all"]=0
        rows.append(rec)
    q=pd.DataFrame(rows);q.to_csv(OUT/"lane_rows.csv",index=False)
    if len(q)<160:raise RuntimeError(f"coverage {len(q)}")
    lanes={}
    for sec,g in q.groupby("second"):
        d={"R":int(len(g)),"share":float(len(g)/len(q)),
           "p2_top2":int(g.p2_top2.sum()),"p2_top2_rate":float(g.p2_top2.mean()),
           "st_top2":int(g.st_top2.sum()),"st_top2_rate":float(g.st_top2.mean()),
           "beats_inner_st":int(g.beats_inner_st.sum()),"beats_inner_st_rate":float(g.beats_inner_st.mean()),
           "inner_collapse":int(g.inner_collapse.sum()),"inner_collapse_rate":float(g.inner_collapse.mean()),
           "course_shift_mean":float(g.course_shift.mean())}
        for met in ("score","core","ex","st","straight","avg"):
            d[f"{met}_beats_inner_rate"]=float(g[f"{met}_beats_inner"].mean())
        d["third_counts"]={str(k):int(v) for k,v in g.third.value_counts().sort_index().items()}
        d["third_inside_neighbor_rate"]=float(g.third_is_inside_neighbor.mean())
        d["third_outside_neighbor_rate"]=float(g.third_is_outside_neighbor.mean())
        lanes[str(sec)]=d
    # Deep outer structural patterns.
    deep={}
    for sec in (4,5,6):
        g=q[q.second.eq(sec)]
        if g.empty:continue
        inner=sec-1
        deep[str(sec)]={
          "R":int(len(g)),
          "third_is_inner_neighbor":int((g.third==inner).sum()),
          "third_is_inner_neighbor_rate":float((g.third==inner).mean()),
          "inner_finishes_3rd":int((g.inner_finish==3).sum()),
          "inner_finishes_3rd_rate":float((g.inner_finish==3).mean()),
          "inner_collapses_4plus":int((g.inner_finish>=4).sum()),
          "inner_collapses_4plus_rate":float((g.inner_finish>=4).mean()),
          "foot3_all":int(g.foot3_all.sum()),"foot3_all_rate":float(g.foot3_all.mean())
        }
    pairs=[{"pair":str(k),"R":int(v)} for k,v in q.assign(pair=q.second.astype(str)+"-"+q.third.astype(str)).pair.value_counts().head(20).items()]
    result={"population":"DEV head1 wins; lane-specific SECOND mechanism",
            "R":int(len(q)),"lanes":lanes,"deep_outer":deep,"top_second_third_pairs":pairs,
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_LANE_MECHANISM_V9",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
