# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch `research/3head-player-attack-mode`; production v288 unchanged 94R/52 hits/ROI172.560638%.
- Pre-deadline inputs only; exact v288 exclusion preserved. Jul/Aug NON-PRISTINE. September outcomes UNREAD.

## Reproducible base
- March eligible 4,482R; Wave54 210R/71 heads=33.8095%.
- February eligible 3,970R/478 boat3 heads.
- Current reproducible opponent baseline remains direct ordered-pair C=.25: March 25/71, ¥62,830, ROI99.7302%.
- v4 no_local rejected on frozen March diagnostic (23/71, ROI89.4444%).

## BEFORE WORK — exhibition/original-exhibition venue-aware research (2026-09-16)
- User identified 1head Workflow ID 358760350 as the reference implementation family.
- Verified latest 1head implementation path: `audit_v351_venue_aware_rebuild.py` imports `run_v326_1head_ticketaware_exhibition.py`, whose `corrected_direct()` uses lane/frame correction from `backtest_v3.CORR`, start-exhibition lane bias learned causally from prior data, then within-race relative ranks. Venue-aware v351 selects optional original-exhibition feature groups by venue only when >=80% available; common exhibition + start exhibition require all six boats.
- For 3head, do NOT mix current exhibition into PRE candidate extraction. Build a separate post-exhibition/final layer on the frozen Wave54/PRE universe.
- Reuse the 1head correction contract exactly where applicable: raw exhibition/original metrics -> lane correction -> relative rank; start exhibition -> causal lane-bias correction -> relative rank; original metric labels normalized per venue/source availability.
- First audit February/March availability by venue without reading September outcomes. Then compare baseline vs exhibition-only vs exhibition+original venue-aware features using February-only selection. Freeze before any March settlement diagnostic.
- For opponent ranking, add candidate/boat3 and second/third relative direct-info gaps; for 3head final filter also audit boat3 direct strength vs field. No realized kimarite as input.
- Preserve deterministic 3 tickets/R and current baseline unless a successor wins the predeclared validation and frozen March diagnostic. Production unchanged; September UNREAD.

## Availability audit completed
- Fixed audit Run 34987709625 / Job 104443998031 / Artifact 10403679769 completed success.
- 47 venue-month rows generated for Feb/Mar. Common exhibition/start exhibition is broadly available; original-exhibition availability is venue-specific.
- JCD03 has no original-exhibition group in this source. JCD12/13/18 have turn/lap but straight is absent, confirming that original fields must be selected per venue rather than globally.

## BEFORE NEXT EXECUTION — venue-aware model comparison
- Start now from the successful availability audit. Implement executable v5 comparison on the fixed historical source.
- Candidate A = frozen direct C=.25 baseline; B = baseline + corrected exhibition/start-exhibition; C = B + venue-aware original exhibition fields using the 1head >=80% availability contract.
- February-only grouped validation decides/freeze. March outcomes remain unopened until the winner is frozen; then exactly one March diagnostic. September outcomes remain UNREAD throughout.
- Record feature counts, eligible/readiness counts, February fold metrics, frozen choice, March 3-ticket hits/stake/return/ROI, deterministic output hash, Run/Job/Artifact IDs, and conclusion.
- Production v288 remains unchanged.

## IMPLEMENTATION CORRECTION BEFORE FIRST VALID FREEZE
- Run 34992010310 / Job 104458764351 / Artifact 10405946917 executed, but its February counts were 489 heads for A and 394 common-ready heads for B/C. This violates the canonical February baseline of 478 heads and does not compare A/B/C on the same ready universe. Therefore its frozen winner B is INVALID and must not be used for March.
- Before any March settlement read, repair v5 to copy canonical eligibility/exclusion/source preparation from `research/rebuild_3head_opponent_v1.py`, require A/B/C comparison on one identical common-ready February universe, compute global OOF top3 capture plus fold metrics, and compute venue original `avg` readiness directly rather than `any(metric)`.
- Re-run February only after the repair. Only the repaired run may freeze A/B/C. September outcomes remain UNREAD; production v288 unchanged.

## Exact restart point
- Repair v5 canonical eligibility/common-ready comparison, run a fresh February-only freeze, then and only then run one frozen March diagnostic and write AFTER result.
