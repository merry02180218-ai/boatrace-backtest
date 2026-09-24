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
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"1head-mechanism-discovery-v20"
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

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);a=ap.parse_args()
    root=os.environ["BOATRACECSV_LOCAL_ROOT"];x=pickle.load(a.prepared.open("rb"));rr=x["rows"];cache={};rows=[]
    for r in rr["H078_M375"]:
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p2,pc=v365.formal_post_five6(r);prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3];actual=str(r.get("actual_combo",""))
        p2order=sorted(BOATS,key=lambda b:p2[b],reverse=True)
        day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(root,f"data/programs/waku10/{ymd}.csv")),
                        bycode(load_csv(root,f"data/results/payouts/{ymd}.csv")))
        card=cache[day][0].get(code,{});w=cache[day][1].get(code,{});pay=cache[day][2].get(code,{})
        if not card:continue
        xf=bt.race_features(card,w)
        local_edge=ff(xf[5]["local"])-ff(xf[4]["local"])
        straight_edge=ff(r.get("straight5"))-ff(r.get("straight4"))
        core_edge=ff(r.get("core5"))-ff(r.get("core4"))
        ratio=float(p2[5])/max(float(p2[p2order[1]]),1e-12)
        c5_already=any(s==5 for s,t in formal)
        fire=bool(local_edge>0 and straight_edge>0 and core_edge>0 and ratio>=.25 and not c5_already)
        th=sorted([t for t in BOATS if t!=5],key=lambda t:(-float(pc[(5,t)]),t))
        base=[f"1-{s}-{t}" for s,t in formal];extras=[]
        if fire:
            for t in th[:2]:
                xx=f"1-5-{t}"
                if xx not in base:extras.append(xx)
        tickets=base+extras
        payout=int(float(pay.get("3連単_払戻金") or 0))
        rows.append({"race_code":code,"month":m,"actual_combo":actual,"fire":int(fire),"ratio":ratio,
                     "local_edge":local_edge,"straight_edge":straight_edge,"core_edge":core_edge,
                     "formal_hit":int(actual in base),"new_hit":int(actual in tickets),
                     "extra_count":len(extras),"extras":";".join(extras),"payout":payout})
    q=pd.DataFrame(rows)
    if len(q)!=190 or int(q.formal_hit.sum())!=98:raise RuntimeError("sentinel drift")
    base_stake=190*300;new_stake=base_stake+int(q.extra_count.sum())*100
    base_ret=int(q.loc[q.formal_hit.eq(1),"payout"].sum());new_ret=int(q.loc[q.new_hit.eq(1),"payout"].sum())
    monthly=[]
    for m,g in q.groupby("month"):
        bs=len(g)*300;ns=bs+int(g.extra_count.sum())*100
        br=int(g.loc[g.formal_hit.eq(1),"payout"].sum());nr=int(g.loc[g.new_hit.eq(1),"payout"].sum())
        monthly.append({"month":m,"R":len(g),"fires":int(g.fire.sum()),"extra_tickets":int(g.extra_count.sum()),
                        "baseline_hits":int(g.formal_hit.sum()),"new_hits":int(g.new_hit.sum()),
                        "rescued":int(((g.formal_hit==0)&(g.new_hit==1)).sum()),
                        "baseline_roi":br/bs,"new_roi":nr/ns,"baseline_return":br,"new_return":nr})
    result={"rule":"fixed: local5>4 & straight5>4 & core5>4 & p2ratio>=0.25; add conditional top2 as extra tickets",
            "baseline":{"R":190,"hits":98,"stake":base_stake,"return":base_ret,"roi":base_ret/base_stake},
            "fixed":{"hits":int(q.new_hit.sum()),"stake":new_stake,"return":new_ret,"roi":new_ret/new_stake,
                     "fires":int(q.fire.sum()),"extra_tickets":int(q.extra_count.sum()),
                     "rescued":int(((q.formal_hit==0)&(q.new_hit==1)).sum())},
            "delta_hits":int(q.new_hit.sum()-98),"delta_roi_pp":100*(new_ret/new_stake-base_ret/base_stake),
            "monthly":monthly,"support_outcomes_read":False,"september_outcomes_read":False,"production_changed":False}
    q.to_csv(OUT/"rows.csv",index=False);pd.DataFrame(monthly).to_csv(OUT/"monthly.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print("DEV_1HEAD_FIXED_FIVE_V20",json.dumps(result,ensure_ascii=False))
if __name__=="__main__":main()
