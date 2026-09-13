#!/usr/bin/env python3
"""Fail-closed current-day ENV_ENTRY assembler for frozen HEAD4 v291.

This module does not fetch outcomes, fit a model, or tune thresholds.  It takes a
causal/result-blind current-race base feature row plus already frozen PRE/POST
probabilities and emits the exact 25-feature ENV_ENTRY row expected by
artifacts/head4_v291_downstream_20260630.json.

Source acquisition for the 21 primitive/current-race fields is deliberately kept
separate so each source can be parity-audited.  Missing/non-finite primitives fail
closed; no production median/default is invented here.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping

from head4_v291_downstream_inference import load_artifact, score_env_entry

EXPECTED = [
    "PRE", "POST", "preview_comp", "relative_deg", "wind_speed",
    "wind_adjust_points", "entry_confirmed_same", "entry_course_preview",
    "has_orig", "has_stt", "has_tkz", "tilt", "tilt_bonus", "v91_ex",
    "v91_st_corr", "v91_st_raw", "v91_straight", "score_BASE_v91",
    "score_CORR20_v91", "score_RAW20_v91", "score_wind_v83",
    "history_adjust_online", "history_pct_online", "p4_joint",
    "post_x_entry_same",
]
DERIVED = {"PRE", "POST", "p4_joint", "post_x_entry_same"}
PRIMITIVES = [x for x in EXPECTED if x not in DERIVED]


class EnvEntryBuildError(RuntimeError):
    pass


def _finite(name: str, value: Any) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as e:
        raise EnvEntryBuildError(f"invalid {name}") from e
    if not math.isfinite(x):
        raise EnvEntryBuildError(f"non-finite {name}")
    return x


def assemble(base: Mapping[str, Any], pre: Any, post: Any, artifact: Mapping[str, Any]) -> dict[str, float]:
    features = list(artifact.get("ENV_ENTRY", {}).get("features") or [])
    if features != EXPECTED:
        raise EnvEntryBuildError("frozen ENV_ENTRY schema/order mismatch")
    missing = [k for k in PRIMITIVES if k not in base]
    if missing:
        raise EnvEntryBuildError("missing causal ENV_ENTRY primitives: " + ",".join(missing))
    row = {k: _finite(k, base[k]) for k in PRIMITIVES}
    row["PRE"] = _finite("PRE", pre)
    row["POST"] = _finite("POST", post)
    row["p4_joint"] = row["PRE"] * row["POST"]
    row["post_x_entry_same"] = row["POST"] * row["entry_confirmed_same"]
    # Preserve exact frozen order for JSON/audit readability.
    out = {k: row[k] for k in EXPECTED}
    if any(not math.isfinite(v) for v in out.values()):
        raise EnvEntryBuildError("non-finite assembled ENV_ENTRY row")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-json", required=True, help="result-blind primitive feature JSON")
    ap.add_argument("--pre", required=True, type=float)
    ap.add_argument("--post", required=True, type=float)
    ap.add_argument("--artifact", default="artifacts/head4_v291_downstream_20260630.json")
    ap.add_argument("--out")
    a = ap.parse_args()
    artifact = load_artifact(a.artifact)
    base = json.loads(Path(a.base_json).read_text(encoding="utf-8"))
    row = assemble(base, a.pre, a.post, artifact)
    payload = {
        "policy": "HEAD4_V291_COMP7",
        "frozen_training_cutoff": "2026-06-30",
        "result_blind": True,
        "jul_aug_labels_used": False,
        "september_labels_used": False,
        "features": row,
        "ENV_ENTRY": score_env_entry(row, artifact),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")

if __name__ == "__main__":
    main()
