# CHAT_HANDOFF_20260912_1HEAD_OPPONENT_AUTORESEARCH

## Scope
1号艇頭モデルを固定したうえで、相手選び（SECOND / THIRD / ordered-pair / exact 3-ticket）をゼロベースで自動研究する。**最新GitHubを常に優先する。**

## AUTO_RESEARCH_STATE
- Fixed evaluation cohort: **345 races**.
- Boat-1 head hits: **290/345 = 84.06%**.
- Boat-1 losses remain misses in final exact-trifecta denominator.
- Jul/Aug 2026 are **NON-PRISTINE**.
- September outcomes remain **unread / outcome-blind** unless latest repo explicitly changes this.
- `meet_*` is forbidden unless separately causally reconstructed and audited.
- Boat-1 head model remains frozen at v308 for this opponent research.
- v313 reusable causal cache is committed and is the mandatory data source for repeated opponent experiments.
- v312 outer-gating research is completed.
- **Current active branch: v314 role-split SECOND autoresearch, restarted after fixing a specialist listwise group-size bug.**
- v315 outer boat-specific SECOND research already exists and is chained to a successful v314 completion.

## Current benchmark / diagnostics
v309 baseline on fixed 345R:
- exact3: **132/345 = 38.26%**.
- SECOND TOP2 on 290 head wins: **71.72%**.
- conditional THIRD TOP2 given actual SECOND: **72.76%**.
- actual SECOND TOP2 by boat: boat2 98.25%, boat3 84.27%, boat4 35.71%, boat5 18.75%, boat6 0%.
- Main bottleneck: SECOND ranking, especially boats 4/5/6.

v310 causal p3/p4 head-risk result:
- best HEADRISK_L2_3.
- SECOND TOP2 71.72% -> 72.07%.
- exact3 132/345 -> 133/345 = 38.55%.
- boat4 TOP2 35.71% -> 38.10%; boat5 unchanged 18.75%; boat6 unchanged 0%.
- Conclusion: p3/p4 is a small useful auxiliary signal, not a solution to outer SECOND failure.

v311 family auto-research result (run 34696800597; model calculation succeeded, final push conflicted):
- development best: **DROP_START**.
- SECOND TOP2: **72.41%** vs 71.72% base.
- outer 4/5/6 TOP2: **26.44%** vs 24.14% base.
- exact3: **136/345 = 39.42%** vs 38.26% base.
- boat4 TOP2: **40.48%**; boat5 **18.75%**; boat6 **0%**.
- worst-month TOP2 fell to 60.00%; therefore development-only, not promotion-ready.
- Conclusion: outer 5/6 problem remains and motivates route gating / outer specialist.

## v313 CACHE-FIRST RULE — MANDATORY
Historical causal reconstruction is expensive and must **not** be repeated for every new experiment.

Reusable cache builder:
- `build_v313_1head_opponent_causal_cache.py`
- workflow: `.github/workflows/research-20260913-v313-opponent-causal-cache.yml`

Committed reusable cache:
- `cache_v313_1head_opponent_pre.csv.gz`: **35,462 rows / 580 cols**.
- `cache_v313_1head_opponent_p3.csv.gz`: **21,692 races**.
- `cache_v313_1head_opponent_p4.csv.gz`: **22,271 races**.
- manifest: `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`.
- cache result commit: **`326b9a3c73af383b31ed799fa00f7e762cce9988`**.

Rules:
1. Full PRE/prior reconstruction, p3 causal reconstruction, p4 loading, race-card/history fetches, and settlement joins are performed **once** when building/refeshing the cache.
2. Subsequent SECOND / THIRD / pairwise / ordered-pair / ticket experiments must load the cache by default.
3. A research script must not silently fall back to full historical reconstruction when cache is missing. It must fail fast, build/refresh the cache once, then resume the queued experiment.
4. Rebuild the cache only when upstream causal feature logic/data provenance changes, an explicit cohort change is approved, or a cache audit fails.
5. The cached PRE table removes `meet_*` columns. Outcome/settlement fields may exist only as labels/evaluation fields and must never enter model feature lists.
6. Month M training remains strictly `< M` even when all months coexist in the cache.
7. Missing p3/p4 is never future-backfilled; downstream uses availability flags + neutral sentinel.
8. Jul/Aug remain NON-PRISTINE and September outcomes remain unread regardless of cache contents.

