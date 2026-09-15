# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Non-negotiable rules
Latest GitHub/artifacts win. 2026-09-10 Kiryu3/6/9 results remain unread. 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only. July/August NON-PRISTINE. Never relax fail-closed/NCC/geometry/motion gates merely to pass. No boat/race-specific offsets. Production target persistent Japan self-hosted PC; ideal <=30 sec, maximum <=60 sec. Exact Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.

## Seed
Keep `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`. Current blocker is tracker identity/path representation, not race-specific seed movement.

## Retained progression
v8-v24 established independent/per-frame identity, immutable appearance alone, lane-cell geometry and fixed proposal reachability were insufficient. v25 causal trajectory reachability removed gross wrong-direction paths. v26 translation camera compensation improved feasibility but remained insufficient. v27 leave-one-out similarity run `34893353398` failed all four and was too slow. v28 run `34900743347` failed all four; Kiryu3 died step9/native18, tracker 54.566 sec. v29 run `34906246958` failed all four; shared robust similarity did not solve coordinate mismatch, Kiryu3 died step8/native16, 43.713 sec. Do not widen 24/20/42 motion caps.

## CURRENT candidate: v30 shared robust affine-camera state
File `track_exhibition_boats_v30.py`; implementation `6e406352bf8a28876c61ad67e42b4621657c13e8`. It changes only the shared camera representation from similarity to affine: enumerate C(6,3)=20 exact three-boat affine fits, choose by 4th-smallest six-boat residual then mean of four best, then apply unchanged 24 px/native-frame residual, 20 acceleration, 42 absolute, reverse corridor, NCC, appearance bank, fleet geometry, v25 proposal reachability and fail-closed behavior. No future frame/result/special case/threshold relaxation.

### v30 Actions trigger diagnosis and repair
The dedicated workflow `.github/workflows/regress-exhibition-seed17-track30.yml` was created at `62ad92bd13d617ded98dd0c2c1c59df515246085`. Trigger `f26f5abd0331df306df2db86651e85519c28a9ef`, later retrigger `bac262422a2b0de69bbc9d09845dcdd9f2b78ea3`, and dependency-path repair `0fb3eda2c9fb4a866f6ec4ac151e693c335e7cc6` produced no discoverable v30 Actions run even after propagation. A head-SHA Actions query for repair commit showed other push workflows ran, proving repository Actions itself was alive; the v30 workflow specifically was not registered/triggering.

At ~11:23 JST the existing already-registered v29 regression workflow was therefore converted into a temporary **v30 validation bridge** rather than changing tracker logic or thresholds. Bridge commit: `dca84d404b6bda839e0f6044fd6e6450db827f47`. The workflow path remains `.github/workflows/regress-exhibition-seed17-track29.yml` so GitHub uses an already-known workflow identity, but its run-name, tracker command, output and artifacts now explicitly execute `track_exhibition_boats_v30.py` on the unchanged four-video matrix. Artifact prefix is `seed17-track30-bridge-*`. Immediately after commit, head-SHA run query returned zero; allow normal GitHub propagation, then recheck before further edits. This bridge is validation infrastructure only and does not alter production wrapper or blindness.

## Exact restart point
1. Query Actions runs for head SHA `dca84d404b6bda839e0f6044fd6e6450db827f47` and/or the registered v29 workflow path after propagation.
2. If bridge run exists, inspect all four jobs/artifacts, not workflow status alone. Preserve Kiryu3/6 blindness. Record dead-frame depth, residual/acceleration rejects, +0.5/+1.0/+1.5 centers, physical identity/on-frame sanity, and FastClip+seed+tracker latency.
3. Compare v30 directly with v29/v28. A win must improve feasibility physically without widening gates.
4. If v30 still fails, do not widen 24/20 caps. Next principled direction is temporal camera-state continuity in the beam (camera parameter velocity/acceleration), or independent background-feature camera motion.
5. If bridge still produces no run after propagation, diagnose Actions workflow registration rather than modifying tracker logic. Do not repeatedly create trigger-only commits.
6. Only after one unchanged seed+tracker passes all four sane and <=60 sec may `run_exhibition_ses_live_local.py` be updated, then perform >=1 Japan self-hosted end-to-end live-style validation.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update yet.

## Live-ready milestone
Multiple independent September samples incl varied entry; fully automatic acquisition+seed+tracker; sane identity/geometry with fail-closed retained; <=60 sec (ideal <=30); production wrapper updated; >=1 self-hosted end-to-end live-style success. Prefer 10+ samples before treating SES as stable/predictive. SES is an attack/head-support feature candidate, not direct finishing-order rank.
