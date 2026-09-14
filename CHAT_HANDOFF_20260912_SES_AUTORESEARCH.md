# CHAT HANDOFF — SES AUTO-RESEARCH / LIVE EXHIBITION PIPELINE

Updated: 2026-09-15 JST
Repo: `merry02180218-ai/boatrace-backtest`

## Purpose
Continue BOATCAST start-exhibition video research until immediate post-exhibition live use is reliable: result-blind FastClip -> automatic six-boat seed -> automatic tracking -> SES -> model re-evaluation, with no manual/race-specific edits.

## Non-negotiable rules
- Latest GitHub code/artifacts override old prose/chat memory.
- Never inspect race results before locking exhibition-only judgement on blind samples.
- 2026-09-10 Kiryu3/6/9 results remain unread; preserve blindness.
- 2026-09-09 Kiryu12 and 2026-09-10 Kiryu12 are exposed technical samples only.
- July/August 2026 are NON-PRISTINE.
- Never relax fail-closed/NCC/geometry/motion gates merely to obtain accepted=true.
- Never hard-code boat-number/race-specific offsets.
- accepted=true is necessary but not sufficient: trajectories must remain physically sane/on-frame and preserve identity.
- Final race-by-race operation should be persistent on Japan self-hosted PC; Actions are validation/logging.
- Exact Japan Python: `C:\Users\merry\AppData\Local\Programs\Python\Python311\python.exe`.
- Live latency target: ideal <=30 sec after video availability, maximum <=60 sec.

## Seed state
Current seed remains `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`. Prior Kiryu6 evidence shows v17 can produce a plausible rescued outer-row seed and survive long-horizon result-blind validation. Current blocker remains tracker identity/path preservation rather than race-specific seed movement.

## Retained tracker progression
- v8 joint per-frame assignment: Kiryu12 std/var passed, Kiryu3/6 failed.
- v9 immutable appearance memory: rejected.
- v10 fleet-affine y reference: rejected.
- v11-v18 result-blind motion/path constraints and multi-hypothesis temporal search: failed safely; no threshold relaxation justified.
- v19 predecessor-conditioned beam, run `34835647158`: all four failed closed after healthy beams reached zero-feasible-expansion frames.
- v20 causal rescue proposal, run `34843565746`: all four failed closed.
- v21 verified appearance bank, run `34856451633`: all four failed closed.
- v22 rejection attribution, run `34865180548`: transition gate rejected zero states; finer attribution required.
- v23 fine-grained rejection attribution, run `34872289293`: Kiryu3 mainly hit immutable reverse-motion corridor; Kiryu6/Kiryu12 often lost viability before fleet `_safe_state`, at proposal merge/reachability.
- v24 proposal-merge attribution, run `34876804919`: fixed predecessor reachability/zero-velocity assumptions caused many zero-output merges; runtimes far above live ceiling.
- v25 causal trajectory reachability, run `34882583228`: causal predecessor prediction fixed old gross wrong-direction identity paths; remaining rejects were raw-screen residual/acceleration gates contaminated by camera motion.
- v26 same-frame shared translation, run `34886396511`: materially improved transition acceptance but beams still exhausted; tracker runtime ~51 sec Kiryu6, ~72 sec Kiryu12 std, ~81 sec Kiryu12 varied. Translation-only camera compensation insufficient for zoom/rotation/perspective.

## v27 leave-one-out similarity-camera compensation — COMPLETE / REJECTED
File `track_exhibition_boats_v27.py`.
Implementation commit `8e1e828b9e1dfad308662fa710dac280e925c107`.
Workflow `.github/workflows/regress-exhibition-seed17-track27.yml`.
Workflow creation/trigger commit `a6089aa9099bd8b6749aacd5b8ed76ffc24b6c24`.
Authoritative run `34893353398`.

v27 kept all v25/v26 safety/confidence thresholds unchanged. For each held-out boat it fitted a 2-D similarity transform from the OTHER five boats, then applied the unchanged 24 px/native-frame residual cap and 20 px/native-frame residual-acceleration cap, retaining the 42 px absolute screen-step ceiling, reverse corridor, NCC, appearance bank, fleet geometry and fail-closed behavior.

### Actual v27 four-video audit
All four jobs reached FastClip + seed v17 + tracker v27 and all four failed closed scientifically with `FAIL_CLOSED: verified appearance-bank beam exhausted; no feasible temporal expansion`. No outcome was read.

