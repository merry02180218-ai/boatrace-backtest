#!/usr/bin/env python3
from __future__ import annotations
import sys,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_3head_a60_playerhistory_curve_v1 as base
import analyze_3head_player_history_3v2_ablation_v2 as ph
import run_3head_wave20_manual_gate as w20

OUT=Path("research_3head_a60_full3v2_curve_julaug_v4.json"); CSV=Path("research_3head_a60_full3v2_curve_julaug_v4.csv")
TARGETS=[30,40,50,60,70,80]
HIST_START=pd.Timestamp("2025-10-01")
def n(s):return pd.to_numeric(s,errors="coerce")

def main():
    # Build the same causal PRE/post universe used by frozen A+.60.
    raw={}
    ranges={"oct":("2025-10-01","2025-10-31"),"nov":("2025-11-01","2025-11-30"),"dec":("2025-12-01","2025-12-31"),"jan":("2026-01-01","2026-01-31"),"feb":("2026-02-01","2026-02-28"),"mar":("2026-03-01","2026-03-31"),"apr":("2026-04-01","2026-04-30"),"may":("2026-05-01","2026-05-31"),"jun":("2026-06-01","2026-06-30"),"jul":("2026-07-01","2026-07-31"),"aug":("2026-08-01","2026-08-31")}
    for k,(a,b) in ranges.items():
        x,r,audit=w20.build_pre_enhanced(a,b,True);raw[k]=(x,r)
    frames={k:w20.prep_month(x,r) for k,(x,r) in raw.items()}
    scores,_=w20.make_pre_scores(frames)
    days,cache=w20.prefetch_sources();post,_=w20.build_motor_exhibition(days,cache)
    allrows=[]
    for k in ["jul","aug"]:
        q=scores[k].merge(post,on=["rc","date"],how="left",validate="one_to_one")
        q["race_code"]=q.rc.astype("int64").astype(str).str.zfill(12);q["month"]=k
        allrows.append(q)
    d=pd.concat(allrows,ignore_index=True)
    # Add independently defined strict-prior PLAYER_HISTORY; this reads outcomes only after each day's features are frozen.
    d=ph.add_player_history(d)
    names=ph.NAMES
    full=[]
    for k in names:
        rel=f"pl_rel3_2_{k}";d[rel]=n(d[f"b3_pl_{k}"])-n(d[f"b2_pl_{k}"])
        full += [f"b3_pl_{k}",f"b2_pl_{k}",rel]
    # Candidate pool deliberately only loosens A+.60 inner-motor threshold; all other A gate semantics stay frozen.
    rn=n(d.race_no);pre=n(d.pre_score)
    pool=(rn>=1)&(rn<=12)&(pre>=.925)&base.pg.mask(d,base.pg.A["conds"])&(n(d.post_motor_inner_rank_edge)>=0.0)
    d=d.loc[pool].copy()
    # Causal rolling FULL_3V2 model. Training is strictly earlier dates.
    pred=[]
    for day in sorted(d.date.dt.normalize().unique()):
        te=d[d.date.dt.normalize()==day].copy();tr=d[(d.date<day)&(d.date>=HIST_START)].copy()
        if len(tr)<20 or tr.y.nunique()<2:continue
        model=make_pipeline(SimpleImputer(strategy="median"),StandardScaler(),LogisticRegression(C=.08,class_weight="balanced",solver="liblinear",max_iter=1800,random_state=322))
        model.fit(tr[full],tr.y.astype(int));te["ph_score"]=model.predict_proba(te[full])[:,1];pred.append(te)
    p=pd.concat(pred,ignore_index=True)
    rows=[]
    for mon,g in p.groupby("month"):
        frozen=g[n(g.post_motor_inner_rank_edge)>=.60]
        rows.append({"month":mon,"variant":"FROZEN_A60","target_R":len(frozen),"R":len(frozen),"heads":int(frozen.y.sum()),"head_rate":float(frozen.y.mean()) if len(frozen) else None})
        for target in TARGETS:
            z=g.nlargest(min(target,len(g)),"ph_score")
            rows.append({"month":mon,"variant":"FULL_3V2","target_R":target,"R":len(z),"heads":int(z.y.sum()),"head_rate":float(z.y.mean()) if len(z) else None})
    z=pd.DataFrame(rows);z.to_csv(CSV,index=False)
    out={"policy":{"core_unchanged":True,"full3v2_strict_prior":True,"history_start":"2025-10-01","rolling_window_days":None,"candidate_gate_except_inner_motor_frozen":True,"inner_motor_pool_min":0.0,"opponent_core":"native_v242_5to10","opponent_expanded":"V221_Top6_protected_SECOND4","sep2026_used":False,"jul_aug_non_pristine_descriptive_only":True,"production_changed":False},"rows":rows}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2));print("A60_FULL3V2_CURVE_JULAUG_V4_OK");print("SEPTEMBER_UNREAD");print("PRODUCTION_UNCHANGED")
if __name__=="__main__":main()
