# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Non-negotiable rules
Latest GitHub/artifacts win. 2026-09-10 Kiryu3/6/9 results remain unread. 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only. July/August NON-PRISTINE. Never relax fail-closed/NCC/geometry/motion gates merely to pass. No boat/race-specific offsets. Production target persistent Japan self-hosted PC; ideal <=30 sec, maximum <=60 sec. Exact Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Seed
Keep `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`. Current blocker is tracker identity/path representation, not race-specific seed movement.

## Retained progression
v8-v24 established independent/per-frame identity, immutable appearance alone, lane-cell geometry and fixed proposal reachability were insufficient. v25 causal trajectory reachability removed gross wrong-direction paths. v26 translation camera compensation improved feasibility but remained insufficient. v27 leave-one-out similarity run `34893353398` failed all four and was too slow. v28 run `34900743347` failed all four; Kiryu3 died step9/native18, tracker 54.566 sec. v29 run `34906246958` failed all four; shared robust similarity did not solve coordinate mismatch, Kiryu3 died step8/native16, 43.713 sec. Do not widen 24/20/42 motion caps. v30 had a monkey-patch integration defect and is not scientific evidence.

## v31 fixed-hook audit
Run `34939987130` failed unchanged four-video matrix. Kiryu3 failed at step1/native2 because inherited raw initial-speed gate rejected all 12 transitions before affine consensus; FastClip 7.14 sec, seed 0.93 sec, tracker 1.50 sec. This exposed initial/later coordinate-model inconsistency, not a reason to widen caps.

## v32 initial affine compensation — rejected
`track_exhibition_boats_v32.py`; workflow run `34947013447` on the unchanged matrix failed all four jobs. Kiryu3 job `104308721645` failed closed at step1/native2 after ~3.68 sec tracker time. Crucial diagnostics: `initial_affine_calls=12`, `initial_reject_consensus_fit=0`, `initial_reject_relative_residual=0`, `initial_reject_absolute_speed=12`, accepts=0. The 3-point affine fit produced effectively zero residual for all first-transition candidate sets, so it was too flexible to discriminate identity at this depth; the unchanged 42 px/native-frame absolute ceiling then correctly failed closed. Do not relax that ceiling and do not keep unconstrained initial affine fitting.

## CURRENT candidate: v33 robust initial shared-translation + later affine
File `track_exhibition_boats_v33.py`, implementation commit `38cb94be2ce4f375261fb2df6b3777afaff36d53`. Workflow bridge `.github/workflows/regress-exhibition-seed17-track27.yml` updated for v33 at commit `e6c22636c552114dbfb650f6b01a7f7c0f723bad`. This replaces only the first-transition camera model; later transitions remain v31.

Principle: over one initial stride, estimate fleet-wide camera motion conservatively as the coordinate-wise median of all six raw displacements. Judge each boat by its residual displacement after subtracting this shared translation. Retain unchanged 24 px/native-frame relative-residual cap, unchanged 42 px/native-frame raw absolute ceiling, reverse corridor, appearance/geometry gates and fail-closed behavior. This is deliberately less flexible than v32 affine and cannot exactly interpolate arbitrary three-boat wrong geometry. No future frame, result, boat-number special case, race-specific offset, or confidence relaxation.

Matrix remains unchanged:
1. 2026-09-10 Kiryu3 standard — result blind.
2. 2026-09-10 Kiryu6 standard — result blind.
3. 2026-09-10 Kiryu12 standard — exposed technical calibration.
4. 2026-09-09 Kiryu12 varied `1,2,4,5,6,3` — exposed technical regression.

## Exact restart point
1. Find/inspect the Actions run triggered by the v33 workflow/handoff commits and all four jobs/artifacts.
2. For Kiryu3 first verify whether robust shared translation permits any first transition while the 42 px raw ceiling remains intact; inspect `diagnostics_v33` reject counts.
3. If v33 passes the first step but exhausts later, record exact dead-frame depth and v31 relative-residual/acceleration/reverse rejects. Do not widen 24/20/42 caps.
4. For every accepted sample inspect +0.5/+1.0/+1.5 centers, identity/on-frame sanity, fallback/NCC, min lane separation, and FastClip+seed+tracker latency. Workflow green alone is insufficient.
5. If shared translation is too rigid, next principled direction is a constrained low-DOF camera model (translation + small similarity perturbation bounded independently of boat candidates) or external background-feature camera estimation; do not return to free 3-point affine interpolation.
6. Only after one unchanged seed+tracker passes all four sane and <=60 sec may `run_exhibition_ses_live_local.py` be updated, then perform >=1 Japan self-hosted end-to-end live-style validation.
7. Preserve Kiryu3/6/9 result blindness throughout.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update yet.

## Live-ready milestone
Multiple independent September samples incl varied entry; fully automatic acquisition+seed+tracker; sane identity/geometry with fail-closed retained; <=60 sec (ideal <=30); production wrapper updated; >=1 self-hosted end-to-end live-style success. Prefer 10+ samples before treating SES as stable/predictive. SES is an attack/head-support feature candidate, not direct finishing-order rank.