- Kiryu3 job `104141178728`, artifact `10367634626`: runtime 43.637 sec; beam died after completed step 9 / native frame 18. Samples survived to +0.5 sec only. v27 diagnostics: 2,605 transition calls; 1,163 relative-residual rejects; 559 relative-acceleration rejects; 883 accepts; zero absolute-speed/reverse rejects. Boat6 at +0.5 was ~[547,1008] from seed [616,961], so the old catastrophic left/off-frame path was not allowed to continue, but the beam still exhausted.
- Kiryu6 job `104141178559`, artifact `10367548689`: runtime 49.429 sec; beam died after step 8 / native frame 16. v27 diagnostics: 10,694 calls; 3,530 residual rejects; 3,061 acceleration rejects; 4,103 accepts. +0.5 outer centers remained distinct enough to inspect (boat5 ~[857,826], boat6 ~[927,836]) but y separation was already narrow and the beam exhausted before +1.0.
- Kiryu12 standard job `104141178600`, artifact `10368013212`: runtime 91.545 sec; beam died after step 16 / native frame 32. v27 diagnostics: 27,344 calls; 14,511 residual rejects; 7,278 acceleration rejects; 5,549 accepts; only 6 absolute-speed rejects, zero reverse rejects. Samples survived through +1.0 but runtime is far beyond 60 sec.
- Kiryu12 varied job `104141178372`, artifact `10367763435`: runtime 94.253 sec; beam died after step 18 / native frame 36. v27 diagnostics: 14,938 calls; 5,524 residual rejects; 4,990 acceleration rejects; 4,424 accepts; zero absolute-speed/reverse rejects. Samples survived through +1.0 but runtime is far beyond 60 sec.

Interpretation: similarity-camera decomposition did not solve transition feasibility. Rejection is still dominated by relative residual/acceleration, while reverse/absolute safety gates almost never fire. A key weakness in v27 is that each camera transform uses all other five peer candidates in one least-squares fit; one wrong peer can bias the transform used to judge a sane held-out candidate. Do NOT widen 24/20 caps.

## CURRENT candidate: v28 robust peer-consensus similarity-camera compensation
File `track_exhibition_boats_v28.py`.
Implementation commit `f3adb30c3bc272e5fb72956056446b994331fa3c`.
Workflow `.github/workflows/regress-exhibition-seed17-track28.yml`.
Workflow creation/trigger commit `3d83884f5bc44925102f025a8cd31517eb7f14f3`.
Authoritative run **`34900743347`**, launched on push and queued on the Japan self-hosted runner at this handoff update.

### v28 design
v28 changes only the camera estimator; all numerical safety/confidence caps remain unchanged.
- For each held-out boat, consider only the OTHER five boats.
- Enumerate all C(5,3)=10 three-peer similarity fits.
- Validate each fit on the two peer boats not used to fit it.
- Choose the fit minimizing maximum validation error, then mean validation error as deterministic tie-break.
- Judge the held-out boat with that peer-consensus transform; the held-out boat never explains itself.
- Repeat the same robust consensus for the reconstructed preceding interval, then apply the unchanged 24 px/native-frame residual cap and unchanged 20 px/native-frame residual-acceleration cap.
- Retain unchanged 42 px/native-frame absolute screen-step ceiling, immutable slit-direction/reverse gates, NCC, fleet geometry, appearance bank, v25 causal proposal reachability, and fail-closed behavior.
- No future frame, result, boat-number rule, race-specific offset, or threshold relaxation.

Rationale: v27 showed high residual/acceleration rejection despite almost no reverse/absolute-speed rejection. Robust peer consensus tests whether occasional bad peer hypotheses are corrupting the camera transform rather than loosening physical gates.

## v28 exact restart point
1. Inspect run `34900743347` first; do not launch a duplicate while legitimately queued/running.
2. Fetch all four `seed17-track28-*` artifacts after completion; workflow green alone is insufficient.
3. Inspect `exhibition_tracking_v28.json` for accepted/failure reason, `v28_diagnostic`, dead-frame depth, +0.5/+1.0/+1.5 centers, identity/anchor NCC, min fleet separation, on-frame/identity sanity, and FastClip+seed+tracker latency.
4. Preserve Kiryu3/6 outcome blindness. Kiryu3 boat6 must not revive the old high-NCC left/off-frame wake path; Kiryu6 boats5/6 must remain physically distinct/sane.
5. Compare residual/acceleration reject fractions and dead-frame depth against v27. Success means better robust causal camera decomposition, not looser gates.
6. If v28 has a mechanical/import/runtime failure, fix and rerun immediately.
7. If v28 fails scientifically, do not widen thresholds. Use its diagnostics to decide between explicit multi-frame camera-parameter velocity/zoom state versus changing proposal/beam scoring/representation.
8. If correctness passes but runtime >60 sec, optimize exact computation before production wiring; C(5,3) consensus is intentionally diagnostic and may need caching/vectorization.
9. Only after one unchanged seed+tracker passes all four physically sane and <=60 sec may `run_exhibition_ses_live_local.py` be updated, followed by at least one Japan self-hosted end-to-end live-style validation.
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
