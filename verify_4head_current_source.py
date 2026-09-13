#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy

from assemble_4head_current_source import assemble, CurrentSourceAssembleError
from build_4head_current_bundle import build as build_bundle
from build_4head_env_entry_live import PRIMITIVES

CODE = "202609130101"


def fixtures():
    base = {
        "v91_ex": .61,
        "score_CORR20_v91": .62,
        "score_wind_v83": .63,
        "score_RAW20_v91": .64,
        "score_BASE_v91": .65,
        "preview_comp": .66,
    }
    env_features = {k: .5 for k in PRIMITIVES}
    env_features.update({"PRE": .3, "POST": .4, "p4_joint": .12, "post_x_entry_same": .2})
    env = {
        "result_blind": True,
        "jul_aug_labels_used": False,
        "september_labels_used": False,
        "features": env_features,
        "ENV_ENTRY": .3,
    }
    boats = {}
    st = {}
    for b in range(1, 7):
        boats[str(b)] = {
            "cur_ex": .4 + b / 100,
            "cur_st": .5 + b / 100,
            "cur_orig_lap": .6,
            "cur_orig_turn": .61,
            "cur_orig_straight": .62,
            "cur_orig_avg": .63,
        }
        for tail, value in (
            ("raw", .1 + b / 100),
            ("raw_strength", .2 + b / 100),
            ("raw_rank", float(b)),
            ("corr_strength", .3 + b / 100),
            ("corr_rank", float(b)),
        ):
            st[f"st_{tail}_b{b}"] = value
    exhibition = {
        "race_code": CODE,
        "result_blind": True,
        "odds_used": False,
        "current_boats": boats,
        "st_flat": st,
    }
    vf = {}
    for b in (1, 2, 3, 5, 6):
        vf[f"opp_score_b{b}_v93"] = .7
        for k in ("grade", "national", "local", "motor", "waku", "nst", "direct"):
            vf[f"opp_{k}_b{b}_v93"] = .5
    v93 = {"race_code": CODE, "result_blind": True, "odds_used": False, "v96_used": False, "v93_flat": vf}
    pf = {}
    for b in range(1, 7):
        for k in ("all_p2", "all_win", "frame_p2", "recent_p2", "frame_win"):
            pf[f"b{b}_pl_{k}"] = .1 * b
    player = {
        "race_code": CODE,
        "result_blind": True,
        "same_day_results_used": False,
        "odds_used": False,
        "payout_used": False,
        "v96_used": False,
        "history_end": "2026-09-12",
        "player_flat": pf,
    }
    return base, env, exhibition, v93, player


def must_fail(fn, text: str):
    try:
        fn()
    except CurrentSourceAssembleError:
        return
    raise AssertionError(text)


def main():
    base, env, exhibition, v93, player = fixtures()
    src = assemble(CODE, .3, .4, base, env, exhibition, v93, player)
    assert src["race_code"] == CODE
    assert src["_source_meta"]["result_blind"] is True
    assert src["_source_meta"]["player_history_end"] == "2026-09-12"
    assert src["flat_row"]["opp_score_b1_v93"] == .7
    assert src["flat_row"]["b4_pl_all_win"] == .4
    assert src["flat_row"]["st_corr_strength_b6"] == .36
    assert set(src["env_primitives"]) == set(PRIMITIVES)
    bundle = build_bundle(src)
    assert bundle["race_code"] == CODE
    assert len(bundle["boats"]) == 6
    assert len(bundle["a_features"]) == 17

    # Generated primitives must override stale values from a caller-provided base row.
    stale = dict(base)
    stale["b4_pl_all_win"] = 999
    stale["opp_score_b1_v93"] = 999
    stale["st_corr_strength_b6"] = 999
    src2 = assemble(CODE, .3, .4, stale, env, exhibition, v93, player)
    assert src2["flat_row"]["b4_pl_all_win"] == .4
    assert src2["flat_row"]["opp_score_b1_v93"] == .7
    assert src2["flat_row"]["st_corr_strength_b6"] == .36

    bad_v93 = deepcopy(v93)
    bad_v93["race_code"] = "202609130102"
    must_fail(lambda: assemble(CODE, .3, .4, base, env, exhibition, bad_v93, player), "race mismatch accepted")

    bad_player = deepcopy(player)
    bad_player["same_day_results_used"] = True
    must_fail(lambda: assemble(CODE, .3, .4, base, env, exhibition, v93, bad_player), "same-day result leakage accepted")

    bad_env = deepcopy(env)
    bad_env["september_labels_used"] = True
    must_fail(lambda: assemble(CODE, .3, .4, base, bad_env, exhibition, v93, player), "Sep labels accepted")

    leak = dict(base)
    leak["final_odds"] = 12.3
    must_fail(lambda: assemble(CODE, .3, .4, leak, env, exhibition, v93, player), "market leakage accepted")

    print("PASS: strict HEAD4 current source assembly, generated overrides, parity and fail-closed guards")


if __name__ == "__main__":
    main()
