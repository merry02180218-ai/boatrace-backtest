#!/usr/bin/env python3
"""Frozen A-head March ticket audit wrapper.

Evaluates two predeclared, non-retuned downstream policies on the exact same
frozen A head-candidate population and frozen canonical closing odds:

PRIMARY / pair_only:
  A head gate is authoritative -> v242/v288 pair ranking -> v242 choose_n
  (variable 5..10 tickets) -> exact 10,000-yen Dutch.
  Legacy v243/v288 head-route filters are NOT stacked on top of A.

DIAGNOSTIC / full_v288_overlay:
  Same A population, but legacy v243 + v288 S/A/B route filters are additionally
  applied before ticket construction.

Both arms use replay_v288_historical_day.py decision and settlement machinery.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import replay_v288_historical_day as base


def _pair_only_route(v243_pass, buyable, s_cond, a_cond, b_cond):
    if bool(buyable):
        return "A_HEAD", False, False, False
    return None, False, False, False


def run_one(a, outdir: Path, pair_only: bool):
    original_odds_map = base.odds_map
    original_select = base.prod.select_v288_route

    # Force local frozen canonical closing odds. Returning an empty archive map
    # makes generic replay use official_closing_odds(), whose March files are
    # materialized from frozen Wave21 closing_odds__json by the workflow.
    base.odds_map = lambda row: {}
    if pair_only:
        base.prod.select_v288_route = _pair_only_route

    old = list(sys.argv)
    try:
        sys.argv = [
            "replay_v288_historical_day.py",
            "--date", a.date,
            "--cache", a.cache,
            "--outdir", str(outdir),
            "--expected-history-cutoff", a.expected_history_cutoff,
        ]
        base.main()
    finally:
        base.odds_map = original_odds_map
        base.prod.select_v288_route = original_select
        sys.argv = old


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--expected-history-cutoff", required=True)
    a = ap.parse_args()

    root = Path(a.outdir)
    run_one(a, root / "pair_only", pair_only=True)
    run_one(a, root / "full_v288_overlay", pair_only=False)


if __name__ == "__main__":
    main()
