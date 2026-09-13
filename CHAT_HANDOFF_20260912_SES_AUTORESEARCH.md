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

Kiryu6 diagnosis established that v17 can place rescued boat6 plausibly and validate it through long horizons; current blocker is tracker identity preservation rather than more race-specific seed movement.

## Tracker history
### v8 — insufficient
`track_exhibition_boats_v8.py`, commit `264bf494812b6b72e4af94cacc1d40b009a6dde1`.
Run `34718223751`: Kiryu12 standard SUCCESS, Kiryu12 varied SUCCESS, Kiryu3 FAILURE, Kiryu6 FAILURE. Per-frame joint assignment alone did not preserve identity over time.

### v9 — rejected
`track_exhibition_boats_v9.py`, implementation commit `30a7b7ad2e44e51ccd2d0d2c0df0e32b5c265608`.
Run `34752608413` failed the unchanged four-video matrix. Immutable seed-frame appearance memory did not cure outer-row collapse. Kiryu6 showed 5/6 y separation collapsing to ~7.7px with high fallback counts, implying tracker geometry feedback rather than seed failure.

### v10 — REJECTED after artifact audit
`track_exhibition_boats_v10.py`; workflow `.github/workflows/regress-exhibition-seed17-track10.yml`; workflow commit `a3cd49d1c8feaf1eeb26a09995698933df1ed2cf`; run `34778546662`.
All four matrix jobs failed closed. This is not a coding/import failure; FastClip and seed v17 succeeded and tracker v10 itself reached its safety gates.

v10 changed only lane-cell reference to a robust affine projection from immutable seed y geometry. It regressed previously healthier samples, so do not continue this lane-cell direction.

Artifact evidence:
- Kiryu3 artifact ID `10323234881`: failed `FAIL_CLOSED: tracked center reached frame edge`. At +0.5 boat6 was already ~[297.8,979.6] from seed [616,961], despite v17 slit LK direction being positive (`dominant_dx` +13.269). At +1.0 boat6 reached x~11.7/y~1047.4. This is a clear high-NCC wake/background run opposite the slit motion and validates the need for a motion-direction identity guard.
- Kiryu6 artifact ID `10324139376`: failed `FAIL_CLOSED: no feasible joint six-boat assignment`. Seed v17 was plausible; at +1.0 boat5 had fallen back toward x~728.8 while its immutable slit LK direction was strongly positive (`dominant_dx` +15.848), and later assignment became infeasible.
- Kiryu12 standard artifact ID `10324203882`: also regressed to `FAIL_CLOSED: no feasible joint six-boat assignment`; e.g. boat1/2/3 accumulated many fallback steps. Therefore v10's fleet-affine y reference is rejected rather than tuned.
- Kiryu12 varied artifact ID `10323469202`: job also failed closed.
No thresholds were relaxed and no race results were read.

## CURRENT candidate: tracker v11 immutable slit-motion corridor
File `track_exhibition_boats_v11.py`.
Implementation commit `372aea94e0f718cc7dc2be3502c8761f33433ecf`.
Workflow `.github/workflows/regress-exhibition-seed17-track11.yml`.
Workflow creation commit `5632113f288d442bc1e619e284ba8d6b1a553b47`.
Regression trigger commit `bce6845d3d37852ffbfde22f7a174b3fa8136110`.
Run `34788921925` launched on the Japan self-hosted runner and was queued at this handoff update.

Principled v11 design:
- deliberately return to v9 lane-cell behavior; v10 affine lane reference is NOT inherited;
- keep v9 joint six-boat assignment, immutable anchor memory, adaptive appearance logic, stride2, NCC thresholds and fallback caps unchanged;
- read result-blind v17 `row_details[*].dominant_dx` from `auto_seed_meta_v17.json`;
- only rows with |dominant_dx| >= 4px establish an immutable slit screen-x direction; near-zero rows remain unconstrained;
- reject candidates whose cumulative movement goes more than a resolution-scaled 5% frame width opposite the immutable slit direction;
- reject a single update whose reverse step exceeds a resolution-scaled 1.25% frame width per native frame;
- if filtering leaves no safe candidate, fail closed; never restore an unsafe fallback merely to pass;
- no race result, boat-number rule, race-specific offset or loosened confidence threshold is used.

Rationale: Kiryu3 boat6 and Kiryu6 outer-row failures show that high NCC is not sufficient because wake/background texture can remain highly correlated while moving in the physically wrong screen-x direction. v11 adds an independent motion-consistency identity signal derived before results and before the tracker drifts.

## v11 validation matrix / exact restart point
Run `34788921925`, unchanged four videos:
1. 2026-09-10 Kiryu3 standard — result remains blind.
2. 2026-09-10 Kiryu6 standard — result remains blind.
3. 2026-09-10 Kiryu12 standard — technical calibration.
4. 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3` — technical regression.

Next run must:
1. Inspect all four v11 jobs/artifacts, not workflow green alone.
2. Confirm Kiryu3 boat6 no longer runs left/off-frame against positive slit motion.
3. Confirm Kiryu6 boats5/6 remain distinct and physically sane through +1.5s.
4. Confirm Kiryu12 standard/varied are not regressed by the new guard.
5. Record accepted/failure reason, fallback fractions, median identity/anchor NCC, min lane separation, +0.5/+1.0/+1.5 centers, and FastClip+seed+tracker latency.
6. If v11 merely fails earlier but safely, do NOT relax the corridor or NCC gates to force a pass. Diagnose candidate availability and move toward multi-frame beam/Viterbi trajectory assignment using immutable appearance + motion likelihood.
7. If one unchanged seed+tracker combination passes all four physically sane and <=60 sec, only then update `run_exhibition_ses_live_local.py` and perform a self-hosted end-to-end live-style validation.
8. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID, artifact IDs/evidence and restart point.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update until an unchanged seed+tracker passes the full technical matrix with sane identity/geometry and <=60 sec.

## Live-ready milestone
Before user notification as complete:
- multiple independent September samples including varied entry;
- automatic acquisition + seed + tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30 sec, maximum <=60 sec;
- `run_exhibition_ses_live_local.py` updated to validated pipeline;
- >=1 self-hosted end-to-end live-style success.
Prefer 10+ samples before treating SES as stable/predictive. SES remains an attack/head-support feature candidate, not direct finishing-order rank.
