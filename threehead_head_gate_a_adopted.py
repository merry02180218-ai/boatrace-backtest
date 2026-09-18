from __future__ import annotations

import math
from typing import Mapping, Any

ADOPTED_HEAD_GATE_NAME = "3HEAD_A_PRECISION_V1"
RACE_NO_MIN = 1
RACE_NO_MAX = 12
PRE_PERCENTILE_MIN = 0.925
MOTOR_EWMA_RANK_EDGE_VS2_MIN = 0.20
EXHIBITION_RANK3_MAX = 1.0

REQUIRED_FIELDS = (
    "race_no",
    "pre_score",
    "post_motor_rank_edge2",
    "post_ex_rank3",
)

def _finite_number(v: Any) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None

def passes_adopted_head_gate(row: Mapping[str, Any]) -> bool:
    """
    Frozen adopted 3-head A_precision head-candidate gate.

    Semantics:
      - race 1..12
      - frozen enhanced-PRE percentile >= .925
      - boat3 prior-day motor EWMA-rank edge vs boat2 >= +.20
      - boat3 current exhibition-time rank == 1

    Missing/non-finite inputs fail closed.
    """
    vals = {k: _finite_number(row.get(k)) for k in REQUIRED_FIELDS}
    if any(v is None for v in vals.values()):
        return False

    return (
        RACE_NO_MIN <= vals["race_no"] <= RACE_NO_MAX
        and vals["pre_score"] >= PRE_PERCENTILE_MIN
        and vals["post_motor_rank_edge2"] >= MOTOR_EWMA_RANK_EDGE_VS2_MIN
        and vals["post_ex_rank3"] <= EXHIBITION_RANK3_MAX
    )
