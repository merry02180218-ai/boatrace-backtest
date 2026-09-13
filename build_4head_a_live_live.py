#!/usr/bin/env python3
"""Fail-closed current-day 17-feature A-LIVE assembler for frozen HEAD4 v291 lineage.

The frozen A layer is HEAD4_V273_A_LIVE_QMAP and is evaluated only outside the
S gate. This module only validates/serializes the exact 17 causal feature keys
required by the frozen artifact and runs frozen inference. It never fits/tunes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping

from head4_v273_a_live_inference import load_artifact, score_a, classify


class ALiveBuildError(RuntimeError):
    pass


def _finite_or_none(name: str, value: Any) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as e:
        raise ALiveBuildError(f"invalid {name}") from e
    if not math.isfinite(x):
        raise ALiveBuildError(f"non-finite {name}")
    return x


def expected_features(artifact: Mapping[str, Any]) -> list[str]:
    fs = list((artifact.get("A_SCORE") or {}).get("features") or [])
    if len(fs) != 17 or len(set(fs)) != 17:
        raise ALiveBuildError("frozen A-LIVE schema invalid")
    return fs


def assemble(base: Mapping[str, Any], artifact: Mapping[str, Any]) -> dict[str, float]:
    fs = expected_features(artifact)
    missing = [k for k in fs if k not in base]
    if missing:
        raise ALiveBuildError("missing causal A-LIVE features: " + ",".join(missing))
    row = {k: _finite_or_none(k, base[k]) for k in fs}
    if list(row) != fs:
        raise ALiveBuildError("A-LIVE feature order mismatch")
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-json", required=True, help="result-blind current-race feature JSON")
    ap.add_argument("--pre", required=True, type=float)
    ap.add_argument("--post", required=True, type=float)
    ap.add_argument("--env-entry", required=True, type=float)
    ap.add_argument("--artifact", default="artifacts/head4_v273_a_live_20260630.json")
    ap.add_argument("--out")
    a = ap.parse_args()
    artifact = load_artifact(a.artifact)
    base = json.loads(Path(a.base_json).read_text(encoding="utf-8"))
    row = assemble(base, artifact)
    a_score = score_a(row, artifact)
    cls = classify(a.pre, a.post, a.env_entry, row, artifact)
    payload = {
        "policy": "HEAD4_V273_A_LIVE_QMAP",
        "frozen_training_cutoff": "2026-06-30",
        "production_inference_only": True,
        "result_blind": True,
        "jul_aug_labels_used": False,
        "september_labels_used": False,
        "features": row,
        "A_SCORE_LIVE": a_score,
        "classification": cls,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