Purpose:
- eliminate repeated 20-60 minute reconstruction overhead;
- make formulation experiments fast enough to self-continue;
- separate expensive causal data preparation from inexpensive model research;
- reduce failures caused by repeated network/source reconstruction.

## v312 COMPLETED — outer SECOND gating
Files:
- script: `run_v312_1head_opponent_outer_gate.py`
- workflow: `.github/workflows/research-20260912-v312-outer-gate.yml`
- summary: `summary_v312_1head_opponent_outer_gate.md`
- result commit: **`6d7a2a31d079547885b68cfece3a1a2de22f1211`**.

Baseline on frozen cohort:
- SECOND TOP2 **71.72%**.
- exact3 **132/345 = 38.26%**.
- outer 4/5/6 TOP2 **24.14%**.

Best v312 `GATE_C0.35_O5.0`:
- SECOND TOP2 **73.10%**.
- exact3 **136/345 = 39.42%**.
- outer 4/5/6 TOP2 **28.74%**.
- gate fired 11 races; 9/11 actual outer = 81.82%.
- actual SECOND TOP2: boat2 98.25%, boat3 83.15%, boat4 47.62%, boat5 15.62%, boat6 0%.
- monthly TOP2: Feb 74.51%, Mar 60.00%, Apr 79.17%, May 77.23%, Jun 64.00%.

Interpretation:
- gating materially recovered boat4 but still did not solve boat5/6.
- sparse gate and weak boat5/6 recovery mean do not micro-tune v312 indefinitely.
- next branch was structured role split / boat-specific outer SECOND.

## v314 CURRENT — role-split SECOND
Files:
- script: `run_v314_1head_opponent_role_split.py`
- workflow: `.github/workflows/research-20260913-v314-role-split.yml`

Design:
- fixed 345R / 290 head hits.
- v313 causal cache only.
- no `meet_*`; no future backfill.
- month M trains only before M.
- THIRD frozen v300 conditional L2=.1 for SECOND attribution.
- split SECOND into outer-gate + inner specialist (2/3) + outer specialist (4/5/6), then blend with DROP_START base.

### Failure and automatic restart
Initial v314 run **34706243972** failed in `specialist_predict()` with:
`RuntimeError: no valid listwise groups`.
Root cause was implementation, not data/model evidence:
- `FastSecond` is hard-coded for **5-candidate** listwise groups.
- v314 inner specialist has 2 candidates and outer specialist has 3, so no group could satisfy `group_n=5`.

Fix:
- changed specialist training to the same audited `FastListwise` implementation with dynamic `group_n=len(boats)` (2 for inner, 3 for outer).
- added incomplete specialist test-group assertion.
- fix commit: **`29b944d825cb856eb3c0955e1a5f64e10932b755`**.
- restarted run: **`34710924015`**; latest check shows **in_progress**.

Important: the failed first v314 run started before the committed v313 cache was available and rebuilt cache inside the job. The restarted run is after the cache commit and should use the committed cache; do not interpret the original 90-minute duration as expected model-runtime behavior.

## v315 QUEUED — outer boat-specific SECOND
- v315 implementation commit: **`7505a6a6c4f4a40bf808b95b34ac85d1db0e5d81`**.
- chain commit: **`bcb2e76ecb06e4b9970f1f1712adfa4e1d80c82e`**.
- workflow is chained with `workflow_run` after successful `v314 role-split SECOND` completion.
- therefore if v314 succeeds, verify v315 starts automatically.
- if v314 completes successfully but v315 does not start, treat that as a stopped autoresearch chain and fix/restart it.

