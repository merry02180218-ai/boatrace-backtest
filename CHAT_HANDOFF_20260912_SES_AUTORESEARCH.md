# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Non-negotiable rules
Latest GitHub/artifacts win. 2026-09-10 Kiryu3/6/9 results remain unread. 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only. July/August NON-PRISTINE. Never relax fail-closed/NCC/geometry/motion gates merely to pass. No boat/race-specific offsets. Production target is persistent Japan self-hosted PC; ideal <=30 sec, maximum <=60 sec. Exact Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Seed
Keep `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`. Current blocker remains tracker identity/path representation, not race-specific seed movement.

## Retained progression through v27
v8-v24 progressively established that independent/per-frame identity, immutable appearance alone, lane-cell geometry, and fixed proposal reachability were insufficient. v25 causal trajectory reachability removed gross wrong-direction paths. v26 translation camera compensation improved feasibility but remained insufficient. v27 leave-one-out similarity run `34893353398` failed all four; residual/acceleration gates dominated and runtime was 43.6–94.3 sec.

## v28 COMPLETE / REJECTED
File `track_exhibition_boats_v28.py`, workflow `.github/workflows/regress-exhibition-seed17-track28.yml`, run `34900743347`, head `3d83884f5bc44925102f025a8cd31517eb7f14f3`.
Artifacts: Kiryu3 `10370611700`, Kiryu6 `10371205844`, Kiryu12 `10370942723`, varied `10371386638`.
All four failed closed. Kiryu3 artifact audit: `accepted=false`, `FAIL_CLOSED: verified appearance-bank beam exhausted; no feasible temporal expansion`, dead after step9/native18, tracker runtime 54.566 sec. At +0.5 centers were [1008,409],[957,490],[961,589],[890,695],[883,812],[547,1008]; boat6 old catastrophic path did not continue but identity remained dubious. Diagnostics: 2756 transition calls, 1351 residual rejects, 518 acceleration rejects, 887 accepts. C(5,3) per-held robust consensus was expensive and did not improve dead-frame depth enough.

## v29 COMPLETE / REJECTED
File `track_exhibition_boats_v29.py`. Implementation commit `41c09beb619b60687f2a208db061a42aaebb2166`; trigger commit `8c21cb70206acd54bfddd51ea621805592595dc6`; workflow `.github/workflows/regress-exhibition-seed17-track29.yml`; authoritative run `34906246958` completed FAILURE scientifically, not import failure.
Artifacts: Kiryu3 `10373431188`, Kiryu6 `10372379200`, Kiryu12 `10373605755`, varied `10373017503`.
v29 used ONE shared robust four-of-six similarity-camera state instead of six leave-one-out transforms, with all 24/20/42 caps unchanged. Kiryu3 still failed closed, now after step8/native16, runtime 43.713 sec; +0.5 centers [959,433],[957,490],[961,589],[890,695],[868,845],[561,1010]. Diagnostics: 2765 calls, 1172 residual rejects, 691 acceleration rejects, 902 accepts, zero reverse/absolute rejects. Shared similarity therefore did not solve the coordinate mismatch and slightly worsened dead-frame depth vs v28. Do not tune/widen caps.

## CURRENT candidate: v30 shared robust affine-camera state
File `track_exhibition_boats_v30.py`.
Implementation commit `6e406352bf8a28876c61ad67e42b4621657c13e8`.
Workflow `.github/workflows/regress-exhibition-seed17-track30.yml`, creation commit `62ad92bd13d617ded98dd0c2c1c59df515246085`.
Explicit trigger commit `f26f5abd0331df306df2db86651e85519c28a9ef`.
At this handoff write the GitHub run had not yet appeared in the API; first next action is to resolve the v30 run ID/status and do NOT create a duplicate if queued/running.

### v30 design
v29 showed shared state is not enough if camera representation remains similarity-only. The six boats span a large y range in an oblique camera, so first-order perspective can appear as anisotropic scale/shear. v30 changes ONLY shared camera representation to affine. It enumerates C(6,3)=20 exact three-boat affine fits, selects by 4th-smallest six-boat residual then mean of four best, applies one shared transform to all six, and retains unchanged 24 px/native-frame residual, 20 acceleration, 42 absolute, reverse corridor, NCC, appearance bank, fleet geometry, v25 proposal reachability and fail-closed behavior. No future frame/result/special case/threshold relaxation.

## Exact restart point
1. Find v30 run created by trigger `f26f5abd0331df306df2db86651e85519c28a9ef`; if missing after GitHub propagation, make one harmless trigger edit only once.
2. Inspect all four v30 jobs/artifacts, not workflow status alone. Preserve Kiryu3/6 blindness.
3. Record dead-frame depth, residual/acceleration rejection counts, +0.5/+1.0/+1.5 centers, on-frame/identity sanity and FastClip+seed+tracker latency.
4. Compare v30 against v29/v28. A win must be physically sane and improve feasibility without widening any gate.
5. If v30 still fails, do not widen 24/20 caps. The next principled direction is to stop forcing every candidate through a single instantaneous global camera transform and instead carry a low-dimensional camera-motion state temporally in the beam (camera parameter velocity/acceleration), or derive background-feature camera motion independently from boat hypotheses.
6. Only after one unchanged seed+tracker passes all four sane and <=60 sec may `run_exhibition_ses_live_local.py` be updated, followed by >=1 Japan self-hosted end-to-end live-style validation.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update yet.

## Live-ready milestone
Multiple independent September samples incl varied entry; fully automatic acquisition+seed+tracker; sane identity/geometry with fail-closed retained; <=60 sec (ideal <=30); production wrapper updated; >=1 self-hosted end-to-end live-style success. Prefer 10+ samples before treating SES as stable/predictive. SES is an attack/head-support feature candidate, not direct finishing-order rank.
