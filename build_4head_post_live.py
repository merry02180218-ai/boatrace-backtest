#!/usr/bin/env python3
"""Result-blind current-day HEAD4 v291 POST exhibition feature builder.

This is additive plumbing only. It does not alter v291 or betting policy.
Sources are allow-listed pre-race endpoints only:
- official BOAT RACE beforeinfo (tilt)
- BOATCAST start-display TSV (ST; pinned F/L semantics)
- BOATCAST original-exhibition TSV (label-driven values)

Missing/unpublished/malformed required data fails closed. No result/payout endpoint
is requested and redirects are refused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from fetch_4head_beforeinfo_live import build_url as beforeinfo_url, validate_target

JST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0 (compatible; boatrace-backtest/HEAD4-result-blind)"}
BOATCAST = "https://race.boatcast.jp"
FORBIDDEN = ("result", "pay", "payout", "refund", "odds", "replay")


class PostBuildError(RuntimeError):
    pass


def _clean(v: Any) -> str:
    return " ".join(str(v or "").replace("\u3000", " ").split())


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _num(text: Any) -> float | None:
    s = _clean(text).replace("度", "").replace("+", "")
    if not s or s in {"-", "--", "－"}:
        return None
    if s.startswith("."):
        s = "0" + s
    if s.startswith("-."):
        s = "-0" + s[1:]
    try:
        x = float(s)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def _rank_score(vals: dict[int, float | None], boat: int, lower: bool = True) -> float:
    arr = [(j, v) for j, v in vals.items() if v is not None]
    if vals.get(boat) is None or len(arr) < 2:
        raise PostBuildError(f"rank input incomplete for boat {boat}")
    s = sorted(arr, key=lambda z: z[1], reverse=not lower)
    pos = [j for j, (b, _) in enumerate(s) if b == boat][0]
    return 1 - pos / (len(s) - 1)


def _assert_prerace_url(url: str, prefix: str) -> None:
    low = url.lower()
    if not low.startswith(prefix.lower()):
        raise PostBuildError(f"source outside allow-list: {url}")
    path = low.split("?", 1)[0]
    if any(tok in path for tok in FORBIDDEN):
        raise PostBuildError(f"forbidden source token: {url}")


def _fetch(url: str, prefix: str, timeout: int = 20) -> str:
    _assert_prerace_url(url, prefix)
    r = requests.get(url, headers=UA, timeout=timeout, allow_redirects=False)
    if r.is_redirect or r.is_permanent_redirect:
        raise PostBuildError(f"redirect refused: {url}")
    if r.status_code != 200:
        raise PostBuildError(f"HTTP {r.status_code}: {url}")
    text = r.text
    if not text.strip():
        raise PostBuildError(f"empty source: {url}")
    return text


def boatcast_st_url(hd: str, jcd: int, rno: int) -> str:
    hd, jcd, rno = validate_target(hd, jcd, rno)
    return f"{BOATCAST}/hp_txt/{jcd:02d}/bc_j_stt_{hd}_{jcd:02d}_{rno:02d}.txt"


def boatcast_orig_url(hd: str, jcd: int, rno: int) -> str:
    hd, jcd, rno = validate_target(hd, jcd, rno)
    return f"{BOATCAST}/txt/{jcd:02d}/bc_oriten_{hd}_{jcd:02d}_{rno:02d}.txt"


def parse_start_timing(value: str, flag: str) -> float | None:
    f = _clean(flag).upper()
    if f == "L":
        return None
    x = _num(value)
    if x is None:
        return None
    if f == "F":
        x = -x
    return x


def _coalesce_boatcast_st_records(text: str) -> list[str]:
    """Join BOATCAST physical line wraps back into six logical ST records.

    The bc_j_stt source can wrap a player-name field at a byte boundary, including
    inside a multibyte Japanese character. A logical boat record always starts with
    two tab-separated integers: [entry course, boat number]. Any following physical
    line that does not start a new [1..6, 1..6] record is a continuation.
    """
    records: list[str] = []
    cur: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\r\n")
        cols = line.split("\t")
        is_start = False
        if len(cols) >= 3:
            try:
                first = int(_clean(cols[0]))
                if 1 <= first <= 6:
                    # Live BOATCAST: [course, boat, name, ...].
                    # Legacy fixtures: [boat, nonnumeric placeholder, ...].
                    try:
                        second = int(_clean(cols[1]))
                        is_start = 1 <= second <= 6
                    except Exception:
                        is_start = len(cols) >= 5
            except Exception:
                is_start = False
        if is_start:
            if cur is not None:
                records.append(cur)
            cur = line
        elif cur is not None:
            cur += line
    if cur is not None:
        records.append(cur)
    return records


def parse_boatcast_st(text: str) -> dict[int, float | None]:
    out: dict[int, float | None] = {}
    for raw in _coalesce_boatcast_st_records(text):
        cols = raw.split("\t")
        if len(cols) < 6:
            continue
        # BOATCAST bc_j_stt pinned layout:
        # [0]=entry course, [1]=boat number, [4]=ST value, [5]=F/L flag.
        # Never key by course; course changes would otherwise masquerade as boat identity.
        try:
            boat = int(_clean(cols[1]))
        except Exception:
            try:
                boat = int(_clean(cols[0]))
            except Exception:
                continue
        if not 1 <= boat <= 6:
            continue
        out[boat] = parse_start_timing(cols[4], cols[5])
    if set(out) != set(range(1, 7)):
        raise PostBuildError(f"ST rows incomplete: boats={sorted(out)}")
    return out


def _norm_label(s: str) -> str:
    return _clean(s).replace(" ", "")


def parse_boatcast_original(text: str) -> tuple[list[str], dict[int, list[float | None]]]:
    lines = [x.rstrip("\r\n") for x in text.splitlines() if x.strip()]
    if len(lines) < 4 or not lines[0].strip().startswith("data="):
        raise PostBuildError("original exhibition: bad data marker")
    status = lines[1].split("\t", 1)[0].strip()
    if status != "1":
        raise PostBuildError(f"original exhibition not measured: status={status}")
    labels = [_norm_label(x) for x in lines[2].split("\t") if _norm_label(x)]
    if not 1 <= len(labels) <= 3:
        raise PostBuildError(f"original exhibition: unexpected labels={labels}")
    # BOATCAST can physically wrap the player-name field mid-record.
    logical_rows: list[str] = []
    cur: str | None = None
    for raw in lines[3:]:
        cols = raw.split("\t")
        is_start = False
        if cols:
            try:
                boat0 = int(_clean(cols[0]))
                is_start = 1 <= boat0 <= 6
            except Exception:
                is_start = False
        if is_start:
            if cur is not None:
                logical_rows.append(cur)
            cur = raw
        elif cur is not None:
            cur += raw
    if cur is not None:
        logical_rows.append(cur)

    rows: dict[int, list[float | None]] = {}
    for raw in logical_rows:
        cols = raw.split("\t")
        if len(cols) < 2 + len(labels):
            continue
        try:
            boat = int(_clean(cols[0]))
        except Exception:
            continue
        if 1 <= boat <= 6:
            rows[boat] = [_num(v) for v in cols[2:2 + len(labels)]]
    if set(rows) != set(range(1, 7)):
        raise PostBuildError(f"original exhibition rows incomplete: boats={sorted(rows)}")
    return labels, rows


def original_scores(labels: list[str], rows: dict[int, list[float | None]], boat: int = 4) -> dict[str, float]:
    # Exact frozen semantics: a metric family not supplied by a measured venue
    # remains 0.5; supplied metric families are rank-scored lower-is-better.
    ret = {"lap": 0.5, "turn": 0.5, "straight": 0.5}
    for k, label in enumerate(labels):
        vals = {b: rows[b][k] if k < len(rows[b]) else None for b in range(1, 7)}
        sc = _rank_score(vals, boat, True)
        lab = _norm_label(label)
        if "直線" in lab:
            ret["straight"] = sc
        elif "まわり" in lab or "回り" in lab or "ターン" in lab:
            ret["turn"] = sc
        elif "一周" in lab or "周" in lab or "ラップ" in lab:
            ret["lap"] = sc
    return ret


def parse_tilt4_beforeinfo(html: str) -> float:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[float] = []
    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        header_idx = None
        for tr in trs:
            cells = [_clean(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
            for i, cell in enumerate(cells):
                if "チルト" in cell:
                    header_idx = i
                    break
            if header_idx is not None:
                break
        if header_idx is None:
            continue
        for tr in trs:
            cells = [_clean(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
            if not cells or cells[0] != "4" or header_idx >= len(cells):
                continue
            x = _num(cells[header_idx])
            if x is not None:
                candidates.append(x)
    if len(candidates) != 1:
        raise PostBuildError(f"tilt4 ambiguous/missing: candidates={candidates}")
    return candidates[0]


def build_from_sources(hd: str, jcd: int, rno: int, before_html: str, st_text: str, orig_text: str) -> dict[str, Any]:
    validate_target(hd, jcd, rno)
    st = parse_boatcast_st(st_text)
    if st.get(4) is None or st.get(3) is None:
        raise PostBuildError("required ST for boat 3/4 missing")
    os = original_scores(*parse_boatcast_original(orig_text), boat=4)
    tilt4 = parse_tilt4_beforeinfo(before_html)
    features = {
        "ex_st_rank4": _rank_score(st, 4, True),
        "ex_st_4": float(st[4]),
        "ex_st_edge_4v3": float(st[3]) - float(st[4]),
        "orig_straight4": os["straight"],
        "orig_lap4": os["lap"],
        "orig_turn4": os["turn"],
        "tilt4": tilt4,
    }
    if list(features) != ["ex_st_rank4", "ex_st_4", "ex_st_edge_4v3", "orig_straight4", "orig_lap4", "orig_turn4", "tilt4"]:
        raise PostBuildError("POST exhibition feature order drift")
    if any(not math.isfinite(float(v)) for v in features.values()):
        raise PostBuildError("non-finite POST feature")
    return features


def fetch_and_build(hd: str, jcd: int, rno: int, timeout: int = 20) -> dict[str, Any]:
    bu = beforeinfo_url(hd, jcd, rno)
    su = boatcast_st_url(hd, jcd, rno)
    ou = boatcast_orig_url(hd, jcd, rno)
    before = _fetch(bu, "https://www.boatrace.jp/owpc/pc/race/beforeinfo", timeout)
    st = _fetch(su, f"{BOATCAST}/hp_txt/{int(jcd):02d}/bc_j_stt_", timeout)
    orig = _fetch(ou, f"{BOATCAST}/txt/{int(jcd):02d}/bc_oriten_", timeout)
    features = build_from_sources(hd, jcd, rno, before, st, orig)
    return {
        "schema": "head4_v291_post_live_v1",
        "status": "READY",
        "hd": hd,
        "jcd": int(jcd),
        "rno": int(rno),
        "fetched_at_jst": datetime.now(JST).isoformat(timespec="seconds"),
        "result_or_payout_requested": False,
        "v291_changed": False,
        "features": features,
        "sources": {
            "beforeinfo": {"url": bu, "sha256": _sha(before)},
            "boatcast_st": {"url": su, "sha256": _sha(st)},
            "boatcast_original": {"url": ou, "sha256": _sha(orig)},
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--jcd", required=True, type=int)
    ap.add_argument("--rno", required=True, type=int)
    ap.add_argument("--outdir", default="live_freeze/head4_v291/post")
    ap.add_argument("--timeout", type=int, default=20)
    a = ap.parse_args()
    try:
        payload = fetch_and_build(a.date, a.jcd, a.rno, a.timeout)
    except Exception as e:
        # Fail closed: no partial feature payload is emitted as READY.
        raise SystemExit(f"FAIL_CLOSED: {type(e).__name__}: {e}")
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{a.date}_{a.jcd:02d}_{a.rno:02d}R_post.json"
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "READY", "path": str(p), "features": payload["features"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