## Leakage / causal safety rules — mandatory
1. Never use same-race result, later-race result, end-of-day aggregates, post-race exhibition, payout/result fields, or features reconstructed with future information as predictors.
2. Historical/player/motor/foot features must be available strictly before prediction time; prefer prior-day frozen state if exact intraday versioning is not proven.
3. Non-time-versioned source tables are unsafe until causal reconstruction proves availability.
4. `meet_*` remains forbidden unless separately reconstructed causally and audited.
5. Monthly walk-forward: month M trains only on dates/months before M; never fit/calibrate on evaluation-month outcomes.
6. Missing p3/p4 must not be future-backfilled.
7. Feb-Jun hyperparameter/config selection is development-only, not pristine validation.
8. Global future-distribution thresholds are not production-compatible.
9. Every opponent experiment asserts **345R and 290 head hits** before scoring.
10. Keep SECOND, THIRD, and ticket-policy changes separable for attribution.
11. Every new feature must have provenance/leak status before use.
12. Suspiciously large gains trigger a dedicated causal/leakage audit before acceptance.

## Self-continuing research rule — mandatory
The auto-research must NOT stop merely because the current hypothesis fails or is flat.
- A failed/flat experiment is diagnostic evidence, not a stopping condition.
- After each valid negative result, inspect failure decomposition and choose the next materially different leak-safe hypothesis automatically.
- Do not endlessly tune one weak formulation; switch model class or target decomposition when gains saturate.
- Keep the 345R/290-head-hit cohort fixed during opponent comparisons unless a separate explicit cohort experiment is requested.
- If research is found stopped and the next handoff step is clear, restart it automatically.
- Continue until the user stops/redefines it, all materially distinct leak-safe approaches are exhausted and documented, or a technical/data blocker prevents a valid experiment.

## Automatic branch sequence
1. v311 feature-family attribution / compact listwise SECOND — completed.
2. v312 inner-vs-outer gating — completed.
3. **v314 role-split SECOND — current/restarted.**
4. **v315 outer boat-specific SECOND — already implemented and chained after v314 success.**
5. If v314/v315 remain weak, implement **pairwise SECOND ranking with outer-balanced weighting**.
6. Then multiclass/listwise alternatives with route/class balancing.
7. Error-driven PRE/prior feature engineering: ST, motor, player/form, lane geometry, prior foot/turn, causal p3/p4; never unsafe `meet_*`.
8. Once SECOND capture stabilizes, rebuild conditional THIRD separately.
9. If factorized SECOND×THIRD remains limiting, fit direct 20 ordered `(second,third)` pair model.
10. Only after probability/ranking models stabilize, optimize exactly-3-ticket policy.
11. Suspicious large gain -> leakage/causal audit branch immediately.

## Required metrics every experiment
- exact3 on full 345 denominator.
- SECOND TOP1/TOP2/TOP3 on 290 boat1-head-win races.
- conditional THIRD TOP1/TOP2/TOP3 when relevant.
- by actual SECOND boat 2/3/4/5/6.
- outer 4/5/6 capture.
- monthly breakdown and worst month.
- delta vs clean BASE.

## Decision rules
- SECOND TOP2 gain <= about 0.5pp with essentially unchanged outer capture => weak; move to next model class.
- Gain concentrated in one month/boat => audit stability; do not treat as general improvement.
- Outer capture improves while inner 2/3 collapses enough to reduce overall TOP2/exact3 => use gated blending, not wholesale replacement.
- When SECOND ceases to be dominant error, move effort to THIRD or ordered-pair according to latest decomposition.
- Promotion requires leak-safe implementation, stable monthly behavior, production-compatible calibration, and prospective/outcome-blind validation.

## RESUME_INSTRUCTION
A fresh chat or automation check should:
1. read this handoff and latest GitHub; latest GitHub wins.
2. confirm committed v313 cache exists; do not repeat full reconstruction unless cache is stale/audited invalid.
3. check v314 restarted run `34710924015` or any newer v314 run.
4. if v314 fails, inspect exact logs and fix/restart causally safe code rather than merely reporting it.
5. if v314 succeeds, verify v315 starts automatically; if not, start/fix v315.
6. after v315, record result here and autonomously choose pairwise SECOND or the next materially distinct branch if SECOND remains dominant.
7. preserve 345R / 290 head hits, Jul/Aug NON-PRISTINE, September unread, no `meet_*`, no future information.
8. update this handoff after every meaningful result, failure, fix, restart, or branch transition.
