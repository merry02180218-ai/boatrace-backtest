# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 JST
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
- v20 causal rescue proposal, authoritative run `34843565746`: all four failed closed; adaptive appearance as proposal-only did not solve late beam exhaustion.

## v21 verified appearance bank — REJECTED, diagnostic progress
File `track_exhibition_boats_v21.py`.
Implementation commit `555796903f400528f94173dba42e41a02685431a`.
Workflow `.github/workflows/regress-exhibition-seed17-track21.yml`.
Authoritative run **`34856451633`**.

All four unchanged matrix jobs reached tracker v21 and failed closed; FastClip and seed v17 succeeded. This is tracker logic, not environment/downloader/seed failure. No outcome was read and no gate was relaxed.

Artifact IDs:
- Kiryu3 `10353063788`
- Kiryu6 `10353487395`
- Kiryu12 standard `10353830465`
- Kiryu12 varied `10353193682`

Fresh artifact audit:
- Kiryu3: `FAIL_CLOSED: verified appearance-bank beam exhausted; no feasible temporal expansion`; tracker runtime 53.055s. Beam survived through native frame 18. At final dead step all 24 predecessors attempted rescue, 219 bank proposals were generated, but zero predecessors produced a feasible expansion. Last best centers were approximately `[[997,409],[951,492],[964,589],[900,699],[975,819],[520,1016]]`. At +0.5s boat6 was already around `[561,1010]`, so the old outer-row pathology remains physically concerning even though failure is safe. Bank sizes on best path were 2/2/2/2/1/2.
- Kiryu6: same fail-closed reason; tracker runtime 50.531s. Beam survived through native frame 20. At the final dead step all 24 predecessors attempted rescue and generated 284 bank proposals, but zero predecessors expanded. Last best centers approximately `[[930,448],[873,503],[1006,606],[952,742],[897,834],[921,843]]`; boats5/6 y separation had collapsed to about 9px, so fleet geometry is again at the edge of identity failure. Bank sizes 2/3/4/2/3/2.

Key conclusion: v21 is not failing because trusted-bank proposal count is zero. Hundreds of rescue proposals exist at the dead frames. The immediate unknown is whether those proposals are rejected primarily by the current-frame fleet-state safety function or by predecessor transition/motion consistency. Threshold loosening would be unjustified.

## CURRENT candidate: v22 rejection-attribution diagnostic
File `track_exhibition_boats_v22.py`.
Implementation commit **`94444b58858208bc9341840f3708bf3dcf33637e`**.
Workflow `.github/workflows/regress-exhibition-seed17-track22.yml`.
Workflow commit **`a413cec2a413aedace8acfb800121612e4944a1c`**.
Authoritative run **`34865180548`** launched on Japan self-hosted runner; four matrix jobs were queued at this handoff update.

v22 deliberately makes **no tracking-behaviour change**. It wraps the existing v21/v20 path with counters for:
- `_safe_state` calls / rejects / accepts;
- `_transition` calls / rejects / accepts.
It annotates the normal tracker JSON as `v22-diagnostic` while preserving v21 gates exactly. Purpose: attribute late verified-bank beam exhaustion before choosing the next algorithmic change. `quality_thresholds_relaxed=false` and `behavior_changed_from_v21=false` are recorded.

## v22 exact restart point
1. Inspect run `34865180548` all four jobs after completion and download all artifacts.
2. Read `exhibition_tracking_v22.json` for each race. Record the v22 rejection counters plus v21 diagnostics, runtime, centers and bank/proposal counts.
3. Because counters are cumulative, compare the final/dead-step behavior with prior v21 diagnostics. If needed, add per-step rejection attribution next; do not infer more than counters support.
4. If fleet-state safety rejection dominates, instrument/split `_safe_state` into order/gap/edge/duplicate/reverse-corridor rejection categories before changing any gate. If transition rejection dominates, inspect/split `v17._transition` rejection causes and move toward stronger multi-frame trajectory likelihood / Viterbi-style path scoring while keeping hard safety bounds unchanged.
5. Do NOT increase acceptance by lowering `.48`, reverse corridor, geometry, edge or duplicate gates.
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
