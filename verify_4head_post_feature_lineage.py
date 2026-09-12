#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "artifacts/head4_v291_downstream_20260630.json"
MANIFEST = ROOT / "artifacts/head4_post_feature_lineage_v1.json"
HISTORICAL = ROOT / "analyze_v250_4head_rebuild_baseline.py"


def main() -> None:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = HISTORICAL.read_text(encoding="utf-8")

    frozen = artifact["POST"]["features"]
    declared = manifest["feature_order"]
    details = manifest["features"]

    assert artifact["frozen_training_cutoff"] == "2026-06-30"
    assert artifact["jul_aug_labels_used"] is False
    assert artifact["september_labels_used"] is False
    assert frozen == declared, (frozen, declared)
    assert len(frozen) == 16
    assert set(details) == set(declared)

    # Prove that the manifest points to the exact historical constructor rather
    # than a newly invented formula. This verifier intentionally validates
    # lineage/schema only; it does NOT claim current-day beforeinfo value parity.
    assert "def pre_features(x,s4):" in source
    assert "def post_features(code,tkz,stt,orig):" in source
    for name in declared:
        assert f"'{name}'" in source, name
        item = details[name]
        assert item["stage"] in {"PRE", "POST"}
        assert item["constructor"] in {"pre_features", "post_features"}
        assert item["expression"]
        assert item["source_lineage"]
        assert item["live_status"]

    assert manifest["decision"].startswith("ACCEPT lineage/schema manifest only")
    assert "NOT approval" in manifest["decision"]
    print("HEAD4_POST_LINEAGE_SCHEMA_OK 16/16")


if __name__ == "__main__":
    main()
