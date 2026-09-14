#!/usr/bin/env python3
"""Current-day readiness gate for HEAD4_B3_WR_ST_SHADOW_V1.

Verification-only. This gate combines the proven source contracts and refuses to
claim READY when frozen v283 exact-current inputs would require September race
outcomes. Production is never authorized here.
"""
from __future__ import annotations

import json

from build_4head_env_entry_live import PRIMITIVES as ENV_PRIMITIVES
from head4_v291_downstream_inference import load_artifact

ARTIFACT = "artifacts/head4_v291_downstream_20260630.json"
BLOCKED_V283 = [
    "pref_pl_all_p2",
    "pref_pl_all_win",
    "pref_pl_frame_p2",
    "pref_pl_recent_p2",
    "pref_pl_frame_win",
]


def main() -> None:
    artifact = load_artifact(ARTIFACT)
    second = list(artifact.get("v283_SECOND", {}).get("features") or [])
    assert len(ENV_PRIMITIVES) == 21
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
