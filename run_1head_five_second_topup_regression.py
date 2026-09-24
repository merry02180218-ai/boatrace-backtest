#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,pickle
from pathlib import Path
import numpy as np

import backtest as bt
import onehead_five_second_topup as topup
import onehead_production_profile as prod
import run_v299_1head_trifecta3_policy_search as v299
import run_v365_1head_exact3_hit_push as v365

DEV=("2026-02","2026-03","2026-04","2026-05","2026-06")
BOATS=(2,3,4,5,6)

def ff(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except Exception:
        return np.nan

def load_csv(root,rel):
    p=Path(root)/rel
    if not p.is_file(): return []
    with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def bycode(rows): return {str(r.get("レースコード","")).zfill(12):r for r in rows}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--prepared",required=True,type=Path);ap.add_argument("--csv-root",required=True);a=ap.parse_args()
    x=pickle.load(a.prepared.open("rb"));cache={};R=hits=fires=extras_n=ret=0
    rows=x["rows"]["H078_M375"]
    for r in rows:
        code=str(r["race_code"]).zfill(12);m=code[:4]+"-"+code[4:6]
        if m not in DEV:continue
        p2,pc=v365.formal_post_five6(r);prob=v299.pair_prob(p2,pc,prod.TICKET_ALPHA)
        formal=v299.STRATEGIES["HYBRID"](p2,pc,prob)[:3];base=[f"1-{s}-{t}" for s,t in formal]
        day=code[:8]
        if day not in cache:
            ymd=f"{day[:4]}/{day[4:6]}/{day[6:8]}"
            cache[day]=(bycode(load_csv(a.csv_root,f"data/programs/race_cards/{ymd}.csv")),
                        bycode(load_csv(a.csv_root,f"data/programs/waku10/{ymd}.csv")),
                        bycode(load_csv(a.csv_root,f"data/results/payouts/{ymd}.csv")))
        card=cache[day][0].get(code,{});w=cache[day][1].get(code,{});pay=cache[day][2].get(code,{})
        if not card:raise RuntimeError(f"missing card {code}")
        xf=bt.race_features(card,w)
        local_edge=ff(xf[5]["local"])-ff(xf[4]["local"])
        straight_edge=ff(r.get("straight5"))-ff(r.get("straight4"))
        core_edge=ff(r.get("core5"))-ff(r.get("core4"))
        meta=topup.regime_meta(p2,local_edge,straight_edge,core_edge,prod.FIVE_SECOND_TOPUP_P2_RATIO_MIN)
        fire=bool(meta["applied"])
        ex=topup.extra_tickets(pc,base,prod.FIVE_SECOND_TOPUP_EXTRA_TICKETS) if fire else []
        actual=str(r.get("actual_combo",""));tickets=base+ex
        payout=int(float(pay.get("3連単_払戻金") or 0))
        R+=1;fires+=int(fire);extras_n+=len(ex)
        hit=int(actual in tickets);hits+=hit;ret+=payout if hit else 0
    stake=R*300+extras_n*prod.FIVE_SECOND_TOPUP_STAKE_YEN_PER_TICKET
    got={"R":R,"fires":fires,"extra_tickets":extras_n,"hits":hits,"stake":stake,"return":ret,"roi":ret/stake}
    expected={"R":190,"fires":21,"extra_tickets":63,"hits":102,"stake":63300,"return":84280}
    for k,v in expected.items():
        if got[k]!=v:raise RuntimeError(f"topup regression drift {k}: expected={v} got={got[k]} all={got}")
    print("PROD_1HEAD_FIVE_TOPUP_REGRESSION",json.dumps(got,ensure_ascii=False))

if __name__=="__main__":main()
