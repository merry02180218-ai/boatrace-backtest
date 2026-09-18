#!/usr/bin/env python3
"""A-head-gate March ticket audit wrapper.

Forces replay_v288_historical_day.py to ignore BoatraceCSV archived od3 and use
only the locally materialized frozen canonical closing-odds archive.
All v288 decision/ticket logic remains unchanged.
"""
from __future__ import annotations

import argparse
import sys
import replay_v288_historical_day as base


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--date",required=True)
    ap.add_argument("--cache",required=True)
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--expected-history-cutoff",required=True)
    a=ap.parse_args()

    original_odds_map=base.odds_map
    # Returning an empty map makes the generic replay take its official/local
    # closing-odds fallback.  In this audit that local archive is materialized
    # from the frozen Wave21 canonical closing_odds__json source.
    base.odds_map=lambda row: {}
    old=list(sys.argv)
    try:
        sys.argv=[
            "replay_v288_historical_day.py",
            "--date",a.date,
            "--cache",a.cache,
            "--outdir",a.outdir,
            "--expected-history-cutoff",a.expected_history_cutoff,
        ]
        base.main()
    finally:
        base.odds_map=original_odds_map
        sys.argv=old


if __name__=="__main__":
    main()
