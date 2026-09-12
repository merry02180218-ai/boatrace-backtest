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
- Do not production-wire experimental code until multi-race technical generalization is demonstrated.
- `accepted=true` is necessary but NOT sufficient: trajectories must also stay physically sane/on-frame and preserve identity.
- Final race-by-race operation should be persistent on Japan self-hosted PC; Actions are validation/logging.
- Exact Japan Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Latency target
Ideal <=30 sec after video availability; maximum <=60 sec.
Downloader: `download_boatcast_exhibition_fastclip.py`.

## Important audit correction: old v13 handoff claim is not authoritative
Artifact reinspection of run `34688954987` for 2026-09-10 Kiryu3 showed `exhibition_tracking_v5.json` actually had `accepted=false`, boat6 LOW (fallback .565), with boat6 drifting to x~65/y~1087 by +1.5s. Therefore the older prose claim that this run was ALL HIGH/accepted=true must NOT be used. Latest artifact JSON wins. The race result remains unread and MUST remain blind.

## v14 seed — generic 2D fallback
`auto_seed_exhibition_motion_v14.py` starts from the v13-equivalent short persistence+direction validation and searches a resolution-relative 2D grid ONLY for rows that fail it. This fixed the Kiryu6 wrong-y/rail seed generically, moving boat6 away from the bad foreground row toward y~795.5, but tracker identity collision remained.

## Tracker v6 — rejected
`track_exhibition_boats_v6.py`, commit `4436499f9bb2dd7cc8a3b49a3b75db81e198d13d`.
It clipped each boat's template search IMAGE to a dynamic vertical cell. Four-race run `34711310461` showed this can remove valid template evidence when rows are close; e.g. standard Kiryu12 boat2 regressed from healthy HIGH/0 fallback/NCC .848 to LOW/fallback .391/NCC .567. Do not production-wire v6.

## Tracker v7 — center-gated lane partition, useful but not sufficient
`track_exhibition_boats_v7.py`, commit `9930d3d55ecb85e48b276a542ee3fa552729509c`.
Principled change: keep the local search image uncut, but only accept template-match CENTERS inside the boat's dynamic vertical cell. Same NCC/fallback thresholds as v5/v6; no loosened gate.

Earlier seed14+v7 four-sample audit:
- 2026-09-10 Kiryu12 standard: accepted=true, ALL HIGH.
- 2026-09-09 Kiryu12 varied `1,2,4,5,6,3`: accepted=true; boat3 MEDIUM, others HIGH.
- 2026-09-10 Kiryu6: accepted=false; outer rows 5/6 collapse toward left/background.
- 2026-09-10 Kiryu3: accepted=true/all HIGH BUT physically invalid; boat6 runs near/off frame by +1.5s.
Conclusion: v7 improves cell clipping pathology but does NOT solve false wake/background identity. Do not production-wire it.

## v15/v16 prior experiment — rejected direction
`auto_seed_exhibition_motion_v15.py` is a faster short-horizon 2D rescue. `auto_seed_exhibition_motion_v16.py` added longer-horizon validation but could override rows already healthy under v13-equivalent short persistence/direction, causing regressions. Retained rule: long-horizon evidence must never override a healthy short-gate row.

