# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-16 17:07+ JST
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

## v36/v37 — rejected
v36 perspective-band translation and v37 robust continuous linear row-perspective camera field both preserved the hard 24/18/42 motion caps and identity/geometry/reverse gates but still exhausted the unchanged four-case beam. They are not production candidates.

## CURRENT candidate: v38 robust quadratic row-perspective camera field
File `track_exhibition_boats_v38.py`; implementation commit `8216983b20c371f8e0982232dd6c7d1521f1d06b`. v38 keeps v35 proposal generation and all immutable thresholds, fitting a robust degree-2 displacement field versus image y from same-frame six-boat motion only. No future frame, result, boat/race special case, offset, or threshold relaxation.

### 2026-09-16 runner-stall audit
Workflow commit `88013d07c0af16a35159b5bf169c0954f30ee682` launched Run `35057861647` at 14:01 JST. At 17:07 JST the run was still `queued` with all four matrix jobs queued (`104671693217` Kiryu3, `104671693248` Kiryu6, `104671693212` Kiryu12, `104671693079` Kiryu12var). A direct job rerun was refused because GitHub considers the workflow run already running. This is infrastructure/self-hosted-runner contention/stall, not a v38 technical result; do not classify v38 pass/fail from this queued run.

To keep research moving, the workflow was refreshed result-blind with commit `4e11b333f28e443d9e89f23b13bfdbe43d2d4828` at 17:07 JST. This should create a fresh v38 matrix Run when Actions accepts the push. If both old and fresh v38 runs remain queued, inspect self-hosted runner availability/contention before changing tracker code. Do not create v39 merely because the runner has not executed v38.

## Unchanged matrix
1. 2026-09-10 Kiryu3 standard — result blind.
2. 2026-09-10 Kiryu6 standard — result blind.
3. 2026-09-10 Kiryu12 standard — exposed technical calibration.
4. 2026-09-09 Kiryu12 varied `1,2,4,5,6,3` — exposed technical regression.

## Exact restart point
1. Locate the fresh SES v38 Run from workflow refresh commit `4e11b333f28e443d9e89f23b13bfdbe43d2d4828`; also recheck stalled Run `35057861647`.
2. If a v38 run executes, inspect all four jobs/artifacts: dead-frame depth, `diagnostics_v38`, accepted/failure reason, FastClip/seed/tracker latency. For accepted samples inspect +0.5/+1.0/+1.5 centers, identity sanity, NCC/fallback and lane separation. CI green alone is insufficient.
3. If v38 still fails technically because candidate-derived camera estimates are unstable, next direction is candidate-independent background-feature camera motion or another bounded low-DOF camera model, not widening 24/18/42 caps.
4. If runs remain queued, treat as runner infrastructure blocker and keep tracker unchanged until actual v38 evidence exists.
5. Preserve Kiryu3/6/9 result blindness.
6. Only after one unchanged seed+tracker passes all four sane and <=60 sec update `run_exhibition_ses_live_local.py`, then perform >=1 Japan self-hosted end-to-end live-style validation.

## Production wrapper warning
`run_exhibition_ses_live_local.py` is NOT live-ready and must not be used for betting decisions until the unchanged matrix passes. Do not production-wire v38 merely because it launches or one sample passes.

## Live-ready milestone
Multiple independent September samples incl varied entry; fully automatic acquisition+seed+tracker; sane identity/geometry with fail-closed retained; <=60 sec (ideal <=30); production wrapper updated only to a validated tracker; >=1 self-hosted end-to-end live-style success. Prefer 10+ samples before treating SES as stable/predictive. SES is an attack/head-support feature candidate, not direct finishing-order rank.
