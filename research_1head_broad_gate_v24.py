#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,pickle
from pathlib import Path
import numpy as np
import pandas as pd
import backtest as bt
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365
import onehead_production_profile as prod

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)
TURN_CORR={4:-0.10,5:-0.20}
STRAIGHT_CORR={4:0.0,5:0.0}
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v24"
OUT.mkdir(parents=True,exist_ok=True)

def ff(x):
    try:
        v=float(x);return v if np.isfinite(v) else np.nan
    except:return np.nan
def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file():return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def bycode(rs):return {str(r.get("レースコード","")).zfill(12):r for r in rs}
def orig(row,b):
    vals={"turn":np.nan,"straight":np.nan}
    for i in (1,2,3):
        lab=str(row.get(f"計測項目{i}",""))
        v=ff(row.get(f"艇{b}_値{i}"))
        if "まわり" in lab or "回り" in lab:vals["turn"]=v
        elif "直線" in lab:vals["straight"]=v
    return vals

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    root=os.environ["BOATRACECSV_LOCAL_ROOT"]
    pred=pd.read_csv("analysis_v308_1head_volume_opponent_joint_pred.csv",dtype={"race_code":str})
    pred.race_code=pred.race_code.astype(str).str.zfill(12)
    pred=pred[pred.month.isin(DEV)&pred.actual_combo.fillna("").astype(str).str.startswith("1-")].copy()
    cache={};feat={}
    for _,r in pred.iterrows():
        code=str(r.race_code).zfill(12);day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")),
                        bycode(load_csv(root,f"data/previews/original_exhibition/{ymd}.csv")),
                        bycode(load_csv(root,f"data/results/payouts/{ymd}.csv")))
        cards,waku,origm,pays=cache[day];card=cards.get(code,{});w=waku.get(code,{})
        if not card:continue
        xf=bt.race_features(card,w);o=origm.get(code,{})
        o4,o5=orig(o,4),orig(o,5)
        turn=(o4["turn"]+TURN_CORR[4])-(o5["turn"]+TURN_CORR[5]) if np.isfinite(o4["turn"]) and np.isfinite(o5["turn"]) else np.nan
        straight=(o4["straight"]+STRAIGHT_CORR[4])-(o5["straight"]+STRAIGHT_CORR[5]) if np.isfinite(o4["straight"]) and np.isfinite(o5["straight"]) else np.nan
        feat[code]={"month":str(r.month),"actual2":int(str(r.actual_combo).split("-")[1]),
                    "local":ff(xf[5]["local"])-ff(xf[4]["local"]),
                    "wr":ff(xf[5]["wr"])-ff(xf[4]["wr"]),
                    "turn":turn,"straight":straight,
                    "payout":int(float(pays.get(code,{}).get("3連単_払戻金") or 0))}
    bf=pd.DataFrame([{"race_code":k,**v} for k,v in feat.items()])
    bf["rule"]=(bf.local>0)&(bf.wr>0)&(bf.turn>0)&(bf.straight>0)
    broad_monthly=[]
    for m,g in bf.groupby("month"):
        h=g[g.rule]
        broad_monthly.append({"month":m,"R":len(g),"y5":int((g.actual2==5).sum()),
                              "rule_R":len(h),"rule_y5":int((h.actual2==5).sum()),
                              "rule_rate":float((h.actual2==5).mean()) if len(h) else None})
    # H078 exact3 evaluation
    x=pickle.load(a.prepared.open("rb"));rows=[]
    for r in x["rows"]["H078_M375"]:
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV or code not in feat:continue
        p2,pc=v365.formal_post_five6(r);prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3];base=[f"1-{s}-{t}" for s,t in formal]
        p2order=sorted(BOATS,key=lambda b:p2[b],reverse=True);ratio=float(p2[5])/max(float(p2[p2order[1]]),1e-12)
        th=sorted([t for t in BOATS if t!=5],key=lambda t:(-float(pc[(5,t)]),t))
        actual=str(r.get("actual_combo",""));f=feat[code]
        for label,fire in [
          ("BROAD4",bool(f["local"]>0 and f["wr"]>0 and f["turn"]>0 and f["straight"]>0)),
          ("BROAD4_P2",bool(f["local"]>0 and f["wr"]>0 and f["turn"]>0 and f["straight"]>0 and ratio>=.25))
        ]:
            extras=[]
            if fire and not any(s==5 for s,t in formal):
                for t in th[:2]:
                    xx=f"1-5-{t}"
                    if xx not in base:extras.append(xx)
            tickets=base+extras
            rows.append({"race_code":code,"month":m,"variant":label,"formal_hit":int(actual in base),
                         "new_hit":int(actual in tickets),"fire":int(fire),"extra_count":len(extras),
                         "payout":f["payout"],"ratio":ratio})
    q=pd.DataFrame(rows)
    variants={}
    for label,g in q.groupby("variant"):
        bs=len(g)*300;ns=bs+int(g.extra_count.sum())*100
        br=int(g.loc[g.formal_hit.eq(1),"payout"].sum());nr=int(g.loc[g.new_hit.eq(1),"payout"].sum())
        variants[label]={"R":len(g),"baseline_hits":int(g.formal_hit.sum()),"hits":int(g.new_hit.sum()),
                         "rescued":int(((g.formal_hit==0)&(g.new_hit==1)).sum()),
                         "fires":int(g.fire.sum()),"extra_tickets":int(g.extra_count.sum()),
                         "baseline_roi":br/bs,"roi":nr/ns,"baseline_return":br,"return":nr}
    result={"broad_rule":"local5>4 & wr5>4 & corrected turn5>4 & corrected straight5>4",
            "broad_monthly":broad_monthly,"h078_variants":variants,
            "support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    bf.to_csv(OUT/"broad_rows.csv",index=False);q.to_csv(OUT/"h078_rows.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_BROAD_GATE_V24",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
