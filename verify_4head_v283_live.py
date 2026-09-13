#!/usr/bin/env python3
from __future__ import annotations

import copy
import math

from build_4head_v283_live import V283LiveBuildError, assemble_conditional, assemble_second
from head4_v291_downstream_inference import BOATS, load_artifact, score_conditional_third, score_second, v283_top4


def main() -> None:
    a = load_artifact()
    sst = a["v283_SECOND"]
    cst = a["v283_COND_THIRD"]
    assert len(sst["features"]) == 25
    assert len(cst["features"]) == 69

    second = []
    for b in BOATS:
        r = {"boat": b}
        r.update(dict(zip(sst["features"], sst["imputer_median"])))
        second.append(r)
    cond = []
    for s in BOATS:
        for t in BOATS:
            if s == t:
                continue
            r = {"second_boat": s, "third_boat": t}
            r.update(dict(zip(cst["features"], cst["imputer_median"])))
            cond.append(r)

    srows = assemble_second(second, a)
    crows = assemble_conditional(cond, a)
    assert len(srows) == 5 and len(crows) == 20
    p2 = score_second(srows, a)
    pc = score_conditional_third(crows, a)
    assert set(p2) == set(BOATS) and abs(sum(p2.values()) - 1.0) < 1e-12
    for s in BOATS:
        assert abs(sum(pc[(s, t)] for t in BOATS if t != s) - 1.0) < 1e-12
    top4 = v283_top4(p2, pc)
    assert len(top4) == 4 and len(set(top4)) == 4

    bad = copy.deepcopy(second); bad[0].pop(sst["features"][0])
    try:
        assemble_second(bad, a)
    except V283LiveBuildError:
        pass
    else:
        raise AssertionError("missing SECOND feature did not fail closed")

    badc = copy.deepcopy(cond); badc.pop()
    try:
        assemble_conditional(badc, a)
    except V283LiveBuildError:
        pass
    else:
        raise AssertionError("missing conditional row did not fail closed")

    assert a["jul_aug_labels_used"] is False
    assert a["september_labels_used"] is False
    assert a["v96_production_signal_used"] is False
    assert a["parity"]["v283"]["second_max_abs"] <= a["parity"]["v283"]["tol"]
    assert a["parity"]["v283"]["conditional_max_abs"] <= a["parity"]["v283"]["tol"]
    print("HEAD4 v283 SECOND5/conditional20 live adapter contract PASS")


if __name__ == "__main__":
    main()
