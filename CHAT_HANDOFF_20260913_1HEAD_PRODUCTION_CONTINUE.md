# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## Mandatory operating rule
**Before starting any work, write the intended next work into this handoff file first.**
If the chat/tool execution stops midway, the next session must read this file + latest GitHub and resume the unfinished item automatically. Do not wait for the user to repeat the instruction.

## User correction / actual target
Make the frozen 1-head stack genuinely usable in production while preserving the established backtest logic. This is NOT a generic 10,000-yen Dutch allocator.

Final operational output must be:
**frozen 1-head selection -> v317 SECOND -> v318 THIRD -> v320 HYBRID alpha=.70 exactly 3 tickets -> current trifecta odds for those 3 tickets -> composite odds `1/(1/o1+1/o2+1/o3)` -> BUY/SKIP output.**

## Important source audit correction (2026-09-13)
The earlier tentative assumption that v308 itself requires same-race exhibition/close-time information was checked against source and is **not correct**.

- `analyze_v294_1head_verified_prepost_research.freeze_true_pre()` builds PRE from scheduled race cards and strictly prior-day player history; its PRE universe explicitly has **no actual-entry/current-exhibition gate**.
- v305 classifies prior player history and prior-day exhibition history as safe, current card grade/wr/local/nst/motor as safe, and removes operationally unproven `meet_*` snapshot features.
- v307 explicitly replaces unsafe meeting-snapshot signal with causal prior-day features only and forbids `meet_*`.
- v308 starts from that `freeze_true_pre()` path, adds only v305-safe transfer features + v307 causal features, and asserts no `meet_*` enters the safe feature set.

Therefore, to match the backtest, **do not invent a separate post-exhibition v308 gate. v308 is the PRE head selector.** Same-race exhibition may later be researched as a separate prospective overlay, but it must not be inserted into the frozen v308 production path without a new causal backtest.

## Confirmed frozen research state
- head model: **v308**
- selected operating point: **q=0.980, opponent mass>=0.375**
- development cohort: **345R**
- head hits: **290/345 = 84.06%**
- v308-era exact3: 132/345 = 38.26%
- frozen opponent stack after later causal research:
  - SECOND **v317 OUTER_L2_1**
  - THIRD **v318 DROPSTART_T0.1**
  - tickets **v320 HYBRID alpha=.70**, exactly 3/race
- v320 development exact3: **139/345 = 40.29%**
- Jul/Aug 2026 are NON-PRISTINE/reference-only
- September outcomes remain unread/outcome-blind
- v321 Jul/Aug reference validation is complete and cannot tune/promote the model

## Backtest-alignment priority
User instruction: **progress so real production matches the established backtest result/logic.** Production convenience must not redefine the model. The historical reference to preserve is v308 q=.980 + opponent mass>=.375 producing 345R / 290 head hits, followed by the frozen v317/v318/v320 opponent stack.

## Do not do
- Do not tune on Jul/Aug.
- Do not read September outcomes.
- Do not invent a replacement model.
- Do not turn this into 10,000-yen Dutch allocation.
- Do not insert same-race exhibition/close-time fields into v308 merely because they are available LIVE.
- Do not silently use Legacy PRE in place of v308.
- Do not stop merely because one workflow fails when technical continuation is clear.
- Do not claim production readiness until current-input execution and historical alignment both pass.

## Completed in this continuation
- Source-level feature-boundary audit completed before production code changes.
- Result: v308 is PRE-safe by design; the previous post-exhibition-v308 assumption was corrected before implementation.
- v308 reference re-confirmed from committed summary: q=.980 + mass>=.375 => 345R / 290 head hits = 84.06%.
- v320 exact-3 race file confirmed: 345 rows, HYBRID alpha=.70, 139 exact3 hits.
- Existing result-free official live 3連単 odds fetcher `fetch_live_trifecta_odds.py` confirmed reusable; it requests odds3t only and validates 120 combinations.
- **v322 completed successfully.** GitHub Actions run **34753932483** / artifact **10316354325**.
- v322 frozen assertions passed: **345 races / 290 head wins / 139 exact3 hits**.
- Historical 3-ticket closing-odds coverage: **339/345 = 98.26%**.
- Evaluable overall: **339R / 136 hits = 40.12% / ROI 91.27%** under the notional composite-odds accounting convention.
- Descriptive threshold diagnostics: >=2.5 gave 114R / ROI 100.12%, >=3.0 gave 59R / ROI 100.80%, but these are reused Feb-Jun development evidence and are **not promoted** as LIVE cutoffs.

## NEXT CONCRETE ACTION — current-date frozen production adapter (written before code change)
1. Locate the exact reusable v308 feature/model path plus v321 frozen v317/v318/v320 scoring components already in repo.
2. Inspect current result-blind 2026-09-13 input layout and any existing PRE diagnostic workflow/artifact source. Do not read September outcomes.
3. Implement the smallest adapter that scores current scheduled races with **v308 semantics**, using only scheduled/static and strictly prior-day information; forbid `meet_*` and same-race exhibition/result/payout fields.
4. Derive/freeze the production v308 score cutoff and opponent-mass gate exactly from the historical frozen path; no retuning on Jul/Aug/September.
5. Assert historical alignment before using the adapter for current races: same frozen development selector must remain 345R / 290 head hits.
6. Feed only current v308-qualified races into frozen v317 SECOND + v318 THIRD + v320 HYBRID alpha=.70 exactly 3 tickets.
7. Fetch current odds only for those three tickets, compute composite odds, and output race / v308 score / mass / 3 tickets / each odds / composite odds / BUY-SKIP status. Until a prospective BUY cutoff is legitimately frozen, BUY-SKIP must be fail-safe and must not silently use the descriptive v322 threshold grid.
8. Create/modify the dedicated GitHub Actions workflow, then verify a real run ID, inspect logs/artifacts, and fix technical failures. Before each fix/restart, update this handoff first.
