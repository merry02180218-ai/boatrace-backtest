#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import backtest as bt

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v11"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x);return v if np.isfinite(v) else np.nan
    except:return np.nan
def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file():return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def bycode(rows):return {str(r.get("レースコード","")).zfill(12):r for r in rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    x=pickle.load(a.prepared.open("rb"));rr=x["rows"];cache={};rows=[]
    for b in rr["H078_M375"]:
        code=str(b["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p=str(b.get("actual_combo","")).split("-")
        if len(p)!=3 or p[0]!="1":continue
        actual2=int(p[1]);day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cards=bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv"))
            waku=bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv"))
            res=bycode(load_csv(root,f"data/results/realtime/{ymd}.csv"))
            cache[day]=(cards,waku,res)
        cards,waku,res=cache[day]
        card=cards.get(code,{});w=waku.get(code,{});r=res.get(code,{})
        if not card or not r:continue
        xfeat=bt.race_features(card,w)
        # actual ST by boat
        bst={}
        for c in range(1,7):
            try:boat=int(float(r.get(f"{c}コース_艇番","")))
            except:continue
            bst[boat]=ff(r.get(f"{c}コース_スタートタイミング"))
        rec={"race_code":code,"month":m,"actual2":actual2}
        for cand,inner in ((4,3),(5,4)):
            c=xfeat[cand];i=xfeat[inner]
            rec[f"c{cand}_label"]=int(actual2==cand)
            rec[f"c{cand}_actual_st_edge"]=(bst.get(inner,np.nan)-bst.get(cand,np.nan)) if np.isfinite(bst.get(inner,np.nan)) and np.isfinite(bst.get(cand,np.nan)) else np.nan
            rec[f"c{cand}_actual_st_beats"]=int(np.isfinite(rec[f"c{cand}_actual_st_edge"]) and rec[f"c{cand}_actual_st_edge"]>0)
            # positive = candidate predicted faster / stronger
            rec[f"c{cand}_waku_st_edge"]=ff(i["waku_st"])-ff(c["waku_st"])
            rec[f"c{cand}_national_st_edge"]=ff(i["nst"])-ff(c["nst"])
            rec[f"c{cand}_waku_sr_edge"]=ff(i["waku_sr"])-ff(c["waku_sr"])
            rec[f"c{cand}_meet_st_edge"]=(ff(i["meet_st"])-ff(c["meet_st"])) if i["meet_st"] is not None and c["meet_st"] is not None else np.nan
            rec[f"c{cand}_motor2_edge"]=ff(c["motor2"])-ff(i["motor2"])
            rec[f"c{cand}_motor3_edge"]=ff(c["motor3"])-ff(i["motor3"])
            rec[f"c{cand}_wr_edge"]=ff(c["wr"])-ff(i["wr"])
            rec[f"c{cand}_local_edge"]=ff(c["local"])-ff(i["local"])
            rec[f"c{cand}_pastwin_edge"]=ff(c["past_win"])-ff(i["past_win"])
            for met in ("score","core","ex","st","straight","avg"):
                cv=ff(b.get(f"{met}{cand}"));iv=ff(b.get(f"{met}{inner}"))
                rec[f"c{cand}_{met}_edge"]=cv-iv if np.isfinite(cv) and np.isfinite(iv) else np.nan
        rows.append(rec)
    q=pd.DataFrame(rows);q.to_csv(OUT/"rows.csv",index=False)
    summary={}
    for cand in (4,5):
        pos=q[q[f"c{cand}_label"].eq(1)];neg=q[q[f"c{cand}_label"].eq(0)]
        d={"R":int(len(q)),"positive_R":int(len(pos)),
           "actual_st_beats_inner_pos":int(pos[f"c{cand}_actual_st_beats"].sum()),
           "actual_st_beats_inner_pos_rate":float(pos[f"c{cand}_actual_st_beats"].mean())}
        for feat in ("waku_st","national_st","waku_sr","meet_st","motor2","motor3","wr","local","pastwin","score","core","ex","st","straight","avg"):
            col=f"c{cand}_{feat}_edge"
            ps=pd.to_numeric(pos[col],errors="coerce");ns=pd.to_numeric(neg[col],errors="coerce")
            d[feat]={"pos_R":int(ps.notna().sum()),"pos_mean":float(ps.mean()) if ps.notna().any() else None,
                     "pos_positive_rate":float((ps>0).mean()) if ps.notna().any() else None,
                     "neg_mean":float(ns.mean()) if ns.notna().any() else None,
                     "neg_positive_rate":float((ns>0).mean()) if ns.notna().any() else None}
        # How well pre-race ST proxies predict the sign of actual ST edge.
        valid=q[pd.to_numeric(q[f"c{cand}_actual_st_edge"],errors="coerce").notna()].copy()
        for feat in ("waku_st","national_st","waku_sr","meet_st","st"):
            col=f"c{cand}_{feat}_edge";v=valid[pd.to_numeric(valid[col],errors="coerce").notna()]
            if len(v):
                actual=(v[f"c{cand}_actual_st_edge"]>0);pred=(v[col]>0)
                d[f"{feat}_actualST_sign_accuracy"]=float((actual==pred).mean())
        summary[str(cand)]=d
    result={"population":"DEV head1 wins; can pre-race ST/history explain 4/5 second actual ST edge?",
            "candidates":summary,"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_ST_PROXY_V11",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
