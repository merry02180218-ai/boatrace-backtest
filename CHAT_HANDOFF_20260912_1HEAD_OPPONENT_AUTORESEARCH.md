# CHAT_HANDOFF_20260912_1HEAD_OPPONENT_AUTORESEARCH

## Scope
1号艇頭モデルを固定したうえで、相手選び（SECOND / THIRD / exact 3-ticket）をゼロベースで自動研究する。最新GitHubを常に優先する。

## AUTO_RESEARCH_STATE
- Fixed evaluation cohort: **345 races**.
- Boat-1 head hits: **290/345 = 84.06%**.
- Boat-1 losses remain misses in final exact-trifecta denominator.
- Jul/Aug 2026 are **NON-PRISTINE**.
- September outcomes remain **unread / outcome-blind** unless latest repo explicitly changes this.
- `meet_*` is forbidden unless separately causally reconstructed and audited.
- Current branch: **v312 inner-vs-outer SECOND gating / outer specialist**.
- Current infrastructure change: **v313 reusable causal cache** is now mandatory for repeated opponent research.

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

Reusable cache files:
- `cache_v313_1head_opponent_pre.csv.gz`
- `cache_v313_1head_opponent_p3.csv.gz`
- `cache_v313_1head_opponent_p4.csv.gz`
- manifest: `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`

Rules:
1. Full PRE/prior reconstruction, p3 causal reconstruction, p4 loading, race-card/history fetches, and settlement joins are performed **once** when building/refeshing the cache.
2. Subsequent SECOND / THIRD / pairwise / ordered-pair / ticket experiments must load the cache by default.
3. A research script must not silently fall back to full historical reconstruction when cache is missing. It must fail fast, build/refesh the cache once, then resume the queued experiment.
4. Rebuild the cache only when upstream causal feature logic/data provenance changes, an explicit cohort change is approved, or a cache audit fails.
5. The cached PRE table must remove `meet_*` columns. Outcome/settlement fields may exist only as labels/evaluation fields and must never enter model feature lists.
6. Month M training remains strictly `< M` even when all months coexist in the cache.
7. Missing p3/p4 is never future-backfilled; downstream continues to use availability flags + neutral sentinel.
8. Jul/Aug remain NON-PRISTINE and September outcomes remain unread regardless of cache contents.

Purpose of this rule:
- eliminate repeated 20-60 minute reconstruction overhead;
- make model-formulation experiments fast enough to self-continue;
- separate expensive causal data preparation from inexpensive model research;
- reduce failures caused by repeated network/source reconstruction.

## CURRENT_STEP
1. Build v313 reusable causal cache once.
2. Cache commit automatically triggers v312 workflow.
3. v312 loads only the cache and runs outer SECOND gating on fixed 345R/290 head wins.
4. If v312 is weak/flat, move automatically to pairwise SECOND rather than over-tuning gating.

v312 files:
- script: `run_v312_1head_opponent_outer_gate.py`
- workflow: `.github/workflows/research-20260912-v312-outer-gate.yml`
- v312 now has a hard cache requirement and no longer performs the full historical reconstruction itself.
- workflow timeout reduced to 45 minutes because model research should be much lighter once cache exists.

## Leakage / causal safety rules — mandatory
1. Never use same-race result, later-race result, end-of-day aggregates, post-race exhibition, payout/result fields, or features reconstructed with future information as predictors.
2. Historical/player/motor/foot features must be available strictly before prediction time; prefer prior-day frozen state if exact intraday versioning is not proven.
3. Non-time-versioned source tables are unsafe until causal reconstruction proves availability.
4. `meet_*` remains forbidden in this research unless separately reconstructed causally.
5. Monthly walk-forward: month M trains only on dates/months before M; never fit/calibrate on evaluation-month outcomes.
6. Missing p3/p4 must not be future-backfilled.
7. Feb-Jun hyperparameter/config selection is development-only, not pristine validation.
8. Global future-distribution thresholds are not production-compatible.
9. Every opponent experiment asserts 345R and 290 head hits before scoring.
10. Keep SECOND, THIRD, and ticket-policy changes separable for attribution.
11. Every new feature must have provenance/leak status before use.
12. Suspiciously large gains trigger a dedicated causal/leakage audit before acceptance.

## Self-continuing research rule — mandatory
The auto-research must NOT stop merely because the current hypothesis fails or is flat.
- A failed/flat experiment is diagnostic evidence, not a stopping condition.
- After each valid negative result, inspect the failure decomposition and choose the next materially different leak-safe hypothesis automatically.
- Do not endlessly tune one weak formulation; switch model class or target decomposition when gains saturate.
- Keep the 345R/290-head-hit cohort fixed during opponent comparisons unless a separate explicit cohort experiment is requested.
- If research is found stopped and the next handoff step is clear, restart it automatically.
- Continue until the user stops/redefines it, all materially distinct leak-safe approaches are exhausted and documented, or a technical/data blocker prevents a valid experiment.

## Automatic branch sequence
1. v311 feature-family attribution / compact listwise SECOND — completed.
2. v312 inner-vs-outer gating / outer SECOND specialist — current.
3. Pairwise SECOND ranking with outer-balanced weighting if v312 is weak.
4. Multiclass/listwise alternatives with route/class balancing.
5. Error-driven PRE/prior feature engineering: ST, motor, player/form, lane geometry, prior foot/turn, causal p3/p4; never unsafe `meet_*`.
6. Once SECOND capture stabilizes, rebuild conditional THIRD separately.
7. If factorized SECOND×THIRD remains limiting, fit direct 20 ordered `(second,third)` pair model.
8. Only after probability/ranking models stabilize, optimize exactly-3-ticket policy.
9. Suspicious large gain -> leakage/causal audit branch immediately.

## Decision rules
- SECOND TOP2 gain <= about 0.5pp with essentially unchanged outer capture => weak; move to next model class.
- Gain concentrated in one month/boat => audit stability; do not treat as general improvement.
- Outer capture improves while inner 2/3 collapses enough to reduce overall TOP2/exact3 => use gated blending, not wholesale replacement.
- When SECOND ceases to be dominant error, move effort to THIRD or ordered-pair according to latest decomposition.
- Promotion requires leak-safe implementation, stable monthly behavior, production-compatible calibration, and prospective/outcome-blind validation.

## RESUME_INSTRUCTION
A fresh chat should:
1. read this handoff and latest GitHub;
2. check whether v313 cache build is running/completed;
3. if cache missing and no cache build is active, trigger/fix the cache build;
4. once cache exists, verify v312 is automatically running from cache;
5. if v312 completes, record results here and automatically choose the next branch using the decision rules;
6. if any research step is stopped unexpectedly, restart the clear next step rather than merely reporting the stop.
