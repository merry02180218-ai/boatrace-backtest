from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

EXPECTED_A_RACES = 52
EXPECTED_DAYS = 25
OFFICIAL_ODDS_SOURCE = "boatrace_official_closing_odds3t_archive"


def aggregate_arm(root: Path, arm: str):
    summaries = []
    replay_files = []

    for p in root.rglob("day_summary.json"):
        if p.parent.name != arm:
            continue
        try:
            z = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        summaries.append((p, z))
        q = p.with_name("day_replay.csv")
        if q.exists() and q.stat().st_size:
            replay_files.append(q)

    if not summaries:
        raise RuntimeError(f"no day summaries found for arm={arm}")

    total = {
        "pre_candidates": 0,
        "live_evaluable": 0,
        "input_or_decision_errors": 0,
        "genuine_no_bets": 0,
        "bets": 0,
        "hits": 0,
        "stake": 0.0,
        "payout": 0.0,
    }
    days = []
    for p, z in sorted(summaries, key=lambda x: x[1].get("date", "")):
        for k in total:
            total[k] += z.get(k, 0) or 0
        days.append({
            "date": z.get("date"),
            "pre_candidates": z.get("pre_candidates"),
            "live_evaluable": z.get("live_evaluable"),
            "errors": z.get("input_or_decision_errors"),
            "no_bets": z.get("genuine_no_bets"),
            "bets": z.get("bets"),
            "hits": z.get("hits"),
            "stake": z.get("stake"),
            "payout": z.get("payout"),
            "roi": z.get("roi"),
        })

    route = defaultdict(lambda: {"bets": 0, "hits": 0, "stake": 0.0, "payout": 0.0})
    all_bets = []
    odds_source_counts = defaultdict(int)
    evaluable_rows = 0

    for p in replay_files:
        df = pd.read_csv(p, low_memory=False)
        if "evaluation_status" in df.columns:
            e = df[df.evaluation_status == "EVALUABLE"].copy()
            evaluable_rows += len(e)
            if "odds_source" in e.columns:
                for v, n in e.odds_source.fillna("").astype(str).value_counts().items():
                    odds_source_counts[v] += int(n)

        if "decision" not in df.columns:
            continue
        b = df[df.decision == "BET"].copy()
        for _, r in b.iterrows():
            rt = str(r.get("route", ""))
            route[rt]["bets"] += 1
            route[rt]["hits"] += int(r.get("hit", 0) or 0)
            route[rt]["stake"] += float(r.get("total_stake", 0) or 0)
            route[rt]["payout"] += float(r.get("return_yen", 0) or 0)
            all_bets.append({
                "date": str(r.get("date", "")),
                "race_code": str(r.get("race_code", "")),
                "route": rt,
                "hit": int(r.get("hit", 0) or 0),
                "stake": float(r.get("total_stake", 0) or 0),
                "payout": float(r.get("return_yen", 0) or 0),
                "comp_odds": None if pd.isna(r.get("comp_odds")) else float(r.get("comp_odds")),
                "top_n": None if pd.isna(r.get("top_n")) else int(r.get("top_n")),
            })

    for _, z in route.items():
        z["roi"] = 100 * z["payout"] / z["stake"] if z["stake"] else None

    coverage_ok = int(total["pre_candidates"]) == EXPECTED_A_RACES
    day_count_ok = len(summaries) == EXPECTED_DAYS
    error_free = int(total["input_or_decision_errors"]) == 0
    odds_pinned = (
        evaluable_rows == int(total["live_evaluable"])
        and set(odds_source_counts) <= {OFFICIAL_ODDS_SOURCE}
        and int(odds_source_counts.get(OFFICIAL_ODDS_SOURCE, 0)) == evaluable_rows
    )

    return {
        "arm": arm,
        "candidate_count_expected": EXPECTED_A_RACES,
        "candidate_count_replayed": int(total["pre_candidates"]),
        "day_count": len(summaries),
        "live_evaluable": int(total["live_evaluable"]),
        "input_or_decision_errors": int(total["input_or_decision_errors"]),
        "genuine_no_bets": int(total["genuine_no_bets"]),
        "bets": int(total["bets"]),
        "hits": int(total["hits"]),
        "hit_rate_on_bets": total["hits"] / total["bets"] if total["bets"] else None,
        "head_gate_to_bet_rate": total["bets"] / EXPECTED_A_RACES,
        "stake": float(total["stake"]),
        "payout": float(total["payout"]),
        "profit": float(total["payout"] - total["stake"]),
        "roi": 100 * total["payout"] / total["stake"] if total["stake"] else None,
        "route_breakdown": dict(route),
        "odds_source_counts": dict(odds_source_counts),
        "coverage_ok": coverage_ok,
        "day_count_ok": day_count_ok,
        "error_free": error_free,
        "frozen_canonical_odds_only": odds_pinned,
        "days": days,
        "bets_detail": all_bets,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="research_3head_a_v288_ticket_march_summary.json")
    a = ap.parse_args()

    root = Path(a.root)
    pair_only = aggregate_arm(root, "pair_only")
    overlay = aggregate_arm(root, "full_v288_overlay")

    out = {
        "policy": "3HEAD_A_PRECISION_V1_DOWNSTREAM_MARCH_AUDIT",
        "head_gate_source_run": 35364404883,
        "head_gate_marker": "3HEAD_A_MARCH_PARITY_OK",
        "head_gate_march": {
            "n": 52,
            "heads": 21,
            "rate": 21 / 52,
        },
        "primary": {
            "name": "A_HEAD_PLUS_PAIR_TICKET_ENGINE",
            "description": (
                "Frozen A is the authoritative head gate; legacy v243/v288 head-route "
                "filters are not stacked. Existing pair ranking, v242 choose_n 5..10, "
                "and exact 10,000-yen Dutch remain unchanged."
            ),
            "result": pair_only,
        },
        "diagnostic_overlay": {
            "name": "A_HEAD_PLUS_FULL_V288_ROUTE_OVERLAY",
            "description": (
                "Same frozen A population with legacy v243 + v288 S/A/B head-route "
                "filters additionally stacked; diagnostic only."
            ),
            "result": overlay,
        },
        "comparison": {
            "bet_count_delta_primary_minus_overlay": pair_only["bets"] - overlay["bets"],
            "roi_delta_pp_primary_minus_overlay": (
                pair_only["roi"] - overlay["roi"]
                if pair_only["roi"] is not None and overlay["roi"] is not None
                else None
            ),
            "profit_delta_yen_primary_minus_overlay": pair_only["profit"] - overlay["profit"],
        },
        "audit": {
            "march_head_gate_frozen_before_ticket_audit": True,
            "head_gate_thresholds_retuned": False,
            "pair_or_ticket_thresholds_retuned_for_A": False,
            "primary_replaces_legacy_head_gate": True,
            "target_results_used_for_decision": False,
            "settlement_joined_after_decisions": True,
            "frozen_wave21_canonical_closing_odds_forced": True,
            "september_2026_outcomes_used": False,
        },
    }

    Path(a.out).write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))

    bad = []
    for label, z in [("primary", pair_only), ("overlay", overlay)]:
        if not z["coverage_ok"]:
            bad.append(f"{label}: coverage {z['candidate_count_replayed']}/52")
        if not z["day_count_ok"]:
            bad.append(f"{label}: days {z['day_count']}/25")
        if not z["error_free"]:
            bad.append(f"{label}: errors {z['input_or_decision_errors']}")
        if not z["frozen_canonical_odds_only"]:
            bad.append(f"{label}: odds sources {z['odds_source_counts']}")
    if bad:
        raise RuntimeError("formal audit incomplete: " + "; ".join(bad))


if __name__ == "__main__":
    main()
