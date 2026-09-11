#!/usr/bin/env python3
"""Run v298 with the latest verified v297 multi-source settlement audit.

Model/prediction logic stays in v298.  Settlement happens only after PRE features
are frozen and uses the already-audited v297 policy: realtime result first, payout
fallback, archived combo only for a row already present in an official settlement
source.  Scheduled rows absent from official settlement sources are void/unsettled,
not betting losses.  Every officially-settled selected race remains in the final
exact denominator, including boat-1 losses.
"""
import analyze_v298_1head_threat_listwise_trifecta5 as v298
import run_v297_1head_guard_trifecta5_research as settlement


if __name__=='__main__':
    settlement.AUDIT.clear()
    # v298 calls the imported v297 module at settlement time; replace only that
    # post-freeze attachment function with the verified multi-source audit.
    v298.v297.settle_full_after_freeze=settlement.settle_union_after_freeze
    v298.main()
