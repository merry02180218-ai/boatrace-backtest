#!/usr/bin/env python3
from __future__ import annotations
import sys, json, numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import verify_v288_operational_pre_replay as v288
import run_3head_a_purchase_gate_dev as pg
import run_3head_wave20_manual_gate as w20

SRC=Path("analysis_v243_3head_expand_feature_audit.csv")
OUT=Path("research_3head_a60_playerhistory_curve_v1.json")
CSV=Path("research_3head_a60_playerhistory_curve_v1.csv")
MONTHS=["nov","dec","jan","feb"]
RANGES={"oct":("2025-10-01","2025-10-31"),"nov":("2025-11-01","2025-11-30"),
        "dec":("2025-12-01","2025-12-31"),"jan":("2026-01-01","2026-01-31"),"feb":("2026-02-01","2026-02-28")}

def n(s): return pd.to_numeric(s,errors="coerce")

def build_a60():
    raw={}
    for k,(a,b) in RANGES.items():
        x,r,audit=w20.build_pre_enhanced(a,b,True); raw[k]=(x,r)
    frames={k:w20.prep_month(x,r) for k,(x,r) in raw.items()}
    scores,_=w20.make_pre_scores(frames)
    days,cache=w20.prefetch_sources(); post,_=w20.build_motor_exhibition(days,cache)
    rows=[]
    for k in MONTHS:
        q=scores[k].merge(post,on=["rc","date"],how="left",validate="one_to_one")
        rn=n(q.race_no); pre=n(q.pre_score)
        m=(rn>=1)&(rn<=12)&(pre>=.925)&pg.mask(q,pg.A["conds"])&(n(q.post_motor_inner_rank_edge)>=.60)
        z=q.loc[m,["rc","date","y","post_motor_inner_rank_edge"]].copy()
        z["race_code"]=z.rc.astype("int64").astype(str).str.zfill(12); z["a60_head"]=n(z.y).fillna(0).astype(int)
        rows.append(z[["race_code","date","a60_head","post_motor_inner_rank_edge"]])
    return pd.concat(rows,ignore_index=True).drop_duplicates("race_code")

def metric(z):
    r=len(z); h=int(z.a60_head.sum()) if r else 0
    return {"races":r,"boat3_wins":h,"head_rate":h/r if r else None}

def main():
    a=build_a60()
    # Fixed A+.60 cohort strength curve first; PLAYER_HISTORY ranking is layered in next audit.
    # This establishes the volume/head-rate baseline without touching CORE.
    a["month"]=a.race_code.str[:6]
    rows=[]
    for m,g in a.groupby("month"):
        rows.append({"month":m,"races":len(g),"heads":int(g.a60_head.sum()),"head_rate":float(g.a60_head.mean()) if len(g) else None})
    out={"policy":{"core_unchanged":True,"a60_gate_frozen":True,"opponent_core":"native_v242_5to10","opponent_expanded":"V221_Top6_protected_SECOND4","threshold_tuning":False,"sep2026_used":False,"production_changed":False},
         "a60_baseline":rows}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    pd.DataFrame(rows).to_csv(CSV,index=False)
    print(json.dumps(out,ensure_ascii=False,indent=2));print("A60_PLAYERHISTORY_CURVE_V1_OK");print("SEPTEMBER_UNREAD");print("PRODUCTION_UNCHANGED")
if __name__=="__main__": main()
