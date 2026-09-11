#!/usr/bin/env python3
"""Fail-closed 2026-09-11 HEAD4_V291_COMP7 orchestration.

This wrapper consumes the frozen PRE scan output.  It is deliberately result-blind.
For today's zero-PRE-candidate state it completes successfully without touching
POST/exhibition/opponent/odds paths.  If a PRE candidate exists, it refuses to
fabricate missing LIVE POST/ENV_ENTRY/v282 inference and exits non-zero until
those frozen final inference artifacts are explicitly wired.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

POLICY = "HEAD4_V291_COMP7"
PRE_CUT = 0.28
PRE = Path("scan_20260911_4head_v291_pre.csv")
OUT = Path("pipeline_20260911_4head_v291_audit.json")
JST = timezone(timedelta(hours=9))


def main() -> None:
    if not PRE.exists():
        raise RuntimeError(f"missing PRE scan: {PRE}")
    q = pd.read_csv(PRE, dtype={"race_code": str})
    if "PRE" not in q.columns:
        raise RuntimeError("PRE column missing")
    q["race_code"] = q.race_code.astype(str).str.zfill(12)
    eligible = q[pd.to_numeric(q.PRE, errors="coerce") >= PRE_CUT].copy()
    audit = {
        "policy": POLICY,
        "target_date": "2026-09-11",
        "generated_at_jst": datetime.now(JST).isoformat(),
        "result_blind": True,
        "pre_cut_inclusive": PRE_CUT,
        "pre_rows": int(len(q)),
        "pre_eligible_rows": int(len(eligible)),
        "pre_eligible_race_codes": eligible.race_code.tolist(),
        "result_or_payout_used": False,
    }
    if eligible.empty:
        audit.update({
            "status": "COMPLETE_NO_PRE_CANDIDATE",
            "downstream_requested": False,
            "post_requested": False,
            "env_entry_requested": False,
            "v282_v283_requested": False,
            "odds_requested": False,
            "bet_count": 0,
            "note": "Frozen PRE gate eliminated all races; downstream must not run.",
        })
        OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return

    # Fail closed. Historical v250/v264/v282 scripts are walk-forward research
    # programs, not persisted final LIVE inference artifacts. Re-training or
    # inventing an inference recipe here would change the frozen prospective
    # semantics after seeing September inputs.
    audit.update({
        "status": "BLOCKED_MISSING_FROZEN_DOWNSTREAM_INFERENCE_ARTIFACT",
        "downstream_requested": False,
        "required_next": [
            "frozen final POST inference through 2026-06-30",
            "frozen final ENV_ENTRY inference through 2026-06-30",
            "frozen final v282 SECOND and conditional THIRD inference artifacts",
        ],
        "note": "No fallback, v96, post-cutoff labels, or September outcomes are allowed.",
    })
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise RuntimeError(audit["status"] + ": " + ",".join(eligible.race_code.tolist()))


if __name__ == "__main__":
    main()
