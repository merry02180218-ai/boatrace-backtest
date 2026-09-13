#!/usr/bin/env python3
"""Result-free serialization-lineage audit for frozen HEAD4 v291 POST inputs.

This audit closes the remaining raw-source provenance question without reading
race results.  It pins the exact BoatraceCSV commit that scrapes BOATCAST and
verifies that original-exhibition labels/raw numeric values and start-display ST
are serialized to the archived preview CSV representation without a hidden
model-side transform.

No Jul/Aug outcomes or September outcomes are read.  v291 and betting policy are
not modified.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

PIN = "563c69ccd28853b8b4953489c673877a9dfeb4e8"
BASE = f"https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/{PIN}/"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts" / "head4_boatcast_serialization_lineage_20260630.json"
SEMANTIC = ROOT / "artifacts" / "head4_boatcast_parity_contract_20260630.json"

FILES = {
    "original_scraper": "scripts/boatrace/original_exhibition_scraper.py",
    "preview_scraper": "scripts/boatrace/preview_tsv_scraper.py",
    "converter": "scripts/boatrace/converter.py",
}


def fetch(path: str) -> str:
    req = urllib.request.Request(
        BASE + path,
        headers={"User-Agent": "Mozilla/5.0 HEAD4-lineage-audit"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def require(text: str, needles: list[str], name: str) -> None:
    missing = [x for x in needles if x not in text]
    if missing:
        raise AssertionError(f"{name}: pinned source contract changed/missing: {missing}")


def main() -> None:
    src = {k: fetch(v) for k, v in FILES.items()}

    # BOATCAST original-exhibition TSV -> typed values.
    require(
        src["original_scraper"],
        [
            "bc_oriten_{date_yyyymmdd}_{jo}_{rno}.txt",
            "data.measure_labels =",
            "value1=_to_float(parts[2])",
            "value2=_to_float(parts[3])",
            "value3=_to_float(parts[4])",
            "return float(cleaned)",
        ],
        "original scraper",
    )

    # Typed original-exhibition values -> CSV: labels and values are emitted
    # directly; only None -> blank / Python numeric -> string formatting occurs.
    require(
        src["converter"],
        [
            "labels = list(data.measure_labels) + [\"\"] * 3",
            "boat.value1",
            "boat.value2",
            "boat.value3",
            "def _fmt_optional(value) -> str:",
            "return str(value)",
            "writer.writerow(original_exhibition_to_row(item))",
        ],
        "original converter",
    )

    # BOATCAST start-display TSV -> RacePreview start_timing.
    require(
        src["preview_scraper"],
        [
            '"bc_j_stt"',
            "st_value = cols[4]",
            "st_flag = cols[5].strip()",
            'if flag == "L":',
            'if flag == "F":',
            "return -abs(parsed)",
            '"start_timing": self._parse_start_timing(st_value, st_flag)',
        ],
        "preview ST scraper",
    )

    # RacePreview start_timing -> archived CSV directly.
    require(
        src["converter"],
        [
            "str(boat.start_timing) if boat.start_timing is not None else \"\"",
            "writer.writerow(row)",
        ],
        "preview converter",
    )

    semantic = json.loads(SEMANTIC.read_text(encoding="utf-8"))
    hist = semantic["historical"]
    assert semantic["status"] == "PASS", semantic
    assert semantic["production_hookup"] is False
    assert semantic["jul_aug_used"] is False
    assert semantic["september_outcomes_used"] is False
    assert semantic["v291_changed"] is False
    assert hist["result_or_payout_files_read"] is False
    assert hist["lane4_score_mismatch"] == 0
    assert hist["original_rows"] == 12250
    assert hist["st_rows"] == 12749

    report = {
        "status": "PASS",
        "scope": "HEAD4 BOATCAST raw-parser -> archived CSV serialization lineage -> frozen v291 POST semantic parity",
        "pinned_boatracecsv_commit": PIN,
        "result_or_payout_files_read": False,
        "jul_aug_outcomes_used": False,
        "september_outcomes_used": False,
        "v291_changed": False,
        "betting_overlay_changed": False,
        "evidence": {
            "original_exhibition": "BOATCAST TSV labels/value1..3 are parsed to floats then written directly as measure_labels/value1..3 CSV cells; None alone becomes blank.",
            "start_display": "BOATCAST ST value+flag is normalized by pinned parser (F negative, L missing) then RacePreview.start_timing is written directly to CSV.",
            "archived_semantic_parity": {
                "original_rows": hist["original_rows"],
                "st_rows": hist["st_rows"],
                "lane4_score_mismatch": hist["lane4_score_mismatch"],
            },
        },
        "decision": "ACCEPT archived Apr-Jun BoatraceCSV preview representation as the exact serialized output of the pinned BOATCAST parser lineage for the fields used here. This closes the prior hidden-transform concern; production wiring still requires the current-day fail-closed builder/field-completeness CI.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
