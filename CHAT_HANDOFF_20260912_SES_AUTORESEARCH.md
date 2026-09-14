# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-14 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue BOATCAST start-exhibition video research until immediate post-exhibition live use is reliable: result-blind FastClip -> automatic six-boat seed -> automatic tracking -> SES -> model re-evaluation, with no manual/race-specific edits.

## Non-negotiable rules
- Latest GitHub code/artifacts override old prose/chat memory.
- Never inspect race results before locking exhibition-only judgement on blind samples.
- 2026-09-10 Kiryu3/6/9 results remain unread; preserve blindness.
- 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only.
- July/August 2026 are NON-PRISTINE.
- Never relax fail-closed/NCC/geometry/motion gates merely to obtain accepted=true.
- Never hard-code boat-number/race-specific offsets.
- accepted=true is necessary but not sufficient: trajectories must remain physically sane/on-frame and preserve identity.
- Final race-by-race operation should be persistent on Japan self-hosted PC; Actions are validation/logging.
- Exact Japan Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.
- Live latency target: ideal <=30 sec after video availability, maximum <=60 sec.

## Seed state
Current seed remains `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
Evidence still indicates the principal blocker is tracker identity/path preservation rather than seed placement.

## Retained tracker progression
- v8 joint per-frame assignment: Kiryu12 std/var passed, Kiryu3/6 failed.
- v9 immutable appearance memory: rejected.
- v10 fleet-affine y reference: rejected.
- v11-v18 progressively added result-blind motion/path constraints and multi-hypothesis temporal search; all failed safely without justifying threshold relaxation.
- v19 predecessor-conditioned beam, run `34835647158`: all four failed closed after healthy beams eventually reached a frame with zero feasible expansion. Diagnosis: immutable slit appearance becomes proposal-brittle after appearance phase shift.

## v20 completed audit — REJECTED, but diagnostic progress
File `track_exhibition_boats_v20.py`.
Authoritative unchanged four-video run: **`34843565746`**.

All four jobs reached tracker v20 and failed closed. FastClip and seed v17 succeeded in all jobs, so this is not an environment/import/downloader/seed failure. The tracker exhausted safe predecessor expansions. No results were read and no threshold was relaxed.

v20 used a causal adaptive template only as a rescue proposal source, while every proposed center still had to pass immutable-anchor NCC plus all v19 motion/fleet/geometry guards. The failure therefore supports the planned next direction: do not loosen `.48`; instead retain multiple historical appearances only after they were strongly verified against the immutable anchor and require consensus/chain-of-trust when using them later.

## CURRENT candidate: tracker v21 verified appearance bank
File: `track_exhibition_boats_v21.py`
Implementation commit: **`555796903f400528f94173dba42e41a02685431a`**
Workflow: `.github/workflows/regress-exhibition-seed17-track21.yml`
Workflow creation commit: **`ee3c50df717013a9b493a30a1d691683d223adbf`**
Explicit regression trigger commit: **`52a78f304237ab1f8183e29d1c284206ae783624`**
Authoritative v21 run: **`34856451633`** — queued on Japan self-hosted runner at this handoff update.

### v21 design
v21 keeps v20/v19 standard immutable predecessor-conditioned tracking first. It changes rescue appearance only:
- each path keeps a small per-boat trusted appearance bank;
- the bank begins with the immutable slit anchor;
- a new look can enter the bank only after the selected state has already survived the unchanged temporal/fleet safety gates, the proposal source is immutable, immutable NCC is at least the existing strong threshold `.80`, and temporal spacing is satisfied;
- the immutable anchor is never removed;
- rescue is attempted only when standard expansion has no feasible successor;
- rescue searches each trusted look inside the same physically reachable predecessor ROI;
- the exact rescue patch must still pass immutable-anchor NCC >= existing `.48`;
- after the bank grows beyond one look, a rescue candidate must be supported by at least two trusted looks and median bank NCC >= `.48`;
- bank cap is 5 looks per boat; no future frame feedback is used;
- existing slit-direction reverse corridor, lane/order, duplicate-patch, frame-edge, jump, fleet geometry and final confidence gates remain unchanged;
- no result, boat-number rule, race-specific offset or relaxed quality threshold is used.

Workflow parameters remain strict/comparable: `--stride 2 --topk 6 --per-boat-keep 5 --per-path-keep 12 --beam-width 24 --bank-cap 5`.

## v21 exact restart point
1. Inspect run **`34856451633`** all four jobs when they leave queue; workflow color alone is insufficient.
2. If any job has a coding/runtime error, inspect logs, fix and rerun immediately.
3. For each race inspect `exhibition_tracking_v21.json` and record accepted/failure reason, rescue attempts/successes, bank proposal/admission counts and final bank sizes, median immutable identity NCC, min lane separation, +0.5/+1.0/+1.5 centers, physical sanity, tracker runtime, and total FastClip+seed+tracker latency.
4. Specifically require Kiryu3 boat6 not to run reverse-left/off-frame and Kiryu6 boats5/6 to remain distinct/sane through +1.5s; require both Kiryu12 technical samples not to regress.
5. If v21 merely fails earlier but safely, do NOT loosen NCC or corridor gates. Diagnose whether bank proposal availability or consensus is the bottleneck, then move to a stronger multi-frame beam/Viterbi trajectory likelihood using immutable appearance + trusted appearance history + motion likelihood.
6. Only if one unchanged seed+tracker combination passes all four physically sane with total latency <=60 sec may `run_exhibition_ses_live_local.py` be updated.
7. After a four-sample technical pass, perform at least one Japan self-hosted end-to-end live-style validation before calling live-ready.
8. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID and artifact/log evidence.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update until an unchanged seed+tracker passes the full technical matrix with sane identity/geometry and <=60 sec.

## Live-ready milestone
Before user notification as complete:
- multiple independent September samples including varied entry;
- automatic acquisition + seed + tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30 sec, maximum <=60 sec;
- `run_exhibition_ses_live_local.py` updated to the validated pipeline;
- >=1 self-hosted end-to-end live-style success.
Prefer 10+ samples before treating SES as stable/predictive. SES remains an attack/head-support feature candidate, not direct finishing-order rank.
