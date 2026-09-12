# CHAT_HANDOFF_20260912_1HEAD_OPPONENT_AUTORESEARCH

## Scope / fixed rules
1号艇頭モデルを固定したうえで、相手選び（SECOND / THIRD / ordered-pair / exact 3-ticket）をゼロベースで自動研究する。最新GitHubを常に優先する。

- Fixed evaluation cohort: **345 races**.
- Boat-1 head hits: **290/345 = 84.06%**.
- Boat-1 losses remain misses in final exact-trifecta denominator.
- Boat-1 head model remains frozen at v308 during opponent research.
- Jul/Aug 2026 are **NON-PRISTINE**.
- September outcomes remain **unread / outcome-blind** unless latest repo explicitly changes this.
- `meet_*` forbidden unless separately causally reconstructed/audited.
- Never use same-race/later-race results, end-of-day aggregates, post-race exhibition, payouts/results or future-contaminated reconstructions as predictors.
- Monthly walk-forward: month M trains only before M.
- Missing p3/p4 is never future-backfilled.
- Every opponent experiment must assert **345R / 290 head hits** before scoring.

## v313 cache-first rule — mandatory
Committed reusable causal cache is mandatory:
- `cache_v313_1head_opponent_pre.csv.gz`: 35,462 rows / 580 cols
- `cache_v313_1head_opponent_p3.csv.gz`: 21,692 races
- `cache_v313_1head_opponent_p4.csv.gz`: 22,271 races
- manifest `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`
- cache commit `326b9a3c73af383b31ed799fa00f7e762cce9988`
Do not silently fall back to heavy full reconstruction.

## Clean benchmark — v309
- exact3 **132/345 = 38.26%**
- SECOND TOP2 **71.72%**
- conditional THIRD TOP2 given actual SECOND **72.76%**
- SECOND TOP2 by actual boat: 2=98.25%, 3=84.27%, 4=35.71%, 5=18.75%, 6=0%
Main bottleneck is SECOND, especially 4/5/6.

## v310 causal p3/p4
Best `HEADRISK_L2_3`: SECOND TOP2 72.07%, exact3 133/345=38.55%, boat4 38.10%, boat5 18.75%, boat6 0%. Small auxiliary gain only.

## v311 feature-family
Development best `DROP_START`: SECOND TOP2 **72.41%**, outer 4/5/6 **26.44%**, exact3 **136/345=39.42%**, worst-month TOP2 60.00%. Development-only.

## v312 outer gate — completed
Result commit `6d7a2a31d079547885b68cfece3a1a2de22f1211`.
Best `GATE_C0.35_O5.0`:
- SECOND TOP2 **73.10%**
- exact3 **136/345=39.42%**
- outer 4/5/6 **28.74%**
- boat2 98.25%, boat3 83.15%, boat4 47.62%, boat5 15.62%, boat6 0%
- monthly TOP2 Feb 74.51, Mar 60.00, Apr 79.17, May 77.23, Jun 64.00
Boat4 recovery only; 5/6 unresolved.

## v314 role-split SECOND — completed
Successful result commit `d07beaa35c8bd4f62beb391e1cc877189cc34d21` after dynamic specialist group-size fix `29b944d825cb856eb3c0955e1a5f64e10932b755`.
Actual SECOND TOP2 by boat: 2=94.74%, 3=75.28%, 4=45.24%, 5=25.00%, 6=7.69%.
Monthly TOP2: Feb 68.63%, Mar 53.33%, Apr 77.08%, May 75.25%, Jun 62.67%.
Recovered some 5/6 but sacrificed inner 2/3; do not promote.

## v315 pairwise SECOND — completed
Result commit `2419b4e2887b47a6d64f9a4e2339ce1c15b760e1`.
DROP_START base: TOP2 72.41%, outer 26.44%, exact3 136/345=39.42%, worst month 60.00%.
Best `PAIR_ow1.0_m1.00`:
- SECOND TOP2 **72.76%** (+0.35pp)
- outer **27.59%** (+1.15pp)
- exact3 **133/345=38.55%** (worse)
- boat2 99.12%, boat3 83.15%, boat4 40.48%, boat5 18.75%, boat6 7.69%
- monthly TOP2 Feb 72.55%, Mar 60.00%, Apr 79.17%, May 76.24%, Jun 66.67%
Decision: weak gain; do not micro-tune pairwise.

