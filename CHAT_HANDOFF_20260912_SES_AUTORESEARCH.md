# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-14 JST
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

## Tracker v8 — insufficient
File `track_exhibition_boats_v8.py`, commit `264bf494812b6b72e4af94cacc1d40b009a6dde1`.
Workflow run `34718223751` matrix: Kiryu12 standard SUCCESS, Kiryu12 varied SUCCESS, Kiryu3 FAILURE, Kiryu6 FAILURE. v8 is 2/4 and not live-ready. Per-frame joint six-boat assignment alone does not preserve identity over time.

## Tracker v9 — rejected after 4/4 matrix failure
File `track_exhibition_boats_v9.py`.
Run `34752608413` on the unchanged four-video matrix failed all four jobs. v9 added immutable seed-frame anchor appearance memory on top of v8, but did not cure the outer-row collapse.

### Key v9 Kiryu6 artifact diagnosis
Artifact `seed17-track9-kiryu6`, artifact ID `10315947350`.
- v17 selected_sec = 29.75 and seed6 remained plausible.
- tracker failed closed at native frame 1131 because `dynamic_lane_cells` became invalid.
- last centers at failure:
  - 1 [780.14,452.89]
  - 2 [870.28,512.96]
  - 3 [979.91,604.05]
  - 4 [1033.32,733.01]
  - 5 [650.77,852.14]
  - 6 [679.22,859.86]
- boats5/6 y separation collapsed to only ~7.72 px.
- fallback counts were already 5=22 and 6=21, while boats1-4 remained 0.
- immutable anchor-time templates for 5/6 were still around y~765/y~819, so the later y convergence is physically suspicious.

Interpretation: the dynamic lane cells were built from the previous raw tracked centers. Once an outer row drifted, its own wrong center moved the next frame's lane boundary, creating a self-reinforcing identity/lane collapse. This is a tracker geometry feedback problem, not evidence that the v17 seed needs another race-specific move. Do not relax lane-separation or confidence thresholds.

## CURRENT candidate: tracker v10 fleet-affine lane reference
File `track_exhibition_boats_v10.py`.
Implementation commit: `f92e02643d96300f0a2d1ff7f6524892e4e6b760`.
Workflow `.github/workflows/regress-exhibition-seed17-track10.yml`.
Workflow commit: `a3cd49d1c8feaf1eeb26a09995698933df1ed2cf`.
Run: `34778546662` (launched by push; initially queued on Japan self-hosted runner at this handoff update).

Principled v10 change:
- keep v9 joint six-boat assignment, immutable anchor memory, adaptive appearance logic, stride2, NCC thresholds and fallback caps unchanged;
- replace only the dynamic vertical lane-cell reference;
- initialize immutable seed-frame y positions once;
- each frame fit a robust affine mapping from immutable seed y geometry to the current fleet y geometry;
- clip each boat's residual around that fleet-affine reference using a scale-aware allowance derived from immutable neighboring seed gaps (`max(12px, 0.28 * local initial gap)`);
- build lane cells from those fleet-consistent reference y values rather than directly from raw potentially drifting centers;
- fail closed if projected order degenerates or a lane cell becomes too small;
- no race result, boat number, race-specific offset, or loosened quality threshold is used.

Rationale: allow ordinary camera/perspective vertical motion while preventing one bad outer-row track from dragging its own future lane boundary into a neighboring identity. This directly targets the v9 Kiryu6 failure mechanism without touching the seed or lowering gates.

## v10 validation matrix
Run `34778546662`, unchanged videos:
1. 2026-09-10 Kiryu3 standard — result remains blind.
2. 2026-09-10 Kiryu6 standard — result remains blind.
3. 2026-09-10 Kiryu12 standard — technical calibration.
4. 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3` — technical regression.

When the run completes, inspect actual artifact JSON, not workflow green only. For each job inspect:
- accepted/failure reason;
- +0.5/+1.0/+1.5 physical centers and on-frame identity;
- fallback fractions and median NCC/anchor evidence;
- minimum lane separation;
- whether Kiryu3 boat6 and Kiryu6 boats5/6 remain distinct;
- FastClip + seed + tracker latency, max <=60 sec.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update until one unchanged seed+tracker combination passes the full technical matrix with sane identity/geometry and <=60 sec.

## Exact restart point
1. Inspect run `34778546662` all four jobs/artifacts when completed.
2. If v10 has a technical coding/import failure, fix and rerun immediately.
3. If v10 gets past the old lane-cell collapse but still loses identity, do not relax gates. Next direction should use stronger multi-frame/beam/Viterbi fleet-consistent temporal appearance assignment or explicit immutable-anchor trajectory likelihood, not seed offsets.
4. If v17+v10 passes 4/4 physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` to v17+v10 and perform a self-hosted end-to-end live-style validation.
5. Only after technical live validation expand toward 10+ September samples before treating SES as stable/predictive.
6. Update this handoff after every meaningful result/design change with commit SHA, Run ID, artifact IDs/evidence, failure diagnosis and exact restart point.

## Live-ready milestone
Before user notification as complete:
- multiple independent September samples including varied entry;
- automatic acquisition + seed + tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30 sec, maximum <=60 sec;
- `run_exhibition_ses_live_local.py` updated to validated pipeline;
- >=1 self-hosted end-to-end live-style success.
SES remains an attack/head-support feature candidate, not direct finishing-order rank.
