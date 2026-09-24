#!/usr/bin/env python3
from __future__ import annotations
import csv,json,os
from pathlib import Path
import numpy as np
import pandas as pd
import backtest as bt

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-broad-five-v22"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except:return np.nan

def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file(): return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def bycode(rs): return {str(r.get("レースコード","")).zfill(12):r for r in rs}

def main():
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    pred=pd.read_csv("analysis_v308_1head_volume_opponent_joint_pred.csv",dtype={"race_code":str})
    pred.race_code=pred.race_code.astype(str).str.zfill(12)
    pred=pred[pred.month.isin(DEV)].copy()
    pred=pred[pred.actual_combo.fillna("").astype(str).str.startswith("1-")].copy()
    cache={};rows=[]
    for _,r in pred.iterrows():
        code=str(r.race_code).zfill(12);parts=str(r.actual_combo).split("-")
        if len(parts)!=3:continue
        sec=int(parts[1]);day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")))
        card=cache[day][0].get(code,{});w=cache[day][1].get(code,{})
        if not card:continue
        x=bt.race_features(card,w);a=x[5];b=x[4]
        rec={"race_code":code,"month":str(r.month),"actual2":sec,"y5":int(sec==5)}
        for name,key,higher in [
          ("local","local",True),("wr","wr",True),("motor2","motor2",True),("motor3","motor3",True),
          ("waku_st","waku_st",False),("national_st","nst",False),("meet_st","meet_st",False)
        ]:
            av=ff(a.get(key));bv=ff(b.get(key))
            # positive always means 5 is better than 4
            if higher:edge=av-bv
            else:edge=bv-av
            rec[f"{name}_edge"]=edge
            rec[f"{name}_better"]=int(np.isfinite(edge) and edge>0)
        rows.append(rec)
    q=pd.DataFrame(rows)
    q.to_csv(OUT/"rows.csv",index=False)
    pos=q[q.y5.eq(1)];neg=q[q.y5.eq(0)]
    summary={"R":int(len(q)),"positive_R":int(len(pos)),"positive_rate":float(q.y5.mean()),"features":{}}
    for name in ("local","wr","motor2","motor3","waku_st","national_st","meet_st"):
        col=f"{name}_edge";flag=f"{name}_better"
        ps=pd.to_numeric(pos[col],errors="coerce");ns=pd.to_numeric(neg[col],errors="coerce")
        summary["features"][name]={
          "pos_mean":float(ps.mean()),"neg_mean":float(ns.mean()),
          "pos_better_rate":float(pos[flag].mean()),"neg_better_rate":float(neg[flag].mean()),
          "lift_ratio":float(pos[flag].mean()/max(neg[flag].mean(),1e-12))
        }
    # interpretable combo rules
    rules={}
    specs={
      "LOCAL":q.local_better.eq(1),
      "LOCAL_WR":q.local_better.eq(1)&q.wr_better.eq(1),
      "LOCAL_MOTOR2":q.local_better.eq(1)&q.motor2_better.eq(1),
      "LOCAL_MEETST":q.local_better.eq(1)&q.meet_st_better.eq(1),
      "LOCAL_WR_MOTOR2":q.local_better.eq(1)&q.wr_better.eq(1)&q.motor2_better.eq(1),
      "LOCAL_WR_MEETST":q.local_better.eq(1)&q.wr_better.eq(1)&q.meet_st_better.eq(1)
    }
    base=float(q.y5.mean())
    for name,m in specs.items():
        g=q[m]
        rules[name]={"R":int(len(g)),"y5_R":int(g.y5.sum()),"rate":float(g.y5.mean()) if len(g) else None,
                     "lift_vs_base":float(g.y5.mean()/base) if len(g) else None,
                     "recall":float(g.y5.sum()/max(q.y5.sum(),1))}
    monthly={}
    for m,g in q.groupby("month"):
        monthly[m]={"R":int(len(g)),"y5_R":int(g.y5.sum()),"y5_rate":float(g.y5.mean())}
    result={"population":"all DEV boat1 winners from v308; target boat5 second vs others",
            "summary":summary,"rules":rules,"monthly":monthly,
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_BROAD_FIVE_V22",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
