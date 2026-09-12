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
Recent v9 acquisition evidence:
- 2026-09-10 Kiryu12: 4.664 sec total (resolve 1.076 + download 3.588)
- 2026-09-09 Kiryu12: 4.677 sec total (resolve 1.043 + download 3.634)

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
v7 fixed candidate-time geometry (selected 28.25 sec; min gap 52 px) but still saturated-shifted isolated extremes. Boat1 and boat3 shifts caused tracker entry-order violation. Motion-extreme status alone is insufficient evidence to shift.

### v8 short-horizon visual validation — 9/9 PASS, 9/10 FAIL
File: `auto_seed_exhibition_motion_v8.py`
Implementation commit `36e5e6447714ec165467438154287d6a6b2e6814`.
9/9 run `34687634261`:
- selected 28.25 sec, min gap 52 px
- rejected bad boat1/boat3 shifts using ~0.18 sec local template comparison
- tracker accepted=true; 1 HIGH,2 HIGH,3 MEDIUM,4 HIGH,5 HIGH,6 HIGH
- core sum ~18.8 sec
Unchanged v8 re-test on 9/10 run `34687751940` FAILED tracker quality because the incorrect base/wake seed still had very high 0.18 sec NCC and the needed boat1 shift was rejected. Conclusion: one very short horizon can validate a persistent wake/background patch and is not enough.

### v9 CURRENT LEADING CANDIDATE — multi-horizon visual persistence
File: `auto_seed_exhibition_motion_v9.py`
Implementation commit `ccd37a1ef2b54acaea7c2a107e7881c257cc27b5`.
Method:
1. v7-style geometry-aware candidate-time selection.
2. Isolated extreme motion only proposes +/-120; it is not automatically applied.
3. Compare base vs shifted candidate over result-blind horizons 0.15/0.30/0.45/0.60 sec.
4. Learn local x velocity from successful matches, allow camera pan, penalize vertical drift and failed horizons.
5. Candidate score = median NCC + 0.25*min NCC - 0.006*mean dy - 0.11*failed horizons.
6. Shift accepted only if shifted candidate passes persistence gate and beats base by >=0.025.
7. Adjacent extreme rows remain ambiguous/unshifted.
No race outcomes/results are read.

#### v9 evidence A: 2026-09-10 Kiryu12, standard entry order
Workflow commit `056a3bdb47a9c49c4f278fec53295b5ae1b46c3e`; run `34687887563`.
- fastclip 4.664 sec
- seed v9 5.474 sec
- selected 27.75 sec; min gap 27 px
- boat1 base persistence score 0.669 vs shifted score 1.1369 -> correctly accepts -120, final [1169,429]
- tracker v5 6.944 sec
- accepted=true, ALL SIX HIGH
- fallback: 1 .348, 2 0, 3 0, 4 .130, 5 0, 6 .043
- median NCC: 1 .965, 2 .848, 3 .831, 4 .825, 5 .875, 6 .883
- core acquisition+seed+track ~=17.1 sec
Artifact `10296314181`.

#### v9 evidence B: 2026-09-09 Kiryu12, nonstandard entry order `1,2,4,5,6,3`
Workflow commit `63e11b20b208f1613a4e363f2ebd19e86ded5171`; run `34687982108`.
- fastclip 4.677 sec
- seed v9 6.289 sec
- selected 28.25 sec; min gap 52, median gap 57
- boat1: base score 1.1007 vs shifted .949 -> correctly rejects -120
- boat3: base score .9443 vs shifted .625 (shifted gate false) -> correctly rejects +120
- tracker v5 7.218 sec
- accepted=true
- quality: 1 HIGH, 2 HIGH, 3 MEDIUM, 4 HIGH, 5 HIGH, 6 HIGH
- fallback: 1 .174,2 .043,3 .391,4 0,5 0,6 0
- median NCC: 1 .922,2 .895,3 .861,4 .901,5 .881,6 .877
- core ~=18.2 sec
Artifact `10296370913`.

v9 therefore has two unchanged-code September technical passes, including one nonstandard entry order, and makes opposite/correct visual-gate decisions on the problematic extreme rows. This is a major improvement but still NOT live-ready.

## Remaining geometry concern
9/9 boat3 is only MEDIUM and has large raw +1.5 center displacement with very few LK features near endpoint, despite median NCC .861 and accepted=true. Treat this as a reason to require more independent samples and potentially add an endpoint/identity sanity check if new samples show the same pathology. Do not simply relax or ignore it.

## Third-sample source already available without results
Historical blind acquisition workflow `.github/workflows/blind-validate-kiryu-20260910-batch.yml` captured 2026-09-10 Kiryu races 3,6,9 before result lookup in this research thread.
Run `34579347851` artifacts:
- race3 artifact `10191092541`
- race6 artifact `10191134655`
- race9 artifact `10191176757`
These contain full exhibition videos/contact sheets/blind-lock metadata. Their results have not been looked up in this SES thread. Use one or more as next independent samples. IMPORTANT: derive actual exhibition entry order from the pre-race video/contact sheet only; do not guess and do not inspect results.

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
Current `run_exhibition_ses_live_local.py` is still old (seed v1 + tracker v3). Do NOT update yet. Once v9 or later passes >=3 independent September samples with sane identity/geometry, wire validated seed + tracker v5 stride2 + output `exhibition_tracking_v5.json`, then perform end-to-end self-hosted live-style validation.

## Workflow
`.github/workflows/benchmark-fast-exhibition-clip.yml` runs on `[self-hosted, japan]`, supports race_date/stadium/race/clip start/duration/entry order. Latest benchmark configuration is v9 and was most recently set to 2026-09-09 Kiryu12 for unchanged-code confirmation.

## Required behavior for future sessions / automation
1. Read this file first.
2. Inspect latest GitHub commits/files/workflow runs; latest GitHub wins.
3. Inspect actual job logs, not just green/red status.
4. Continue implementation/testing autonomously.
5. Update this file after meaningful design/result changes.
6. Never claim live readiness without accepted=true evidence plus geometry sanity across multiple independent races.
7. Next immediate action: derive entry order result-blind for one of 2026-09-10 Kiryu 3/6/9, then run unchanged v9 + tracker v5 as third independent sample.

## Done-enough-to-notify milestone
Notify user only when a seed/refinement version generalizes across multiple independent September races with varied entry order; tracker quality passes without manual/race-specific offsets; geometry/identity is sane; latency fits post-exhibition operation; live local wrapper is updated; and at least one end-to-end self-hosted live-style validation succeeds.
