#!/usr/bin/env python3
"""Validate and normalize current-day causal sources for HEAD4_B3_WR_ST_SHADOW_V1.

Research-shadow only. This module never fetches race results, settles outcomes, or
submits wagers. It only accepts complete, pre-deadline, result-blind snapshots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from build_4head_env_entry_live import PRIMITIVES as ENV_PRIMITIVES
from head4_v291_downstream_inference import load_artifact

POLICY = "HEAD4_B3_WR_ST_SHADOW_V1"
DEFAULT_DOWNSTREAM = "artifacts/head4_v291_downstream_20260630.json"
POST_FIELDS = (
    "ex_st_rank4", "ex_st_4", "ex_st_edge_4v3", "orig_straight4",
    "orig_lap4", "orig_turn4", "tilt4",
)
POST_FIELD_SOURCES = {
    "ex_st_rank4": "official_beforeinfo",
    "ex_st_4": "official_beforeinfo",
    "ex_st_edge_4v3": "official_beforeinfo",
    "tilt4": "official_beforeinfo",
    "orig_straight4": "boatcast",
    "orig_lap4": "boatcast",
    "orig_turn4": "boatcast",
}
FORBIDDEN_KEYS = {
    "result", "results", "race_result", "payout", "settlement", "return_yen",
    "actual_head4", "hit", "y4head", "kimarite", "1着_艇番", "払戻", "払戻金",
}


class CurrentSourceError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise CurrentSourceError(f"{path}: JSON object required")
    return obj


def _walk_keys(obj: Any):
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            yield str(key)
            yield from _walk_keys(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk_keys(value)


def _assert_result_blind(obj: Mapping[str, Any], label: str) -> None:
    bad = sorted({key for key in _walk_keys(obj) if key in FORBIDDEN_KEYS})
    if bad:
        raise CurrentSourceError(f"{label}: forbidden result/payout keys: {','.join(bad)}")


def _finite(name: str, value: Any) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError) as exc:
        raise CurrentSourceError(f"invalid {name}") from exc
    if not math.isfinite(x):
        raise CurrentSourceError(f"non-finite {name}")
    return x


def _aware(value: Any, name: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise CurrentSourceError(f"invalid {name}") from exc
    if dt.tzinfo is None:
        raise CurrentSourceError(f"{name} must be timezone-aware")
    return dt


def _race_code(obj: Mapping[str, Any], expected: str, label: str) -> None:
    got = str(obj.get("race_code", "")).zfill(12)
    if got != expected:
        raise CurrentSourceError(f"{label}: race_code mismatch: {got!r} != {expected!r}")


def _provenance(
    obj: Mapping[str, Any], *, label: str, deadline: datetime
) -> tuple[dict[str, Any], datetime]:
    prov = obj.get("source_provenance")
    if not isinstance(prov, dict):
        raise CurrentSourceError(f"{label}: source_provenance required")
    if prov.get("result_blind") is not True or prov.get("complete") is not True:
        raise CurrentSourceError(f"{label}: complete result-blind provenance required")
    captured = _aware(prov.get("captured_at_jst", ""), f"{label}.captured_at_jst")
    if captured >= deadline:
        raise CurrentSourceError(f"{label}: snapshot was not frozen before deadline")
    return prov, captured


def _validate_post(obj: Mapping[str, Any], race_code: str, deadline: datetime) -> dict[str, float]:
    _assert_result_blind(obj, "POST")
    _race_code(obj, race_code, "POST")
    prov, _ = _provenance(obj, label="POST", deadline=deadline)
    sources = prov.get("field_sources")
    if not isinstance(sources, Mapping):
        raise CurrentSourceError("POST: source_provenance.field_sources required")
    for field, expected in POST_FIELD_SOURCES.items():
        if str(sources.get(field, "")).strip().lower() != expected:
            raise CurrentSourceError(f"POST: {field} must be proven from {expected}")
    features = obj.get("features")
    if not isinstance(features, Mapping):
        raise CurrentSourceError("POST: features mapping required")
    missing = [name for name in POST_FIELDS if name not in features]
    if missing:
        raise CurrentSourceError("POST: missing features: " + ",".join(missing))
    return {name: _finite(f"POST.{name}", features[name]) for name in POST_FIELDS}


def _validate_env(obj: Mapping[str, Any], race_code: str, deadline: datetime) -> dict[str, float]:
    _assert_result_blind(obj, "ENV")
    _race_code(obj, race_code, "ENV")
    _provenance(obj, label="ENV", deadline=deadline)
    raw = obj.get("primitives")
    if not isinstance(raw, Mapping):
        raise CurrentSourceError("ENV: primitives mapping required")
    missing = [name for name in ENV_PRIMITIVES if name not in raw]
    if missing:
        raise CurrentSourceError("ENV: missing primitives: " + ",".join(missing))
    return {name: _finite(f"ENV.{name}", raw[name]) for name in ENV_PRIMITIVES}


def _second_features(artifact_path: str) -> list[str]:
    artifact = load_artifact(artifact_path)
    features = list(artifact.get("v283_SECOND", {}).get("features") or [])
    if len(features) != 25:
        raise CurrentSourceError("frozen v283 SECOND schema size mismatch")
    return features


def _validate_boats(
    obj: Mapping[str, Any], race_code: str, deadline: datetime, second_features: list[str]
) -> dict[str, dict[str, float]]:
    _assert_result_blind(obj, "BOATS")
    _race_code(obj, race_code, "BOATS")
    _provenance(obj, label="BOATS", deadline=deadline)
    raw = obj.get("boats")
    if not isinstance(raw, Mapping):
        raise CurrentSourceError("BOATS: boats mapping required")
    out: dict[str, dict[str, float]] = {}
    for boat in range(1, 7):
        row = raw.get(str(boat), raw.get(boat))
        if not isinstance(row, Mapping):
            raise CurrentSourceError(f"BOATS: missing boat row {boat}")
        missing = [name for name in second_features if name not in row]
        if missing:
            raise CurrentSourceError(
                f"BOATS: boat {boat} missing SECOND primitives: " + ",".join(missing)
            )
        out[str(boat)] = {
            name: _finite(f"BOATS.{boat}.{name}", row[name])
            for name in second_features
        }
    return out


def validate_and_normalize(
    *, post_path: Path, env_path: Path, boats_path: Path, race_code: str,
    deadline_jst: str, artifact_path: str = DEFAULT_DOWNSTREAM,
) -> dict[str, Any]:
    code = str(race_code).zfill(12)
    if len(code) != 12 or not code.isdigit():
        raise CurrentSourceError("race_code must be 12 digits")
    deadline = _aware(deadline_jst, "deadline_jst")
    post_obj, env_obj, boats_obj = _load(post_path), _load(env_path), _load(boats_path)
    post = _validate_post(post_obj, code, deadline)
    env = _validate_env(env_obj, code, deadline)
    second_features = _second_features(artifact_path)
    boats = _validate_boats(boats_obj, code, deadline, second_features)
    captured = [
        _aware(post_obj["source_provenance"]["captured_at_jst"], "POST.captured_at_jst"),
        _aware(env_obj["source_provenance"]["captured_at_jst"], "ENV.captured_at_jst"),
        _aware(boats_obj["source_provenance"]["captured_at_jst"], "BOATS.captured_at_jst"),
    ]
    return {
        "race_code": code,
        "policy": POLICY,
        "result_blind": True,
        "complete": True,
        "post_sources_complete": True,
        "captured_at_jst": max(captured).isoformat(),
        "deadline_jst": deadline.isoformat(),
        "post_features": post,
        "env_primitives": env,
        "boats": boats,
        "v283_second_features": second_features,
        "source_sha256": {
            "post": _sha256(post_path),
            "env": _sha256(env_path),
            "boats": _sha256(boats_path),
        },
        "source_coverage": {
            "POST.beforeinfo": ["ex_st_rank4", "ex_st_4", "ex_st_edge_4v3", "tilt4"],
            "POST.boatcast": ["orig_straight4", "orig_lap4", "orig_turn4"],
            "ENV": "complete external causal snapshot required; no internal recomputation proven",
            "V283_BOATS": "6 complete rows x frozen 25-feature SECOND schema required",
        },
        "production_action_authorized": False,
        "jul_aug_labels_used": False,
        "september_outcomes_used": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--post-json", required=True)
    ap.add_argument("--env-json", required=True)
    ap.add_argument("--boats-json", required=True)
    ap.add_argument("--race-code", required=True)
    ap.add_argument("--deadline-jst", required=True)
    ap.add_argument("--artifact", default=DEFAULT_DOWNSTREAM)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = validate_and_normalize(
        post_path=Path(args.post_json),
        env_path=Path(args.env_json),
        boats_path=Path(args.boats_json),
        race_code=args.race_code,
        deadline_jst=args.deadline_jst,
        artifact_path=args.artifact,
    )
    dest = Path(args.out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    normalized_post = {
        "race_code": out["race_code"],
        "features": out["post_features"],
        "source_provenance": _load(Path(args.post_json))["source_provenance"],
    }
    (dest / "post.json").write_text(
        json.dumps(normalized_post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (dest / "env_primitives.json").write_text(
        json.dumps(out["env_primitives"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (dest / "boats.json").write_text(
        json.dumps(out["boats"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {k: v for k, v in out.items() if k not in {"post_features", "env_primitives", "boats"}}
    (dest / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": "CURRENT_SOURCES_VALID_SHADOW_ONLY",
        "race_code": out["race_code"],
        "out_dir": str(dest),
        "production_action_authorized": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
