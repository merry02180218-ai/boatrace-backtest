# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## Mandatory operating rule
**Before starting any work, write the intended next work into this handoff file first.**
If the chat/tool execution stops midway, the next session must read this file + latest GitHub and resume the unfinished item automatically. Do not wait for the user to repeat the instruction.

## User correction / actual target
The task is NOT to jump to a generic LIVE/odds/Dutch implementation and NOT to restart old research blindly.
Resume the exact 1-head work from the latest 2026-09-13 conversation and repository state, with the goal of making the frozen 1-head model actually usable in production.

The production objective is now explicit:
**PRE candidate scan -> post-exhibition v308 final gate -> frozen v317 SECOND -> frozen v318 THIRD -> v320 HYBRID alpha=.70 exactly 3 tickets -> fetch live trifecta odds for those 3 tickets -> compute 3-ticket synthetic/composite odds -> BUY/SKIP decision.**

Important correction: **do not treat v308 as a pure PRE model.** v308 may depend on information only available close to race time (for example exhibition-related inputs). Therefore the implementation must first audit the exact v308 feature boundary and preserve the backtest behavior. Any feature unavailable at PRE time stays in the post-exhibition/final gate. PRE scanning must use only information that is genuinely available before exhibition/close-time data.

## Confirmed research state
From `CHAT_HANDOFF_20260912_1HEAD_OPPONENT_AUTORESEARCH.md`:
- head model fixed: **v308**
- development cohort: 345R; head hits 290/345 = 84.06%
- frozen opponent stack: SECOND v317 OUTER_L2_1 / THIRD v318 DROPSTART_T0.1 / v320 HYBRID alpha=.70 exactly 3 tickets
- Jul/Aug are NON-PRISTINE/reference-only; September outcomes remain unread/outcome-blind
- v321 Jul/Aug reference validation is complete and cannot tune/promote the model

## Latest 2026-09-13 continuation context
The latest conversation established that the active productionization target was the 1-head frozen model/opponent selection, not a new model micro-tune. The repo currently also contains `.github/workflows/diag-1head-pre-20260913.yml`, which scores the canonical Legacy PRE ranking against the result-blind 2026-09-13 production input artifact. This must be reconciled with v308 and the frozen v317/v318/v320 downstream stack before declaring production readiness.

## Work to do NOW (written before execution)
1. Inspect the exact v308 implementation/backtest inputs and classify every feature as PRE-available vs exhibition/close-time-only vs forbidden/outcome-derived.
2. Reproduce the fixed backtest selection logic and identify the exact row universe that produced the frozen 345R / 290 head-hit result. Do not change thresholds or feature semantics simply to make LIVE implementation easier.
3. Inspect `diag-1head-pre-20260913.yml` / Legacy PRE and determine whether it can act only as a recall-oriented first-stage scanner. Measure the PRE stage against the frozen backtest universe so it does not silently drop v308-qualified races.
4. Define the two-stage production contract:
   - Stage A PRE: result-blind, no exhibition-only values; produce candidate races only.
   - Stage B FINAL: once required straight-before-race/exhibition inputs are available, execute the original v308 gate unchanged (or prove any production adapter is numerically equivalent on the frozen backtest).
5. Only races passing Stage B continue through frozen v317 SECOND + v318 THIRD + v320 HYBRID alpha=.70 to exactly 3 trifecta tickets.
6. For the 3 selected tickets, fetch current trifecta odds and compute composite odds as `1 / (1/o1 + 1/o2 + 1/o3)`. The final operational output must include race, 3 tickets, each current odds value, composite odds, and BUY/SKIP state. This is **not** a 10,000-yen Dutch allocator.
7. Add fail-closed checks for missing/stale inputs and forbidden leakage. Never silently fill missing close-time information with later data and never silently fall back to an older model.
8. Validate the production path against the frozen backtest behavior first. Any mismatch with the historical v308/v317/v318/v320 outputs must be explained and fixed before LIVE use.
9. Trigger/verify actual GitHub Actions run(s), record run IDs/status/results, and continue fixing/restarting when technical continuation is clear.
10. BEFORE every subsequent code change/restart, append the exact intended next action here first; AFTER completion append the run/commit/result.

## Backtest-alignment priority
User instruction: **progress so the real-production implementation matches the established backtest result/logic.** Production convenience must not redefine the model. The first-stage PRE scanner may be broader than the final v308 set, but the final Stage B decision must reproduce the frozen v308 behavior as closely as the available prediction-time data allows. If exact reproduction is impossible because a historical feature was not truly available at prediction time, stop using that feature in LIVE only after explicitly proving the issue and re-backtesting a leak-safe replacement; do not hide the discrepancy.

## Do not do
- Do not tune on Jul/Aug.
- Do not read September outcomes.
- Do not invent a replacement model.
- Do not convert the task into 10,000-yen Dutch allocation.
- Do not use exhibition/close-time fields in the PRE candidate scanner.
- Do not stop merely because one workflow fails when a technical continuation is clear.
- Do not claim production readiness until the current-input path has actually run successfully and historical backtest alignment has been checked.