## v316 multiclass SECOND — completed
Files:
- `run_v316_1head_opponent_multiclass_second.py`
- `.github/workflows/research-20260913-v316-multiclass-second.yml`
Result commit: **`56fa0eba373f9a512ce68634beaaf91346add9d7`**.
Summary: `summary_v316_1head_opponent_multiclass_second.md`.

Initial run failed only due sklearn API compatibility; workflow was pinned to scikit-learn 1.6.1 and rerun `34721463366` completed successfully.
Best `MC_ow1.0_m0.50`:
- SECOND TOP2 **72.76%** vs DROP_START 72.41% (+0.35pp)
- outer 4/5/6 TOP2 **27.59%** vs 26.44%
- exact3 **136/345=39.42%** (unchanged from DROP_START)
- worst-month TOP2 **66.67%** vs 60.00%
- by actual SECOND: boat2 97.37%, boat3 85.39%, boat4 42.86%, boat5 18.75%, boat6 0%
- monthly TOP2: Feb 72.55%, Mar 66.67%, Apr 79.17%, May 75.25%, Jun 66.67%
Decision: stability improved but total/outer gain is only +0.35/+1.15pp and boat5/6 remains unresolved. Under the <=0.5pp rule this is weak; do not micro-tune multiclass.

## v317 CURRENT — error-driven causal PRE/prior SECOND feature engineering
Files:
- `run_v317_1head_opponent_error_features.py`
- `.github/workflows/research-20260913-v317-error-features.yml`
Implementation commit: **`d1d913be6f57d3f5d7678fa0de4f257824f03a93`**.
Workflow commit: **`9c38d51d736c963ac115ca183e2c301f2f6681bc`**.

Design:
- fixed 345R/290 head hits
- v313 cache only; no full reconstruction
- no `meet_*`; no future backfill; month M trains only before M
- THIRD frozen at v300 conditional L2=.1
- preserves strongest clean formulation by dropping START family
- adds only derived interactions from already-audited PRE/prior features with outer-route / boat5 / boat6 identity
- candidate safe source families include causal p3/p4 (`v310_*`), motor, player/form, lane/position, prior turn/straight/overall/vh/gh transforms
- compares OUTER / HEADRISK / BOAT56 / FULL interaction modes with small L2 grid
- Feb-Jun development only; Jul/Aug NON-PRISTINE; September unread

Fresh automation/chat MUST check the newest v317 workflow first. If v317 fails, inspect exact logs and fix/restart. If it succeeds, record results here and continue automatically.

## Automatic branch sequence
1. v311 feature-family attribution — completed.
2. v312 outer gating — completed.
3. v314 role-split SECOND — completed, unstable.
4. v315 pairwise SECOND — completed, weak.
5. v316 multiclass SECOND — completed, weak but more stable.
6. **v317 error-driven causal PRE/prior feature engineering — CURRENT.**
7. If v317 remains weak/unstable, SECOND model classes are considered saturated enough to rebuild conditional THIRD separately while preserving the best clean SECOND reference.
8. If factorized SECOND×THIRD remains limiting, direct 20 ordered `(second,third)` pair model.
9. After ranking/probability models stabilize, optimize exactly-3-ticket policy.
10. Suspicious large gain -> immediate leakage/causal audit.

## Required metrics every experiment
- exact3 on full 345 denominator
- SECOND TOP1/TOP2/TOP3 on 290 boat1-head-win races
- conditional THIRD TOP1/TOP2/TOP3 when relevant
- by actual SECOND boat 2/3/4/5/6
- outer 4/5/6 capture
- monthly breakdown and worst month
- delta vs clean BASE

## Decision rules
- SECOND TOP2 gain <= about 0.5pp with essentially unchanged outer capture => weak; switch model class/target rather than micro-tune.
- Gain concentrated in one month/boat => audit stability.
- Outer capture improves while inner 2/3 collapses enough to reduce overall TOP2/exact3 => gated blend only.
- When SECOND is no longer dominant or safe SECOND variants saturate, move to THIRD/ordered-pair based on latest decomposition.
- Promotion requires leak-safe implementation, stable monthly behavior, production-compatible calibration and prospective/outcome-blind validation.

## Self-continuing rule — mandatory
A failed/flat experiment is diagnostic evidence, not a stopping condition. If research is found stopped and the next leak-safe branch is clear, implement/start it automatically and update this handoff. Do not merely report that it stopped.
