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
- v11 (`372aea94e0f718cc7dc2be3502c8761f33433ecf`): immutable slit-motion corridor on top of v9. Run `34788921925`; all four failed closed. It prevented unsafe continuation but was too myopic to recover a feasible per-frame assignment.
- v12 (`13a929a8a296ac92247ba6664f9e5bd35ec9cb4e`): four-step per-boat motion memory while remaining greedy per frame. Run `34804266678`; all four failed safely/fail-closed.
- v13 (`ed02d51599da88c3930370116d70b5d390d5ee0b`): first multi-hypothesis complete six-boat beam tracker. Run `34807739191`; all four unchanged jobs failed closed because every beam hypothesis died. No result was read and no quality threshold was relaxed.

## v13 artifact diagnosis — authoritative
Run `34807739191` artifacts were inspected, not just workflow conclusions.

All four failed with `all beam hypotheses died` while fallback use remained zero at the failure point, so this is not a missing-video/import/runtime failure and not merely weak fallback quality:
- Kiryu3: failed after 3 tracking steps, failure frame 930 from slit frame 927. Last boat6 center ~[551.6,978.2].
- Kiryu6: failed after 8 tracking steps, failure frame 901 from slit 893. Last boats5/6 ~[815.0,678.2] / [851.0,797.0].
- Kiryu12 standard: failed after 12 tracking steps, frame 915 from slit 903.
- Kiryu12 varied `1,2,4,5,6,3`: failed after 15 tracking steps, frame 912 from slit 897.

Technical interpretation: v13 can kill the physically correct path very early because each boat's appearance candidates are generated around one current x prediction. Once that prediction is locally wrong, the correct alternative may never enter the beam; increasing beam width alone cannot recover a candidate that was never generated. The next change therefore expands candidate coverage without lowering NCC/confidence gates.

## CURRENT candidate: tracker v14 diversified directional beam
File: `track_exhibition_boats_v14.py`
Implementation commit: `a2df021c038a09f4df324545426b4892800e9eda`
Workflow: `.github/workflows/regress-exhibition-seed17-track14.yml`
Workflow creation commit: `45560a70dc39a29d433a890f423f6c5ae1a27e4d`
Explicit trigger commit: `8e1d4bdaaffee32d2fb1b3666e7ac235089a4e09`
Current Run: `34809061470`
Workflow ID: `357548031`

### v14 design
v14 keeps v13's fail-closed hard geometry/direction gates and existing NCC/confidence/fallback thresholds. It does not make passing easier by lowering quality requirements.

Principled changes:
- for each boat, call the unchanged v9 appearance matcher around three bounded horizontal anchors: current v13 prediction, prediction -0.50*search_x, prediction +0.50*search_x;
- deduplicate nearby appearance candidates and retain several spatially distinct high-NCC alternatives;
- ask the original v13 feasibility code for a larger feasible transition pool, still under the same hard lane/order/jump/duplicate/edge/reverse-direction constraints;
- rerank that already-feasible pool with a soft result-blind preference for cumulative and step motion aligned with immutable slit `dominant_dx`;
- use `beam-width=8` / `per-state-keep=8` in this validation to preserve more hypotheses; confidence/NCC gates remain unchanged;
- no race result, boat-number exception or race-specific offset.

Rationale: v13's immediate beam deaths show that path diversity is useless if the correct local candidate is omitted. v14 targets candidate omission rather than weakening fail-closed safety.

### v14 validation matrix / exact restart point
Run `34809061470` is confirmed on GitHub Actions and is queued on the Japan self-hosted runner. Four unchanged jobs exist:
1. 2026-09-10 Kiryu3 standard — result remains blind.
2. 2026-09-10 Kiryu6 standard — result remains blind.
3. 2026-09-10 Kiryu12 standard — technical calibration.
4. 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3` — technical regression.

At this handoff update, all four v14 jobs are queued. Do not invent a result before completion.

## Exact next actions
1. Inspect Run `34809061470` once jobs leave queued state.
2. If technical code/runtime failure occurs, inspect logs, patch and rerun immediately.
3. If tracking runs complete, inspect artifacts/JSON rather than trusting workflow green alone.
4. Compare v14 beam survival depth against v13's 3/8/12/15-step deaths. If v14 survives longer but still dies, identify which boat/candidate/hard constraint removes the last plausible path.
5. Specifically audit Kiryu3 boat6 and Kiryu6 boats5/6 at +0.5/+1.0/+1.5s for slit-direction consistency, separation, edge survival and identity.
6. Record accepted/failure reason, beam-size history, fallback counts/fractions, median anchor/adaptive NCC, min separation, horizon centers and FastClip+seed+tracker latency.
7. Verify Kiryu12 standard and varied-entry samples are not regressed.
8. If v14 still fails safely, do NOT relax NCC/confidence/corridor gates. Next principled direction is a windowed candidate lattice / Viterbi pass over the short 1.5s segment with appearance+motion likelihood, so candidate alternatives survive across a fixed temporal window before committing.
9. Only if one unchanged seed+tracker combination passes all four physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` and perform a self-hosted end-to-end live-style validation.
10. Update this handoff after every meaningful v14 result/design change with exact commit SHA, Run ID, artifact IDs/evidence and restart point.

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
