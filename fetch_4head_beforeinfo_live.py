#!/usr/bin/env python3
"""Generalized result-blind official beforeinfo fetcher for HEAD4 LIVE.

This module only requests the official BOAT RACE `beforeinfo` page.  It never
follows links and never requests result/payout endpoints.  It persists the raw
HTML plus an immutable metadata/table snapshot so downstream feature-building
can be audited before any result exists.

This is acquisition plumbing only: it deliberately does NOT invent POST,
ENV_ENTRY, A-LIVE or v283 feature values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE = "https://www.boatrace.jp/owpc/pc/race/beforeinfo"
UA = {"User-Agent": "Mozilla/5.0 (compatible; boatrace-backtest/HEAD4-result-blind)"}
JST = timezone(timedelta(hours=9))
FORBIDDEN = ("result", "pay", "payout", "refund", "odds3t")


class BeforeInfoError(RuntimeError):
    pass


def clean(s: Any) -> str:
    return " ".join(str(s).split())


def validate_target(hd: str, jcd: int, rno: int) -> tuple[str, int, int]:
    if not re.fullmatch(r"20\d{6}", str(hd)):
        raise BeforeInfoError("hd must be YYYYMMDD")
    jcd = int(jcd)
    rno = int(rno)
    if not 1 <= jcd <= 24:
        raise BeforeInfoError("jcd must be 1..24")
    if not 1 <= rno <= 12:
        raise BeforeInfoError("rno must be 1..12")
    return str(hd), jcd, rno


def build_url(hd: str, jcd: int, rno: int) -> str:
    hd, jcd, rno = validate_target(hd, jcd, rno)
    return f"{BASE}?rno={rno}&jcd={jcd:02d}&hd={hd}"


def assert_result_blind_url(url: str) -> None:
    low = url.lower()
    if not low.startswith(BASE.lower() + "?"):
        raise BeforeInfoError("unexpected source endpoint")
    # Endpoint path is allow-listed. Query values are numeric/date only.
    path = low.split("?", 1)[0]
    if any(x in path.replace("beforeinfo", "") for x in FORBIDDEN):
        raise BeforeInfoError("forbidden endpoint token")


def parse_beforeinfo_html(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title = clean(soup.title.get_text(" ", strip=True)) if soup.title else ""
    tables = []
    for ti, table in enumerate(soup.find_all("table")):
        rows = []
        for tr in table.find_all("tr"):
            cells = [clean(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append({"index": ti, "rows": rows})
    text = clean(soup.get_text(" ", strip=True))
    return {
        "title": title,
        "table_count": len(tables),
        "tables": tables,
        "text_head": text[:4000],
    }


def fetch_beforeinfo(hd: str, jcd: int, rno: int, timeout: int = 20) -> tuple[str, dict[str, Any]]:
    url = build_url(hd, jcd, rno)
    assert_result_blind_url(url)
    r = requests.get(url, headers=UA, timeout=timeout, allow_redirects=False)
    if r.is_redirect or r.is_permanent_redirect:
        raise BeforeInfoError("redirect refused for result-blind source")
    if r.status_code != 200:
        raise BeforeInfoError(f"HTTP {r.status_code}")
    html = r.text
    if not html.strip():
        raise BeforeInfoError("empty beforeinfo body")
    parsed = parse_beforeinfo_html(html)
    fetched = datetime.now(JST).isoformat(timespec="seconds")
    meta = {
        "schema": "head4_beforeinfo_snapshot_v1",
        "source_kind": "official_beforeinfo_only",
        "source_url": url,
        "hd": str(hd),
        "jcd": int(jcd),
        "rno": int(rno),
        "fetched_at_jst": fetched,
        "sha256_html": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "http_status": int(r.status_code),
        "redirect_followed": False,
        "result_endpoint_requested": False,
        "payout_endpoint_requested": False,
        "parsed": parsed,
    }
    return html, meta


def persist_snapshot(outdir: Path, html: str, meta: dict[str, Any]) -> tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"{meta['hd']}_{int(meta['jcd']):02d}_{int(meta['rno']):02d}R_beforeinfo"
    html_path = outdir / f"{stem}.html"
    json_path = outdir / f"{stem}.json"
    html_path.write_text(html, encoding="utf-8")
    json_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return html_path, json_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--jcd", required=True, type=int)
    ap.add_argument("--rno", required=True, type=int)
    ap.add_argument("--outdir", default="live_freeze/head4_v291/beforeinfo")
    ap.add_argument("--timeout", type=int, default=20)
    args = ap.parse_args()
    html, meta = fetch_beforeinfo(args.date, args.jcd, args.rno, args.timeout)
    hp, jp = persist_snapshot(Path(args.outdir), html, meta)
    print(json.dumps({"status": "OK", "html": str(hp), "metadata": str(jp), "sha256_html": meta["sha256_html"], "table_count": meta["parsed"]["table_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
