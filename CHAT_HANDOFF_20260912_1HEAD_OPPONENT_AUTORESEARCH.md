# CHAT_HANDOFF_20260912_1HEAD_OPPONENT_AUTORESEARCH

## Fixed rules
1号艇頭モデルv308を固定し、相手選び SECOND / THIRD / ordered-pair / exact-3-ticket を自動研究する。最新GitHub優先。
- Fixed cohort **345 races**, boat1 head hits **290/345=84.06%**. Boat1 losses remain misses in exact denominator.
- Jul/Aug 2026 **NON-PRISTINE**; September outcomes **unread/outcome-blind**.
- `meet_*` forbidden unless separately causal-audited. No same/later-race result, end-of-day aggregate, post-race exhibition, payout/result or future-contaminated predictor.
- Month M trains only before M. Missing p3/p4 never future-backfilled.
- Every opponent experiment asserts **345R / 290 head hits**.

## v313 cache-first mandatory
Use committed causal cache only; do not silently rebuild heavy history:
- `cache_v313_1head_opponent_pre.csv.gz` 35,462 rows / 580 cols
- `cache_v313_1head_opponent_p3.csv.gz` 21,692 races
- `cache_v313_1head_opponent_p4.csv.gz` 22,271 races
- manifest `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`, commit `326b9a3c73af383b31ed799fa00f7e762cce9988`.

## Benchmarks and completed SECOND research
v309 clean base: exact3 **132/345=38.26%**, SECOND TOP2 **71.72%**, conditional THIRD TOP2 **72.76%**. SECOND TOP2 by actual boat: 2=98.25, 3=84.27, 4=35.71, 5=18.75, 6=0%. Main bottleneck was outer SECOND.

v310 causal p3/p4: best SECOND TOP2 72.07%, exact3 133/345; small auxiliary gain.

v311 DROP_START: SECOND TOP2 72.41%, outer456 26.44%, exact3 136/345=39.42%, worst month 60%; development-only.

v312 outer gate, result `6d7a2a31d079547885b68cfece3a1a2de22f1211`: SECOND TOP2 **73.10%**, outer456 **28.74%**, exact3 136/345. Boat4 improved to 47.62%, boat5 15.62%, boat6 0%; sparse/unstable.

v314 role split, result `d07beaa35c8bd4f62beb391e1cc877189cc34d21`: boat TOP2 2=94.74,3=75.28,4=45.24,5=25.00,6=7.69%; sacrificed inner boats, unstable, no promotion.

v315 pairwise, result `2419b4e2887b47a6d64f9a4e2339ce1c15b760e1`: SECOND TOP2 72.76%, outer 27.59%, exact3 133/345; weak.

v316 multiclass, result `56fa0eba373f9a512ce68634beaaf91346add9d7`: SECOND TOP2 72.76%, outer 27.59%, exact3 136/345, worst month 66.67%; stable but weak, 5/6 unresolved.

## v317 completed — error-driven causal SECOND features
Workflow run **34724618109** completed successfully. Result commit pushed by workflow after rebase (log shows main advanced to `397d4ac...`). Summary `summary_v317_1head_opponent_error_features.md`.
- Frozen **345R / 290 head hits** confirmed.
- Best **OUTER_L2_1**: SECOND TOP2 **72.76%**, outer456 **28.74%**, exact3 **137/345=39.71%**, worst-month SECOND TOP2 **66.67%**.
- By actual SECOND: boat2 97.37%, boat3 84.27%, boat4 45.24%, boat5 18.75%, boat6 0%.
- Monthly TOP2: Feb 70.59, Mar 66.67, Apr 79.17, May 75.25, Jun 68.00%.
- BOAT56 variants could recover boat6 to 15.38% and outer456 to 29.89%, but overall TOP2 fell to 72.07% and exact3 did not improve, so not selected.
Decision: overall SECOND TOP2 did not improve beyond the <=0.5pp saturation rule. Safe SECOND model classes are sufficiently saturated; move target to conditional THIRD rather than micro-tune SECOND.

## v318 CURRENT — conditional THIRD rebuild
Files:
- `run_v318_1head_opponent_third_rebuild.py`
- `.github/workflows/research-20260913-v318-third-rebuild.yml`
Implementation commit **`06c03db1cc4ec67aed86f34ce26ac54477a6c354`**; workflow commit **`2be175120b73e400e09bcbe919062be60559dcd8`**.

Design:
- fixed 345R/290 head hits; v313 cache only; no `meet_*`; no future backfill; month M trains only before M.
- SECOND fixed to v317 **OUTER_L2_1** so changes are attributable to THIRD.
- Rebuild conditional THIRD using ALL / DROP_START / COMPACT safe feature formulations and L2 grid.
- Report conditional THIRD TOP1/TOP2/TOP3, exact3, monthly/worst-month while retaining full 345 exact denominator.
- Feb-Jun development only; Jul/Aug NON-PRISTINE; September unread.
- Workflow file creation should trigger v318. Fresh check must inspect newest v318 run first.

## Automatic branch sequence
1. SECOND family/gating/role/pairwise/multiclass/error-feature research v311-v317 — completed; saturated enough.
2. **v318 conditional THIRD rebuild — CURRENT.**
3. If v318 THIRD gain is weak/unstable, implement direct **20 ordered `(second,third)` pair model** using only leak-safe cached/pre-race features.
4. If v318 materially improves THIRD, preserve it and still compare factorized SECOND×THIRD against direct ordered-pair.
5. Once ranking/probability model stabilizes, optimize exactly-3-ticket policy.
6. Suspicious large gain -> immediate leakage/causal audit.

## Required metrics
- exact3 on full 345 denominator
- SECOND TOP1/TOP2/TOP3 on 290 head-win races
- conditional THIRD TOP1/TOP2/TOP3
- by actual SECOND/route where relevant
- outer456 capture
- monthly breakdown and worst month
- delta vs clean/base formulation.

## Self-continuing rule
A failed/flat experiment is diagnostic evidence, not a stopping condition. If research is stopped and the next leak-safe branch is clear, implement/start it automatically and update this handoff. Do not merely report stopped state. If v318 completes, record results here and automatically move to direct ordered-pair if warranted.