#!/usr/bin/env python3
"""HEAD4_V291_COMP7 live market/ticket runner.

This runner intentionally consumes only already-frozen pre-result model outputs:
- S-layer scores: PRE, POST, ENV_ENTRY
- independent v282/v283 opponent probabilities: P2 and P3(third|second)

It then performs the production-critical market path:
  frozen S gate -> frozen v283 TOP2XTOP2 Top4 -> immutable official odds3t
  snapshot before deadline -> composite >= 7.0 -> exact JPY10,000 Dutch
  -> persist BET/PASS audit row before any result exists.

No result or payout endpoint is requested. No v96 input/fallback is accepted.
A-layer is deliberately not enabled here until its final LIVE A_SCORE artifact and
OOF-semantics mapping are frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

import analyze_v234_3head_waku10_restored_replay as v234
import fetch_live_trifecta_odds as live

JST = timezone(timedelta(hours=9))
POLICY = "HEAD4_V291_COMP7"
HEAD = 4
BOATS = (1, 2, 3, 5, 6)
PRE_CUT = 0.28
POST_CUT = 0.25
ENV_ENTRY_CUT = 0.224790
COMP_CUT = 7.0
BANK = 10000
TOP_N = 4
ALPHA2 = 0.60
PAIR_MODE = "TOP2XTOP2"
DEFAULT_AUDIT = "live_audit_4head_v291.jsonl"


def now_jst() -> datetime:
    return datetime.now(JST)


def parse_deadline(s: str) -> datetime:
    if not s:
        raise RuntimeError("--deadline-jst is required for LIVE betting operation")
    dl = datetime.fromisoformat(s)
    if dl.tzinfo is None:
        dl = dl.replace(tzinfo=JST)
    return dl.astimezone(JST)


def require_before_deadline(deadline: datetime, stage: str) -> datetime:
    now = now_jst()
    if now >= deadline:
        raise RuntimeError(
            f"deadline passed at {stage}: now={now.isoformat()} deadline={deadline.isoformat()}"
        )
    return now


def _as_float(x, name: str) -> float:
    try:
        v = float(x)
    except Exception as e:
        raise RuntimeError(f"invalid {name}: {x!r}") from e
    if not math.isfinite(v):
        raise RuntimeError(f"invalid {name}: {x!r}")
    return v


def parse_p2(obj) -> Dict[int, float]:
    if isinstance(obj, str):
        out = {int(k): _as_float(v, f"p2[{k}]") for k, v in (x.split(":", 1) for x in obj.split("|"))}
    elif isinstance(obj, Mapping):
        out = {int(k): _as_float(v, f"p2[{k}]") for k, v in obj.items()}
    else:
        raise RuntimeError("p2 must be mapping or v282 pipe string")
    if set(out) != set(BOATS):
        raise RuntimeError(f"p2 boats must be exactly {BOATS}; got {sorted(out)}")
    if any(v < 0 for v in out.values()) or sum(out.values()) <= 0:
        raise RuntimeError("p2 probabilities invalid")
    return out


def parse_cond(obj) -> Dict[Tuple[int, int], float]:
    out: Dict[Tuple[int, int], float] = {}
    if isinstance(obj, str):
        for x in obj.split("|"):
            pair, val = x.split(":", 1)
            s, t = pair.split(">", 1)
            out[(int(s), int(t))] = _as_float(val, f"cond[{pair}]")
    elif isinstance(obj, Mapping):
        for k, val in obj.items():
            if isinstance(k, str):
                sep = ">" if ">" in k else "-"
                s, t = k.split(sep, 1)
                key = (int(s), int(t))
            else:
                key = tuple(k)
            out[(int(key[0]), int(key[1]))] = _as_float(val, f"cond[{k}]")
    else:
        raise RuntimeError("cond must be mapping or v282 pipe string")
    exp = {(s, t) for s in BOATS for t in BOATS if s != t}
    if set(out) != exp:
        raise RuntimeError(f"conditional probability pairs incomplete: {len(out)}/{len(exp)}")
    if any(v < 0 for v in out.values()):
        raise RuntimeError("conditional probabilities invalid")
    return out


def _joint_order(p2: Mapping[int, float], pc: Mapping[Tuple[int, int], float]) -> List[Tuple[int, int]]:
    rows = []
    for s in BOATS:
        for t in BOATS:
            if s == t:
                continue
            score = ALPHA2 * math.log(max(p2[s], 1e-12)) + (1.0 - ALPHA2) * math.log(max(pc[(s, t)], 1e-12))
            rows.append((score, s, t))
    rows.sort(key=lambda x: (-x[0], x[1], x[2]))
    return [(s, t) for _, s, t in rows]


def v283_top4(p2: Mapping[int, float], pc: Mapping[Tuple[int, int], float]) -> List[str]:
    """Exact frozen v283 TOP2XTOP2 ordering, alpha2=.60, first 4 only."""
    base = _joint_order(p2, pc)
    second_rank = sorted(BOATS, key=lambda s: (-p2[s], s))
    cond_rank = {
        s: sorted([t for t in BOATS if t != s], key=lambda t: (-pc[(s, t)], t))
        for s in BOATS
    }
    s1, s2 = second_rank[:2]
    pool = [(s, cond_rank[s][k]) for k in (0, 1) for s in (s1, s2)]
    pool.sort(key=lambda x: base.index(x))
    tickets = [f"4-{s}-{t}" for s, t in pool]
    if len(tickets) != TOP_N or len(set(tickets)) != TOP_N:
        raise RuntimeError("v283 Top4 invariant failed")
    if any(not x.startswith("4-") for x in tickets):
        raise RuntimeError("head invariant failed")
    return tickets


def composite_odds(odds: Sequence[float]) -> float:
    if len(odds) != TOP_N:
        raise RuntimeError(f"v291 requires exactly {TOP_N} odds")
    vals = [_as_float(x, "odds") for x in odds]
    if any(x <= 0 for x in vals):
        raise RuntimeError("odds must be positive")
    return 1.0 / sum(1.0 / x for x in vals)


def dutch(tickets: Sequence[str], odds: Sequence[float]) -> List[dict]:
    if len(tickets) != TOP_N or len(odds) != TOP_N:
        raise RuntimeError("v291 Dutch requires exactly four tickets")
    stakes = np.asarray(v234.v205.round_dutch(list(odds), BANK), dtype=int)
    if int(stakes.sum()) != BANK:
        raise RuntimeError(f"Dutch total != {BANK}")
    if np.any(stakes % 100 != 0):
        raise RuntimeError("Dutch stake is not a 100-yen multiple")
    # v291 Top4 means all four tickets are purchased. Fail closed if rounding
    # ever produces a zero stake instead of silently changing the ticket count.
    if np.any(stakes <= 0):
        raise RuntimeError("v291 Top4 produced zero-stake ticket")
    return [
        {"combo": t, "odds": float(o), "stake": int(s)}
        for t, o, s in zip(tickets, odds, stakes)
    ]


def fetch_odds(date: str, jcd: int, race: int, deadline: datetime):
    require_before_deadline(deadline, "before odds fetch")
    requested_at = now_jst()
    params = {"rno": race, "jcd": f"{jcd:02d}", "hd": date}
    resp = live.safe_get(live.BASE, params)
    html = resp.text
    fetched_at = require_before_deadline(deadline, "after odds fetch")
    parsed = live.parse_odds(html)
    if set(parsed) != live.expected_combos() or len(parsed) != 120:
        raise RuntimeError(f"official odds3t incomplete: {len(parsed)}/120")
    odds = {f"{a}-{b}-{c}": float(o) for (a, b, c), o in parsed.items()}
    meta = {
        "source": "BOAT RACE official odds3t only",
        "url": resp.url,
        "count": 120,
        "requested_at_jst": requested_at.isoformat(),
        "fetched_at_jst": fetched_at.isoformat(),
        "sha256": hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest(),
        "complete": True,
        "result_endpoint_requested": False,
        "payout_endpoint_requested": False,
    }
    return odds, meta


def s_eligible(pre: float, post: float, env_entry: float) -> bool:
    return pre >= PRE_CUT and post >= POST_CUT and env_entry >= ENV_ENTRY_CUT


def persist_audit(path: str, row: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # Append-only decision ledger. The odds snapshot hash/timestamps are embedded
    # in each row; callers should archive the file as an immutable prospective log.
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()


def evaluate_market(inp: dict, odds_map: Mapping[str, float], odds_meta: dict, deadline: datetime) -> dict:
    race_code = str(inp["race_code"]).zfill(12)
    pre = _as_float(inp["PRE"], "PRE")
    post = _as_float(inp["POST"], "POST")
    env = _as_float(inp["ENV_ENTRY"], "ENV_ENTRY")
    if not s_eligible(pre, post, env):
        return {
            "race_code": race_code,
            "policy": POLICY,
            "layer": "S",
            "eligible": False,
            "decision": "NO_BET",
            "reason": "S_GATE_FAIL",
            "scores": {"PRE": pre, "POST": post, "ENV_ENTRY": env},
            "thresholds": {"PRE": PRE_CUT, "POST": POST_CUT, "ENV_ENTRY": ENV_ENTRY_CUT},
            "tickets": [],
            "total_stake": 0,
            "result_or_payout_used": False,
        }
    p2 = parse_p2(inp["p2"])
    pc = parse_cond(inp["cond"])
    top4 = v283_top4(p2, pc)
    vals = [_as_float(odds_map[t], f"odds[{t}]") for t in top4]
    comp = composite_odds(vals)
    bet = comp >= COMP_CUT
    ticket_rows = dutch(top4, vals) if bet else [
        {"combo": t, "odds": float(o), "stake": 0} for t, o in zip(top4, vals)
    ]
    decision_time = require_before_deadline(deadline, "before decision persist")
    return {
        "race_code": race_code,
        "policy": POLICY,
        "layer": "S",
        "eligible": True,
        "pair_model": {"branch": "v282/v283 independent", "mode": PAIR_MODE, "alpha2": ALPHA2, "v96_used": False},
        "scores": {"PRE": pre, "POST": post, "ENV_ENTRY": env},
        "thresholds": {"PRE": PRE_CUT, "POST": POST_CUT, "ENV_ENTRY": ENV_ENTRY_CUT},
        "ordered_top4": top4,
        "composite_odds": float(comp),
        "composite_cut": COMP_CUT,
        "decision": "BET" if bet else "PASS",
        "tickets": ticket_rows,
        "total_stake": int(sum(x["stake"] for x in ticket_rows)),
        "snapshot_timestamp_jst": odds_meta.get("fetched_at_jst"),
        "decision_time_jst": decision_time.isoformat(),
        "deadline_jst": deadline.isoformat(),
        "deadline_state": "LIVE_FROZEN_BEFORE_DEADLINE",
        "odds_snapshot": odds_meta,
        "result_or_payout_used": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-json", required=True, help="pre-result S scores + frozen v282/v283 p2/cond JSON")
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

        # S-gate failure does not need an odds request, but is still persisted.
        pre = _as_float(inp["PRE"], "PRE")
        post = _as_float(inp["POST"], "POST")
        env = _as_float(inp["ENV_ENTRY"], "ENV_ENTRY")
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
        # Re-check immediately before the append that constitutes the prospective freeze.
        row["decision_time_jst"] = require_before_deadline(deadline, "immediately before audit append").isoformat()
        row["seconds"] = time.perf_counter() - t0
        persist_audit(args.audit, row)
        print(json.dumps(row, ensure_ascii=False, indent=2))
    except Exception as e:
        err = {
            "policy": POLICY,
            "decision": "ERROR_NO_BET",
            "error": str(e),
            "deadline_jst": deadline.isoformat(),
            "now_jst": now_jst().isoformat(),
            "result_or_payout_used": False,
            "seconds": time.perf_counter() - t0,
        }
        print(json.dumps(err, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
