# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-12 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue development of the BOATCAST start-exhibition video pipeline until it is reliable enough for live use immediately after exhibition. The target is automatic result-blind acquisition, six-boat seeding/tracking, SES scoring, and later model re-evaluation without manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results always override old chat memory.
- Never inspect race results before locking exhibition-video judgement for a blind/pristine validation sample.
- July/August 2026 are NON-PRISTINE / research-only.
- September 2026 onward is preferred for clean validation, but any sample whose result was already exposed must be marked calibration/non-pristine.
- Do not weaken fail-closed quality thresholds just to obtain `accepted=true`.
- Do not hard-code a boat-number-specific offset learned from one race.
- Do not wire an experimental seed/tracker into production LIVE until it generalizes across multiple independent races.
- GitHub Actions are for validation/logging. Final race-by-race operation should be a persistent process on the Japan self-hosted PC to avoid queue/startup delay.

## Live latency target
Target SES availability: within 30–60 sec after exhibition video becomes available; ideal <30 sec.

Japan self-hosted Python path:
`C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`

Do not guess alternate Python paths.

## BOATCAST acquisition
Current low-latency downloader: `download_boatcast_exhibition_fastclip.py`
Typical benchmark clip start 82 sec / duration 52 sec.
Known acquisition timings: 2026-09-10 Kiryu12 as low as ~4.2 sec historically; v6 run 13.515 sec. 2026-09-09 Kiryu12 ~8.4–9.3 sec.

## Tracker
Current tracker: `track_exhibition_boats_v5.py`
- result-blind, stride 2 (~15 fps effective)
- LK prediction + bounded adaptive template match
- arbitrary exhibition entry order
- fail closed on entry-order violation or lane separation <=4 px during tracking
- confidence-aware HIGH/MEDIUM/LOW quality
- overall accepted only when all six pass
Do not relax quality gates merely to pass.

## Seed history / evidence
### v3
`auto_seed_exhibition_motion_v3.py`: permissive six-row LK + per-row coherent hull-side refinement. Improved boats 2–6 on 9/10 but boat1 remained LOW.

### v6 calibration success and generalization failure
`auto_seed_exhibition_motion_v6.py`: fleet-relative extreme motion -> saturated +/-120 px shift.
- 2026-09-10 Kiryu12 run `34603144372`: accepted=true, all HIGH. Only boat1 shifted -120 from [1289,429] to [1169,429].
- 2026-09-09 Kiryu12 run `34604306399`: failed closed lane separation. v6 chose 30.0 sec where final two rows were only 20.5 px apart and shifted both adjacent extreme rows +120.
Conclusion: v6 NOT live-ready.

### v7 geometry-aware candidate selection — FAILED but informative
File: `auto_seed_exhibition_motion_v7.py`
Commits: implementation `27c0a639e97701a0c363bd08a1f208d6b61a7739`; benchmark workflow `a0567e828fde0ace6be76fe990d711f5b7ece747`.
Run: `34687516774` on 2026-09-09 Kiryu12, entry order `1,2,4,5,6,3`.
Fastclip: 8.376 sec. Seed v7: 4.901 sec.
v7 successfully fixed candidate-time geometry:
- selected_sec 28.25 instead of v6 30.0
- min vertical gap 52 px, median gap 57 px
- gaps [56.5,57,84,52,103]
But it still saturated-shifted isolated extreme rows:
- boat1 motion [1106.5,398.5] -> [986.5,398.5] (-120)
- boat3 motion [680,751] -> [800,751] (+120)
Tracker then failed closed with entry-order violation: expected `[1,2,4,5,6,3]`, got `[2,1,4,5,6,3]`.
Diagnosis: candidate time/vertical geometry is now much better, but motion-extreme status alone is insufficient evidence to accept a horizontal seed shift. The boat1 -120 correction useful on 9/10 is harmful on 9/9 at 28.25.

### v8 current experiment — short-horizon visual validation
File: `auto_seed_exhibition_motion_v8.py`
Implementation commit: `36e5e6447714ec165467438154287d6a6b2e6814`
Workflow commit: `e421a1c8f38212152978ce618b7e0b3d43302e20`
Workflow run: `34687634261` (2026-09-09 Kiryu12), currently pending/in progress at this handoff update.
Design:
1. Keep v7 geometry-aware candidate-time selection.
2. Extreme motion is only a proposal.
3. For each isolated extreme row compare base v3 seed vs proposed +/-120 seed using only a short ~0.18 sec future video window.
4. Use local template NCC with vertical-drift penalty; accept shift only if shifted score beats base by margin 0.035 and passes visual gate.
5. Adjacent extreme rows remain ambiguous and are not shifted.
6. This is result-blind and bounded; it is not a full 1.5 sec tracker sweep and does not inspect race outcome.
Next action: inspect actual logs of run `34687634261`. If v8 passes 9/9, immediately re-test unchanged v8 on 9/10 to ensure it preserves the known useful correction; then expand to additional September races.

## Validation plan before LIVE integration
Require multiple independent September samples with different entry orders/camera geometry. Practical minimum before wiring production:
- at least 3 independent September samples (more is better)
- automatic acquisition + automatic seed + tracker only; no manual seed edits
- tracker accepted on required samples, or documented fail-closed rate low enough for operations
- no absurd center displacement / identity jumps
- arbitrary entry order handled correctly
- result-blind lock before result comparison
- core processing <=30 sec where feasible and <=60 sec maximum target
Then expand toward 10+ samples before treating SES as stable/predictive.

## Scientific interpretation
SES is an attack/head-support feature candidate, not a direct finishing-order rank. Do not join race results until exhibition judgement is locked.

## Production/live wrapper
Current `run_exhibition_ses_live_local.py` is still old (seed v1 + tracker v3). Do NOT update until v8 or later generalizes across multiple independent samples. Once validated, wire validated seed + tracker v5 stride2 + output `exhibition_tracking_v5.json`, then build persistent Japan-PC watcher.

## Workflow
`.github/workflows/benchmark-fast-exhibition-clip.yml` runs on `[self-hosted, japan]`, supports inputs race_date/stadium/race/clip start/duration/entry order, and is currently configured to benchmark v8 on 2026-09-09 Kiryu12.

## Required behavior for future sessions / automation
1. Read this file first.
2. Inspect latest GitHub commits/files/workflow runs; latest GitHub wins.
3. Inspect actual job logs, not just green/red status.
4. Continue implementation/testing autonomously.
5. Update this file after meaningful design/result changes.
6. Never claim live readiness without accepted=true evidence plus geometry sanity across multiple independent races.

## Done-enough-to-notify milestone
Notify user only when a seed/refinement version generalizes across multiple independent September races with varied entry order; tracker quality passes without manual/race-specific offsets; geometry/identity is sane; latency fits post-exhibition operation; live local wrapper is updated; and at least one end-to-end self-hosted live-style validation succeeds.
