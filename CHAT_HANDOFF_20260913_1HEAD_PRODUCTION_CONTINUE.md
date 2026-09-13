# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## Mandatory operating rule
**Before starting any work, write the intended next work into this handoff file first.**
If the chat/tool execution stops midway, the next session must read this file + latest GitHub and resume the unfinished item automatically. Do not wait for the user to repeat the instruction.

## User correction / actual target
The task is NOT to jump to a generic LIVE/odds/Dutch implementation and NOT to restart old research blindly.
Resume the exact 1-head work from the latest 2026-09-13 conversation and repository state, with the goal of making the frozen 1-head model actually usable in production.

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
1. Inspect the latest repository tree/commits and all 1-head files/workflows created after the v321 handoff, especially the 2026-09-13 PRE diagnostic and any v308 production/LIVE scripts.
2. Recover the exact unfinished task and result from the immediately previous 1-head chat/repo work; do not substitute a different LIVE design.
3. Identify the production gap: how a current race enters the v308 gate and then gets frozen v317 SECOND + v318 THIRD + v320 exact-3-ticket output using only information available at prediction time.
4. Implement/fix the smallest production path necessary to run that frozen stack on current result-blind input.
5. Add fail-closed checks for missing/stale inputs and forbidden leakage; never silently fall back to an older model.
6. Trigger/verify the actual GitHub Actions run(s), inspect outputs/errors, and continue fixing/restarting until the production path works or there is a genuinely external blocker.
7. BEFORE each subsequent implementation/restart, update this handoff with the next intended action and, after completion, append run IDs/status/results so another chat can resume exactly.

## Do not do
- Do not tune on Jul/Aug.
- Do not read September outcomes.
- Do not invent a replacement model.
- Do not stop merely because one workflow fails when a technical continuation is clear.
- Do not claim production readiness until the current-input path has actually run successfully.
