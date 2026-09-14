#!/usr/bin/env python3
from __future__ import annotations

from datetime import date

from build_4head_v283_player_history_julaug import (
    PlayerHistoryBuildError,
    build_for_card,
)


def card(code: str, names: list[str]) -> dict[str, str]:
    z = {"レースコード": code}
    for b, n in enumerate(names, 1):
        z[f"艇{b}_選手名"] = n
    return z


def result(code: str, winner: int, second: int) -> dict[str, str]:
    return {"レースコード": code, "1着_艇番": str(winner), "2着_艇番": str(second)}


def main() -> None:
    names = [f"選手{b}" for b in range(1, 7)]
    target_card = card("202609010101", names)

    # Sparse synthetic loader: only two allowed completed races matter.  The
    # builder still scans the full causal date range but never requests Sep outcomes.
    calls = []
    def loader(d: date):
        calls.append(d)
        if d == date(2026, 7, 1):
            return [card("202607010101", names)], [result("202607010101", 1, 2)]
        if d == date(2026, 8, 31):
            return [card("202608310101", names)], [result("202608310101", 2, 1)]
        return [], []

    z = build_for_card(date(2026, 9, 1), target_card, day_loader=loader)
    assert z["exact_for_target"] is True
    assert z["usable_for_exact_v283"] is True
    assert z["september_outcomes_read"] is False
    assert z["jul_aug_outcomes_allowed"] is True
    assert z["jul_aug_result_rows_ingested"] == 2
    assert max(calls) == date(2026, 8, 31)

    # boat 1: two races, one win and two top2 finishes.
    b1 = z["boats"]["1"]
    assert abs(b1["pref_pl_all_win"] - ((1 + 2/6) / 4)) < 1e-12
    assert abs(b1["pref_pl_all_p2"] - ((2 + 2/3) / 4)) < 1e-12
    assert abs(b1["pref_pl_recent_p2"] - 1.0) < 1e-12
    assert abs(b1["pref_pl_frame_win"] - ((1 + 3*.125) / 5)) < 1e-12
    assert abs(b1["pref_pl_frame_p2"] - ((2 + 3*.25) / 5)) < 1e-12

    # Exact Sep-14 reconstruction must refuse because it would require Sep 1-13 outcomes.
    try:
        build_for_card(date(2026, 9, 14), target_card, day_loader=loader)
    except PlayerHistoryBuildError as e:
        assert "September outcomes" in str(e)
    else:
        raise AssertionError("Sep-14 exact history did not fail closed")

    # Audit/truncated mode may expose the Aug-31 snapshot, but must mark it unusable
    # for exact v283 inference and still must not request September outcomes.
    calls.clear()
    t = build_for_card(date(2026, 9, 14), target_card, allow_truncated=True, day_loader=loader)
    assert t["exact_for_target"] is False
    assert t["usable_for_exact_v283"] is False
    assert t["history_end"] == "2026-08-31"
    assert t["september_outcomes_read"] is False
    assert max(calls) == date(2026, 8, 31)

    print("HEAD4 v283 Jul-Aug player-history causal contract PASS")


if __name__ == "__main__":
    main()
