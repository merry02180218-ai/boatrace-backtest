# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-13 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue BOATCAST start-exhibition video development until immediate post-exhibition live use is reliable: result-blind FastClip -> automatic six-boat seed -> automatic tracking -> SES -> later model re-evaluation, with no manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results override this handoff and old chat memory.
- Never inspect race results before locking exhibition-only judgement on blind/pristine samples.
- July/August 2026 are NON-PRISTINE/research-only; September preferred.
- Never weaken fail-closed quality gates merely to obtain `accepted=true`.
- Never hard-code boat-number-specific/race-specific offsets.
- `accepted=true` is necessary but not sufficient: trajectories must be physically sane/on-frame and preserve identity.
- Final race-by-race operation should be persistent on Japan self-hosted PC; Actions are validation/logging.
- Exact Japan Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.
- Live latency target: ideal <=30 sec after video availability, maximum <=60 sec.

## Blindness status
- 2026-09-10 Kiryu3/6/9 results remain unread in this SES research thread. Preserve this.
- 2026-09-09 Kiryu12 result is already exposed and is technical regression only.
- 2026-09-10 Kiryu12 is technical calibration/exposed.

## Important audit correction
Old prose that v13 passed Kiryu3 was wrong. Artifact reinspection of run `34688954987` showed `accepted=false`, boat6 LOW fallback .565 and drift near/off frame by +1.5s. Artifact JSON wins over older prose.

## Seed state: v17
File `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
It runs v14, freezes healthy rows, and applies long-horizon .15/.30/.45/.60/.90/1.20s validation only to rows that v14 rescued. It remains the current seed candidate.

Kiryu6 artifact diagnosis from run `34713478083` showed v17 seed itself is plausible:
- selected_sec 29.75
- seeds 1 [790,420.5], 2 [849,470.5], 3 [882,531.5], 4 [935.5,600], 5 [737,717], 6 [829,795.5]
- v14 rescued boat6 from bad rail/background center [989,930.5] to [829,795.5]
- boat6 long-survival passed 6/6 horizons, median NCC ~.959, min ~.920, net dx +196, final long center ~[1025,776], on-frame and direction-consistent.
Therefore current blocker is tracker identity preservation, not additional race-specific seed movement.

## Rejected/insufficient tracker directions
- v6 clipped the search image to lane cells and removed valid evidence; rejected.
- v7 center-gated candidate centers without clipping and improved regression, but Kiryu6 outer rows still collapsed and Kiryu3 could be confidence-green while physically invalid.
- v8 joint six-boat assignment file `track_exhibition_boats_v8.py`, commit `264bf494812b6b72e4af94cacc1d40b009a6dde1`.
  Workflow `.github/workflows/regress-exhibition-seed17-track8.yml`, run `34718223751`.
  Actual matrix: Kiryu12 standard SUCCESS, Kiryu12 varied SUCCESS, Kiryu3 FAILURE, Kiryu6 FAILURE. So v8 is 2/4 and NOT live-ready.
  v8 jointly chooses top-k candidates with lane/order/jump/mutual-exclusion guards, but per-frame joint assignment alone is insufficient to preserve identity over time.

## CURRENT tracker candidate: v9 immutable anchor appearance memory
File `track_exhibition_boats_v9.py`.
Implementation commit: `30a7b7ad2e44e51ccd2d0d2c0df0e32b5c265608`.
Workflow `.github/workflows/regress-exhibition-seed17-track9.yml`.
Workflow commit: `df572569c200f49002ddf05915d14c8f52841603`.
Run: `34752608413`.
At this handoff update the run was queued/in progress on Japan self-hosted runner; inspect actual artifacts/JSON after completion.

Principled v9 change relative to v8:
- retain v8 joint fleet assignment, dynamic lane cells, entry-order guard, max-step guard, mutual exclusion, edge guard, stride2, min-NCC/strong-NCC and fallback caps;
- keep an immutable seed-frame anchor template for every boat alongside the adaptive template;
- generate candidates from both adaptive and anchor memories, union/deduplicate them, and score every proposed patch against both memories;
- joint score rewards both adaptive similarity and immutable-anchor similarity so gradual wake/background contamination is disfavored;
- adaptive template updates only when adaptive NCC >=.72 AND anchor NCC >=.55, otherwise it freezes;
- final identity confidence uses actual appearance evidence while existing numeric quality thresholds/fallback caps stay unchanged;
- fail-closed paths now write diagnostic JSON before exiting, including last valid centers/candidate counts/step, so failed artifacts are inspectable;
- no race result, boat-number special case, or race-specific offset is used.

## v9 validation matrix
Unchanged four technical videos:
1. 2026-09-10 Kiryu3 standard — result remains blind.
2. 2026-09-10 Kiryu6 standard — result remains blind.
3. 2026-09-10 Kiryu12 standard — technical calibration.
4. 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3` — technical regression.

Run `34752608413` must be audited beyond workflow green. For every job inspect:
- accepted flag and failure reason;
- +0.5/+1.0/+1.5 centers and physical on-frame behavior;
- fallback fractions;
- median identity/anchor/adaptive NCC;
- minimum lane separation;
- diagnostic last centers for failed jobs;
- acquisition + seed + tracker runtime, requiring <=60 sec and preferring <=30 sec core path.
Pay special attention to Kiryu3 boat6 and Kiryu6 boats5/6.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update until one unchanged seed+tracker combination passes the four-sample technical matrix with sane identity/geometry and <=60 sec.

## Immediate next actions
1. Inspect run `34752608413` all four jobs/artifacts when completed.
2. If v17+v9 fails, use the newly persisted failure diagnostics; do not relax thresholds. Next principled direction is stronger multi-frame/beam/Viterbi fleet-consistent temporal appearance assignment rather than seed offsets.
3. If v17+v9 passes 4/4 physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` to v17+v9 and run one self-hosted end-to-end live-style validation.
4. After technical live validation, expand toward 10+ September samples before treating SES as stable/predictive.
5. Update this handoff after every meaningful design/result change with commit SHA, Run ID, artifact evidence, failure and exact restart point.

## Live-ready milestone
Before user notification as complete:
- multiple independent September samples including varied entry;
- automatic acquisition + seed + tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30 sec, maximum <=60 sec;
- `run_exhibition_ses_live_local.py` updated to validated pipeline;
- >=1 self-hosted end-to-end live-style success.
SES remains an attack/head-support feature candidate, not direct finishing-order rank.
