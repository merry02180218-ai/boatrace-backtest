#!/usr/bin/env python3
"""Offline invariant verifier for HEAD4_V291_COMP7 market runner.

No network and no race result data are accessed.
"""
from __future__ import annotations

from datetime import timedelta

import run_20260911_4head_v291_live as r


def probs():
    p2 = {1: 0.40, 2: 0.30, 3: 0.15, 5: 0.10, 6: 0.05}
    # Each candidate second has deterministic third preference by boat number,
    # with enough variation to exercise the joint-score ordering.
    pc = {}
    for s in r.BOATS:
        rem = [t for t in r.BOATS if t != s]
        weights = [0.50, 0.25, 0.15, 0.10]
        for t, w in zip(rem, weights):
            pc[(s, t)] = w
    return p2, pc


def make_input(pre=r.PRE_CUT, post=r.POST_CUT, env=r.ENV_ENTRY_CUT):
    p2, pc = probs()
    return {
        "race_code": "202609111403",
        "PRE": pre,
        "POST": post,
        "ENV_ENTRY": env,
        "p2": p2,
        "cond": {f"{s}>{t}": v for (s, t), v in pc.items()},
        # Deliberately present junk benchmark data: production logic must ignore it.
        "v96_rank": 1,
    }


def fake_meta():
    return {
        "source": "OFFLINE_TEST",
        "fetched_at_jst": r.now_jst().isoformat(),
        "result_endpoint_requested": False,
        "payout_endpoint_requested": False,
    }


def main():
    # Inclusive S boundaries.
    assert r.s_eligible(r.PRE_CUT, r.POST_CUT, r.ENV_ENTRY_CUT)
    assert not r.s_eligible(r.PRE_CUT - 1e-12, r.POST_CUT, r.ENV_ENTRY_CUT)
    assert not r.s_eligible(r.PRE_CUT, r.POST_CUT - 1e-12, r.ENV_ENTRY_CUT)
    assert not r.s_eligible(r.PRE_CUT, r.POST_CUT, r.ENV_ENTRY_CUT - 1e-12)

    p2, pc = probs()
    top4 = r.v283_top4(p2, pc)
    assert len(top4) == 4 and len(set(top4)) == 4
    assert all(x.startswith("4-") for x in top4)

    # Exact composite boundary: four equal odds 28.0 -> 7.0.
    assert abs(r.composite_odds([28.0] * 4) - 7.0) < 1e-12
    deadline = r.now_jst() + timedelta(hours=1)
    odds7 = {t: 28.0 for t in top4}
    row = r.evaluate_market(make_input(), odds7, fake_meta(), deadline)
    assert row["decision"] == "BET"
    assert abs(row["composite_odds"] - 7.0) < 1e-12
    assert len(row["tickets"]) == 4
    assert row["total_stake"] == 10000
    assert all(x["stake"] > 0 and x["stake"] % 100 == 0 for x in row["tickets"])
    assert row["pair_model"]["v96_used"] is False

    # Just below floor must PASS and never stake.
    odds_low = {t: 27.999 for t in top4}
    row = r.evaluate_market(make_input(), odds_low, fake_meta(), deadline)
    assert row["decision"] == "PASS"
    assert row["composite_odds"] < 7.0
    assert row["total_stake"] == 0
    assert len(row["tickets"]) == 4
    assert all(x["stake"] == 0 for x in row["tickets"])

    # Failed S gate must not become a market candidate.
    row = r.evaluate_market(make_input(pre=r.PRE_CUT - 0.001), {}, {}, deadline)
    assert row["decision"] == "NO_BET"
    assert row["reason"] == "S_GATE_FAIL"
    assert row["total_stake"] == 0

    # Deadline is hard-fail; equality counts as expired.
    try:
        r.require_before_deadline(r.now_jst() - timedelta(seconds=1), "offline-test")
        raise AssertionError("expired deadline accepted")
    except RuntimeError as e:
        assert "deadline passed" in str(e)

    print("PASS: HEAD4_V291_COMP7 live invariants")


if __name__ == "__main__":
    main()
