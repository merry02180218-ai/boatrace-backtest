#!/usr/bin/env python3
"""Build frozen v283 player-history primitives through the allowed Aug-31 boundary.

This is a verification-only helper.  It reproduces the v221 causal player-state
update order used by the frozen v283 opponent model:

1. freeze target-race player features from state accumulated strictly before target day
2. only afterwards would target-day results be ingested

July/August 2026 outcomes are now allowed by explicit user approval.  September
2026 outcomes remain forbidden/UNREAD.  Therefore exact target-day reconstruction
is permitted only through 2026-09-01.  Later September targets fail closed unless
`allow_truncated=True`, in which case the returned object is explicitly marked
NOT usable for exact v283 inference.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable

from backtest import rows
from backtest_v4 import clean_name

PRELOAD = date(2025, 10, 1)
LAST_ALLOWED_OUTCOME_DAY = date(2026, 8, 31)
FIRST_FORBIDDEN_OUTCOME_DAY = date(2026, 9, 1)


class PlayerHistoryBuildError(RuntimeError):
    pass


def _ii(x: Any, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def _bycode(rs: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(r.get("レースコード", "")).zfill(12): r
        for r in rs
        if r.get("レースコード")
    }


def _blank() -> dict[str, Any]:
    return {
        "n": 0,
        "w": 0,
        "p2": 0,
        "nf": defaultdict(int),
        "wf": defaultdict(int),
        "p2f": defaultdict(int),
        "r": deque(maxlen=30),
    }


def player_stats(s: dict[str, Any], boat: int) -> dict[str, float]:
    """Exact v221 pstat semantics for the five v283 pref_pl_* inputs."""
    n = int(s["n"])
    nf = int(s["nf"][boat])
    recent = list(s["r"])
    return {
        "pref_pl_all_p2": (float(s["p2"]) + 2 / 3) / (n + 2),
        "pref_pl_all_win": (float(s["w"]) + 2 / 6) / (n + 2),
        "pref_pl_frame_p2": (float(s["p2f"][boat]) + 3 * .25) / (nf + 3),
        "pref_pl_recent_p2": sum(recent) / len(recent) if recent else 1 / 3,
        "pref_pl_frame_win": (float(s["wf"][boat]) + 3 * .125) / (nf + 3),
    }


def ingest_day(
    state: dict[str, dict[str, Any]],
    cards: Iterable[dict[str, Any]],
    results: Iterable[dict[str, Any]],
) -> tuple[int, int]:
    """Apply the same result update order as v221 for one completed day."""
    cm = _bycode(cards)
    rm = _bycode(results)
    updates = 0
    result_rows = 0
    for code, card in cm.items():
        rr = rm.get(code, {})
        if rr:
            result_rows += 1
        winner = _ii(rr.get("1着_艇番"))
        second = _ii(rr.get("2着_艇番"))
        for b in range(1, 7):
            name = clean_name(card.get(f"艇{b}_選手名", ""))
            if not name:
                continue
            s = state[name]
            s["n"] += 1
            s["w"] += int(winner == b)
            s["p2"] += int(winner == b or second == b)
            s["nf"][b] += 1
            s["wf"][b] += int(winner == b)
            s["p2f"][b] += int(winner == b or second == b)
            s["r"].append(int(winner == b or second == b))
            updates += 1
    return updates, result_rows


def _repo_day_loader(d: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ymd = d.strftime("%Y/%m/%d")
    cards = rows(f"data/programs/race_cards/{ymd}.csv")
    results = rows(f"data/results/realtime/{ymd}.csv")
    return cards, results


def build_for_card(
    target: date,
    card: dict[str, Any],
    *,
    allow_truncated: bool = False,
    day_loader: Callable[[date], tuple[list[dict[str, Any]], list[dict[str, Any]]]] = _repo_day_loader,
) -> dict[str, Any]:
    if target < PRELOAD:
        raise PlayerHistoryBuildError("target before PRELOAD")
    exact = target <= FIRST_FORBIDDEN_OUTCOME_DAY
    if not exact and not allow_truncated:
        raise PlayerHistoryBuildError(
            "exact player history requires September outcomes; September is UNREAD, fail closed"
        )

    last_needed = target - timedelta(days=1)
    last_ingest = min(last_needed, LAST_ALLOWED_OUTCOME_DAY)
    state: dict[str, dict[str, Any]] = defaultdict(_blank)
    d = PRELOAD
    days = card_rows = result_rows = updates = 0
    jul_aug_result_rows = 0
    while d <= last_ingest:
        cards, results = day_loader(d)
        u, rr = ingest_day(state, cards, results)
        days += 1
        card_rows += len(cards)
        result_rows += rr
        updates += u
        if date(2026, 7, 1) <= d <= date(2026, 8, 31):
            jul_aug_result_rows += rr
        d += timedelta(days=1)

    boats: dict[str, dict[str, float]] = {}
    for b in range(1, 7):
        name = clean_name(card.get(f"艇{b}_選手名", ""))
        if not name:
            raise PlayerHistoryBuildError(f"missing target player name boat {b}")
        boats[str(b)] = player_stats(state[name], b)

    return {
        "schema": "head4_v283_player_history_julaug_v1",
        "target_date": target.isoformat(),
        "history_start": PRELOAD.isoformat(),
        "history_end": last_ingest.isoformat() if last_ingest >= PRELOAD else None,
        "last_allowed_outcome_day": LAST_ALLOWED_OUTCOME_DAY.isoformat(),
        "september_outcomes_read": False,
        "jul_aug_outcomes_allowed": True,
        "jul_aug_result_rows_ingested": jul_aug_result_rows,
        "exact_for_target": exact,
        "usable_for_exact_v283": exact,
        "days_scanned": days,
        "card_rows_seen": card_rows,
        "result_races_seen": result_rows,
        "player_updates": updates,
        "boats": boats,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--race-cards", required=True)
    ap.add_argument("--race-code", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-truncated", action="store_true")
    a = ap.parse_args()

    target = date.fromisoformat(a.target_date)
    code = str(a.race_code).zfill(12)
    cards = _bycode(rows(a.race_cards))
    if code not in cards:
        raise SystemExit(f"target race card not found: {code}")
    try:
        z = build_for_card(target, cards[code], allow_truncated=a.allow_truncated)
    except PlayerHistoryBuildError as e:
        raise SystemExit(str(e))
    Path(a.out).write_text(json.dumps(z, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "READY" if z["usable_for_exact_v283"] else "TRUNCATED_NOT_USABLE", "out": a.out}, ensure_ascii=False))


if __name__ == "__main__":
    main()
