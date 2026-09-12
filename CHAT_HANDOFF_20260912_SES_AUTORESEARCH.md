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
Latest artifact reinspection of run `34688954987` for 2026-09-10 Kiryu3 showed `exhibition_tracking_v5.json` actually had `accepted=false`, boat6 LOW (fallback .565), with boat6 drifting to x~65/y~1087 by +1.5s. Therefore the older prose claim that this run was ALL HIGH/accepted=true must NOT be used. Latest artifact JSON wins.
The race result remains unread and MUST remain blind.

## v14 seed — generic 2D fallback
`auto_seed_exhibition_motion_v14.py`.
Starts from the v13-equivalent short persistence+direction validation and searches a resolution-relative 2D grid ONLY for rows that fail it. This fixed the Kiryu6 wrong-y/rail seed generically, moving boat6 from the bad foreground row toward y~795.5, but tracker identity collision remained.

## Tracker v6 — rejected
`track_exhibition_boats_v6.py`, commit `4436499f9bb2dd7cc8a3b49a3b75db81e198d13d`.
It clipped each boat's template search IMAGE to a dynamic vertical cell. Four-race run `34711310461` showed this can remove valid template evidence when rows are close; e.g. standard Kiryu12 boat2 regressed from healthy HIGH/0 fallback/NCC .848 to LOW/fallback .391/NCC .567. Do not production-wire v6.

## Tracker v7 — center-gated lane partition, useful but not sufficient
`track_exhibition_boats_v7.py`, commit `9930d3d55ecb85e48b276a542ee3fa552729509c`.
Workflow `.github/workflows/regress-exhibition-seed14-track7.yml`, commit `16889e45456722256f1b638abb9df888e0853e6a`, run `34712928619`.
Principled change: keep the local search image uncut, but only accept template-match CENTERS inside the boat's dynamic vertical cell. Same NCC/fallback thresholds as v5/v6; no loosened gate.

Four-sample artifact audit:
- 2026-09-10 Kiryu12 standard: accepted=true, ALL HIGH, min separation 26.689px. fallback 1=.348,2=0,3=0,4=.130,5=0,6=.043. median NCC 1=.965,2=.848,3=.831,4=.825,5=.875,6=.883. This successfully restores boat2 without lowering thresholds.
- 2026-09-09 Kiryu12 varied `1,2,4,5,6,3`: accepted=true; 1/2/4/5/6 HIGH, boat3 MEDIUM. min separation 45.026px. boat3 fallback .391/NCC .861; +1.5 center x~267/y~857. Technical pass but weaker outer-row behavior.
- 2026-09-10 Kiryu6: accepted=false. boats1-4 HIGH, boat5 MEDIUM fallback .391/NCC .873, boat6 LOW fallback .609/NCC .923. 5/6 trajectories still collapse toward left/background by +1.5 despite center gating.
- 2026-09-10 Kiryu3: accepted=true and all tiers HIGH, BUT physically invalid: boat6 runs to x~36/y~1060 by +1.5 (near/off frame) and SES flips drastically relative to prior exhibition lock. This is a critical example that confidence acceptance alone cannot establish identity.
Conclusion: v7 improves cell clipping pathology but does NOT solve false wake/background identity for rescued outer rows. Do not production-wire it yet.

## v15/v16 prior experiment — rejected direction
`auto_seed_exhibition_motion_v15.py` is a faster short-horizon 2D rescue. `auto_seed_exhibition_motion_v16.py` added longer-horizon validation but could override rows that were already healthy under v13-equivalent short persistence/direction, causing regressions. Key rule retained: long-horizon evidence must never override a healthy short-gate row.

## CURRENT seed candidate: v17 rescued-row-only long survival
`auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
Design:
- run v14;
- preserve every non-rescued/healthy v14 row EXACTLY;
- ONLY rows that v14 rescued are revalidated through .15/.30/.45/.60/.90/1.20s;
- require >=5/6 good horizons, median NCC >=.55, min NCC >=.35, dominant-LK direction consistency, and on-frame survival for the final long matches;
- if v14 chosen rescue fails, re-rank only the bounded result-blind 2D candidates already generated by v14 using long survival + fleet geometry;
- fail closed if no rescue candidate survives;
- no result, boat-number special case or race-specific offset.

Regression workflow `.github/workflows/regress-exhibition-seed17-track7.yml`, commit `bb54c2bbb5e9dbc171ae3ab9558771770ab79861`, run `34713478083`.
Matrix: Kiryu3, Kiryu6, Kiryu12 standard, Kiryu12 varied. At this handoff update the run had just been queued. Inspect actual artifacts/JSON after completion; workflow green alone is insufficient.

## Blindness status
Results for 2026-09-10 Kiryu3/6/9 remain unread in this SES research thread. Preserve blindness. 2026-09-09 Kiryu12 is technical regression only after earlier result exposure. 2026-09-10 Kiryu12 is technical calibration/exposed.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old (seed v1 + tracker v3). DO NOT update until one unchanged seed+tracker combination passes the four-sample technical matrix with sane identity/geometry and <=60s.

## Immediate next actions
1. Inspect run `34713478083` all four jobs/artifacts.
2. For each inspect seed v17 decisions, runtime, tracker accepted, fallback, NCC, min separation and +0.5/+1.0/+1.5 physical trajectories.
3. Pay special attention to Kiryu3 boat6 and Kiryu6 boats5/6. `accepted=true` with edge/off-frame drift is a failure.
4. If v17+v7 still fails, do NOT relax thresholds. Next principled direction is joint six-boat mutual-exclusion / fleet-consistent assignment, not more race-specific seed offsets.
5. Only after a four-sample sane pass update `run_exhibition_ses_live_local.py` and perform a self-hosted end-to-end live-style validation.
6. Update this handoff after meaningful results/design changes.

## Live-ready milestone
Before notifying user as complete:
- multiple independent September samples incl varied entry;
- automatic acquisition+seed+tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30s, maximum <=60s;
- `run_exhibition_ses_live_local.py` updated to validated pipeline;
- >=1 self-hosted end-to-end live-style success.
Prefer 10+ samples before treating SES as stable/predictive. SES remains an attack/head-support feature candidate, not direct finishing-order rank.
