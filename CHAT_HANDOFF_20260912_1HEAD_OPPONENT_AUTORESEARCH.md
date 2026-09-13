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
- Narrow-frame fix `2f020cb6517c50319a3bf849e6dfa93a650eb44a` reduced monthly copy amplification, but run `34748125204` still died in prepare with exit 137.

### Root causes found 2026-09-13
This is not being treated as merely a GitHub runner problem.

1. The original prepare implementation copied the fully expanded, highly fragmented v294->v307 dataframe for each Jul/Aug head fold, amplifying memory before v308 OOF/HGB+LR training.
2. v321 also called `v303.opponent_mass(d)` during prepare. That helper is hard-wired to `TM=list(v298.TEST_MONTHS)`, i.e. the legacy Feb-Jun development months. It therefore cannot produce Jul/Aug opponent masses, while also rebuilding large SECOND/THIRD tables and models unnecessarily. This was semantically wrong and resource-heavy.
3. After splitting prepare/SECOND/THIRD jobs, run `34749658497` proved prepare and SECOND can complete, but both BASE THIRD and frozen v318 THIRD still died with hosted-runner shutdown while constructing the full conditional table. The legacy builder emits 20 ordered pairs for every historical race even though `pc_predict` trains only rows with `train_group==1`. This created roughly 900k rows unnecessarily for Jul/Aug.

Fix commit **`46d3a398679bacf57cc5325d4e817041d452e712`**:
- preserve exact chronological THIRD semantics while building folds compactly;
- for historical month `< M`, emit only the four THIRD candidates conditional on the actual SECOND for valid `1-x-y` races, exactly the rows consumed by `train_group==1`;
- for target month `M`, still emit all 20 ordered pairs for inference;
- build Jul and Aug folds separately and release each fold before the next;
- no threshold/model/ticket-policy tuning and no change to frozen v318 DROP_START configuration.

Restarted v321 run: **`34750719803`**, head SHA `46d3a398679bacf57cc5325d4e817041d452e712`; at verification it was **queued**.

### Current staged design
1. **prepare**: build Jul/Aug causal PRE/head universe, enforce September absence, remove `meet_*`, project to exact head inputs + symmetric opponent columns.
2. **second**: frozen BASE SECOND + v317 SECOND predictions.
3. **base-third**: compact chronological BASE THIRD folds for v308 opponent mass.
4. **third**: compact chronological frozen v318 DROP_START THIRD folds.
5. **score**: reconstruct frozen v308 gate and apply v320 HYBRID alpha=.70 exactly 3 tickets.

Invariant notes:
- v321 artifacts are NON-PRISTINE infrastructure only; not development cache replacements.
- v313 p3/p4 remain frozen; Jul/Aug missing p3/p4 stay unavailable/neutral and are never future-backfilled.
- September outcomes remain unread and any September row causes fail-closed termination.
- `meet_*` remains forbidden.
- Month M remains trained only on `< M`.
- No Jul/Aug tuning of thresholds, features, alpha, or ticket strategy is allowed.

## Self-continuing rule
A failed/flat experiment is diagnostic evidence, not a stopping condition. If execution stops and a leak-safe technical continuation is clear, implement/restart it and update this file. For any new workflow/restart, verify an actual Actions run ID and status. If v321 completes, record its Jul/Aug metrics as NON-PRISTINE reference only; do not start another development micro-tune unless a new causal hypothesis is explicitly defined.
