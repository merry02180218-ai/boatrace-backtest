# CHAT_HANDOFF_20260912_1HEAD_OPPONENT_AUTORESEARCH

## Fixed rules
1号艇頭モデルv308を固定し、相手選び SECOND / THIRD / ordered-pair / exact-3-ticket を研究する。最新GitHub優先。
- Fixed development cohort: **345 races**; boat1 head hits **290/345=84.06%**. Boat1 losses remain misses in exact denominator.
- Jul/Aug 2026 are **NON-PRISTINE/reference-only**. They cannot promote or tune a model.
- September outcomes must remain **unread/outcome-blind**.
- `meet_*` forbidden unless separately causal-audited.
- No same/later-race result, end-of-day aggregate, post-race exhibition, payout/result or future-contaminated predictor.
- Month M trains strictly on **< M**. Missing p3/p4 are never future-backfilled.
- Every development opponent experiment asserts **345R / 290 head hits**.

## Mandatory causal cache
Use committed v313 causal cache for development research; do not silently rebuild it:
- `cache_v313_1head_opponent_pre.csv.gz`
- `cache_v313_1head_opponent_p3.csv.gz`
- `cache_v313_1head_opponent_p4.csv.gz`
- `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`

## Completed development branch
- v309 clean base: exact3 **132/345=38.26%**; SECOND TOP2 **71.72%**.
- v310 causal p3/p4: SECOND TOP2 **72.07%**; exact3 **133/345**.
- v311 DROP_START: SECOND TOP2 **72.41%**; exact3 **136/345=39.42%**.
- v312 outer gate: SECOND TOP2 **73.10%**; outer456 **28.74%**; exact3 **136/345**.
- v314 role split: unstable, no promotion.
- v315 pairwise SECOND: SECOND TOP2 **72.76%**; exact3 **133/345**.
- v316 multiclass SECOND: SECOND TOP2 **72.76%**; exact3 **136/345**.
- v317 error-driven causal features: best OUTER_L2_1, SECOND TOP2 **72.76%**, outer456 **28.74%**, exact3 **137/345=39.71%**. SECOND considered saturated.
- v318 conditional THIRD rebuild: best DROPSTART_T0.1, THIRD TOP2 **72.76%**, exact3 **137/345=39.71%**; flat.
- v319 direct ordered-pair: best ALL_P0.3 pair TOP3 **46.21%**, exact3 **134/345=38.84%**; weaker than factorized v317+v318.
- v320 exact-3-ticket policy: development winner **HYBRID alpha=.70**, exact3 **139/345=40.29%** on full 345 denominator. Exactly 3 tickets per race. This is development evidence only.

## Development decision boundary
SECOND -> THIRD -> ordered-pair -> exact-3-ticket sequence is complete. The current development winner is frozen at:
- head: v308
- SECOND: v317 OUTER_L2_1
- THIRD: v318 DROPSTART_T0.1
- ticket policy: v320 HYBRID alpha=.70
Do not invent more ticket-order micro-tuning from reused Feb-Jun outcomes. A new development branch requires a genuinely new causal hypothesis.

## v321 Jul/Aug NON-PRISTINE reference check
v321 is a contamination-aware stress check only and cannot alter the development decision boundary.

History:
- Initial run `34739967420` failed because the audited source horizon ended at 2026-06-30.
- Fix `274864650cb8a8d5607217464b2e32a043de1772` extended only the v321 source horizon through **2026-08-31**, with an explicit September fail-closed check.
- Repeated attempts of run `34741655731` and then run `34745855880` were terminated around the long monolithic Python step.
- Memory projection commit `badbc36831a91cb90d478c944ca5d0bcd1b9de8e` was insufficient.
- Two-job split (`prepare -> evaluate`) at `0f0836bb65a6abe3b52bcc790fca29e9aaa5a7a3` still failed in prepare run `34746675136` with runner shutdown / exit 143.

### Root cause found 2026-09-13
This is not being treated as merely a GitHub runner problem. The v321 prepare implementation was copying the fully expanded, highly fragmented v294->v307 dataframe for each target month:
`tr=d[d.month<tm].copy(); te=d[d.month==tm].copy()`.
That frame contains hundreds of columns produced by repeated `frame.insert` operations (confirmed by repeated pandas fragmentation warnings). The monthly copies therefore amplified memory immediately before the expensive v308 head OOF/HGB+LR folds. Earlier exit 137 and repeated shutdowns in the same region are consistent with this code-side resource design problem.

Fix commit **`2f020cb6517c50319a3bf849e6dfa93a650eb44a`**:
- extract the narrow symmetric opponent cache first;
- project the head frame to only metadata + the exact frozen v308 core/guard/causal head feature columns;
- delete the full expanded dataframe before monthly head copies/training;
- add explicit per-month head-fold heartbeat output;
- keep all model settings and leakage boundaries unchanged.

Restarted v321 workflow run: **`34748125204`** (push of the fix commit; initially `in_progress`).

### Current staged design
1. **prepare**: build Jul/Aug causal PRE/head-selection universe, enforce September absence, remove `meet_*`, project to exact head inputs + symmetric opponent columns, and upload:
   - `cache_v321_julaug_nonpristine_slim.csv.gz`
   - `cache_v321_julaug_nonpristine_head.csv`
   - `cache_v321_julaug_nonpristine_meta.csv`
2. **evaluate**: download artifacts, apply frozen v317 SECOND + v318 THIRD + v320 HYBRID alpha=.70, and write final race/monthly/summary outputs.

Invariant notes:
- v321 artifacts are NON-PRISTINE infrastructure only; not development cache replacements.
- v313 p3/p4 remain frozen; Jul/Aug missing p3/p4 stay unavailable/neutral and are never future-backfilled.
- September outcomes remain unread and any September row causes fail-closed termination.
- `meet_*` remains forbidden.
- Month M remains trained only on `< M`.
- No Jul/Aug tuning of thresholds, features, alpha, or ticket strategy is allowed.

## Self-continuing rule
A failed/flat experiment is diagnostic evidence, not a stopping condition. If execution stops and a leak-safe technical continuation is clear, implement/restart it and update this file. For any new workflow/restart, verify an actual Actions run ID and status. If v321 completes, record its Jul/Aug metrics as NON-PRISTINE reference only; do not start another development micro-tune unless a new causal hypothesis is explicitly defined.
