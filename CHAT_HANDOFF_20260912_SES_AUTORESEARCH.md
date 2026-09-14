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
- 2026-09-10 Kiryu3/6/9 results remain unread. Preserve blindness.
- 2026-09-09 Kiryu12 result is exposed technical regression only.
- 2026-09-10 Kiryu12 is exposed technical calibration.

## Seed state
Current seed remains `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
Kiryu6 evidence continues to indicate that v17 can place rescued outer rows plausibly; current blocker is tracker identity preservation, not more race-specific seed movement.

## Tracker history summary
- v8 (`264bf494812b6b72e4af94cacc1d40b009a6dde1`): per-frame joint six-boat assignment. Kiryu12 standard/varied passed, Kiryu3/Kiryu6 failed.
- v9 (`30a7b7ad2e44e51ccd2d0d2c0df0e32b5c265608`): immutable seed-frame appearance memory. Still allowed outer-row wake/background collapse.
- v10: fleet-affine y-cell reference. Rejected after all four matrix jobs failed closed and previously healthier samples regressed.
- v11 (`372aea94e0f718cc7dc2be3502c8761f33433ecf`): immutable slit-motion corridor. Run `34788921925`; all four failed closed. It prevented unsafe continuation but was too myopic to recover a feasible per-frame assignment.
- v12 (`13a929a8a296ac92247ba6664f9e5bd35ec9cb4e`): four-step per-boat motion memory while remaining greedy per frame. Run `34804266678`; all four failed safely/fail-closed.
- v13 (`ed02d51599da88c3930370116d70b5d390d5ee0b`): first multi-hypothesis complete six-boat beam tracker. Run `34807739191`; all four unchanged jobs failed closed because every beam hypothesis died. No result was read and no quality threshold was relaxed.
- v14 (`a2df021c038a09f4df324545426b4892800e9eda`): diversified directional beam, bounded local appearance searches around prediction and +/-0.50*search_x, larger feasible transition pool, same hard gates/thresholds. Run `34809061470` now fully audited below.

## v13 diagnosis retained
Run `34807739191` showed all four failed with `all beam hypotheses died` while fallback use remained zero at the failure point. The key problem was candidate omission: if the locally correct appearance candidate was not generated around the current x prediction, beam width could not recover it. This motivated v14 candidate diversification rather than threshold relaxation.

## v14 completed audit — authoritative
Workflow `.github/workflows/regress-exhibition-seed17-track14.yml`, Run `34809061470`.
Artifacts inspected directly:
- Kiryu3 artifact ID `10333959406`
- Kiryu6 artifact ID `10333899996`
- Kiryu12 standard artifact ID `10334655876`
- Kiryu12 varied artifact ID `10334536496`

Results:
- **Kiryu3: rejected/fail closed** — `FAIL_CLOSED: no feasible v14 six-boat beam state at step 2` (4 native frames). No fallback had yet been used. Last centers were still essentially seed positions: 1 [523,683], 2 [777,738.5], 3 [800.5,787.5], 4 [593,836], 5 [555,883.5], 6 [616,961]. Candidate diversity did not solve the very-early omission/feasibility conflict.
- **Kiryu12 standard: rejected/fail closed** — `FAIL_CLOSED: no feasible v14 six-boat beam state at step 12` (24 native frames). Last centers: 1 [1216,637], 2 [1173,723], 3 [1219,756], 4 [1129,836], 5 [1108,922], 6 [1095,982]. Fallback counts across 11 samples: 1=10, 2=6, 3=8, 4=7, 5=5, 6=3. This is not a clean identity pass.
- **Kiryu12 varied `1,2,4,5,6,3`: rejected/fail closed** — `FAIL_CLOSED: no feasible v14 six-boat beam state at step 8` (16 native frames). Last centers: 1 [1176,671], 2 [1150,731], 4 [1113,825], 5 [1078,888], 6 [982,983], 3 [983,1059]. Fallback counts across 7 samples: 1=6, 2=6, 4=4, 5=1, 6=3, 3=1.
- **Kiryu6: workflow/quality accepted but NOT sufficient for production**. Final centers remained on-frame/distinct: 1 [214,456], 2 [206,497], 3 [362,560], 4 [522,626], 5 [936,721], 6 [1072,816]. Fallback fractions: 1=.174, 2=.087, 3=.130, 4=.348, 5=.348, 6=.565. Median identity NCC: 1=.706, 2=.708, 3=.673, 4=.639, 5=.862, 6=.846. Median anchor NCC: 1=.495, 2=.325, 3=.542, 4=.685, 5=.890, 6=.846. Boat6's .565 fallback fraction is too weak to treat this single acceptance as stable proof. Outer boats nevertheless stayed physically distinct/on-frame through +1.5s.

Interpretation: v14 improved candidate coverage enough to produce one technical acceptance, but three unchanged samples still die and the successful Kiryu6 path relies heavily on fallback for boat6. Increasing beam width again is not the principled next step. The remaining problem is that candidate generation is still conditioned on the current prediction, so the correct path can disappear before temporal scoring can rescue it.

## CURRENT candidate: tracker v15 full-cell anchor lattice + multi-frame beam
File: `track_exhibition_boats_v15.py`
Implementation commit: `1d18621d725343437aed81554713a1db8017eb68`
Workflow: `.github/workflows/regress-exhibition-seed17-track15.yml`
Workflow creation/trigger commit: `fbd8aac8ae321402f0206f4293ad061584280092`
Current Run: `34816553593`
Workflow ID: `357605796`
At this handoff update Run `34816553593` is confirmed queued on the Japan self-hosted runner. Do not invent results before completion.

### v15 design
v15 deliberately preserves v13's temporal beam, immutable slit-motion corridor, hard geometry/order/jump/duplicate/edge/direction gates, existing NCC thresholds, fallback caps and adaptive appearance behavior.

New candidate-lattice change only:
- keep the unchanged local v9 dual-memory proposals around each beam state's current prediction;
- additionally compute immutable seed-anchor NCC peaks across the boat's **entire current lane cell**, independent of current x prediction;
- use full-frame `matchTemplate` response per immutable anchor/frame, then retain NMS-separated peaks whose centers lie in the current lane cell;
- merge local candidates and full-cell anchor candidates, deduplicate nearby positions and pass them into the unchanged v13 multi-frame six-boat beam;
- the temporal beam therefore receives alternatives that can survive even when the current x prediction is locally wrong, approximating a short-window candidate lattice/Viterbi selector without relaxing safety gates;
- no result, boat-number rule, race-specific offset or quality-threshold relaxation.

Validation uses the same unchanged four-video matrix and `--stride 2 --beam-width 8 --per-state-keep 8`.

## Exact restart point
1. Inspect Run `34816553593` as soon as it leaves queued state.
2. If code/runtime fails, inspect logs, fix v15/workflow and rerun immediately.
3. If tracker runs complete, inspect all four artifacts/JSON; workflow green alone is insufficient.
4. Record for every race: accepted/failure reason, failure step/beam survival, fallback counts/fractions, median adaptive/anchor NCC, min separation, +0.5/+1.0/+1.5 centers, on-frame/identity sanity, and FastClip+seed+tracker latency.
5. Specifically verify Kiryu3 boat6 no longer disappears immediately and Kiryu6 boats5/6 remain distinct without unsafe high fallback dependence. Verify Kiryu12 standard and varied do not regress.
6. If v15 still fails because full-cell anchor candidates are insufficient, do NOT relax NCC/corridor/geometry gates. Next principled direction is an explicit fixed-window Viterbi/DP candidate graph over the 1.5s segment using state-independent per-frame appearance peaks plus immutable motion likelihood, rather than committing/update-feedback every step.
7. Only if one unchanged seed+tracker combination passes all four physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` and perform at least one self-hosted end-to-end live-style validation.
8. Update this handoff after every meaningful result/design change with exact commits, Run IDs, artifact IDs/evidence and restart point.

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
