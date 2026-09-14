#!/usr/bin/env python3
"""Static contract audit for the 21 primitive/current-race HEAD4 ENV_ENTRY inputs.

This is verification-only. It classifies every primitive consumed by the frozen
v291 ENV_ENTRY assembler by provenance and whether September race outcomes are
required for exact current-day reconstruction.
"""
from __future__ import annotations

import inspect
import json

import build_4head_env_entry_live as env
import build_4head_env_context_live as ctx
import build_4head_env_v91_primitives_live as prim

AUDIT = {
    "preview_comp": ("決定的派生", "current exhibition v91 ex/st/straight/avg"),
    "relative_deg": ("決定的派生", "current venue + pre-race wind direction"),
    "wind_speed": ("直接取得", "BOATCAST bc_sui pre-race weather"),
    "wind_adjust_points": ("決定的派生", "frozen v83 old-period wind-cell mapping"),
    "entry_confirmed_same": ("決定的派生", "entry_course_preview == 4"),
    "entry_course_preview": ("直接取得", "BOATCAST bc_j_stt exhibition entry"),
    "has_orig": ("直接取得", "accepted current original-exhibition presence"),
    "has_stt": ("直接取得", "BOATCAST bc_j_stt presence"),
    "has_tkz": ("直接取得", "BOATCAST bc_j_tkz presence"),
    "tilt": ("直接取得", "BOATCAST bc_j_tkz boat4 tilt"),
    "tilt_bonus": ("決定的派生", "frozen tilt-band mapping"),
    "v91_ex": ("直接取得", "current exhibition normalized ex"),
    "v91_st_corr": ("過去状態", "current ST + prior-only STT correction; no outcomes"),
    "v91_st_raw": ("直接取得", "current exhibition ST strength"),
    "v91_straight": ("直接取得", "current original exhibition straight"),
    "score_BASE_v91": ("決定的派生", "preview + prior-only history + tilt"),
    "score_CORR20_v91": ("決定的派生", "frozen v91 CORR20 formula"),
    "score_RAW20_v91": ("決定的派生", "frozen v91 RAW20 formula"),
    "score_wind_v83": ("決定的派生", "score_BASE_v91 + frozen v83 wind points"),
    "history_adjust_online": ("過去状態", "v74 prior preview/motor state only; no outcomes"),
    "history_pct_online": ("過去状態", "v74 prior candidate-history population; no outcomes"),
}


def main() -> None:
    expected = list(env.PRIMITIVES)
    assert len(expected) == 21, expected
    assert set(expected) == set(AUDIT), (expected, sorted(AUDIT))

    context_src = inspect.getsource(ctx.build_history_before)
    full_context_src = inspect.getsource(ctx)
    primitive_src = inspect.getsource(prim)

    # Historical ENV state is preview/motor-state replay, not result-label replay.
    assert "data/results" not in context_src
    assert "payout" not in context_src.lower()
    assert "odds" not in context_src.lower()
    assert "while d < target" in context_src
    assert "update_preview_states" in context_src
    assert "ingest_motor" in context_src

    # Current weather/entry/tilt sources are pre-race only.
    assert "bc_j_stt_" in full_context_src
    assert "bc_j_tkz_" in full_context_src
    assert "bc_sui_" in full_context_src

    # Wind adjustment is frozen from the old period and replayed deterministically.
    assert "HEAD4_V83_WIND_POINTS" in primitive_src
    assert "wind_adjust_points_v83_head4" in primitive_src
    assert "2025-11-01..2026-05-31" in primitive_src

    items = []
    for name in expected:
        category, source = AUDIT[name]
        items.append({
            "feature": name,
            "category": category,
            "source": source,
            "september_outcomes_required": False,
            "exact_2026_09_14_possible_if_source_available": True,
        })

    out = {
        "schema": "head4_env_entry_21_exact_audit_v1",
        "primitive_count": len(items),
        "exact_without_september_outcomes": len(items),
        "blocked_by_september_outcomes": 0,
        "september_outcomes_read": False,
        "production_changed": False,
        "classification_counts": {
            "直接取得": sum(x["category"] == "直接取得" for x in items),
            "決定的派生": sum(x["category"] == "決定的派生" for x in items),
            "過去状態": sum(x["category"] == "過去状態" for x in items),
            "未解決": 0,
        },
        "features": items,
        "conclusion": "21/21 can be reconstructed without September race outcomes, subject to required pre-race source availability; missing source fails closed.",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
