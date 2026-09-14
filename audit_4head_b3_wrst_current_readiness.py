#!/usr/bin/env python3
"""Current-day readiness gate for HEAD4_B3_WR_ST_SHADOW_V1.

Verification-only. This gate combines the proven source contracts and refuses to
claim READY when frozen v283 exact-current inputs would require September race
outcomes. Production is never authorized here.

This audit intentionally uses only the Python standard library so CI does not
need the full model-runtime dependency stack merely to verify the frozen schema.
"""
from __future__ import annotations

import json
from pathlib import Path

ARTIFACT = Path("artifacts/head4_v291_downstream_20260630.json")
ENV_PRIMITIVES = [
    "preview_comp", "relative_deg", "wind_speed", "wind_adjust_points",
    "entry_confirmed_same", "entry_course_preview", "has_orig", "has_stt",
    "has_tkz", "tilt", "tilt_bonus", "v91_ex", "v91_st_corr", "v91_st_raw",
    "v91_straight", "score_BASE_v91", "score_CORR20_v91", "score_RAW20_v91",
    "score_wind_v83", "history_adjust_online", "history_pct_online",
]
BLOCKED_V283 = [
    "pref_pl_all_p2",
    "pref_pl_all_win",
    "pref_pl_frame_p2",
    "pref_pl_recent_p2",
    "pref_pl_frame_win",
]


def main() -> None:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    second = list(artifact.get("v283_SECOND", {}).get("features") or [])
    assert len(ENV_PRIMITIVES) == 21
    assert len(set(ENV_PRIMITIVES)) == 21
    assert len(second) == 25
    assert all(x in second for x in BLOCKED_V283)
    exact_v283 = [x for x in second if x not in BLOCKED_V283]
    assert len(exact_v283) == 20

    report = {
        "schema": "head4_b3_wrst_current_readiness_v1",
        "policy": "HEAD4_B3_WR_ST_SHADOW_V1",
        "production_policy": "HEAD4_V291_COMP7",
        "production_changed": False,
        "production_action_authorized": False,
        "september_outcomes_read": False,
        "jul_aug_outcomes_allowed": True,
        "target_example": "2026-09-14",
        "groups": {
            "POST": {
                "status": "READY_IF_PREDEADLINE_SOURCES_AVAILABLE",
                "fields": 7,
                "september_outcomes_required": False,
            },
            "ENV_ENTRY_PRIMITIVES": {
                "status": "READY_IF_PREDEADLINE_SOURCES_AVAILABLE",
                "exact_fields": 21,
                "total_fields": 21,
                "september_outcomes_required": False,
            },
            "V283_SECOND": {
                "status": "BLOCKED_FOR_EXACT_2026_09_14_UNDER_SEPTEMBER_UNREAD",
                "exact_fields_without_september_outcomes": 20,
                "total_fields": 25,
                "blocked_fields": BLOCKED_V283,
                "blocked_reason": "exact player-history state for Sep-14 requires Sep-01..Sep-13 race outcomes",
            },
        },
        "overall_status": "BLOCKED_EXACT_V283_SEPTEMBER_UNREAD",
        "may_emit_frozen_exact_wrst_decision": False,
        "allowed_next_action": "verification-only truncated/alternate history variant must be explicitly separated from frozen exact v283 and production",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
