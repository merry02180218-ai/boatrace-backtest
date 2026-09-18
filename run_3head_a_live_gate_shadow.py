#!/usr/bin/env python3
"""Deadline-safe shadow evaluator for the adopted 3-head A head gate.

Consumes the morning pre/motor cache from build_3head_a_daily_shadow.py.
If the race is not a pre+motor candidate, exits without requesting exhibition.
For candidates, fetches only current Boatcast exhibition time and applies the
frozen exhibition-rank==1 rule.  It does not fetch odds, results, or payouts and
does not place or construct a bet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timedelta, timezone

import joblib
import requests

from threehead_head_gate_a_adopted import passes_adopted_head_gate

JST = timezone(timedelta(hours=9))


def now_jst():
    return datetime.now(JST)


def parse_deadline(s: str):
    dl = datetime.fromisoformat(s)
    if dl.tzinfo is None:
        dl = dl.replace(tzinfo=JST)
    return dl.astimezone(JST)


def require_before_deadline(dl, stage: str):
    now = now_jst()
    if now >= dl:
        raise RuntimeError(
            f"deadline passed at {stage}: now={now.isoformat()} deadline={dl.isoformat()}"
        )
    return now


def get_text(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
    r.raise_for_status()
    return r.content.decode("utf-8", errors="replace")


def parse_exhibition_times(body: str) -> list[float]:
    lines = [x for x in body.splitlines() if x.strip()]
    if len(lines) < 8 or not lines[0].startswith("data="):
        raise RuntimeError("Boatcast tkz incomplete")
    vals = []
    for row in lines[2:8]:
        c = row.split("\t")
        if len(c) < 2:
            raise RuntimeError("Boatcast tkz row incomplete")
        try:
            v = float(c[1])
        except Exception as e:
            raise RuntimeError(f"invalid exhibition time: {c[1]!r}") from e
        if not math.isfinite(v):
            raise RuntimeError("non-finite exhibition time")
        vals.append(v)
    if len(vals) != 6:
        raise RuntimeError(f"exhibition time count != 6: {len(vals)}")
    return vals


def exhibition_rank3(times: list[float]) -> int:
    if len(times) != 6 or any(not math.isfinite(float(x)) for x in times):
        raise RuntimeError("six finite exhibition times required")
    e3 = float(times[2])
    # Exact research semantics: rank = 1 + number of strictly faster boats.
    return 1 + sum(float(x) < e3 for i, x in enumerate(times) if i != 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--jcd", type=int, required=True)
    ap.add_argument("--race", type=int, required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--deadline-jst", required=True)
    args = ap.parse_args()

    dl = parse_deadline(args.deadline_jst)
    target = datetime.strptime(args.date, "%Y%m%d").date()
    if dl.date() != target:
        raise RuntimeError("deadline target-date mismatch")
    if not 1 <= args.jcd <= 24 or not 1 <= args.race <= 12:
        raise RuntimeError("invalid jcd/race")

    z = joblib.load(args.cache)
    if str(z.get("date", "")) != args.date:
        raise RuntimeError("A shadow cache date mismatch")
    if z.get("target_result_or_payout_used") is not False:
        raise RuntimeError("target result/payout leakage guard failed")
    if z.get("target_exhibition_used") is not False:
        raise RuntimeError("morning cache unexpectedly used target exhibition")

    code = f"{args.date}{args.jcd:02d}{args.race:02d}"
    pc = z.get("pre_motor_candidates", {}).get(code)
    if not pc:
        print(json.dumps({
            "race_code": code,
            "decision": "NO_HEAD_GATE",
            "reason": "not pre+motor candidate",
            "result_or_payout_used": False,
            "exhibition_requested": False,
        }, ensure_ascii=False, indent=2))
        return

    require_before_deadline(dl, "before exhibition fetch")
    jo = f"{args.jcd:02d}"
    rr = f"{args.race:02d}"
    url = f"https://race.boatcast.jp/hp_txt/{jo}/bc_j_tkz_{args.date}_{jo}_{rr}.txt"
    requested_at = now_jst()
    body = get_text(url)
    fetched_at = require_before_deadline(dl, "after exhibition fetch")
    times = parse_exhibition_times(body)
    rank3 = exhibition_rank3(times)

    row = {
        "race_no": pc["race_no"],
        "pre_score": pc["pre_score"],
        "post_motor_rank_edge2": pc["post_motor_rank_edge2"],
        "post_ex_rank3": rank3,
    }
    passed = passes_adopted_head_gate(row)
    emitted_at = require_before_deadline(dl, "before decision emit")

    out = {
        "policy": "3HEAD_A_PRECISION_V1_SHADOW",
        "race_code": code,
        "decision": "HEAD_GATE_PASS" if passed else "NO_HEAD_GATE",
        "gate": row,
        "exhibition_times": times,
        "deadline_jst": dl.isoformat(),
        "requested_at_jst": requested_at.isoformat(),
        "fetched_at_jst": fetched_at.isoformat(),
        "decision_time_jst": emitted_at.isoformat(),
        "source": url,
        "source_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "result_or_payout_used": False,
        "odds_requested": False,
        "bet_constructed": False,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
            "decision": "ERROR_NO_HEAD_GATE",
            "error": str(e),
            "result_or_payout_used": False,
            "bet_constructed": False,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
