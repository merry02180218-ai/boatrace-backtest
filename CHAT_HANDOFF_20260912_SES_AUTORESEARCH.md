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
Kiryu6 evidence continues to indicate that v17 can place rescued outer rows plausibly; the current blocker is tracker identity preservation, not more race-specific seed movement.

## Tracker history summary
- v8 (`264bf494812b6b72e4af94cacc1d40b009a6dde1`): per-frame joint six-boat assignment. Kiryu12 standard/varied passed, Kiryu3/Kiryu6 failed.
- v9 (`30a7b7ad2e44e51ccd2d0d2c0df0e32b5c265608`): immutable seed-frame appearance memory. Still allowed outer-row wake/background collapse.
- v10: fleet-affine y-cell reference. Rejected after all four matrix jobs failed closed and previously healthier samples regressed.
- v11 (`372aea94e0f718cc7dc2be3502c8761f33433ecf`): immutable slit-motion corridor on top of v9. Run `34788921925`; all four failed closed. It prevented unsafe continuation but was too myopic to recover a feasible per-frame assignment.
- v12 (`track_exhibition_boats_v12.py`, implementation commit `13a929a8a296ac92247ba6664f9e5bd35ec9cb4e`, workflow commit `c725772c4ec2cf68651a91258159a553b0a53c7c`): added four-step per-boat motion memory while remaining greedy per frame. Run `34804266678`; all four unchanged matrix jobs failed safely/fail-closed. Therefore v12 is rejected as the production candidate. No confidence/NCC/fallback threshold was relaxed and no blind result was read.

## v11/v12 technical conclusion
The failure family is temporal identity ambiguity, especially on outer rows: locally high-NCC wake/background candidates can be plausible for one frame but become physically wrong over a sequence. Hard per-frame filtering and greedy recent-motion penalties can fail earlier/safely but cannot recover an alternative historical path after a locally bad decision.

Therefore the next principled architecture is multi-hypothesis temporal assignment, not threshold tuning and not more seed offsets.

## CURRENT candidate: tracker v13 multi-hypothesis beam fleet tracker
File: `track_exhibition_boats_v13.py`
Implementation commit: `ed02d51599da88c3930370116d70b5d390d5ee0b`
Workflow: `.github/workflows/regress-exhibition-seed17-track13.yml`
Workflow creation commit: `1859df64edb47ac6fc239f0e7d9de7a1851fd9a2`
Regression trigger commit: `d1c35075b70262f64e70b089b8d75616b8d3c9ce`
Current Run: `34807739191`

### v13 design
v13 is the first tracker in this line that retains multiple complete six-boat identity hypotheses across frames rather than committing to one fleet assignment every frame.

It preserves the result-blind/fail-closed safety principles from v9/v11:
- seed v17 only; no race-specific/boat-specific offset;
- immutable seed-frame anchor appearance plus adaptive appearance;
- dynamic lane cells, entry-order preservation, lane spacing and frame-edge safety;
- unchanged `min_ncc=.48`, `strong_ncc=.80`, weak fallback cap `.35`, strong fallback cap `.50`;
- immutable slit-direction guard derived from result-blind v17 `dominant_dx`;
- stride2 operation;
- no race result/future-frame feature.

New temporal architecture:
- each beam state owns six centers, velocity, recent step history, fallback counters, appearance histories, adaptive templates and horizon samples;
- each frame generates adaptive+immutable-anchor NCC candidates plus safe prediction fallback for every boat;
- feasible six-boat combinations are scored jointly using appearance, LK/velocity prediction, recent per-boat motion continuity and robust fleet motion;
- hard-reject entry-order/lane-cell violations, near-duplicate boat centers, excessive jumps, frame-edge positions and large reverse movement against immutable slit direction;
- keep several diverse fleet paths (`beam-width=6`, up to six transitions per parent) instead of discarding all but the local winner;
- final selection still must pass the unchanged confidence/fallback gates. Beam search is recovery architecture, not gate relaxation.

### v13 validation matrix / exact restart point
Run `34807739191` is confirmed on GitHub Actions and currently queued on the Japan self-hosted runner with four unchanged jobs:
1. 2026-09-10 Kiryu3 standard — result remains blind.
2. 2026-09-10 Kiryu6 standard — result remains blind.
3. 2026-09-10 Kiryu12 standard — technical calibration.
4. 2026-09-09 Kiryu12 varied entry `1,2,4,5,6,3` — technical regression.

At this handoff update, all four jobs exist and are queued. Do not invent a result until they complete.

## Exact next actions
1. Inspect Run `34807739191` all four jobs after they leave queued state.
2. If there is a code/runtime failure, inspect job logs, patch v13/workflow and rerun immediately.
3. If technically completed, inspect artifacts/JSON rather than trusting workflow green alone.
4. Specifically audit Kiryu3 boat6 and Kiryu6 boats5/6 at +0.5/+1.0/+1.5s for direction, edge survival, separation and identity.
5. Record accepted/failure reason, beam-size history, fallback counts/fractions, median identity/anchor/adaptive NCC, min lane separation, horizon centers and FastClip+seed+tracker latency.
6. Verify Kiryu12 standard and varied-entry samples are not regressed.
7. If v13 still fails safely, do NOT relax gates. Diagnose whether candidate generation is too local or beam diversity/path scoring is insufficient; next principled step is a windowed/offline-within-the-1.5s-segment Viterbi/candidate lattice or better immutable appearance descriptor, still result-blind.
8. Only if one unchanged seed+tracker combination passes all four physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` and perform a self-hosted end-to-end live-style validation.
9. Update this handoff after the v13 result with exact Run/artifact IDs and restart point.

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
