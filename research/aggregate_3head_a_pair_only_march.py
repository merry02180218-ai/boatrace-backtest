from __future__ import annotations
import argparse, json
from pathlib import Path
from collections import defaultdict
import pandas as pd

EXPECTED=52

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);ap.add_argument("--out",default="research_3head_a_pair_only_march_summary.json");a=ap.parse_args()
    root=Path(a.root)
    summaries=[]; replay=[]
    for p in root.rglob("day_summary.json"):
        try:z=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        summaries.append(z)
        q=p.with_name("day_replay.csv")
        if q.exists() and q.stat().st_size:replay.append(q)
    if not summaries:raise RuntimeError("no day summaries")
    keys=["pre_candidates","live_evaluable","input_or_decision_errors","genuine_no_bets","bets","hits","stake","payout"]
    total={k:0 for k in keys}
    for z in summaries:
        for k in keys: total[k]+=z.get(k,0) or 0
    if int(total["pre_candidates"])!=EXPECTED:raise RuntimeError(f"coverage {total['pre_candidates']} != {EXPECTED}")
    frames=[pd.read_csv(p,low_memory=False) for p in replay]
    df=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
    if not df.empty:
        df["head3_actual"]=df["actual_combo"].astype(str).str.startswith("3-")
        bets=df[df.decision=="BET"].copy()
        nob=df[(df.evaluation_status=="EVALUABLE")&(df.decision=="NO_BET")].copy()
        errs=df[df.evaluation_status!="EVALUABLE"].copy()
        bet_head=int(bets.head3_actual.sum()); no_head=int(nob.head3_actual.sum())
        head_capture=bet_head/int(df.head3_actual.sum()) if int(df.head3_actual.sum()) else None
        detail_cols=["date","race_code","actual_combo","head3_actual","hit","return_yen","top_n","comp_odds","route","purchase_gate_value","purchase_gate_pass"]
        detail=bets.reindex(columns=detail_cols).to_dict("records")
        errors=errs[["date","race_code","error_type","error","actual_combo","head3_actual"]].to_dict("records")
    else:
        bet_head=no_head=0;head_capture=None;detail=[];errors=[]
    out={
      "policy":"3HEAD_A_PRECISION_V1_PAIR_ONLY_MARCH_DIAGNOSTIC",
      "diagnostic_only":True,
      "march_already_open":True,
      "head_gate_changed":False,
      "v288_sab_gate_used":False,
      "pair_ranking":"existing_v288_pair_model",
      "ticket_count":"existing_v242_choose_n_5_to_10",
      "staking":"exact_10000_yen_dutch",
      "candidate_count":int(total["pre_candidates"]),
      "live_evaluable":int(total["live_evaluable"]),
      "errors":int(total["input_or_decision_errors"]),
      "no_bets":int(total["genuine_no_bets"]),
      "bets":int(total["bets"]),
      "hits":int(total["hits"]),
      "ticket_hit_rate":total["hits"]/total["bets"] if total["bets"] else None,
      "stake":float(total["stake"]),
      "payout":float(total["payout"]),
      "profit":float(total["payout"]-total["stake"]),
      "roi":100*total["payout"]/total["stake"] if total["stake"] else None,
      "bet_head3_count":bet_head,
      "bet_head3_rate":bet_head/total["bets"] if total["bets"] else None,
      "no_bet_head3_count":no_head,
      "head_winner_capture_rate_by_bets":head_capture,
      "bets_detail":detail,
      "error_detail":errors,
      "september_2026_outcomes_used":False,
    }
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
if __name__=="__main__":main()
