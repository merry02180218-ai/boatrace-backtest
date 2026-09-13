#!/usr/bin/env python3
"""Result-free BOATCAST source/feature contract audit for frozen HEAD4 v291 POST.

Additive research tooling only. It does NOT wire BOATCAST into production.
Apr-Jun archived preview inputs are read through the repository's existing
BoatraceCSV fetch layer; no race-result or payout path is touched.
"""
from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path

from backtest import rows as remote_rows
from analyze_v23_20260902_daypreview import original_scores

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts" / "head4_boatcast_parity_contract_20260630.json"
START = date(2026, 4, 1)
END = date(2026, 6, 30)


def _f(x):
    try:
        v = float(str(x).strip())
        return v if math.isfinite(v) else None
    except Exception:
        return None


def norm_label(s: str) -> str:
    return str(s or "").replace(" ", "").replace("　", "").strip()


def label_family(label: str) -> str | None:
    s = norm_label(label)
    if "直線" in s:
        return "straight"
    if "まわり" in s or "回り" in s or "ターン" in s:
        return "turn"
    if "一周" in s or "周" in s or "ラップ" in s:
        return "lap"
    return None


def rank_score(vals: dict[int, float | None], boat: int, lower: bool = True) -> float:
    arr = [(b, v) for b, v in vals.items() if v is not None]
    if boat not in vals or vals[boat] is None or len(arr) < 2:
        return 0.5
    s = sorted(arr, key=lambda z: z[1], reverse=not lower)
    pos = [j for j, (b, _) in enumerate(s) if b == boat][0]
    return 1.0 - pos / (len(s) - 1)


def parse_original_exhibition_tsv(text: str) -> dict:
    lines = [x.rstrip("\r\n") for x in str(text).splitlines() if x.strip()]
    if lines and lines[0].strip().lower() == "data=":
        lines = lines[1:]
    if len(lines) < 2:
        raise ValueError("short original-exhibition TSV")
    meta = lines[0].split("\t")
    if len(meta) < 2:
        raise ValueError("missing status/ncols")
    status = int(meta[0])
    ncols = int(meta[1])
    labels = [norm_label(x) for x in lines[1].split("\t") if norm_label(x)]
    labels = [x for x in labels if label_family(x) is not None]
    if ncols > 0 and len(labels) > ncols:
        labels = labels[-ncols:]
    boats = {}
    for line in lines[2:]:
        p = line.split("\t")
        try:
            b = int(str(p[0]).strip())
        except Exception:
            continue
        if b not in range(1, 7):
            continue
        nums = [_f(x) for x in p[1:]]
        nums = nums[-len(labels):] if labels else []
        boats[b] = {lab: val for lab, val in zip(labels, nums)}
    return {"status": status, "ncols": ncols, "labels": labels, "boats": boats}


def original_lane4_scores(parsed: dict) -> dict[str, float]:
    out = {"straight": 0.5, "lap": 0.5, "turn": 0.5}
    for lab in parsed.get("labels", []):
        fam = label_family(lab)
        if fam is None:
            continue
        vals = {b: parsed.get("boats", {}).get(b, {}).get(lab) for b in range(1, 7)}
        out[fam] = rank_score(vals, 4, True)
    return out


def parse_st_value(raw_value, flag="") -> float | None:
    s = str(raw_value or "").strip()
    fl = str(flag or "").strip().upper()
    if fl == "L":
        return None
    if s.startswith("."):
        s = "0" + s
    v = _f(s)
    if v is None:
        return None
    return -abs(v) if fl == "F" else v


def parse_start_display_tsv(text: str) -> dict[int, float | None]:
    out = {}
    for line in str(text).splitlines():
        p = line.rstrip("\r\n").split("\t")
        if len(p) < 6:
            continue
        try:
            b = int(str(p[0]).strip())
        except Exception:
            continue
        if b in range(1, 7):
            out[b] = parse_st_value(p[4], p[5])
    return out


