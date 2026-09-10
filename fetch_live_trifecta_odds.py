#!/usr/bin/env python3
"""Result-free BOAT RACE 3連単 live odds snapshot fetcher.

Fetches ONLY the official odds3t page. It never requests result/payout endpoints.
Writes an immutable timestamped CSV + metadata JSON and validates that all 120
ordered trifecta combinations are present before the snapshot is considered usable.

Usage:
  python fetch_live_trifecta_odds.py --date 20260910 --jcd 16 --race 5 --out snapshots

For live operation, run repeatedly until the desired purchase-time snapshot and then
freeze that timestamped file. Do not overwrite a frozen snapshot.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
BASE = "https://www.boatrace.jp/owpc/pc/race/odds3t"
UA = "Mozilla/5.0 (compatible; boatrace-backtest/1.0; +https://github.com/)"

# Explicit deny-list. This script must never fetch these paths.
FORBIDDEN = ("/result", "/pay", "result?", "pay?")


def safe_get(url: str, params: dict, timeout: int = 15) -> requests.Response:
    low = url.lower()
    if any(x in low for x in FORBIDDEN):
        raise RuntimeError(f"forbidden result/payout endpoint: {url}")
    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    if "odds3t" not in r.url.lower():
        raise RuntimeError(f"unexpected redirect away from odds3t: {r.url}")
    return r


def _num(s: str):
    s = s.strip().replace(",", "")
    if s in {"-", "--", "—", "欠場", "返還"}:
        return None
    m = re.fullmatch(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    v = float(s)
    return v if v > 0 else None


def parse_strategy_text(html: str) -> Dict[Tuple[int, int, int], float]:
    """Parse explicit forms such as 1-2-3 12.4 or 1 2 3 12.4."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    out: Dict[Tuple[int, int, int], float] = {}
    # Strictly require three different boat numbers and a decimal/integer odds token.
    pat = re.compile(r"(?<!\d)([1-6])\s*[-→>]?\s*([1-6])\s*[-→>]?\s*([1-6])\s+([0-9]+(?:\.[0-9]+)?)(?!\d)")
    for a, b, c, od in pat.findall(text):
        t = (int(a), int(b), int(c))
        if len(set(t)) == 3:
            v = float(od)
            if v >= 1.0:
                out[t] = v
    return out


def parse_strategy_cells(html: str) -> Dict[Tuple[int, int, int], float]:
    """DOM fallback: scan each table row and recover groups [1,2,3,odds]."""
    soup = BeautifulSoup(html, "html.parser")
    out: Dict[Tuple[int, int, int], float] = {}
    for tr in soup.find_all("tr"):
        vals = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        tokens: List[str] = []
        for v in vals:
            # Keep cell boundaries but split whitespace and arrows/hyphens.
            parts = [p for p in re.split(r"\s+|[-→>]", v) if p]
            tokens.extend(parts)
        for i in range(max(0, len(tokens) - 3)):
            a, b, c = tokens[i:i+3]
            if not (a in "123456" and b in "123456" and c in "123456"):
                continue
            t = (int(a), int(b), int(c))
            if len(set(t)) != 3:
                continue
            # Search a short window after the combo for the odds number.
            for x in tokens[i+3:i+7]:
                od = _num(x)
                if od is not None and od >= 1.0:
                    out.setdefault(t, od)
                    break
    return out


def parse_strategy_anchor(html: str) -> Dict[Tuple[int, int, int], float]:
    """Attribute-aware fallback for layouts carrying combination text in nested tags."""
    soup = BeautifulSoup(html, "html.parser")
    out: Dict[Tuple[int, int, int], float] = {}
    for node in soup.find_all(["li", "div", "td", "span"]):
        txt = node.get_text(" ", strip=True)
        m = re.search(r"(?<!\d)([1-6])\s*[-→>]\s*([1-6])\s*[-→>]\s*([1-6])(?!\d)", txt)
        if not m:
            continue
        t = tuple(map(int, m.groups()))
        if len(set(t)) != 3:
            continue
        nums = re.findall(r"\d+(?:\.\d+)?", txt[m.end():])
        for x in nums:
            od = _num(x)
            if od is not None and od >= 1.0:
                out[t] = od
                break
    return out


def parse_odds(html: str) -> Dict[Tuple[int, int, int], float]:
    candidates = [parse_strategy_text(html), parse_strategy_cells(html), parse_strategy_anchor(html)]
    # Merge, preferring the strategy with greatest coverage, then fill missing from others.
    candidates.sort(key=len, reverse=True)
    out = dict(candidates[0]) if candidates else {}
    for d in candidates[1:]:
        for k, v in d.items():
            out.setdefault(k, v)
    return out


def expected_combos() -> set[Tuple[int, int, int]]:
    return {(a,b,c) for a in range(1,7) for b in range(1,7) for c in range(1,7)
            if len({a,b,c}) == 3}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--jcd", required=True, help="venue code, e.g. 16=児島, 14=鳴門")
    ap.add_argument("--race", required=True, type=int, choices=range(1,13))
    ap.add_argument("--out", default="odds_snapshots")
    ap.add_argument("--allow-incomplete", action="store_true", help="debug only; never use incomplete snapshot for betting")
    args = ap.parse_args()

    if not re.fullmatch(r"20\d{6}", args.date):
        raise SystemExit("--date must be YYYYMMDD")
    jcd = str(args.jcd).zfill(2)
    params = {"rno": args.race, "jcd": jcd, "hd": args.date}

    requested_at = datetime.now(JST)
    r = safe_get(BASE, params)
    fetched_at = datetime.now(JST)
    html = r.text
    sha256 = hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest()
    odds = parse_odds(html)

    exp = expected_combos()
    got = set(odds)
    missing = sorted(exp - got)
    extra = sorted(got - exp)
    complete = (len(got) == 120 and not missing and not extra)

    stamp = fetched_at.strftime("%Y%m%dT%H%M%S.%f%z")
    stem = f"odds3t_{args.date}_jcd{jcd}_r{args.race:02d}_{stamp}"
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    # Save raw HTML too, so parser behavior is auditable without re-fetching a later page.
    raw_path = outdir / f"{stem}.html"
    raw_path.write_text(html, encoding="utf-8")

    csv_path = outdir / f"{stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["first", "second", "third", "combo", "odds"])
        for (a,b,c), od in sorted(odds.items()):
            w.writerow([a,b,c,f"{a}-{b}-{c}",f"{od:.1f}"])

    meta = {
        "source": "BOAT RACE official odds3t only",
        "requested_url": BASE,
        "resolved_url": r.url,
        "params": params,
        "requested_at_jst": requested_at.isoformat(),
        "fetched_at_jst": fetched_at.isoformat(),
        "http_status": r.status_code,
        "html_sha256": sha256,
        "parsed_count": len(got),
        "expected_count": 120,
        "complete": complete,
        "missing": ["-".join(map(str,x)) for x in missing],
        "extra": ["-".join(map(str,x)) for x in extra],
        "result_endpoint_requested": False,
        "payout_endpoint_requested": False,
        "usable_for_betting": bool(complete),
        "csv": str(csv_path),
        "raw_html": str(raw_path),
    }
    meta_path = outdir / f"{stem}.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(meta, ensure_ascii=False, indent=2))
    if not complete and not args.allow_incomplete:
        print("ERROR: did not parse all 120 trifecta combinations; snapshot is NOT usable.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
