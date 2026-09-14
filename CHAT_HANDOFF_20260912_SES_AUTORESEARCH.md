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

## Tracker progression retained
- v8 joint per-frame assignment: Kiryu12 std/var passed, Kiryu3/6 failed.
- v9 immutable appearance memory: rejected.
- v10 fleet-affine y reference: rejected.
- v11 slit-motion corridor: safe but insufficient.
- v12 short motion memory: failed safely.
- v13 first multi-hypothesis fleet beam: beams eventually died.
- v14 prediction-local diversification: unstable; one weak Kiryu6 acceptance only.
- v15 immutable-anchor lattice + beam: all four accepted=false.
- v16 motion-aware reranking: all four failed; candidate generation still depended on prior hypothesis.
- v17 fixed state-independent candidate graph + temporal fleet DP: completed and rejected below.

## v17 completed audit — authoritative
File `track_exhibition_boats_v17.py`.
Regression workflow `.github/workflows/regress-exhibition-seed17-track17.yml`.
Run **`34823290910`**.
Artifacts:
- Kiryu12 varied: `10338468885`
- Kiryu6: `10338559298`
- Kiryu3: `10339073552`
- Kiryu12 standard: `10339452028`

All four tracker jobs failed closed. FastClip and seed v17 succeeded, so this is an algorithmic tracking/search issue, not an environment/import problem.

Key diagnosis from artifact/log inspection:
- Each frame could still produce the configured **96 feasible six-boat fleet states** before the temporal beam later became infeasible/exhausted.
- Therefore the dominant failure is no longer simply “no safe candidate exists”.
- v17 prunes to the top 96 states by state-local appearance score before temporal DP. Many near-identical high-NCC wake/background hypotheses can consume the whole state budget, discarding a lower-local-score but temporally coherent identity path.
- Beam/path deduplication also used a fleet-average displacement metric, which can collapse a materially different hypothesis for one outer boat because the other five boats agree.
- This explains why merely increasing beam width or weakening NCC/reverse/geometry gates is not principled and remains prohibited.

## CURRENT candidate: tracker v18 hypothesis-diverse fleet DP
File `track_exhibition_boats_v18.py`.
Implementation commit **`06595fa7358635bb8a3ff61bc3d96e2cc7beaeae`**.
Regression workflow `.github/workflows/regress-exhibition-seed17-track18.yml`.
Workflow commit **`ceff05bd59a0d391c0933fee61028f9dbea6d1d5`**.
Explicit regression-trigger commit **`5849d9d3a96feaa0e816b280a8e4675a26e3e566`**.
Run **`34826924155`** launched on the Japan self-hosted runner; all four jobs were queued at this handoff update.

### v18 design
v18 changes SEARCH DIVERSITY only and deliberately keeps v17 visual/safety/final gates unchanged.
- Same result-blind immutable-anchor candidate lattice and fixed current-frame graph as v17.
- Same entry-order, lane separation, image-edge, duplicate-patch, slit-motion reverse, max-step, NCC and final confidence gates.
- No race result, future-result/frame feedback, boat-number rule or race-specific offset.
- For pre-DP frame-state retention, states are first diversified by a six-boat signature of each boat's x-progress relative to the immutable slit seed, using coarse 32px buckets. The best state per bucket is kept before remaining slots are filled by local appearance score.
- Beam deduplication now uses the **maximum per-boat center displacement** rather than the six-boat mean, so a distinct identity hypothesis for one boat is not erased merely because the other five boats match.
- Workflow args remain `--stride 2 --topk 6 --frame-state-keep 96 --beam-width 24`.
- No quality threshold was relaxed.

## Exact restart point
1. Inspect Run `34826924155` as soon as jobs leave queued/running state.
2. If any job has a coding/runtime error, diagnose/fix/rerun immediately.
3. If tracker executes, inspect all four artifact JSONs rather than trusting workflow green/red alone.
4. Record accepted/failure reason, temporal failure step, per-frame state/beam sizes, fallback fractions if any, median identity/anchor NCC, min lane separation, +0.5/+1.0/+1.5 centers, physical trajectory sanity, FastClip time, seed time, tracker time and total latency.
5. Specifically require Kiryu3 boat6 not to run reverse-left/off-frame and Kiryu6 boats5/6 to remain distinct/sane through +1.5s.
6. Confirm Kiryu12 standard and varied-entry samples are not regressed.
7. Do NOT relax min-NCC, reverse corridor, geometry/order, edge or confidence gates merely to pass.
8. If v18 still exhausts while 96 safe states exist per frame, next principled direction is **transition-aware state generation conditioned on beam predecessors**: each predecessor proposes safe current-frame candidates around both the predecessor and immutable anchor, builds K-best joint expansions, combines/deduplicates them, and beam-selects. Use only current/past frame information; no future frame/result leakage.
9. Only after one unchanged seed+tracker passes all four physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` and perform a Japan self-hosted end-to-end live-style validation.
10. Update this handoff after every meaningful result/design change with exact commits, Run IDs, artifact IDs/evidence and restart point.

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
