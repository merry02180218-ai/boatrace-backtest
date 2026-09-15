# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Non-negotiable rules
Latest GitHub/artifacts win. 2026-09-10 Kiryu3/6/9 results remain unread. 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only. July/August NON-PRISTINE. Never relax fail-closed/NCC/geometry/motion gates merely to pass. No boat/race-specific offsets. Production target persistent Japan self-hosted PC; ideal <=30 sec, maximum <=60 sec. Exact Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Seed
Keep `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`. Current blocker is tracker identity/path representation, not race-specific seed movement.

## Retained progression
v8-v24 established independent/per-frame identity, immutable appearance alone, lane-cell geometry and fixed proposal reachability were insufficient. v25 causal trajectory reachability removed gross wrong-direction paths. v26 translation camera compensation improved feasibility but remained insufficient. v27 leave-one-out similarity run `34893353398` failed all four and was too slow. v28 run `34900743347` failed all four; Kiryu3 died step9/native18, tracker 54.566 sec. v29 run `34906246958` failed all four; shared robust similarity did not solve coordinate mismatch, Kiryu3 died step8/native16, 43.713 sec. Do not widen 24/20/42 motion caps. v30 had a monkey-patch integration defect and is not scientific evidence.

## v31 fixed-hook audit — rejected as complete candidate
`track_exhibition_boats_v31.py`; latest file commit lineage includes `67b96545afa4803b61b16cb797802a1922cbb303` parent state. Run `34939987130` completed FAILURE on the unchanged four-video matrix. Artifacts were produced for all four: Kiryu3 `10384773540`, Kiryu6 `10385665009`, Kiryu12 `10385320205`, Kiryu12 varied `10384044633`.

Critical evidence available from the Kiryu3 job log: tracker v31 failed closed with `beam exhausted at step 1 native_frame=2`; diagnostics showed `transition_calls=12`, `transition_reject_initial_speed=12`, `transition_accepts=0`, while affine consensus was never called. Thus v31's robust affine camera model was not even allowed to judge the first transition: the inherited raw 24 px/native-frame initial-speed gate rejected every path before camera compensation. FastClip 7.14 sec, seed v17 0.93 sec, tracker 1.50 sec on this failure, so latency is not the current blocker. No race result was read.

This exposes a coordinate-model inconsistency rather than evidence for widening motion thresholds: later transitions are judged after affine camera removal, but the first transition was judged only in raw screen coordinates.

## CURRENT candidate: v32 affine-compensated initial transition
File `track_exhibition_boats_v32.py`, implementation commit `67b96545afa4803b61b16cb797802a1922cbb303`. Workflow bridge `.github/workflows/regress-exhibition-seed17-track27.yml` updated at commit `b828c8e838bc1cd3f0bdd18c605dfcd311ea92d6`; that push launches the unchanged four-video Japan self-hosted matrix.

v32 changes only the first causal transition: it uses the same v31 C(6,3) robust affine fleet consensus immediately, applies the unchanged 24 px/native-frame fleet-relative residual cap, retains a hard 42 px/native-frame absolute raw-screen ceiling, and retains immutable reverse-direction, appearance/NCC, fleet geometry and fail-closed behavior. Later transitions delegate unchanged to v31 including the 20 px residual-acceleration gate. No future frame, result, boat/race special case, or race-specific offset is used. This is a coordinate-model consistency correction, not a threshold relaxation.

Matrix remains unchanged:
1. 2026-09-10 Kiryu3 standard — result blind.
2. 2026-09-10 Kiryu6 standard — result blind.
3. 2026-09-10 Kiryu12 standard — exposed technical calibration.
4. 2026-09-09 Kiryu12 varied `1,2,4,5,6,3` — exposed technical regression.

## Exact restart point
1. Find the Actions run triggered by commit `b828c8e838bc1cd3f0bdd18c605dfcd311ea92d6` and inspect all four jobs/artifacts.
2. First verify Kiryu3 gets past step1/native2 and that `diagnostics_v32.initial_affine_calls>0`; inspect initial residual/absolute/reverse rejects rather than workflow status alone.
3. For every sample record dead-frame depth or accepted state, +0.5/+1.0/+1.5 centers, physical identity/on-frame sanity, fallback/NCC, min lane separation, and FastClip+seed+tracker latency.
4. If v32 still exhausts later, do not widen 24/20/42 caps. Diagnose temporal camera-state continuity inside the beam (camera parameter velocity/acceleration) or independent background-feature camera motion.
5. Only after one unchanged seed+tracker passes all four sane and <=60 sec may `run_exhibition_ses_live_local.py` be updated, then perform >=1 Japan self-hosted end-to-end live-style validation.
6. Preserve Kiryu3/6/9 result blindness throughout.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update yet.

## Live-ready milestone
Multiple independent September samples incl varied entry; fully automatic acquisition+seed+tracker; sane identity/geometry with fail-closed retained; <=60 sec (ideal <=30); production wrapper updated; >=1 self-hosted end-to-end live-style success. Prefer 10+ samples before treating SES as stable/predictive. SES is an attack/head-support feature candidate, not direct finishing-order rank.
