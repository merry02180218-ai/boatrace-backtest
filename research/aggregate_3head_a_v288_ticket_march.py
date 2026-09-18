from __future__ import annotations
import argparse
import json
from pathlib import Path
from collections import defaultdict

import pandas as pd

EXPECTED_A_RACES=52

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--out",default="research_3head_a_v288_ticket_march_summary.json")
    a=ap.parse_args()

    root=Path(a.root)
    summaries=[]
    replay_files=[]
    for p in root.rglob("day_summary.json"):
        try:
            z=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        summaries.append((p,z))
        q=p.with_name("day_replay.csv")
        if q.exists() and q.stat().st_size:
            replay_files.append(q)

    if not summaries:
        raise RuntimeError("no day summaries found")

    total={
        "pre_candidates":0,"live_evaluable":0,"input_or_decision_errors":0,
        "genuine_no_bets":0,"bets":0,"hits":0,"stake":0.0,"payout":0.0
    }
    days=[]
    for p,z in sorted(summaries,key=lambda x:x[1].get("date","")):
        for k in total:
            total[k]+=z.get(k,0) or 0
        days.append({
            "date":z.get("date"),
            "pre_candidates":z.get("pre_candidates"),
            "live_evaluable":z.get("live_evaluable"),
            "errors":z.get("input_or_decision_errors"),
            "no_bets":z.get("genuine_no_bets"),
            "bets":z.get("bets"),
            "hits":z.get("hits"),
            "stake":z.get("stake"),
            "payout":z.get("payout"),
            "roi":z.get("roi"),
        })

    route=defaultdict(lambda:{"bets":0,"hits":0,"stake":0.0,"payout":0.0})
    all_bets=[]
    for p in replay_files:
        df=pd.read_csv(p,low_memory=False)
        if "decision" not in df.columns:
            continue
        b=df[df.decision=="BET"].copy()
        for _,r in b.iterrows():
            rt=str(r.get("route",""))
            route[rt]["bets"]+=1
            route[rt]["hits"]+=int(r.get("hit",0) or 0)
            route[rt]["stake"]+=float(r.get("total_stake",0) or 0)
            route[rt]["payout"]+=float(r.get("return_yen",0) or 0)
            all_bets.append({
                "date":str(r.get("date","")),
                "race_code":str(r.get("race_code","")),
                "route":rt,
                "hit":int(r.get("hit",0) or 0),
                "stake":float(r.get("total_stake",0) or 0),
                "payout":float(r.get("return_yen",0) or 0),
                "comp_odds":None if pd.isna(r.get("comp_odds")) else float(r.get("comp_odds")),
                "top_n":None if pd.isna(r.get("top_n")) else int(r.get("top_n")),
            })

    for rt,z in route.items():
        z["roi"]=100*z["payout"]/z["stake"] if z["stake"] else None

    if int(total["pre_candidates"]) != EXPECTED_A_RACES:
        raise RuntimeError(
            f"A candidate coverage mismatch {total['pre_candidates']} != {EXPECTED_A_RACES}"
        )

    out={
        "policy":"3HEAD_A_PRECISION_V1_PLUS_V288_DOWNSTREAM_MARCH_AUDIT",
        "head_gate_source_run":35364404883,
        "head_gate_marker":"3HEAD_A_MARCH_PARITY_OK",
        "candidate_count_expected":EXPECTED_A_RACES,
        "candidate_count_replayed":int(total["pre_candidates"]),
        "live_evaluable":int(total["live_evaluable"]),
        "input_or_decision_errors":int(total["input_or_decision_errors"]),
        "genuine_no_bets":int(total["genuine_no_bets"]),
        "bets":int(total["bets"]),
        "hits":int(total["hits"]),
        "hit_rate_on_bets":total["hits"]/total["bets"] if total["bets"] else None,
        "head_gate_to_bet_rate":total["bets"]/EXPECTED_A_RACES,
        "stake":float(total["stake"]),
        "payout":float(total["payout"]),
        "profit":float(total["payout"]-total["stake"]),
        "roi":100*total["payout"]/total["stake"] if total["stake"] else None,
        "route_breakdown":dict(route),
        "days":days,
        "bets_detail":all_bets,
        "audit":{
            "march_head_gate_frozen_before_ticket_audit":True,
            "v288_thresholds_retuned_for_A":False,
            "target_results_used_for_decision":False,
            "settlement_joined_after_decisions":True,
            "odds_note":"historical closing snapshot where exact archived od3 is unavailable",
            "september_2026_outcomes_used":False,
        }
    }
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
