# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Non-negotiable rules
Latest GitHub/artifacts win. 2026-09-10 Kiryu3/6/9 results remain unread. 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only. July/August NON-PRISTINE. Never relax fail-closed/NCC/geometry/motion gates merely to pass. No boat/race-specific offsets. Production target persistent Japan self-hosted PC; ideal <=30 sec, maximum <=60 sec. Exact Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Seed
Keep `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`. Current blocker is tracker identity/path representation, not race-specific seed movement.

## Retained progression
v8-v24 established independent/per-frame identity, immutable appearance alone, lane-cell geometry and fixed proposal reachability were insufficient. v25 causal trajectory reachability removed gross wrong-direction paths. v26 translation camera compensation improved feasibility but remained insufficient. v27 leave-one-out similarity run `34893353398` failed all four and was too slow. v28 run `34900743347` failed all four; Kiryu3 died step9/native18, tracker 54.566 sec. v29 run `34906246958` failed all four; shared robust similarity did not solve coordinate mismatch, Kiryu3 died step8/native16, 43.713 sec. Do not widen 24/20/42 motion caps.

## v30 audit — implementation defect, do not interpret scientifically
`track_exhibition_boats_v30.py` intended a shared robust affine-camera transition, but the 2026-09-15 automation audit found it monkey-patched `v25.transition_ok`, while the actual retained v25 transition hook is `_transition_v25`. Therefore v30 had not been correctly integrated and must not be treated as a scientific affine-camera result. The earlier Actions-registration issue also delayed exposing this defect. No race results were read.

## CURRENT candidate: v31 fixed-hook shared robust affine camera
File `track_exhibition_boats_v31.py`; implementation commit `32fed5fa19bb044a114fb957db8dea698003d9f9`.

v31 preserves the intended v30 science but installs it at the actual v25 `_transition_v25` hook/signature. For each causal transition it enumerates C(6,3)=20 exact three-boat affine fits, chooses fleet consensus by fourth-smallest six-boat residual then trimmed mean of the best four, keeps the unchanged 24 px/native-frame residual cap, reconstructs previous-previous centers causally from `last_step` and retains the unchanged 20 px/native-frame residual-acceleration cap, 42 absolute cap, reverse corridor, NCC/appearance/fleet geometry and fail-closed behavior. No future frame/result/special case/threshold relaxation.

### Actions repair + live regression launch
The historical v27 workflow ID `358168090` is registered. The bridge workflow `.github/workflows/regress-exhibition-seed17-track27.yml` was updated at commit `5593a24a406b69d490f3a5e54a6a48ff16f6af34` to execute v31 on the unchanged four-video matrix. This push successfully triggered Actions run `34939987130`; it was queued on the Japan self-hosted runner at the handoff update. This confirms the prior workflow-registration blocker is repaired.

Matrix remains unchanged:
1. 2026-09-10 Kiryu3 standard — result blind.
2. 2026-09-10 Kiryu6 standard — result blind.
3. 2026-09-10 Kiryu12 standard — exposed technical calibration.
4. 2026-09-09 Kiryu12 varied `1,2,4,5,6,3` — exposed technical regression.

## Exact restart point
1. Inspect run `34939987130` all four jobs/artifacts as soon as complete; do not rely on workflow green alone.
2. Confirm tracker actually executed v31 and inspect `diagnostics_v31`: dead-frame depth if failed, affine residual/acceleration rejects, reverse rejects, +0.5/+1.0/+1.5 centers, physical identity/on-frame sanity, fallback/NCC, min lane separation, FastClip+seed+tracker latency.
3. Compare directly with v29/v28. A win must improve feasible path depth/physical sanity without widening gates.
4. If v31 fails scientifically, do not widen 24/20/42 caps. Next principled direction remains temporal camera-state continuity inside the beam (camera parameter velocity/acceleration), or independent background-feature camera motion.
5. Only after one unchanged seed+tracker passes all four sane and <=60 sec may `run_exhibition_ses_live_local.py` be updated, then perform >=1 Japan self-hosted end-to-end live-style validation.
6. Preserve Kiryu3/6/9 result blindness throughout.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update yet.

## Live-ready milestone
Multiple independent September samples incl varied entry; fully automatic acquisition+seed+tracker; sane identity/geometry with fail-closed retained; <=60 sec (ideal <=30); production wrapper updated; >=1 self-hosted end-to-end live-style success. Prefer 10+ samples before treating SES as stable/predictive. SES is an attack/head-support feature candidate, not direct finishing-order rank.
