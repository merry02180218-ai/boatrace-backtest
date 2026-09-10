#!/usr/bin/env python3
"""Apply frozen HEAD4_V291_COMP7 to immutable pre-deadline Top4 odds snapshots.

This script is intentionally result-blind.  Upstream must already have produced an
eligible frozen S/A signal and the frozen v283 ordered Top4 tickets.  This script
only performs snapshot validation, composite-odds gating, and exact 10,000-yen
inverse-odds Dutch allocation.

Input CSV columns
-----------------
race_code, layer, snapshot_ts, deadline_ts,
ticket1, odds1, ticket2, odds2, ticket3, odds3, ticket4, odds4

Optional columns are preserved.  Timestamps must be offset-aware ISO-8601 values.
For formal OOS, snapshot_ts must be strictly earlier than deadline_ts.
"""
from __future__ import annotations

import argparse
import csv
import math
from datetime import datetime
from pathlib import Path
from typing import Iterable

POLICY_VERSION = "HEAD4_V291_COMP7"
HEAD = 4
N = 4
COMPOSITE_MIN = 7.0
BANK_YEN = 10_000
UNIT_YEN = 100
TOTAL_UNITS = BANK_YEN // UNIT_YEN

REQUIRED = [
    "race_code", "layer", "snapshot_ts", "deadline_ts",
    "ticket1", "odds1", "ticket2", "odds2", "ticket3", "odds3", "ticket4", "odds4",
]


def parse_ts(s: str) -> datetime:
    s = str(s).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    x = datetime.fromisoformat(s)
    if x.tzinfo is None or x.utcoffset() is None:
        raise ValueError(f"timestamp must be offset-aware: {s!r}")
    return x


def parse_ticket(s: str) -> tuple[int, int, int]:
    p = str(s).strip().replace("_", "-").split("-")
    if len(p) != 3:
        raise ValueError(f"bad trifecta ticket: {s!r}")
    t = tuple(int(x) for x in p)
    if sorted(t) != sorted(set(t)):
        raise ValueError(f"ticket contains duplicate boats: {s!r}")
    if any(x < 1 or x > 6 for x in t):
        raise ValueError(f"boat outside 1..6: {s!r}")
    if t[0] != HEAD:
        raise ValueError(f"v291 head must be boat 4: {s!r}")
    return t


def composite_odds(odds: Iterable[float]) -> float:
    o = [float(x) for x in odds]
    if len(o) != N or any((not math.isfinite(x) or x <= 0.0) for x in o):
        raise ValueError(f"need four positive finite odds, got {o}")
    return 1.0 / sum(1.0 / x for x in o)


def hamilton_dutch(odds: Iterable[float]) -> list[int]:
    """Return exact yen stakes summing to 10,000 in 100-yen units."""
    o = [float(x) for x in odds]
    inv = [1.0 / x for x in o]
    den = sum(inv)
    exact = [TOTAL_UNITS * x / den for x in inv]
    units = [math.floor(x) for x in exact]
    remain = TOTAL_UNITS - sum(units)
    order = sorted(range(N), key=lambda i: (-(exact[i] - units[i]), i))
    for i in order[:remain]:
        units[i] += 1
    stakes = [int(x * UNIT_YEN) for x in units]
    if sum(stakes) != BANK_YEN:
        raise AssertionError(f"Dutch stake sum mismatch: {stakes}")
    return stakes


def apply_row(row: dict[str, str]) -> dict[str, str]:
    missing = [k for k in REQUIRED if not str(row.get(k, "")).strip()]
    if missing:
        raise ValueError(f"{row.get('race_code','?')}: missing {missing}")

    layer = str(row["layer"]).strip().upper()
    if layer not in {"S", "A"}:
        raise ValueError(f"{row['race_code']}: layer must be S or A")

    snap = parse_ts(row["snapshot_ts"])
    deadline = parse_ts(row["deadline_ts"])
    if not snap < deadline:
        raise ValueError(f"{row['race_code']}: snapshot is not pre-deadline")

    tickets = [str(row[f"ticket{i}"]).strip() for i in range(1, N + 1)]
    parsed = [parse_ticket(x) for x in tickets]
    if len(set(parsed)) != N:
        raise ValueError(f"{row['race_code']}: Top4 tickets must be unique")

    odds = [float(row[f"odds{i}"]) for i in range(1, N + 1)]
    comp = composite_odds(odds)
    bet = comp >= COMPOSITE_MIN
    stakes = hamilton_dutch(odds) if bet else [0] * N

    out = dict(row)
    out.update({
        "policy_version": POLICY_VERSION,
        "snapshot_valid_pre_deadline": "1",
        "top4_composite_odds": f"{comp:.9f}",
        "composite_min": f"{COMPOSITE_MIN:.6f}",
        "decision": "BET" if bet else "PASS",
        "total_stake_yen": str(BANK_YEN if bet else 0),
    })
    for i, stake in enumerate(stakes, 1):
        out[f"stake{i}_yen"] = str(stake)
        if bet:
            out[f"gross_if_ticket{i}_hits_yen"] = f"{stake * odds[i-1]:.0f}"
        else:
            out[f"gross_if_ticket{i}_hits_yen"] = "0"
    return out


def run(inp: Path, outp: Path) -> None:
    with inp.open(newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            raise ValueError("input has no header")
        miss = [k for k in REQUIRED if k not in r.fieldnames]
        if miss:
            raise ValueError(f"input header missing {miss}")
        rows = [apply_row(dict(x)) for x in r]
    if not rows:
        raise ValueError("input has zero rows")
    fields = list(rows[0].keys())
    for row in rows[1:]:
        for k in row:
            if k not in fields:
                fields.append(k)
    with outp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def self_test() -> None:
    assert abs(composite_odds([20, 30, 40, 50]) - 7.7922077922) < 1e-8
    s = hamilton_dutch([20, 30, 40, 50])
    assert sum(s) == 10_000 and all(x % 100 == 0 for x in s)
    base = {
        "race_code":"TEST", "layer":"S",
        "snapshot_ts":"2026-09-11T10:00:00+09:00",
        "deadline_ts":"2026-09-11T10:10:00+09:00",
        "ticket1":"4-1-2", "odds1":"20",
        "ticket2":"4-1-3", "odds2":"30",
        "ticket3":"4-2-1", "odds3":"40",
        "ticket4":"4-2-3", "odds4":"50",
    }
    o = apply_row(base)
    assert o["decision"] == "BET" and int(o["total_stake_yen"]) == 10_000
    low = dict(base); low.update({"odds1":"10","odds2":"20","odds3":"30","odds4":"40"})
    assert apply_row(low)["decision"] == "PASS"
    bad = dict(base); bad["snapshot_ts"] = bad["deadline_ts"]
    try:
        apply_row(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("deadline integrity test failed")
    print("v291 self-test OK", s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", type=Path)
    ap.add_argument("output", nargs="?", type=Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test(); return
    if a.input is None or a.output is None:
        ap.error("provide INPUT OUTPUT, or use --self-test")
    run(a.input, a.output)


if __name__ == "__main__":
    main()