def historical_audit():
    orig_rows = st_rows = 0
    orig_dates = st_dates = 0
    label_families = {"straight": 0, "lap": 0, "turn": 0}
    two_metric_rows = three_metric_rows = 0
    lane4_score_mismatch = 0
    negative_st = 0
    d = START
    while d <= END:
        ymd = d.strftime("%Y/%m/%d")
        ors = remote_rows(f"data/previews/original_exhibition/{ymd}.csv")
        srs = remote_rows(f"data/previews/stt/{ymd}.csv")
        if ors:
            orig_dates += 1
        if srs:
            st_dates += 1
        for r in ors:
            orig_rows += 1
            labels = [r.get(f"計測項目{k}", "") for k in (1, 2, 3)]
            fams = [label_family(x) for x in labels if norm_label(x)]
            nf = len([x for x in fams if x])
            two_metric_rows += int(nf == 2)
            three_metric_rows += int(nf >= 3)
            for fam in fams:
                if fam:
                    label_families[fam] += 1
            ours = {"straight": 0.5, "lap": 0.5, "turn": 0.5}
            for k, lab in enumerate(labels, 1):
                fam = label_family(lab)
                if fam is None:
                    continue
                vals = {b: _f(r.get(f"艇{b}_値{k}")) for b in range(1, 7)}
                ours[fam] = rank_score(vals, 4, True)
            ref = original_scores(r, 4)
            if any(abs(float(ours[k]) - float(ref[k])) > 1e-12 for k in ours):
                lane4_score_mismatch += 1
        for r in srs:
            st_rows += 1
            for b in range(1, 7):
                v = _f(r.get(f"艇{b}_スタート展示"))
                negative_st += int(v is not None and v < 0)
        d += timedelta(days=1)
    return {
        "window": [str(START), str(END)],
        "source": "BoatraceCSV via backtest.rows",
        "result_or_payout_files_read": False,
        "original_dates": orig_dates,
        "st_dates": st_dates,
        "original_rows": orig_rows,
        "st_rows": st_rows,
        "label_family_rows": label_families,
        "two_metric_rows": two_metric_rows,
        "three_metric_rows": three_metric_rows,
        "lane4_score_mismatch": lane4_score_mismatch,
        "negative_st_values": negative_st,
    }


def self_test():
    t = "data=\n1\t3\n一周\tまわり足\t直線\n" + "\n".join([
        "1\tA\t6.80\t6.10\t6.90", "2\tB\t6.75\t6.05\t6.85", "3\tC\t6.70\t6.00\t6.80",
        "4\tD\t6.65\t5.95\t6.75", "5\tE\t6.85\t6.15\t6.95", "6\tF\t6.90\t6.20\t7.00",
    ])
    p = parse_original_exhibition_tsv(t)
    assert p["status"] == 1
    assert set(p["labels"]) == {"一周", "まわり足", "直線"}
    assert set(original_lane4_scores(p)) == {"straight", "lap", "turn"}
    assert parse_st_value(".08", "F") == -0.08
    assert parse_st_value(".09", "") == 0.09
    assert parse_st_value(".03", "L") is None
    st = parse_start_display_tsv("4\tname\tx\tx\t.08\tF\n5\tname\tx\tx\t.03\tL")
    assert st[4] == -0.08 and st[5] is None
    t2 = "data=\n1\t2\n一周\t直線\n1\tA\t6.8\t6.9\n4\tD\t6.7\t6.8\n"
    assert original_lane4_scores(parse_original_exhibition_tsv(t2))["turn"] == 0.5


def main():
    self_test()
    h = historical_audit()
    status = "PASS" if h["lane4_score_mismatch"] == 0 and h["original_rows"] > 0 and h["st_rows"] > 0 else "FAIL"
    report = {
        "status": status,
        "scope": "HEAD4 BOATCAST parser/source-contract and Apr-Jun result-free semantic parity",
        "production_hookup": False,
        "frozen_cutoff": "2026-06-30",
        "jul_aug_used": False,
        "september_outcomes_used": False,
        "v291_changed": False,
        "source_contract": {
            "original_url": "https://race.boatcast.jp/txt/{jo:02d}/bc_oriten_{YYYYMMDD}_{jo:02d}_{race:02d}.txt",
            "st_url": "https://race.boatcast.jp/hp_txt/{jo:02d}/bc_j_stt_{YYYYMMDD}_{jo:02d}_{race:02d}.txt",
            "original_mapping": "label-driven; lower raw value ranks higher; lane4 rank score",
            "st_F": "negative numeric",
            "st_L": "missing/fail-closed upstream",
        },
        "historical": h,
        "decision": "Accept parser contract/archived feature semantics if PASS; production hookup remains rejected until raw BOATCAST-vs-archived value parity is demonstrated.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
