#!/usr/bin/env python3
"""Fail-closed POST scorer for HEAD4_B3_WR_ST_SHADOW_V1.

It consumes one frozen PRE-scan row plus seven proven current exhibition features.
No default substitution is allowed for the seven POST-only inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

import pandas as pd

from head4_b3_wrst_shadow_inference import DEFAULT_ARTIFACT, POLICY, load_artifact, score_post

POST_ONLY = [
    "ex_st_rank4", "ex_st_4", "ex_st_edge_4v3", "orig_straight4",
    "orig_lap4", "orig_turn4", "tilt4",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(v, name):
    try:
        x = float(v)
    except Exception as e:
        raise RuntimeError(f"invalid {name}") from e
    if not math.isfinite(x):
        raise RuntimeError(f"non-finite {name}")
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pre-scan", required=True)
    ap.add_argument("--race-code", required=True)
    ap.add_argument("--post-json", required=True)
    ap.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    code = str(a.race_code).zfill(12)
    pre_path, post_path = Path(a.pre_scan), Path(a.post_json)
    pre = pd.read_csv(pre_path, dtype={"race_code": str})
    pre["race_code"] = pre.race_code.astype(str).str.zfill(12)
    q = pre[pre.race_code == code]
    if len(q) != 1:
        raise RuntimeError(f"race {code} not unique in PRE scan")
    base = q.iloc[0].to_dict()
    src = json.loads(post_path.read_text(encoding="utf-8"))
    if str(src.get("race_code", "")).zfill(12) != code:
        raise RuntimeError("POST race_code mismatch")
    prov = src.get("source_provenance")
    if not isinstance(prov, dict) or prov.get("result_blind") is not True or prov.get("complete") is not True:
        raise RuntimeError("complete result-blind POST source provenance required")
    captured = datetime.fromisoformat(str(prov.get("captured_at_jst", "")))
    if captured.tzinfo is None:
        raise RuntimeError("POST captured_at_jst must be timezone-aware")
    vals = src.get("features") or {}
    missing = [k for k in POST_ONLY if k not in vals]
    if missing:
        raise RuntimeError("missing POST-only features: " + ",".join(missing))
    row = dict(base)
    for k in POST_ONLY:
        row[k] = finite(vals[k], k)
    art = load_artifact(a.artifact)
    post = score_post(row, art)
    out = {
        "race_code": code,
        "head_policy_id": POLICY,
        "PRE": finite(base["PRE"], "PRE"),
        "POST": post,
        "pre_eligible": bool(finite(base["PRE"], "PRE") >= 0.28),
        "post_eligible": bool(post >= 0.25),
        "post_source_provenance": prov,
        "pre_scan_sha256": sha256(pre_path),
        "post_input_sha256": sha256(post_path),
        "head_artifact_sha256": sha256(Path(a.artifact)),
        "result_or_payout_used": False,
        "production_modified": False,
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
