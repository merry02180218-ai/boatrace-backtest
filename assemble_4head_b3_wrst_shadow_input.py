#!/usr/bin/env python3
"""Assemble one immutable causal bundle for the B3_WR_ST prospective shadow runner."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

POLICY = "HEAD4_B3_WR_ST_SHADOW_V1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def aware(value: str, name: str) -> datetime:
    d = datetime.fromisoformat(str(value))
    if d.tzinfo is None:
        raise RuntimeError(f"{name} must be timezone-aware")
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--head-scores", required=True)
    ap.add_argument("--env-primitives", required=True)
    ap.add_argument("--boats", required=True)
    ap.add_argument("--source-manifest", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    hp, ep, bp, mp = map(Path, (a.head_scores, a.env_primitives, a.boats, a.source_manifest))
    head, env, boats, manifest = load(hp), load(ep), load(bp), load(mp)
    code = str(head.get("race_code", "")).zfill(12)
    if len(code) != 12 or not code.isdigit():
        raise RuntimeError("invalid race_code")
    if head.get("head_policy_id") != POLICY:
        raise RuntimeError("wrong head score policy")
    if head.get("result_or_payout_used") is not False:
        raise RuntimeError("head score provenance is not result-blind")
    if manifest.get("race_code") and str(manifest["race_code"]).zfill(12) != code:
        raise RuntimeError("source manifest race mismatch")
    if manifest.get("result_blind") is not True or manifest.get("complete") is not True:
        raise RuntimeError("complete result-blind source manifest required")
    if manifest.get("post_sources_complete") is not True:
        raise RuntimeError("POST source manifest incomplete")
    captured = aware(manifest.get("captured_at_jst"), "captured_at_jst")
    post_prov = head.get("post_source_provenance") or {}
    if post_prov.get("result_blind") is not True or post_prov.get("complete") is not True:
        raise RuntimeError("POST score provenance incomplete")
    aware(post_prov.get("captured_at_jst"), "POST captured_at_jst")
    payload = {
        "race_code": code,
        "PRE": float(head["PRE"]),
        "POST": float(head["POST"]),
        "env_primitives": env,
        "boats": boats,
        "input_provenance": {
            "head_policy_id": POLICY,
            "result_blind": True,
            "post_sources_complete": True,
            "captured_at_jst": captured.isoformat(),
            "source_manifest_sha256": digest(mp),
            "component_sha256": {
                "head_scores": digest(hp),
                "env_primitives": digest(ep),
                "boats": digest(bp),
            },
            "production_action_authorized": False,
        },
    }
    Path(a.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "READY_SHADOW_ONLY", "race_code": code, "out": a.out, "bundle_sha256": digest(Path(a.out))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
