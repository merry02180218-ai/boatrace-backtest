#!/usr/bin/env python3
"""Prospective, result-blind shadow runner for frozen HEAD4_B3_WR_ST_SHADOW_V1.

This runner never submits a wager. It freezes the model/market decision before the
race deadline in an append-only audit ledger so the record can be settled later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from build_4head_env_entry_live import assemble as assemble_env
from build_4head_v283_rows_live import derive as derive_v283
from head4_v291_downstream_inference import (
    load_artifact as load_downstream,
    score_conditional_third,
    score_env_entry,
    score_second,
)
import run_20260911_4head_v291_live as market

POLICY = "HEAD4_B3_WR_ST_SHADOW_V1"
DEFAULT_AUDIT = "shadow_audit_4head_b3_wrst.jsonl"
FORBIDDEN_KEYS = {
    "result", "results", "race_result", "payout", "settlement", "return_yen",
    "actual_head4", "hit", "y4head", "kimarite", "1着_艇番", "払戻", "払戻金",
}


def file_sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record_sha256(row: dict) -> str:
    raw = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_keys(v)


def verify_result_blind(src: dict, deadline: datetime) -> dict:
    bad = sorted({k for k in walk_keys(src) if k in FORBIDDEN_KEYS})
    if bad:
        raise RuntimeError("forbidden result/payout keys: " + ",".join(bad))
    prov = src.get("input_provenance")
    if not isinstance(prov, dict):
        raise RuntimeError("input_provenance is required")
    if prov.get("head_policy_id") != POLICY:
        raise RuntimeError("wrong head_policy_id")
    if prov.get("result_blind") is not True:
        raise RuntimeError("result_blind provenance required")
    if prov.get("post_sources_complete") is not True:
        raise RuntimeError("POST source set not proven complete")
    h = str(prov.get("source_manifest_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", h):
        raise RuntimeError("invalid source_manifest_sha256")
    captured = datetime.fromisoformat(str(prov.get("captured_at_jst", "")))
    if captured.tzinfo is None:
        raise RuntimeError("captured_at_jst must be timezone-aware")
    if captured.astimezone(market.JST) >= deadline:
        raise RuntimeError("causal bundle was not frozen before deadline")
    return prov


def assemble_downstream(src: dict) -> dict:
    pre = float(src["PRE"])
    post = float(src["POST"])
    down = load_downstream()
    env_row = assemble_env(src.get("env_primitives") or {}, pre, post, down)
    env = score_env_entry(env_row, down)
    second_rows, cond_rows = derive_v283({"boats": src.get("boats") or {}}, down)
    p2 = score_second(second_rows, down)
    cond = score_conditional_third(cond_rows, down)
    return {
        "race_code": str(src["race_code"]).zfill(12),
        "PRE": pre,
        "POST": post,
        "ENV_ENTRY": env,
        "p2": {str(k): float(v) for k, v in p2.items()},
        "cond": {f"{s}>{t}": float(v) for (s, t), v in cond.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-json", required=True)
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--jcd", required=True, type=int)
    ap.add_argument("--race", required=True, type=int)
    ap.add_argument("--deadline-jst", required=True)
    ap.add_argument("--audit", default=DEFAULT_AUDIT)
    a = ap.parse_args()
    t0 = time.perf_counter()
    deadline = market.parse_deadline(a.deadline_jst)
    try:
        market.require_before_deadline(deadline, "shadow startup")
        src = json.loads(Path(a.input_json).read_text(encoding="utf-8"))
        prov = verify_result_blind(src, deadline)
        code = f"{a.date}{a.jcd:02d}{a.race:02d}"
        if str(src.get("race_code", "")).zfill(12) != code:
            raise RuntimeError("race_code mismatch")
        prepared = assemble_downstream(src)
        pre, post, env = float(prepared["PRE"]), float(prepared["POST"]), float(prepared["ENV_ENTRY"])
        if not market.s_eligible(pre, post, env):
            row = {
                "race_code": code,
                "policy": POLICY,
                "shadow_only": True,
                "production_action_taken": False,
                "decision": "SHADOW_NO_BET",
                "reason": "S_GATE_FAIL",
                "scores": {"PRE": pre, "POST": post, "ENV_ENTRY": env},
                "thresholds": {"PRE": market.PRE_CUT, "POST": market.POST_CUT, "ENV_ENTRY": market.ENV_ENTRY_CUT},
                "theoretical_total_stake": 0,
                "odds_requested": False,
                "result_or_payout_used": False,
            }
        else:
            odds, meta = market.fetch_odds(a.date, a.jcd, a.race, deadline)
            base = market.evaluate_market(prepared, odds, meta, deadline)
            raw_decision = base["decision"]
            row = dict(base)
            row.update({
                "policy": POLICY,
                "base_market_policy": "HEAD4_V291_COMP7",
                "shadow_only": True,
                "production_action_taken": False,
                "market_decision": raw_decision,
                "decision": "SHADOW_BET" if raw_decision == "BET" else "SHADOW_PASS",
                "theoretical_total_stake": int(base.get("total_stake", 0)),
                "result_or_payout_used": False,
            })
            row.pop("total_stake", None)
        row["input_provenance"] = prov
        row["input_sha256"] = file_sha256(a.input_json)
        row["decision_time_jst"] = market.require_before_deadline(deadline, "immediately before shadow freeze").isoformat()
        row["deadline_jst"] = deadline.isoformat()
        row["deadline_state"] = "SHADOW_FROZEN_BEFORE_DEADLINE"
        row["seconds"] = time.perf_counter() - t0
        row["decision_record_sha256"] = record_sha256(row)
        market.persist_audit(a.audit, row)
        print(json.dumps(row, ensure_ascii=False, indent=2))
    except Exception as e:
        err = {
            "policy": POLICY,
            "shadow_only": True,
            "production_action_taken": False,
            "decision": "ERROR_NO_SHADOW_DECISION",
            "error": str(e),
            "deadline_jst": deadline.isoformat(),
            "now_jst": market.now_jst().isoformat(),
            "result_or_payout_used": False,
            "seconds": time.perf_counter() - t0,
        }
        print(json.dumps(err, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
