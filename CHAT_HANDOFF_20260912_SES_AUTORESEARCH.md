# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-14 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue BOATCAST start-exhibition video development until immediate post-exhibition live use is reliable: result-blind FastClip -> automatic six-boat seed -> automatic tracking -> SES -> later model re-evaluation, with no manual seed editing.

## Non-negotiable rules
- Latest GitHub code/results override this handoff and old chat memory.
- Never inspect race results before locking exhibition-only judgement on blind/pristine samples.
- 2026-09-10 Kiryu3/6/9 results remain unread; preserve blindness.
- 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only.
- July/August 2026 are NON-PRISTINE/research-only.
- Never weaken fail-closed gates merely to obtain accepted=true.
- Never hard-code boat-number/race-specific offsets.
- accepted=true is necessary but not sufficient: trajectories must remain physically sane/on-frame and preserve identity.
- Final race-by-race operation should be persistent on Japan self-hosted PC; Actions are validation/logging.
- Exact Japan Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.
- Live latency target: ideal <=30 sec after video availability, maximum <=60 sec.

## Seed state
Current seed remains `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
Evidence continues to indicate the principal blocker is tracker identity/path preservation, not race-specific seed movement.

## Retained tracker progression
- v8 joint per-frame assignment: Kiryu12 std/var passed, Kiryu3/6 failed.
- v9 immutable appearance memory: rejected.
- v10 fleet-affine y reference: rejected.
- v11 slit-motion corridor: safe but insufficient.
- v12 short motion memory: failed safely.
- v13-v18 explored multi-hypothesis/fixed-state/DP variants; all exhausted safe temporal paths without justifying gate relaxation.
- v18 authoritative run `34826924155`: all four failed closed despite 96 safe current-frame states; conclusion was that global current-frame pruning loses coherent reachable paths.

## v19 completed audit — authoritative
File `track_exhibition_boats_v19.py`, implementation commit `a305634c8a136e40165303f3df9c88cc4af591bd`.
Workflow `.github/workflows/regress-exhibition-seed17-track19.yml`.
Run **`34835647158`**.

All four unchanged technical videos reached tracker v19 and failed closed; FastClip and seed v17 succeeded. This is algorithmic/path-proposal failure, not an import/environment failure. No results were read and no confidence/safety gate was relaxed.

Artifacts:
- Kiryu3: **`10344470949`**
- Kiryu6: **`10344846076`**
- Kiryu12 standard: **`10344131902`**
- Kiryu12 varied: **`10344206101`**

Key diagnosis from logs/artifacts:
- v19 successfully retained a healthy predecessor-conditioned beam (often the full 24 paths) immediately before failure.
- At a later single frame, every surviving predecessor produced zero feasible expansion.
- Therefore simply enlarging beam width or loosening NCC/motion/geometry gates is not the principled fix.
- The bottleneck is current-frame proposal availability under immutable slit appearance after appearance phase shift; outer-row identity remains the critical case (Kiryu3 boat6; Kiryu6 boats5/6).
- The next method should add a causal appearance proposal source while retaining immutable-anchor verification and every existing physical/fail-closed guard.

## CURRENT candidate: tracker v20 gated causal-appearance rescue
File `track_exhibition_boats_v20.py`.
Implementation commit **`d6ca4c4078a9765f0f6a07ea3891e59c9142a9dd`** (file creation commit immediately preceding workflow creation; verify exact file-history SHA if needed before quoting externally).
Workflow `.github/workflows/regress-exhibition-seed17-track20.yml`.
Workflow creation commit **`9b814a0d325dc75e20e7034e7e596e0c983cbdeb`**.
Regression trigger commit **`08f039abf636786b2aa9f82770ad963466d74e8c`**.
Run **`34843565746`** is the authoritative v20 four-video matrix; all four jobs were queued on the Japan self-hosted runner at this handoff update.

### v20 design
v20 keeps the v19 standard path unchanged and adds a rescue-only proposal source; it does not lower any identity/safety threshold.
- First try the normal v19 immutable-anchor predecessor-conditioned expansion.
- Only when a predecessor has zero standard expansion, search a causal per-path appearance template inside that predecessor's physically reachable ROI.
- A causal appearance template is updated only after a selected state has strong agreement with the original immutable slit anchor (`NCC >= .80`).
- Every rescue proposal is re-checked at the exact proposed center against the original immutable slit anchor and must still satisfy the unchanged `min_ncc=.48` identity gate.
- Adaptive appearance therefore proposes location only; it cannot bypass the immutable identity requirement.
- Fleet safety, temporal motion, slit-direction reverse corridor, fixed lane/order, frame-edge, duplicate-patch, step-size and final confidence gates remain unchanged.
- No future-frame feedback, race result, boat-number rule or race-specific offset is used.
- New diagnostics include `rescue_attempts`, `rescue_predecessors_with_expansion`, and `adaptive_proposals` so failure mode can be separated cleanly.

Workflow parameters remain strict and comparable: `--stride 2 --topk 6 --per-boat-keep 5 --per-path-keep 12 --beam-width 24`.

## v20 exact restart point
1. Inspect Run **`34843565746`** all four jobs when they leave queue; do not infer success from workflow color alone.
2. If there is a runtime/coding error, inspect job logs, fix and rerun immediately.
3. Download and inspect each `seed17-track20-*` artifact JSON.
4. Record per race: accepted/failure reason, `rescue_attempts`, `rescue_predecessors_with_expansion`, `adaptive_proposals`, median immutable identity NCC, min lane separation, +0.5/+1.0/+1.5 centers, physical sanity, tracker runtime, and FastClip+seed+tracker latency.
5. Specifically require Kiryu3 boat6 not to run reverse-left/off-frame and Kiryu6 boats5/6 to remain distinct/sane through +1.5s; also require Kiryu12 standard/varied not to regress.
6. Interpret failure diagnostically without weakening `.48` or any safety gate:
   - `adaptive_proposals == 0` => causal appearance itself cannot find reachable proposals;
   - proposals exist but immutable recheck rejects them => original slit anchor is appearance-brittle after phase shift;
   - proposals pass identity but expansion still dies => temporal/fleet geometry transition is the bottleneck.
7. If immutable recheck is the bottleneck, next principled direction is a **verified appearance bank**: retain multiple historical templates only from states previously verified strongly by immutable anchor, search the bank inside predecessor ROI, and require chain-of-trust/consensus rather than a free adaptive template.
8. Do NOT update production wrapper unless one unchanged seed+tracker passes all four with physically sane identity and total latency <=60 sec.
9. After a technical four-sample pass, update `run_exhibition_ses_live_local.py` and perform at least one Japan self-hosted end-to-end live-style validation.
10. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID, artifact IDs/evidence and restart point.

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
