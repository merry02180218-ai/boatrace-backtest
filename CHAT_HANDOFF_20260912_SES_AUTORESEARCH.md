# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 22:17+ JST
Repo: `merry02180218-ai/boatrace-backtest`

## Non-negotiable rules
Latest GitHub/artifacts win. 2026-09-10 Kiryu3/6/9 results remain UNREAD. 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only. July/August NON-PRISTINE. Never relax fail-closed/NCC/geometry/motion gates merely to pass. No boat/race-specific offsets. Production target persistent Japan self-hosted PC; ideal <=30 sec, maximum <=60 sec. Exact Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Seed
Keep `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`. Current blocker remains tracker identity/path/camera representation, not race-result-informed seed movement.

## Retained progression
v8-v24 established that independent/per-frame identity, immutable appearance alone, lane-cell geometry and fixed proposal reachability were insufficient. v25 causal trajectory reachability removed gross wrong-direction paths. v26-v34 explored causal camera compensation without widening hard gates. v33 proved robust initial translation fixes first-step degeneracy but later affine residuals dominated. v34 applied robust shared translation on every transition. v35 added dual causal proposal centers without widening the 24 px proposal radius.

## v35 — rejected
Implementation commit `2bde28ad3995a851d7830c15821342799d216d46`; workflow commit `80c5ba1b27ee0a9a40c52c77f454f58aa3394f27`; Run `34964674102`. All four unchanged technical matrix jobs failed closed. Artifact IDs: Kiryu3 `10395377288`, Kiryu6 `10394982641`, Kiryu12 `10395396223`, Kiryu12var `10395462279`.

Kiryu3 v35 artifact: `accepted=false`, reason `verified appearance-bank beam exhausted; no feasible temporal expansion`, dead at step9/native frame18, tracker runtime 54.924 sec. Last centers included boat6 `[520,1016]` from seed `[616,961]`. v35 proposal diagnostics: merge_calls=1600, dual_center_calls=1594, shared_only_admits=656, proposal_admits=2995. v34 transition diagnostics inside v35: calls=5532, relative-residual rejects=990, relative-acceleration=0, absolute-speed=0, reverse=0, accepts=4542. This isolated the single global shared-translation residual model as a major bottleneck; proposal diversity alone did not solve it.

## v36 perspective-band translation — rejected
File `track_exhibition_boats_v36.py`; implementation commit `f0bee83b8b967fb264446449c697f67d8a4d6ab4`; workflow commit `043008893b2f333defa915fefa4173ed0d9437ae`; Run `34969600581`. v36 kept exact 24 residual / 18 relative-acceleration / 42 absolute caps and all identity/geometry/reverse gates, estimating shared camera motion separately for upper/lower 3-row bands. All four unchanged matrix jobs again failed closed. Acquisition and seed v17 succeeded; tracker step failed in all four. Therefore the hard two-band perspective model is also insufficient and is rejected.

## CURRENT candidate: v37 robust continuous row-perspective camera field
File `track_exhibition_boats_v37.py`; implementation commit `35b6d4d4a3e9a6cbecf02f48aae769f46585fd64`; workflow commit `c94ccad681a954057df270a394f28891e720711e`.

Principle: preserve v35 proposal generation and every existing hard threshold, but replace discontinuous v36 bands with a low-DOF continuous camera displacement field versus image y. For dx and dy separately, use Theil-Sen median pairwise slope + median intercept over the six previous boat rows, then subtract that predicted camera displacement before applying the unchanged 24 px/native-frame residual gate. Relative residual acceleration remains capped at 18; absolute raw step remains capped at 42. No future frame, result, boat/race rule, offset, confidence relaxation, or threshold widening.

Workflow `.github/workflows/regress-exhibition-seed17-track27.yml` now runs the unchanged four-case matrix with v37. The push at workflow commit `c94ccad681a954057df270a394f28891e720711e` should launch the Japan self-hosted regression. Inspect the resulting Run ID/jobs/artifacts next; do not assume green from launch alone.

## Unchanged matrix
1. 2026-09-10 Kiryu3 standard — result blind.
2. 2026-09-10 Kiryu6 standard — result blind.
3. 2026-09-10 Kiryu12 standard — exposed technical calibration.
4. 2026-09-09 Kiryu12 varied `1,2,4,5,6,3` — exposed technical regression.

## Exact restart point
1. Locate the SES v37 run triggered by commit `c94ccad681a954057df270a394f28891e720711e`.
2. Inspect all four jobs/artifacts, recording dead-frame depth, `diagnostics_v37`, accepted/failure reason, FastClip/seed/tracker latency.
3. For any accepted sample inspect +0.5/+1.0/+1.5 centers, on-frame identity sanity, NCC/fallback and lane separation. CI green alone is insufficient.
4. If v37 still fails because candidate-derived camera estimates remain unstable, next direction should be candidate-independent background-feature camera motion or another bounded low-DOF camera model, not widening 24/18/42 caps.
5. Preserve Kiryu3/6/9 result blindness.
6. Only after one unchanged seed+tracker passes all four sane and <=60 sec update `run_exhibition_ses_live_local.py`, then perform >=1 Japan self-hosted end-to-end live-style validation.

## Production wrapper warning
`run_exhibition_ses_live_local.py` is NOT live-ready and must not be used for betting decisions until the unchanged matrix passes. Do not production-wire v37 merely because it launches or one sample passes.

## Live-ready milestone
Multiple independent September samples incl varied entry; fully automatic acquisition+seed+tracker; sane identity/geometry with fail-closed retained; <=60 sec (ideal <=30); production wrapper updated only to a validated tracker; >=1 self-hosted end-to-end live-style success. Prefer 10+ samples before treating SES as stable/predictive. SES is an attack/head-support feature candidate, not direct finishing-order rank.
