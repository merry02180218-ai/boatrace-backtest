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
- v11-v18 progressively added result-blind motion/path constraints and multi-hypothesis temporal search; all failed safely without justifying threshold relaxation.
- v19 predecessor-conditioned beam, run `34835647158`: all four failed closed after healthy beams eventually reached a frame with zero feasible expansion.
- v20 causal rescue proposal, run `34843565746`: all four failed closed.
- v21 verified appearance bank, run `34856451633`: all four failed closed; verified-bank proposals could still exist near dead frames, so simple proposal absence was not the full explanation.
- v22 rejection attribution, run `34865180548`: transition gate rejected zero states; finer attribution was required.
- v23 fine-grained rejection attribution, run `34872289293`: proved Kiryu3 is stopped mainly by the immutable reverse-motion corridor, while Kiryu6/Kiryu12 viability often disappears before fleet `_safe_state`, at proposal merge/reachability.

## v24 proposal-merge attribution — COMPLETE
File `track_exhibition_boats_v24.py`.
Implementation commit `f3c75fce1f10b3278a08f5f2d5569813e81efd3d`.
Workflow `.github/workflows/regress-exhibition-seed17-track24.yml`.
Workflow commit `d17e7fd200d2861832017a76ceca79ce0fcc32cb`.
Authoritative run **`34876804919`**.

All four unchanged matrix jobs reached tracker v24 and failed closed; FastClip and seed v17 succeeded. v24 is diagnostic-only and intentionally preserves prior behavior.

Artifacts:
- Kiryu3: `10360359164`
- Kiryu6: `10361411914`
- Kiryu12 standard: `10361841075`
- Kiryu12 varied: `10361920291`

Observed failure/runtime:
- Kiryu3: `FAIL_CLOSED: no beam survived frame 1164`, tracker ~1341.68 sec.
- Kiryu6: `FAIL_CLOSED: no beam survived frame 1166`, tracker ~2849.95 sec.
- Kiryu12 standard: `FAIL_CLOSED: no beam survived frame 1154`, tracker ~9847.90 sec.
- Kiryu12 varied: `FAIL_CLOSED: no beam survived frame 1146`, tracker ~896.26 sec.
These latencies are far beyond the <=60 sec live ceiling and must be reduced after correctness is established.

### v24 root-cause evidence
The fixed predecessor reachability radius is now directly implicated in many zero-output merges:
- Kiryu3: 70 zero-output merges / 851 merge calls.
- Kiryu6: 645 / 3240.
- Kiryu12 standard: 138 / 11607.
- Kiryu12 varied: 279 / 1118.
Many candidate proposal distances were only just outside the unchanged 24 px/native-frame radius (for stride2, examples around 48.37 px versus a 48 px radius), while some were much farther (roughly 53-90+ px).

The source code confirms two coupled zero-velocity assumptions:
1. v21 proposal `_merge` admits candidates only inside `24*advance` around the predecessor center.
2. v17 transition logic hard-rejects raw screen displacement above `24*advance`.
This is brittle under shared camera/screen motion. The evidence does NOT justify blindly widening a radius; it motivates a causal trajectory/camera-motion compensated reachability model while retaining identity, reverse-motion and fleet-geometry fail-closed gates.

## CURRENT behavioral candidate: v25 causal camera-compensated trajectory reachability
File `track_exhibition_boats_v25.py`.
Implementation commit **`562db33edfc21dca24fdd7401d7f970d47dd617d`**.
Workflow `.github/workflows/regress-exhibition-seed17-track25.yml`.
Initial workflow commit **`54b957afc0270a114bcd5bb62adbdd32a9004abd`**.
Explicit trigger commit **`844e21fdf324ead70384debc40c18b83ec9e0699`**.
Latest regression run **`34882583228`**; four matrix jobs were queued on the Japan self-hosted runner at the latest check. Earlier run `34882390375` was also queued; use the newer run as authoritative when it starts unless GitHub shows otherwise.

### v25 design
v25 keeps v21 immutable appearance anchors, verified appearance bank, NCC thresholds, beam search, fleet order/separation/edge checks, and immutable reverse-motion corridor. It changes predecessor reachability causally rather than by a free threshold relaxation:
- predict each next center from the predecessor's previous accepted displacement;
- merge proposals inside the same 24 px/native-frame radius around that causal prediction instead of a zero-velocity circle around the old center;
- first step retains the original <=24 px/native-frame raw displacement cap;
- later steps require residual from robust fleet screen motion <=24 px/native-frame;
- individual acceleration <=20 px/native-frame;
- absolute raw screen step <=42 px/native-frame as an outer safety ceiling;
- candidates still must pass immutable appearance/identity, reverse-direction, fleet geometry and edge safety gates;
- if no safe candidate remains, fail closed;
- no future frame, race result, boat-number rule or race-specific offset is used.

The wider absolute screen-step ceiling is not a standalone gate relaxation: a candidate beyond the old zero-velocity radius is only reachable if it is close to the causal trajectory prediction and also passes acceleration, shared-screen-motion, appearance, geometry, edge and reverse-direction checks.

## v25 exact restart point
1. Inspect run `34882583228` jobs first. Do not launch another duplicate while this run is legitimately queued/running.
2. If it completes, download all four `seed17-track25-*` artifacts and inspect `exhibition_tracking_v25.json`, not workflow status alone.
3. For each race record accepted/failure reason, `v25_diagnostic`, fallback fractions, identity/anchor NCC, min lane separation, +0.5/+1.0/+1.5 centers, physical on-frame survival, and FastClip+seed+tracker latency.
4. Kiryu3 result must remain unread. Check specifically whether boat6 is prevented from high-NCC reverse-direction wake/background drift without merely failing earlier for an artificial reason.
5. Check Kiryu6 boats5/6 remain distinct and physically sane.
6. Check both Kiryu12 technical samples are not regressed by causal camera compensation.
7. If v25 fails from a coding/import error, fix and rerun immediately.
8. If v25 fails scientifically, do not loosen gates merely to pass. Use the new causal diagnostics to decide whether the next step should be multi-frame beam/Viterbi trajectory assignment, improved robust shared-camera-motion estimation, or an appearance-continuity refinement.
9. If v25 is correct but too slow, optimize candidate/beam computation only after preserving exactly the validated decisions.
10. Only if one unchanged seed+tracker passes all four with sane identity/geometry and total latency <=60 sec may `run_exhibition_ses_live_local.py` be updated.
11. After a four-sample technical pass, perform at least one Japan self-hosted end-to-end live-style validation before calling live-ready.
12. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID, artifact/log evidence and next restart point.

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
