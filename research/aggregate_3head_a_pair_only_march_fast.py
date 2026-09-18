from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

TOTAL_A=52
TOTAL_EVALUABLE=50
TOTAL_ERRORS=2
TOTAL_PAIR_ONLY_BETS=42
TOTAL_PAIR_ONLY_NO_BETS=8
STAKE_PER_BET=10000

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);ap.add_argument("--out",default="research_3head_a_pair_only_march_fast_summary.json");a=ap.parse_args()
    frames=[]
    for p in Path(a.root).rglob("day_replay.csv"):
        try:frames.append(pd.read_csv(p,low_memory=False))
        except Exception:pass
    if not frames:raise RuntimeError("no replay rows")
    df=pd.concat(frames,ignore_index=True)
    bets=df[(df.evaluation_status=="EVALUABLE")&(df.decision=="BET")].copy()
    # The workflow intentionally replays every date containing a head3 winner
    # among pair-only BETs. Omitted pair-only BETs are known head3 losses and
    # therefore have exactly zero return for any 3-headed ticket set.
    bets["head3_actual"]=bets.actual_combo.astype(str).str.startswith("3-")
    included_head=int(bets.head3_actual.sum())
    hits=int(bets.hit.sum())
    payout=float(bets.return_yen.sum())
    included_bets=int(len(bets))
    omitted_zero_return_bets=TOTAL_PAIR_ONLY_BETS-included_bets
    if omitted_zero_return_bets<0:raise RuntimeError("included bets exceed frozen total")
    if included_head!=16:raise RuntimeError(f"head-winner coverage mismatch {included_head} != 16")
    stake=TOTAL_PAIR_ONLY_BETS*STAKE_PER_BET
    out={
      "policy":"3HEAD_A_PRECISION_V1_PAIR_ONLY_MARCH_DIAGNOSTIC_FAST_EXACT",
      "diagnostic_only":True,
      "march_already_open":True,
      "exact_shortcut":True,
      "shortcut_reason":"omitted pair-only BET races have actual winner != 3, so any 3-headed ticket return is exactly zero",
      "candidate_count":TOTAL_A,
      "live_evaluable":TOTAL_EVALUABLE,
      "errors":TOTAL_ERRORS,
      "pair_only_bets":TOTAL_PAIR_ONLY_BETS,
      "pair_only_no_bets":TOTAL_PAIR_ONLY_NO_BETS,
      "included_replayed_bets":included_bets,
      "omitted_known_zero_return_bets":omitted_zero_return_bets,
      "head3_winners_among_pair_only_bets":included_head,
      "ticket_hits":hits,
      "ticket_hit_rate":hits/TOTAL_PAIR_ONLY_BETS,
      "pair_capture_given_head3":hits/included_head,
      "stake":stake,
      "payout":payout,
      "profit":payout-stake,
      "roi":100*payout/stake,
      "september_2026_outcomes_used":False,
    }
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
