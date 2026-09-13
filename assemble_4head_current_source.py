#!/usr/bin/env python3
"""Assemble generated causal HEAD4 live components into strict --source-json.

This is a wiring layer only.  It does not fetch results/odds, fit models, tune
thresholds, or invent missing values.  Every generated component must carry the
same race_code and pass its own result-blind metadata contract.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping

from build_4head_current_bundle import build as validate_bundle, BundleBuildError
from build_4head_env_entry_live import PRIMITIVES as ENV_PRIMITIVES


class CurrentSourceAssembleError(RuntimeError):
    pass


def _load(path: str) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise CurrentSourceAssembleError(f"JSON object required: {path}")
    return obj


def _num(name: str, value: Any) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as e:
        raise CurrentSourceAssembleError(f"invalid {name}") from e
    if not math.isfinite(x):
        raise CurrentSourceAssembleError(f"non-finite {name}")
    return x


def _code(obj: Mapping[str, Any], label: str) -> str:
    code = str(obj.get("race_code", "")).zfill(12)
    if len(code) != 12 or not code.isdigit():
        raise CurrentSourceAssembleError(f"invalid {label} race_code")
    return code


def _result_blind(obj: Mapping[str, Any], label: str) -> None:
    if obj.get("result_blind") is not True:
        raise CurrentSourceAssembleError(f"{label} is not explicitly result_blind")
    for key in ("odds_used", "payout_used", "v96_used"):
        if obj.get(key) is True:
            raise CurrentSourceAssembleError(f"{label} forbidden metadata: {key}=true")
    if obj.get("same_day_results_used") is True:
        raise CurrentSourceAssembleError(f"{label} same-day results used")


def assemble(
    race_code: str,
    pre: Any,
    post: Any,
    base_flat: Mapping[str, Any],
    env: Mapping[str, Any],
    exhibition: Mapping[str, Any],
    v93: Mapping[str, Any],
    player: Mapping[str, Any],
) -> dict[str, Any]:
    code = str(race_code).zfill(12)
    if len(code) != 12 or not code.isdigit():
        raise CurrentSourceAssembleError("invalid race_code")

    for obj, label in ((exhibition, "exhibition"), (v93, "v93"), (player, "player")):
        if _code(obj, label) != code:
            raise CurrentSourceAssembleError(f"{label} race_code mismatch")
        _result_blind(obj, label)

    # ENV assembler payload has a result_blind contract and its exact frozen row.
    if env.get("result_blind") is not True:
        raise CurrentSourceAssembleError("ENV_ENTRY payload is not result_blind")
    if env.get("jul_aug_labels_used") is True or env.get("september_labels_used") is True:
        raise CurrentSourceAssembleError("ENV_ENTRY payload used prohibited labels")
    env_features = env.get("features")
    if not isinstance(env_features, Mapping):
        raise CurrentSourceAssembleError("ENV_ENTRY features missing")
    missing_env = [k for k in ENV_PRIMITIVES if k not in env_features]
    if missing_env:
        raise CurrentSourceAssembleError("missing ENV_ENTRY primitives: " + ",".join(missing_env))
    env_primitives = {k: _num(k, env_features[k]) for k in ENV_PRIMITIVES}

    current_boats = exhibition.get("current_boats")
    st_flat = exhibition.get("st_flat")
    v93_flat = v93.get("v93_flat")
    player_flat = player.get("player_flat")
    for value, label in (
        (current_boats, "current_boats"),
        (st_flat, "st_flat"),
        (v93_flat, "v93_flat"),
        (player_flat, "player_flat"),
    ):
        if not isinstance(value, Mapping):
            raise CurrentSourceAssembleError(f"missing {label}")

    # Preserve only explicitly supplied causal base features, then overlay generated
    # primitives so stale/manual duplicates cannot override generated values.
    flat = dict(base_flat)
    flat.update(st_flat)
    flat.update(v93_flat)
    flat.update(player_flat)

    src = {
        "race_code": code,
        "PRE": _num("PRE", pre),
        "POST": _num("POST", post),
        "env_primitives": env_primitives,
        "flat_row": flat,
        "current_boats": dict(current_boats),
        "_source_meta": {
            "result_blind": True,
            "odds_used": False,
            "payout_used": False,
            "same_day_results_used": False,
            "jul_aug_labels_used": False,
            "september_labels_used": False,
            "v96_used": False,
            "player_history_end": player.get("history_end"),
        },
    }

    # Reuse the production adapter itself as the final completeness/leakage guard.
    try:
        validate_bundle(src)
    except BundleBuildError as e:
        raise CurrentSourceAssembleError(f"strict source rejected: {e}") from e
    return src


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--race-code", required=True)
    ap.add_argument("--pre", required=True, type=float)
    ap.add_argument("--post", required=True, type=float)
    ap.add_argument("--base-flat-json", required=True)
    ap.add_argument("--env-json", required=True)
    ap.add_argument("--exhibition-json", required=True)
    ap.add_argument("--v93-json", required=True)
    ap.add_argument("--player-json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = assemble(
        a.race_code,
        a.pre,
        a.post,
        _load(a.base_flat_json),
        _load(a.env_json),
        _load(a.exhibition_json),
        _load(a.v93_json),
        _load(a.player_json),
    )
    Path(a.out).write_text(json.dumps(src, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "READY", "race_code": src["race_code"], "out": a.out}, ensure_ascii=False))


if __name__ == "__main__":
    main()
