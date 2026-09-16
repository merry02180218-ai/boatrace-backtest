#!/usr/bin/env python3
"""4HEAD production market runner with approved v283 THIRD close-margin 0.10 expansion.

Production change from HEAD4_V291_COMP7:
- keep frozen v283 base Top4;
- for each of the frozen Top2 SECOND branches, if conditional THIRD
  P(rank2|second) - P(rank3|second) <= 0.10, append that branch's rank3 THIRD;
- therefore production ticket count is 4..6, with duplicates removed.

Everything else stays frozen: S thresholds, v283 SECOND, alpha2=.60, comp>=7,
pre-deadline official odds only, JPY10,000 Dutch, v96 prohibited, fail closed.
No result/payout endpoint is used here.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Mapping, Sequence, Tuple, Dict, List

import numpy as np
import run_20260911_4head_v291_live as base

POLICY = "HEAD4_V291_COMP7_THIRD010"
THIRD_GAP = 0.10
MIN_TICKETS = 4
MAX_TICKETS = 6

# Re-export frozen constants/helpers used by downstream code/verifier.
BOATS = base.BOATS
PRE_CUT = base.PRE_CUT
POST_CUT = base.POST_CUT
ENV_ENTRY_CUT = base.ENV_ENTRY_CUT
COMP_CUT = base.COMP_CUT
BANK = base.BANK
ALPHA2 = base.ALPHA2
PAIR_MODE = base.PAIR_MODE
DEFAULT_AUDIT = "live_audit_4head_v291_third010.jsonl"
now_jst = base.now_jst
parse_deadline = base.parse_deadline
require_before_deadline = base.require_before_deadline
parse_p2 = base.parse_p2
parse_cond = base.parse_cond
fetch_odds = base.fetch_odds
s_eligible = base.s_eligible
persist_audit = base.persist_audit


def production_tickets(p2: Mapping[int, float], pc: Mapping[Tuple[int, int], float]) -> List[str]:
    """Frozen v283 Top4 plus approved per-SECOND THIRD rank3 close-margin additions."""
    tickets = list(base.v283_top4(p2, pc))
    second_rank = sorted(BOATS, key=lambda s: (-float(p2[s]), s))
    for s in second_rank[:2]:
        thirds = sorted((t for t in BOATS if t != s), key=lambda t: (-float(pc[(s, t)]), t))
        gap23 = float(pc[(s, thirds[1])]) - float(pc[(s, thirds[2])])
        if gap23 <= THIRD_GAP:
            extra = f"4-{s}-{thirds[2]}"
            if extra not in tickets:
                tickets.append(extra)
    if not (MIN_TICKETS <= len(tickets) <= MAX_TICKETS):
        raise RuntimeError(f"THIRD010 ticket-count invariant failed: {len(tickets)}")
    if len(set(tickets)) != len(tickets) or any(not x.startswith("4-") for x in tickets):
        raise RuntimeError("THIRD010 ticket invariant failed")
    return tickets


def composite_odds(odds: Sequence[float]) -> float:
    if not (MIN_TICKETS <= len(odds) <= MAX_TICKETS):
        raise RuntimeError(f"THIRD010 requires {MIN_TICKETS}..{MAX_TICKETS} odds")
    vals = [base._as_float(x, "odds") for x in odds]
    if any(x <= 0 for x in vals):
        raise RuntimeError("odds must be positive")
    return 1.0 / sum(1.0 / x for x in vals)


def dutch(tickets: Sequence[str], odds: Sequence[float]) -> List[dict]:
    if len(tickets) != len(odds) or not (MIN_TICKETS <= len(tickets) <= MAX_TICKETS):
        raise RuntimeError("THIRD010 Dutch ticket-count mismatch")
    stakes = np.asarray(base.v234.v205.round_dutch(list(odds), BANK), dtype=int)
    if int(stakes.sum()) != BANK:
        raise RuntimeError(f"Dutch total != {BANK}")
    if np.any(stakes % 100 != 0) or np.any(stakes <= 0):
        raise RuntimeError("Dutch stakes must all be positive 100-yen multiples")
    return [{"combo": t, "odds": float(o), "stake": int(s)} for t, o, s in zip(tickets, odds, stakes)]


def evaluate_market(inp: dict, odds_map: Mapping[str, float], odds_meta: dict, deadline) -> dict:
    race_code = str(inp["race_code"]).zfill(12)
    pre = base._as_float(inp["PRE"], "PRE")
    post = base._as_float(inp["POST"], "POST")
    env = base._as_float(inp["ENV_ENTRY"], "ENV_ENTRY")
    if not s_eligible(pre, post, env):
        return {
            "race_code": race_code, "policy": POLICY, "layer": "S", "eligible": False,
            "decision": "NO_BET", "reason": "S_GATE_FAIL",
            "scores": {"PRE": pre, "POST": post, "ENV_ENTRY": env},
            "thresholds": {"PRE": PRE_CUT, "POST": POST_CUT, "ENV_ENTRY": ENV_ENTRY_CUT},
            "tickets": [], "total_stake": 0, "result_or_payout_used": False,
        }
    p2 = parse_p2(inp["p2"])
    pc = parse_cond(inp["cond"])
    tickets = production_tickets(p2, pc)
    vals = [base._as_float(odds_map[t], f"odds[{t}]") for t in tickets]
    comp = composite_odds(vals)
    bet = comp >= COMP_CUT
    ticket_rows = dutch(tickets, vals) if bet else [
        {"combo": t, "odds": float(o), "stake": 0} for t, o in zip(tickets, vals)
    ]
    decision_time = require_before_deadline(deadline, "before decision persist")
    return {
        "race_code": race_code, "policy": POLICY, "layer": "S", "eligible": True,
        "pair_model": {
            "branch": "v283 independent + THIRD close-margin",
            "mode": PAIR_MODE, "alpha2": ALPHA2, "third_gap": THIRD_GAP,
            "base_top4_preserved": True, "v96_used": False,
        },
        "scores": {"PRE": pre, "POST": post, "ENV_ENTRY": env},
        "thresholds": {"PRE": PRE_CUT, "POST": POST_CUT, "ENV_ENTRY": ENV_ENTRY_CUT},
        "ordered_tickets": tickets, "ticket_count": len(tickets),
        "composite_odds": float(comp), "composite_cut": COMP_CUT,
        "decision": "BET" if bet else "PASS", "tickets": ticket_rows,
        "total_stake": int(sum(x["stake"] for x in ticket_rows)),
        "snapshot_timestamp_jst": odds_meta.get("fetched_at_jst"),
        "decision_time_jst": decision_time.isoformat(), "deadline_jst": deadline.isoformat(),
        "deadline_state": "LIVE_FROZEN_BEFORE_DEADLINE", "odds_snapshot": odds_meta,
        "result_or_payout_used": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-json", required=True)
    ap.add_argument("--jcd", type=int, required=True)
    ap.add_argument("--race", type=int, required=True)
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--deadline-jst", required=True)
    ap.add_argument("--audit", default=DEFAULT_AUDIT)
    args = ap.parse_args()
    t0 = time.perf_counter()
    deadline = parse_deadline(args.deadline_jst)
    try:
        require_before_deadline(deadline, "startup")
        with open(args.input_json, "r", encoding="utf-8") as f:
            inp = json.load(f)
        expected = f"{args.date}{args.jcd:02d}{args.race:02d}"
        if str(inp.get("race_code", "")).zfill(12) != expected:
            raise RuntimeError(f"race_code mismatch: input={inp.get('race_code')} cli={expected}")
        pre = base._as_float(inp["PRE"], "PRE")
        post = base._as_float(inp["POST"], "POST")
        env = base._as_float(inp["ENV_ENTRY"], "ENV_ENTRY")
        if not s_eligible(pre, post, env):
            row = evaluate_market(inp, {}, {}, deadline)
            row["decision_time_jst"] = require_before_deadline(deadline, "before decision persist").isoformat()
            row["deadline_jst"] = deadline.isoformat()
            row["deadline_state"] = "LIVE_FROZEN_BEFORE_DEADLINE"
            row["seconds"] = time.perf_counter() - t0
            persist_audit(args.audit, row)
            print(json.dumps(row, ensure_ascii=False, indent=2))
            return
        odds, meta = fetch_odds(args.date, args.jcd, args.race, deadline)
        row = evaluate_market(inp, odds, meta, deadline)
        row["decision_time_jst"] = require_before_deadline(deadline, "immediately before audit append").isoformat()
        row["seconds"] = time.perf_counter() - t0
        persist_audit(args.audit, row)
        print(json.dumps(row, ensure_ascii=False, indent=2))
    except Exception as e:
        err = {
            "policy": POLICY, "decision": "ERROR_NO_BET", "error": str(e),
            "deadline_jst": deadline.isoformat(), "now_jst": now_jst().isoformat(),
            "result_or_payout_used": False, "seconds": time.perf_counter() - t0,
        }
        print(json.dumps(err, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
