#!/usr/bin/env python3
"""Fail-closed 2026-09-11 HEAD4_V291_COMP7 orchestration.

This wrapper consumes the frozen PRE scan output. It is deliberately result-blind.
For today's zero-PRE-candidate state it completes successfully without touching
POST/exhibition/opponent/odds paths. If a PRE candidate exists, it refuses to
fabricate missing LIVE POST/ENV_ENTRY/v282 inference and exits non-zero until
those frozen final inference artifacts are explicitly wired.

PRODUCTION INVARIANTS — DO NOT RELAX WITHOUT EXPLICIT USER POLICY CHANGE:
- 2026-07/08 are NON-PRISTINE; never use them for performance tuning, threshold
  selection, model selection, or rescue logic. Feature-parity checks may inspect
  inputs/outputs only and must ignore outcomes.
- 2026-09 is outcome-blind. Do not use September results, payouts, hit/miss state,
  or same-day outcomes for fit/calibration/threshold/rescue or before decision freeze.
- v96 is prohibited in the production route, including fallback/rescue use.
- Only a complete official 120-way trifecta odds snapshot fetched before deadline
  is valid. Never substitute post-deadline odds.
- Missing, stale, incomplete, or unverifiable required LIVE input must fail closed
  as ERROR_NO_BET; never fabricate or impute with ad-hoc/current data.
- Never call .fit() / refit on July, August, September, or current LIVE rows.
  POST / ENV_ENTRY / v283 must use the exact frozen <=2026-06-30 recipe/artifacts.
- Persist prospective decision audit before any result/payout endpoint is used.
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

PRODUCTION_INVARIANTS = {
    "jul_aug_2026_non_pristine": True,
    "jul_aug_performance_tuning_prohibited": True,
    "sep_2026_outcome_blind": True,
    "sep_fit_calibration_threshold_rescue_prohibited": True,
    "v96_prohibited": True,
    "official_pre_deadline_odds_only": True,
    "post_deadline_odds_fallback_prohibited": True,
    "required_input_failure_mode": "ERROR_NO_BET",
    "live_refit_prohibited": True,
    "frozen_training_cutoff": "2026-06-30",
    "audit_must_precede_result_or_payout": True,
}


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
        "production_invariants": PRODUCTION_INVARIANTS,
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
    #
    # Specifically prohibited here:
    # - Jul/Aug/Sep labels or outcomes for fitting/tuning/rescue
    # - any v96 fallback
    # - any current/LIVE .fit() or refit
    # - post-deadline odds substitution
    # - guessed/dummy downstream model outputs
    audit.update({
        "status": "BLOCKED_MISSING_FROZEN_DOWNSTREAM_INFERENCE_ARTIFACT",
        "downstream_requested": False,
        "required_next": [
            "frozen final POST inference through 2026-06-30",
            "frozen final ENV_ENTRY inference through 2026-06-30",
            "frozen final v282 SECOND and conditional THIRD inference artifacts",
        ],
        "failure_mode_if_live_inputs_unavailable": "ERROR_NO_BET",
        "note": "No fallback, v96, post-cutoff labels, LIVE refit, September outcomes, or post-deadline odds are allowed.",
    })
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise RuntimeError(audit["status"] + ": " + ",".join(eligible.race_code.tolist()))


if __name__ == "__main__":
    main()
