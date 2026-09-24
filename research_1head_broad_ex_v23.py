#!/usr/bin/env python3
from __future__ import annotations
import csv,json,os
from pathlib import Path
import numpy as np
import pandas as pd
import backtest as bt

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-broad-five-v23"
OUT.mkdir(parents=True,exist_ok=True)

# Same lane corrections used throughout current research. Lower time = better.
EX_CORR={4:-0.01,5:-0.02}
LAP_CORR={4:0.10,5:0.00}
TURN_CORR={4:-0.10,5:-0.20}
STRAIGHT_CORR={4:0.00,5:0.00}

def ff(x):
    try:
        v=float(x);return v if np.isfinite(v) else np.nan
    except:return np.nan

def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file():return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def bycode(rs):return {str(r.get("レースコード","")).zfill(12):r for r in rs}

def orig_values(row,b):
    out={"lap":np.nan,"turn":np.nan,"straight":np.nan}
    labels=[str(row.get(f"計測項目{i}","")).strip() for i in (1,2,3)]
    for i,label in enumerate(labels,1):
        v=ff(row.get(f"艇{b}_値{i}"))
        if not np.isfinite(v):continue
        if "一周" in label:out["lap"]=v
        elif "まわり" in label or "回り" in label:out["turn"]=v
        elif "直線" in label:out["straight"]=v
    return out

def main():
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    pred=pd.read_csv("analysis_v308_1head_volume_opponent_joint_pred.csv",dtype={"race_code":str})
    pred.race_code=pred.race_code.astype(str).str.zfill(12)
    pred=pred[pred.month.isin(DEV)&pred.actual_combo.fillna("").astype(str).str.startswith("1-")].copy()
    cache={};rows=[]
    for _,r in pred.iterrows():
        code=str(r.race_code).zfill(12);p=str(r.actual_combo).split("-")
        if len(p)!=3:continue
        sec=int(p[1]);day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(
              bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
              bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")),
              bycode(load_csv(root,f"data/previews/tkz/{ymd}.csv")),
              bycode(load_csv(root,f"data/previews/stt/{ymd}.csv")),
              bycode(load_csv(root,f"data/previews/original_exhibition/{ymd}.csv"))
            )
        cards,waku,tkz,stt,orig=cache[day]
        card=cards.get(code,{});w=waku.get(code,{})
        if not card:continue
        xf=bt.race_features(card,w)
        z={"race_code":code,"month":str(r.month),"actual2":sec,"y5":int(sec==5),
           "local_edge":ff(xf[5]["local"])-ff(xf[4]["local"]),
           "wr_edge":ff(xf[5]["wr"])-ff(xf[4]["wr"])}
        trow=tkz.get(code,{})
        ex4=ff(trow.get("艇4_展示タイム"));ex5=ff(trow.get("艇5_展示タイム"))
        z["ex_edge"]=(ex4+EX_CORR[4])-(ex5+EX_CORR[5]) if np.isfinite(ex4) and np.isfinite(ex5) else np.nan
        srow=stt.get(code,{})
        st4=ff(srow.get("艇4_スタート展示"));st5=ff(srow.get("艇5_スタート展示"))
        z["stx_edge"]=st4-st5 if np.isfinite(st4) and np.isfinite(st5) else np.nan
        orow=orig.get(code,{})
        o4=orig_values(orow,4);o5=orig_values(orow,5)
        z["lap_edge"]=(o4["lap"]+LAP_CORR[4])-(o5["lap"]+LAP_CORR[5]) if np.isfinite(o4["lap"]) and np.isfinite(o5["lap"]) else np.nan
        z["turn_edge"]=(o4["turn"]+TURN_CORR[4])-(o5["turn"]+TURN_CORR[5]) if np.isfinite(o4["turn"]) and np.isfinite(o5["turn"]) else np.nan
        z["straight_edge"]=(o4["straight"]+STRAIGHT_CORR[4])-(o5["straight"]+STRAIGHT_CORR[5]) if np.isfinite(o4["straight"]) and np.isfinite(o5["straight"]) else np.nan
        # positive always means 5 better than 4
        for c in ("local_edge","wr_edge","ex_edge","stx_edge","lap_edge","turn_edge","straight_edge"):
            z[c.replace("_edge","_better")]=int(np.isfinite(z[c]) and z[c]>0)
        foot=[z[c] for c in ("ex_better","lap_better","turn_better","straight_better")]
        z["foot_better_count"]=sum(foot)
        rows.append(z)
    q=pd.DataFrame(rows);q.to_csv(OUT/"rows.csv",index=False)
    pos=q[q.y5.eq(1)];neg=q[q.y5.eq(0)];base=float(q.y5.mean())
    feats={}
    for name in ("local","wr","ex","stx","lap","turn","straight"):
        edge=f"{name}_edge";better=f"{name}_better"
        ps=pd.to_numeric(pos[edge],errors="coerce");ns=pd.to_numeric(neg[edge],errors="coerce")
        validp=ps.notna();validn=ns.notna()
        feats[name]={"pos_R":int(validp.sum()),"neg_R":int(validn.sum()),
                     "pos_mean":float(ps.mean()) if validp.any() else None,
                     "neg_mean":float(ns.mean()) if validn.any() else None,
                     "pos_better_rate":float(pos.loc[validp,better].mean()) if validp.any() else None,
                     "neg_better_rate":float(neg.loc[validn,better].mean()) if validn.any() else None}
        if feats[name]["pos_better_rate"] is not None and feats[name]["neg_better_rate"]:
            feats[name]["better_lift_ratio"]=feats[name]["pos_better_rate"]/feats[name]["neg_better_rate"]
    specs={
      "LOCAL_WR":q.local_better.eq(1)&q.wr_better.eq(1),
      "LOCAL_STRAIGHT":q.local_better.eq(1)&q.straight_better.eq(1),
      "LOCAL_TURN_STRAIGHT":q.local_better.eq(1)&q.turn_better.eq(1)&q.straight_better.eq(1),
      "LOCAL_EX_STRAIGHT":q.local_better.eq(1)&q.ex_better.eq(1)&q.straight_better.eq(1),
      "LOCAL_WR_STRAIGHT":q.local_better.eq(1)&q.wr_better.eq(1)&q.straight_better.eq(1),
      "LOCAL_WR_TURN_STRAIGHT":q.local_better.eq(1)&q.wr_better.eq(1)&q.turn_better.eq(1)&q.straight_better.eq(1),
      "FOOT3":q.foot_better_count.ge(3),
      "LOCAL_FOOT3":q.local_better.eq(1)&q.foot_better_count.ge(3)
    }
    rules={}
    for n,m in specs.items():
        g=q[m]
        rules[n]={"R":int(len(g)),"y5_R":int(g.y5.sum()),"rate":float(g.y5.mean()) if len(g) else None,
                  "lift_vs_base":float(g.y5.mean()/base) if len(g) else None,
                  "recall":float(g.y5.sum()/max(q.y5.sum(),1))}
    result={"population":"all DEV boat1 winners; broad 5-vs-4 static+exhibition mechanism",
            "R":int(len(q)),"positive_R":int(q.y5.sum()),"base_rate":base,
            "features":feats,"rules":rules,
            "coverage":{"tkz":int(q.ex_edge.notna().sum()),"stt":int(q.stx_edge.notna().sum()),
                        "lap":int(q.lap_edge.notna().sum()),"turn":int(q.turn_edge.notna().sum()),"straight":int(q.straight_edge.notna().sum())},
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_BROAD_EX_V23",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
