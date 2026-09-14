#!/usr/bin/env python3
from __future__ import annotations

from datetime import date

from assemble_4head_b3_wrst_aug31_history_variant import (
    HISTORY_FIELDS,
    POLICY,
    VariantError,
    _schemas,
    assemble,
)


def make_current20() -> dict:
    _, current20 = _schemas()
    return {
        "race_code": "202609140101",
        "source_provenance": {
            "result_blind": True,
            "complete": True,
            "captured_at_jst": "2026-09-14T09:00:00+09:00",
        },
        "boats": {
            str(b): {f: float(b) + i / 100.0 for i, f in enumerate(current20)}
            for b in range(1, 7)
        },
    }


def make_history() -> dict:
    return {
        "target_date": "2026-09-14",
        "history_end": "2026-08-31",
        "september_outcomes_read": False,
        "jul_aug_outcomes_allowed": True,
        "exact_for_target": False,
        "usable_for_exact_v283": False,
        "boats": {
            str(b): {f: 0.1 * b + i / 1000.0 for i, f in enumerate(HISTORY_FIELDS)}
            for b in range(1, 7)
        },
    }


def main() -> None:
    current = make_current20()
    history = make_history()
    z = assemble(
        current_obj=current,
        history_obj=history,
        race_code="202609140101",
        target_date=date(2026, 9, 14),
        deadline_jst="2026-09-14T10:00:00+09:00",
    )
    assert z["policy"] == POLICY
    assert z["exact_for_target"] is False
    assert z["usable_for_frozen_exact_v283"] is False
    assert z["production_action_authorized"] is False
    assert z["september_outcomes_used"] is False
    assert z["history_cutoff"] == "2026-08-31"
    assert len(z["boats"]) == 6
    assert all(len(row) == 25 for row in z["boats"].values())
    for b in range(1, 7):
        for f in HISTORY_FIELDS:
            assert z["boats"][str(b)][f] == history["boats"][str(b)][f]

    # Refuse any history object that claims September outcomes were read.
    bad = make_history()
    bad["september_outcomes_read"] = True
    try:
        assemble(
            current_obj=current, history_obj=bad, race_code="202609140101",
            target_date=date(2026, 9, 14),
            deadline_jst="2026-09-14T10:00:00+09:00",
        )
    except VariantError as e:
        assert "September outcomes" in str(e)
    else:
        raise AssertionError("September-outcome history was accepted")

    # Refuse any truncated object that falsely claims exact v283 usability.
    bad = make_history()
    bad["usable_for_exact_v283"] = True
    try:
        assemble(
            current_obj=current, history_obj=bad, race_code="202609140101",
            target_date=date(2026, 9, 14),
            deadline_jst="2026-09-14T10:00:00+09:00",
        )
    except VariantError as e:
        assert "exact v283" in str(e)
    else:
        raise AssertionError("false exact-v283 history was accepted")

    # Refuse current inputs frozen at or after deadline.
    bad_current = make_current20()
    bad_current["source_provenance"]["captured_at_jst"] = "2026-09-14T10:00:00+09:00"
    try:
        assemble(
            current_obj=bad_current, history_obj=history, race_code="202609140101",
            target_date=date(2026, 9, 14),
            deadline_jst="2026-09-14T10:00:00+09:00",
        )
    except VariantError as e:
        assert "before deadline" in str(e)
    else:
        raise AssertionError("late current snapshot was accepted")

    print("HEAD4 WR_ST Aug31-history verification variant PASS")


if __name__ == "__main__":
    main()
