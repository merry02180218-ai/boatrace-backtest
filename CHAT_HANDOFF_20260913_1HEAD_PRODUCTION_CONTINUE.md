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

## Work to do NOW (written before execution)
1. Treat the existing `diag-1head-pre-20260913.yml` Legacy PRE output as diagnostic only; do not substitute it for v308.
2. Locate/reuse the v321 causal feature preparation and frozen v317/v318/v320 scoring components so production uses the exact same feature semantics and model rules as the frozen backtest.
3. Build the smallest **result-blind current-date v308 PRE adapter** that reconstructs scheduled current race-card static fields, strictly prior-day player/history features, v298 threat structure, v305-safe v303 transfer features, and v307 causal features; no `meet_*`, same-race result/exhibition/payout fields.
4. Fit the head model from historical data exactly as the frozen walk-forward semantics allow for a future date, derive the production head probability cut corresponding to the frozen q=.980 rule from training/OOF data, and compute the frozen opponent confidence/mass needed for the >=.375 gate without using current outcomes.
5. Assert historical alignment before LIVE use: the adapter/model code must reproduce the frozen v308 345R / 290 head-hit selector when run on the development backtest path, or any difference must be explained and fixed.
6. Feed only v308-qualified current races through frozen v317 SECOND + v318 THIRD + v320 HYBRID alpha=.70 exactly-3-ticket logic.
7. Add current trifecta odds retrieval for only those 3 tickets and compute composite odds `1/(1/o1+1/o2+1/o3)`.
8. Output race, v308 score/gate, 3 tickets, each current odds, composite odds, and BUY/SKIP. Do not implement Dutch staking unless separately requested later.
9. Fail closed on missing/stale inputs, missing prior history, forbidden columns, or inability to reproduce model semantics. Never silently fall back to Legacy PRE or an older model.
10. Trigger/verify actual GitHub Actions run IDs and inspect outputs/errors. If technical continuation is clear, write the next intended fix here before changing code/restarting and continue.

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

## NEXT CONCRETE ACTION — v322 (written before code change)
Create `run_v322_1head_composite_odds_backtest.py` and a dedicated GitHub Actions workflow.

Purpose:
1. Load the **already frozen** `analysis_v320_1head_exact3_ticket_policy_best_race.csv` (must assert exactly 345 races, 290 head hits, 139 exact3 hits, HYBRID alpha=.70, exactly 3 unique tickets/race).
2. Load historical closing trifecta odds using the existing audited `analyze_v205_3head_operational_replay.load_odds()` unified odds source. Odds are settlement/diagnostic only; they must not change v308/v317/v318/v320 race or ticket selection.
3. For each race with all three ticket odds available, calculate only the 3-ticket **composite odds** `1/(1/o1+1/o2+1/o3)`; do NOT calculate or output Dutch stakes.
4. For backtest accounting, use the user's composite-odds convention: a hit has notional return `10000 * composite_odds`, a miss has return 0, every evaluable race has notional cost 10000. This is an evaluation convention only, not a staking instruction.
5. Output race-level CSV, monthly summary, overall ROI/coverage, and a descriptive composite-odds threshold grid. Threshold diagnostics are development evidence only and must NOT be silently promoted into a LIVE BUY cutoff.
6. Assert that odds availability cannot alter the frozen 345-race model cohort; report missing-odds races separately rather than dropping them from model metrics.
7. Trigger the workflow and verify its real Actions run ID/result before proceeding to the current-date production adapter.