## Seed v17 — rescued-row-only long survival
`auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
Design:
- run v14;
- preserve every non-rescued/healthy v14 row EXACTLY;
- ONLY v14-rescued rows are revalidated through .15/.30/.45/.60/.90/1.20s;
- require >=5/6 good horizons, median NCC >=.55, min NCC >=.35, dominant-LK direction consistency, and on-frame survival;
- if the v14 rescue fails, rerank only bounded result-blind v14 2D candidates using long survival + fleet geometry;
- fail closed if no rescue survives;
- no result/boat-number/race-specific special case.

### Actual v17 + tracker7 matrix
Workflow `.github/workflows/regress-exhibition-seed17-track7.yml`, commit `bb54c2bbb5e9dbc171ae3ab9558771770ab79861`, run `34713478083`.
- Kiryu12 varied: workflow success.
- Kiryu12 standard: workflow success.
- Kiryu3: workflow success, but workflow green alone is not evidence of physical identity and prior outer-row pathology remains an audit concern.
- Kiryu6: tracker v7 failed closed. Therefore v17+v7 does NOT pass the four-sample unchanged matrix and is NOT live-ready.

### Kiryu6 v17 artifact diagnosis
Fresh artifact inspection from run `34713478083` shows the seed itself is plausible; failure is now primarily tracker-level.
- selected_sec = 29.75
- final seeds: 1 [790.0,420.5], 2 [849.0,470.5], 3 [882.0,531.5], 4 [935.5,600.0], 5 [737.0,717.0], 6 [829.0,795.5]
- dominant LK dx: 1 -12.125, 2 -10.253, 3 -6.552, 4 -0.578, 5 +5.977, 6 +11.010
- v14 rescued only boat6 from the bad original motion center [989,930.5] to [829,795.5].
- v17 long-survival check on boat6 PASSED all 6 horizons with median NCC ~.959, min NCC ~.920, net dx +196, final long-match center about [1025,776], on-frame and direction-consistent.
- v17_rescued_row_count=0 because the v14 boat6 rescue already survived the long gate.
This means adding more race-specific seed movement is the wrong next step. The tracker must preserve identity jointly across the fleet.

## CURRENT tracker candidate: v8 joint six-boat assignment
File `track_exhibition_boats_v8.py`.
Implementation commit `264bf494812b6b72e4af94cacc1d40b009a6dde1`.
Benchmark workflow `.github/workflows/regress-exhibition-seed17-track8.yml`, commit `427d4dfdd395f6cc64e5b1c33a6621acc2ff0297`.
Run `34718223751` was queued at this handoff update.

Principled v8 design:
- retain v7 LK prediction, center-gated dynamic lane cells, stride2, same min-NCC/strong-NCC/fallback caps and final confidence gate;
- for each boat, generate up to top-3 distinct NCC template candidates using local non-maximum suppression plus the existing prediction fallback;
- choose all six boats jointly (max 4^6 combinations/frame) rather than independent argmaxes;
- hard-reject lane-cell violations, entry-order violations, >24*advance per-step jumps, and near-duplicate (<20px) image patches;
- joint score rewards NCC and mildly penalizes distance from temporal prediction and robust fleet step without forcing equal x movement;
- add a physical fail-closed guard if a tracked center reaches within 8px of the image edge;
- no quality threshold was relaxed; no race result, boat number or race-specific correction is used.

### v8 validation matrix
Same unchanged four technical videos:
1. 2026-09-10 Kiryu3 standard (result still blind)
2. 2026-09-10 Kiryu6 standard (result still blind)
3. 2026-09-10 Kiryu12 standard technical calibration
4. 2026-09-09 Kiryu12 varied `1,2,4,5,6,3` technical regression
Inspect actual artifacts/JSON after run `34718223751` completes; workflow green alone is insufficient. Specifically inspect Kiryu3 boat6 and Kiryu6 boats5/6 trajectories through +1.5s, fallback fractions, NCC, min lane separation, physical on-frame survival and latency.

## Blindness status
Results for 2026-09-10 Kiryu3/6/9 remain unread in this SES research thread. Preserve blindness. 2026-09-09 Kiryu12 is technical regression only after earlier result exposure. 2026-09-10 Kiryu12 is technical calibration/exposed.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old (seed v1 + tracker v3). DO NOT update until one unchanged seed+tracker combination passes the four-sample technical matrix with sane identity/geometry and <=60s.

## Immediate next actions
1. Inspect run `34718223751` all four jobs and artifacts after completion.
2. Reject any case where `accepted=true` but trajectories reach/approach frame edges, collapse to background, violate identity, or produce implausible fleet geometry.
3. If v17+v8 passes all four physically sane and <=60s, update `run_exhibition_ses_live_local.py` to v17+v8 and perform one self-hosted end-to-end live-style validation.
4. If v8 still fails, do NOT relax gates. Inspect which joint constraints failed and move toward a stronger fleet-consistent temporal assignment/appearance model rather than seed offsets.
5. Update this handoff after every meaningful result/design change.

## Live-ready milestone
Before notifying user as complete:
- multiple independent September samples incl varied entry;
- automatic acquisition+seed+tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30s, maximum <=60s;
- `run_exhibition_ses_live_local.py` updated to validated pipeline;
- >=1 self-hosted end-to-end live-style success.
Prefer 10+ samples before treating SES as stable/predictive. SES remains an attack/head-support feature candidate, not direct finishing-order rank.
