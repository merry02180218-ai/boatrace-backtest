#!/usr/bin/env python3
"""Fail-closed current-day v283 SECOND/conditional THIRD adapter for HEAD4 v291.

Input rows must already contain the exact causal pre-deadline feature values
required by the frozen v283 artifact. This adapter validates exact row universes
and frozen feature schemas, then runs inference-only SECOND/THIRD scoring and
TOP2XTOP2 ordering. It does not train, tune, fetch outcomes, or use v96.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from head4_v291_downstream_inference import (
    BOATS,
    FrozenInferenceError,
    load_artifact,
    score_conditional_third,
    score_second,
    v283_top4,
)


class V283LiveBuildError(RuntimeError):
    pass


def _validate_feature_row(row: Mapping[str, Any], features: Sequence[str], label: str) -> dict[str, Any]:
    missing = [k for k in features if k not in row]
    if missing:
        raise V283LiveBuildError(f"missing {label} feature keys: " + ",".join(missing[:12]))
    out: dict[str, Any] = {}
    for k in features:
        v = row[k]
        if v is None:
            # Frozen inference permits present NaN/None only through its exact
            # imputer semantics. Keep None present so the scorer performs that.
            out[k] = None
            continue
        try:
            x = float(v)
        except (TypeError, ValueError) as e:
            raise V283LiveBuildError(f"invalid {label} feature {k}") from e
        if not math.isfinite(x):
            # Explicit NaN is allowed by frozen imputer; +/-inf is never allowed.
            if math.isnan(x):
                out[k] = x
                continue
            raise V283LiveBuildError(f"infinite {label} feature {k}")
        out[k] = x
    return out


def assemble_second(rows: Sequence[Mapping[str, Any]], artifact: Mapping[str, Any]) -> list[dict[str, Any]]:
    fs = list(artifact["v283_SECOND"]["features"])
    if len(fs) != 25 or len(set(fs)) != 25:
        raise V283LiveBuildError("frozen SECOND schema mismatch")
    if len(rows) != 5:
        raise V283LiveBuildError(f"SECOND requires 5 rows, got {len(rows)}")
    out = []
    seen = set()
    for r in rows:
        b = int(r.get("boat", 0))
        if b not in BOATS or b in seen:
            raise V283LiveBuildError(f"invalid/duplicate SECOND boat {b}")
        seen.add(b)
        z = {"boat": b}
        z.update(_validate_feature_row(r, fs, "SECOND"))
        out.append(z)
    if seen != set(BOATS):
        raise V283LiveBuildError("SECOND boat universe mismatch")
    out.sort(key=lambda r: int(r["boat"]))
    return out


def assemble_conditional(rows: Sequence[Mapping[str, Any]], artifact: Mapping[str, Any]) -> list[dict[str, Any]]:
    fs = list(artifact["v283_COND_THIRD"]["features"])
    if len(fs) != 69 or len(set(fs)) != 69:
        raise V283LiveBuildError("frozen conditional THIRD schema mismatch")
    if len(rows) != 20:
        raise V283LiveBuildError(f"conditional THIRD requires 20 rows, got {len(rows)}")
    expected = {(s, t) for s in BOATS for t in BOATS if s != t}
    seen = set()
    out = []
    for r in rows:
        s = int(r.get("second_boat", 0)); t = int(r.get("third_boat", 0))
        if (s, t) not in expected or (s, t) in seen:
            raise V283LiveBuildError(f"invalid/duplicate conditional pair {s}>{t}")
        seen.add((s, t))
        z = {"second_boat": s, "third_boat": t}
        z.update(_validate_feature_row(r, fs, "conditional THIRD"))
        out.append(z)
    if seen != expected:
        raise V283LiveBuildError("conditional THIRD pair universe mismatch")
    out.sort(key=lambda r: (int(r["second_boat"]), int(r["third_boat"])))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-json", required=True, help="JSON with second_rows and conditional_rows")
    ap.add_argument("--artifact", default="artifacts/head4_v291_downstream_20260630.json")
    ap.add_argument("--out")
    a = ap.parse_args()
    artifact = load_artifact(a.artifact)
    src = json.loads(Path(a.input_json).read_text(encoding="utf-8"))
    second = assemble_second(src.get("second_rows") or [], artifact)
    cond = assemble_conditional(src.get("conditional_rows") or [], artifact)
    p2 = score_second(second, artifact)
    pc = score_conditional_third(cond, artifact)
    top4 = v283_top4(p2, pc)
    payload = {
        "policy": "HEAD4_V291_COMP7",
        "frozen_training_cutoff": "2026-06-30",
        "production_inference_only": True,
        "result_blind": True,
        "jul_aug_labels_used": False,
        "september_labels_used": False,
        "v96_used": False,
        "p2": {str(k): v for k, v in p2.items()},
        "cond": {f"{s}>{t}": v for (s, t), v in pc.items()},
        "top4": [[4, s, t] for s, t in top4],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    try:
        main()
    except (V283LiveBuildError, FrozenInferenceError) as e:
        raise SystemExit(str(e))
