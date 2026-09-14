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
- v11 (`372aea94e0f718cc7dc2be3502c8761f33433ecf`): immutable slit-motion hard corridor. Safe but all four failed closed.
- v12 (`13a929a8a296ac92247ba6664f9e5bd35ec9cb4e`): short motion memory while still greedy per frame. Failed safely.
- v13 (`ed02d51599da88c3930370116d70b5d390d5ee0b`): first multi-hypothesis six-boat beam tracker. All four unchanged jobs failed because every beam hypothesis eventually died.
- v14 (`a2df021c038a09f4df324545426b4892800e9eda`): candidate diversification around prediction. One weak Kiryu6 acceptance but three unchanged samples failed; not stable.
- v15 (`1d18621d725343437aed81554713a1db8017eb68`): full-cell immutable-anchor lattice plus v13 temporal beam. Completed audit below; rejected.

## v15 completed audit — authoritative
Workflow `.github/workflows/regress-exhibition-seed17-track15.yml`.
Run `34816553593`, head SHA `fbd8aac8ae321402f0206f4293ad061584280092`.
Artifacts:
- Kiryu3 `10336676457`
- Kiryu6 `10337460372`
- Kiryu12 standard `10336671980`
- Kiryu12 varied `10337191325`

Important correction: job-level workflow success is NOT tracker acceptance. Direct artifact JSON shows **all four v15 samples are `accepted=false` / fail-closed**.

### Kiryu3
- Failure: `FAIL_CLOSED: beam exhausted; no feasible multi-frame fleet hypothesis`.
- Died after step 2 / native frame 4.
- Beam sizes `[2,2]`.
- Slit dominant dx: 1 -17.217, 2 -6.933, 3 +5.369, 4 +13.916, 5 +12.186, 6 +13.269.
- Seed boat6 `[616,961]`; best surviving boat6 center already `[555,948]` after only four native frames, i.e. moving left against its immutable positive slit direction before the hard corridor fully rejects it.
- Fallback at failure: only boat5 had 1 fallback; this is not primarily a fallback-cap problem.

### Kiryu6
- Failure: same beam-exhausted fail closed.
- Died after step 12 / native frame 24 (~0.8s at 30fps).
- Beam sizes `[1,1,1,1,1,1,1,2,4,6,8,4]`.
- +0.5s centers remained physically plausible/distinct: 1 `[949.8,449.9]`, 2 `[884.9,502.1]`, 3 `[1001.8,606.8]`, 4 `[927.0,739.9]`, 5 `[857.3,825.1]`, 6 `[979.1,868.1]`.
- +0.5 immutable anchor NCC: 1 .784, 2 .743, 3 .827, 4 .708, 5 .728, 6 fallback.
- Failure therefore occurs after a plausible early path, consistent with temporal ranking/path-survival weakness rather than seed failure.

### Kiryu12 standard
- Failure: beam exhausted after step 22 / native frame 44 (~1.47s).
- Beam stayed mostly full at width 8 but all paths died just before 1.5s.
- +0.5 centers and NCC were usable, but by +1.0 boats2/3 were already fallback on the best path; accumulated fallbacks at failure: boat1=4, boat2=14, boat3=10, boats4-6=0.
- This is not a full technical pass.

### Kiryu12 varied `1,2,4,5,6,3`
- Failure after step 8 / native frame 16 (~0.53s).
- No fallback had been used on the best path at failure.
- +0.5 identity NCC `[.909,.939,.735,.914,.858,.785]`; anchor NCC `[.827,.878,.601,.859,.685,.634]`.
- Candidate appearance alone is therefore not sufficient to preserve a globally feasible trajectory.

### v15 interpretation
Full-cell anchor peaks solved some local candidate omission, but pure appearance-heavy transition ranking can still spend the beam on a high-NCC path that is already moving against immutable slit motion. Kiryu3 boat6 is the clearest example. Increasing beam width or weakening gates is not the principled next step.

## CURRENT candidate: tracker v16 motion-aware anchor-lattice beam
File `track_exhibition_boats_v16.py`.
Implementation commit `29a83e3c88c8a8bdfa2e359452b48d873715b1f7`.
Workflow `.github/workflows/regress-exhibition-seed17-track16.yml`.
Workflow creation commit `706db93595f8838c9b69b3978774e4b03a07cb04`.
Run **`34819659194`** (workflow ID `357628861`) was launched on the Japan self-hosted runner and was queued at this handoff update.

### v16 design
v16 deliberately keeps v15 full-cell immutable-anchor candidate generation and all v13 hard safety/quality gates unchanged. No NCC/fallback threshold is relaxed.

The only algorithmic change is temporal transition ranking:
- ask the unchanged v13 feasibility function for a wider bounded feasible transition pool (max 32 / 4x `per-state-keep`), without bypassing any gate;
- softly reward per-step motion aligned with immutable result-blind v17 slit direction;
- penalize reverse per-step motion before it reaches the existing hard reverse corridor;
- add a soft cumulative reverse-progress penalty;
- add immutable seed-anchor NCC support and a penalty for weak anchor evidence, while retaining the existing min-NCC gate;
- then keep the requested top transition count and proceed through the unchanged v13 beam.

This is designed specifically to stop a wrong high-NCC wake/background path from taking all early beam capacity, while still failing closed if no physically/appearance-consistent path exists.

No result, boat-number rule, race-specific offset, future frame, or quality-threshold relaxation is used.

Validation matrix unchanged:
1. 2026-09-10 Kiryu3 standard — result remains blind.
2. 2026-09-10 Kiryu6 standard — result remains blind.
3. 2026-09-10 Kiryu12 standard — exposed technical calibration.
4. 2026-09-09 Kiryu12 varied `1,2,4,5,6,3` — exposed technical regression.

Workflow args remain `--stride 2 --beam-width 8 --per-state-keep 8`.

## Exact restart point
1. Inspect Run `34819659194` jobs as soon as they leave queued/running state.
2. If there is a Python/import/runtime error, fix v16/workflow and rerun immediately.
3. If tracker executes, inspect all four artifacts/JSON; workflow green alone is insufficient.
4. For each race record: `accepted`, failure reason/step, beam sizes, fallback counts/fractions, median identity/anchor NCC, min separation, +0.5/+1.0/+1.5 centers, on-frame/identity sanity, and FastClip+seed+tracker latency.
5. Specifically require Kiryu3 boat6 to avoid early reverse-left drift against positive slit motion and require Kiryu6 boats5/6 to remain distinct through +1.5s.
6. Verify Kiryu12 standard/varied are not regressed.
7. If v16 still fails, do NOT relax corridor/NCC/geometry gates. Next principled direction is a genuinely fixed-window state-independent per-frame candidate graph / Viterbi-DP over the 1.5s segment, using immutable appearance peaks + slit-motion likelihood and applying fleet feasibility at the path level rather than prediction-feedback cells every frame.
8. Only if one unchanged seed+tracker combination passes all four physically sane and <=60 sec, update `run_exhibition_ses_live_local.py` and perform at least one self-hosted end-to-end live-style validation.
9. Update this handoff after every meaningful result/design change with exact commits, Run IDs, artifact IDs/evidence and restart point.

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
