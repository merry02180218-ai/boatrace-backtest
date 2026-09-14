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
- v11-v18 added result-blind motion/path constraints and multi-hypothesis temporal search; all failed safely without justifying threshold relaxation.
- v19 predecessor-conditioned beam, run `34835647158`: all four failed closed after healthy beams eventually reached a zero-feasible-expansion frame.
- v20 causal rescue proposal, run `34843565746`: all four failed closed.
- v21 verified appearance bank, run `34856451633`: all four failed closed.
- v22 rejection attribution, run `34865180548`: transition gate rejected zero states; finer attribution required.
- v23 fine-grained rejection attribution, run `34872289293`: Kiryu3 mainly hit immutable reverse-motion corridor; Kiryu6/Kiryu12 often lost viability before fleet `_safe_state`, at proposal merge/reachability.
- v24 proposal-merge attribution, run `34876804919`: proved fixed predecessor reachability/zero-velocity assumptions caused many zero-output merges; runtimes were far above live ceiling.
- v25 causal trajectory reachability, run `34882583228`: all four failed closed, but causal predecessor prediction materially fixed old gross wrong-direction identity paths. Dominant remaining transition rejects were raw-screen residual/acceleration gates contaminated by camera motion.

## v26 same-frame shared-translation compensation — COMPLETE / NOT FINAL
File `track_exhibition_boats_v26.py`.
Implementation commit `5ef4a4b614473f946ac63a99ee7becca41549078`.
Workflow `.github/workflows/regress-exhibition-seed17-track26.yml`.
Workflow commit `abb259d56e5ac7039af8529733e368fb3b0bfdca`.
Trigger commit `a09e06afc5c3e93765824cc4cec3d5b31c2ad893`.
Authoritative run `34886396511`.

v26 kept v25 proposal reachability, appearance bank/anchors, beam search, NCC, reverse corridor, fleet geometry and absolute 42 px/native-frame screen-step ceiling. It changed only transition residuals: subtract current six-boat median screen step, then apply unchanged 24 px residual and 20 px acceleration caps in translation-compensated coordinates.

### Actual v26 audit
Kiryu3 job `104118010334` did NOT reach seed/tracker because FastClip failed. This is a technical acquisition failure; it is not evidence for or against tracker v26. Result remains unread.

Three other jobs reached tracker v26 and failed closed scientifically with `FAIL_CLOSED: verified appearance-bank beam exhausted; no feasible temporal expansion`:
- Kiryu6 job `104118010588`, artifact `10365462194`: tracker runtime ~51.10 sec; failure after step 10 / native frame 20. +0.5 centers remained directionally plausible, including boat5 x~857 and boat6 x~927 from seeds x~749/~858. v26 diagnostic: 10,584 transition calls; 2,641 relative-residual rejects; 2,684 relative-acceleration rejects; 5,259 accepts; zero absolute-speed/reverse rejects. This is a large improvement over v25 gate acceptance but beam still exhausted.
- Kiryu12 standard job `104118010689`, artifact `10365565862`: tracker runtime ~71.87 sec; failure after step 17 / native frame 34. v26 diagnostic: 29,726 transition calls; 8,233 relative-residual rejects; 9,314 relative-acceleration rejects; 12,179 accepts; zero absolute-speed/reverse rejects. Sample path survived through +1.0 sec before exhaustion. Runtime exceeded 60 sec.
- Kiryu12 varied job `104118010508`, artifact `10365546388`: tracker runtime ~80.75 sec; failure after step 18 / native frame 36. v26 diagnostic: 16,084 transition calls; 3,823 relative-residual rejects; 5,034 relative-acceleration rejects; 7,227 accepts. Sample path survived through +1.0 sec before exhaustion. Runtime exceeded 60 sec.

Interpretation: translation compensation substantially increases feasible transitions and does not revive the old obvious reverse/off-frame pathology in the inspected artifacts, but the beam still dies. Residual/acceleration rejections remain large. A translation-only shared-camera model cannot represent same-frame zoom/rotation across perspective rows. Do NOT widen the 24/20 caps from this evidence.

## CURRENT candidate: v27 leave-one-out similarity-camera compensation
File `track_exhibition_boats_v27.py`.
Implementation commit `8e1e828b9e1dfad308662fa710dac280e925c107`.
Workflow `.github/workflows/regress-exhibition-seed17-track27.yml`.
Workflow creation/trigger commit `a6089aa9099bd8b6749aacd5b8ed76ffc24b6c24`.
Authoritative run **`34893353398`**.

At this handoff update the Japan self-hosted four-video matrix is active:
- Kiryu6 job `104141178559` in progress.
- Kiryu3 job `104141178728` queued.
- Kiryu12 standard job `104141178600` queued.
- Kiryu12 varied job `104141178372` queued.
Do not launch a duplicate while this run is legitimately queued/running.

### v27 design
v27 keeps all v25/v26 confidence and safety thresholds unchanged and changes only camera-motion decomposition:
- for each boat, fit a 2-D similarity transform (translation + uniform scale + rotation) from the OTHER five boats between predecessor/current frame;
- evaluate the held-out boat against that transform, so a wrong candidate cannot explain away its own error;
- reconstruct the previous interval causally from raw `last_step` and compute the same leave-one-out similarity residual;
- apply the unchanged 24 px/native-frame residual cap and unchanged 20 px/native-frame residual-acceleration cap;
- retain unchanged 42 px/native-frame absolute screen-step ceiling, immutable slit-direction/reverse gates, NCC, fleet geometry, appearance bank, and fail-closed behavior;
- return raw screen `steps` to keep v25 causal proposal prediction unchanged.
No future frame, race result, boat-number special case, race-specific offset, or threshold relaxation is used.

## v27 exact restart point
1. Inspect run `34893353398` first; do not duplicate while active.
2. Fetch all four jobs and `seed17-track27-*` artifacts after completion; workflow green alone is insufficient.
3. Kiryu3 must successfully reacquire FastClip; if acquisition alone fails again, diagnose/retry the technical downloader path separately without treating it as tracker evidence.
4. Inspect each `exhibition_tracking_v27.json`: accepted/failure reason, `v27_diagnostic`, beam survival, +0.5/+1.0/+1.5 centers, identity/anchor NCC, min fleet separation, on-frame/identity sanity, FastClip+seed+tracker latency.
5. Preserve Kiryu3/6 outcome blindness. Confirm Kiryu3 boat6 never revives the old high-NCC left/off-frame wake path and Kiryu6 boats5/6 remain distinct/sane.
6. Compare v27 residual/acceleration reject fractions and dead-frame depth against v26. The goal is better causal camera decomposition, not looser gates.
7. If v27 fails mechanically/import/runtime, fix and rerun immediately.
8. If v27 fails scientifically, do not widen thresholds. Use exact rejection/dead-frame diagnostics to decide whether the next state must explicitly estimate camera velocity/zoom over multiple frames or whether proposal/beam scoring rather than transition feasibility is now the bottleneck.
9. If correctness passes but runtime >60 sec, optimize computation while preserving exact decisions before production wiring.
10. Only after one unchanged seed+tracker passes all four physically sane and <=60 sec may `run_exhibition_ses_live_local.py` be updated; then run at least one Japan self-hosted end-to-end live-style validation.
11. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID, artifact IDs/evidence and restart point.

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
