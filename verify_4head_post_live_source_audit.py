#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "artifacts/head4_post_live_source_audit_v1.json"
LINEAGE = ROOT / "artifacts/head4_post_feature_lineage_v1.json"

EXPECTED = [
    "ex_st_rank4", "ex_st_4", "ex_st_edge_4v3",
    "orig_straight4", "orig_lap4", "orig_turn4", "tilt4",
]
AVAILABLE = {"ex_st_rank4", "ex_st_4", "ex_st_edge_4v3", "tilt4"}
UNPROVEN = {"orig_straight4", "orig_lap4", "orig_turn4"}


def main() -> None:
    a = json.loads(AUDIT.read_text(encoding="utf-8"))
    l = json.loads(LINEAGE.read_text(encoding="utf-8"))
    feats = a["post_exhibition_features"]
    assert list(feats) == EXPECTED, (list(feats), EXPECTED)
    lineage_post = [x for x in l["feature_order"] if x in EXPECTED]
    assert lineage_post == EXPECTED, (lineage_post, EXPECTED)
    for k in AVAILABLE:
        assert feats[k]["status"] == "SOURCE_AVAILABLE_MAPPING_PENDING_VALUE_PARITY", (k, feats[k])
        assert feats[k].get("official_beforeinfo_source"), k
    for k in UNPROVEN:
        assert feats[k]["status"] == "UNPROVEN_SOURCE_FAIL_CLOSED", (k, feats[k])
        assert feats[k].get("official_beforeinfo_source") is None, k
    assert a["summary"] == {
        "source_available": 4,
        "unproven": 3,
        "complete_live_post_builder_authorized": False,
    }
    assert "NON-PRISTINE" in a["outcome_policy"]["jul_aug_2026"]
    assert "outcome-blind" in a["outcome_policy"]["sep_2026"]
    assert a["decision"].startswith("ACCEPT source-availability audit only")
    print("PASS: HEAD4 POST live source audit is fail-closed (4 available / 3 unproven)")


if __name__ == "__main__":
    main()
