#!/usr/bin/env python3
"""Assemble a verification-only WR_ST v283 input using player history frozen at Aug-31.

This path is deliberately separate from frozen exact v283 and production.
It accepts the 20 v283 SECOND features that do not require September outcomes,
then overlays only the five pref_pl_* features from an Aug-31-truncated player
history object.  The output can never claim exact-current v283 compatibility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping

POLICY = "HEAD4_B3_WR_ST_AUG31_HISTORY_VERIFY_V1"
FROZEN_ARTIFACT = Path("artifacts/head4_v291_downstream_20260630.json")
HISTORY_FIELDS = [
    "pref_pl_all_p2",
    "pref_pl_all_win",
    "pref_pl_frame_p2",
    "pref_pl_recent_p2",
    "pref_pl_frame_win",
]
FORBIDDEN_KEYS = {
    "result", "results", "race_result", "payout", "settlement", "return_yen",
    "actual_head4", "hit", "y4head", "kimarite", "1着_艇番", "払戻", "払戻金",
}


class VariantError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    z = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(z, dict):
        raise VariantError(f"{path}: JSON object required")
    return z


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _walk_keys(obj: Any):
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            yield str(k)
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v)


def _result_blind(obj: Mapping[str, Any], label: str) -> None:
    bad = sorted({k for k in _walk_keys(obj) if k in FORBIDDEN_KEYS})
    if bad:
        raise VariantError(f"{label}: forbidden result/payout keys: {','.join(bad)}")


def _finite(v: Any, label: str) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError) as e:
        raise VariantError(f"{label}: invalid numeric") from e
    if not math.isfinite(x):
        raise VariantError(f"{label}: non-finite")
    return x


def _aware(v: Any, label: str) -> datetime:
    try:
        x = datetime.fromisoformat(str(v))
    except ValueError as e:
        raise VariantError(f"{label}: invalid datetime") from e
    if x.tzinfo is None:
        raise VariantError(f"{label}: timezone-aware datetime required")
    return x


def _schemas() -> tuple[list[str], list[str]]:
    a = json.loads(FROZEN_ARTIFACT.read_text(encoding="utf-8"))
    second = list(a.get("v283_SECOND", {}).get("features") or [])
    if len(second) != 25 or not all(x in second for x in HISTORY_FIELDS):
        raise VariantError("frozen v283 SECOND schema mismatch")
    current20 = [x for x in second if x not in HISTORY_FIELDS]
    if len(current20) != 20:
        raise VariantError("expected 20 non-history SECOND features")
    return second, current20


def assemble(
    *, current_obj: Mapping[str, Any], history_obj: Mapping[str, Any],
    race_code: str, target_date: date, deadline_jst: str,
) -> dict[str, Any]:
    _result_blind(current_obj, "CURRENT20")
    code = str(race_code).zfill(12)
    if len(code) != 12 or not code.isdigit():
        raise VariantError("race_code must be 12 digits")
    if str(current_obj.get("race_code", "")).zfill(12) != code:
        raise VariantError("CURRENT20 race_code mismatch")
    prov = current_obj.get("source_provenance")
    if not isinstance(prov, Mapping):
        raise VariantError("CURRENT20 source_provenance required")
    if prov.get("result_blind") is not True or prov.get("complete") is not True:
        raise VariantError("CURRENT20 complete result-blind provenance required")
    deadline = _aware(deadline_jst, "deadline_jst")
    captured = _aware(prov.get("captured_at_jst", ""), "CURRENT20 captured_at_jst")
    if captured >= deadline:
        raise VariantError("CURRENT20 snapshot must be frozen before deadline")

    # The history object must be the explicitly truncated Aug-31 contract.
    if history_obj.get("september_outcomes_read") is not False:
        raise VariantError("history must prove September outcomes were not read")
    if history_obj.get("jul_aug_outcomes_allowed") is not True:
        raise VariantError("history must identify Jul/Aug outcomes as allowed")
    if history_obj.get("history_end") != "2026-08-31":
        raise VariantError("history_end must be 2026-08-31")
    if history_obj.get("exact_for_target") is not False:
        raise VariantError("truncated history must not claim exact_for_target")
    if history_obj.get("usable_for_exact_v283") is not False:
        raise VariantError("truncated history must not claim exact v283 usability")
    if date.fromisoformat(str(history_obj.get("target_date"))) != target_date:
        raise VariantError("history target_date mismatch")
    if target_date <= date(2026, 9, 1):
        raise VariantError("Aug31 truncated variant is only for targets after 2026-09-01")

    second, current20 = _schemas()
    raw = current_obj.get("boats")
    hist = history_obj.get("boats")
    if not isinstance(raw, Mapping) or not isinstance(hist, Mapping):
        raise VariantError("boats mappings required")

    boats: dict[str, dict[str, float]] = {}
    for b in range(1, 7):
        k = str(b)
        row = raw.get(k, raw.get(b))
        hrow = hist.get(k, hist.get(b))
        if not isinstance(row, Mapping) or not isinstance(hrow, Mapping):
            raise VariantError(f"boat {b}: current/history row required")
        missing20 = [f for f in current20 if f not in row]
        if missing20:
            raise VariantError(f"boat {b}: missing current20: {','.join(missing20)}")
        missing5 = [f for f in HISTORY_FIELDS if f not in hrow]
        if missing5:
            raise VariantError(f"boat {b}: missing history5: {','.join(missing5)}")
        out = {f: _finite(row[f], f"boat{b}.{f}") for f in current20}
        out.update({f: _finite(hrow[f], f"boat{b}.{f}") for f in HISTORY_FIELDS})
        if set(out) != set(second):
            raise VariantError(f"boat {b}: assembled SECOND schema mismatch")
        boats[k] = {f: out[f] for f in second}

    return {
        "schema": "head4_b3_wrst_aug31_history_variant_v1",
        "policy": POLICY,
        "race_code": code,
        "target_date": target_date.isoformat(),
        "history_cutoff": "2026-08-31",
        "history_mode": "AUG31_TRUNCATED_VERIFICATION_ONLY",
        "exact_for_target": False,
        "usable_for_frozen_exact_v283": False,
        "production_action_authorized": False,
        "september_outcomes_used": False,
        "jul_aug_outcomes_allowed": True,
        "result_blind_current_sources": True,
        "current_feature_count_per_boat": 20,
        "history_feature_count_per_boat": 5,
        "assembled_feature_count_per_boat": 25,
        "captured_at_jst": captured.isoformat(),
        "deadline_jst": deadline.isoformat(),
        "boats": boats,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--current20-json", required=True)
    ap.add_argument("--history-json", required=True)
    ap.add_argument("--race-code", required=True)
    ap.add_argument("--target-date", required=True)
    ap.add_argument("--deadline-jst", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cp, hp = Path(a.current20_json), Path(a.history_json)
    z = assemble(
        current_obj=_load(cp), history_obj=_load(hp), race_code=a.race_code,
        target_date=date.fromisoformat(a.target_date), deadline_jst=a.deadline_jst,
    )
    z["source_sha256"] = {"current20": _sha(cp), "aug31_history": _sha(hp)}
    Path(a.out).write_text(json.dumps(z, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "READY_VERIFICATION_ONLY_NOT_EXACT",
        "policy": POLICY,
        "race_code": z["race_code"],
        "out": a.out,
        "production_action_authorized": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
