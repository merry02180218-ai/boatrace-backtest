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
Authoritative run `34876804919`.

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
The fixed predecessor reachability radius is directly implicated in many zero-output merges:
- Kiryu3: 70 zero-output merges / 851 merge calls.
- Kiryu6: 645 / 3240.
- Kiryu12 standard: 138 / 11607.
- Kiryu12 varied: 279 / 1118.
Many candidate proposal distances were only just outside the unchanged 24 px/native-frame radius, while some were much farther. The source code confirmed coupled zero-velocity assumptions in proposal merge and transition displacement gates. This motivated causal trajectory/camera-motion compensated reachability rather than blind radius widening.

## v25 causal trajectory reachability — COMPLETE / REJECTED AS FINAL
File `track_exhibition_boats_v25.py`.
Implementation commit `562db33edfc21dca24fdd7401d7f970d47dd617d`.
Workflow `.github/workflows/regress-exhibition-seed17-track25.yml`.
Authoritative run `34882583228`.

All four unchanged matrix jobs reached v25 and failed closed with `FAIL_CLOSED: no feasible beam successors`; this was a scientific fail-closed result, not an import/download/seed failure.

Artifacts:
- Kiryu3: `10364142519`
- Kiryu6: `10363454032`
- Kiryu12 standard: `10364123112`
- Kiryu12 varied: `10363812920`

v25 diagnostics:
- Kiryu3: transition calls 3408; residual rejects 1739; acceleration rejects 1574; reverse rejects 55; accepts 40.
- Kiryu6: calls 4538; residual rejects 1861; acceleration rejects 2375; reverse rejects 261; accepts 41.
- Kiryu12 standard: calls 3469; residual rejects 1986; acceleration rejects 1073; reverse rejects 366; accepts 44.
- Kiryu12 varied: calls 4580; residual rejects 1891; acceleration rejects 2613; reverse rejects 25; accepts 51.

### Important v25 physical evidence
Although all four beams eventually failed closed, the predecessor-conditioned causal proposal prediction materially fixed the prior direction/identity pathology before the dead frame:
- Kiryu3 boat6, previously known to drift left/off-frame against positive slit motion, now moved approximately seed x=616 -> +0.5 x=765 -> +1.0 x=1063 -> +1.5 x=1344, i.e. physically consistent rightward motion.
- Kiryu6 boat5 moved approximately x=737 -> 772 -> 1073 -> 1286 and boat6 x=829 -> 872 -> 1101 -> 1325, remaining broadly sane/distinct through the inspected horizons.
- Both Kiryu12 technical samples were broadly sane before beam exhaustion.

Conclusion: v25 solved much of proposal reachability and the gross wrong-direction identity failure, but later transition gates still reject nearly all successors. The dominant residual/acceleration rejects use raw screen motion relative to the previous fleet step, which mixes shared camera acceleration/pan with boat-relative acceleration. Do not widen thresholds from this evidence.

## CURRENT behavioral candidate: v26 same-frame shared-camera relative motion
File `track_exhibition_boats_v26.py`.
Implementation commit `5ef4a4b614473f946ac63a99ee7becca41549078`.
Workflow `.github/workflows/regress-exhibition-seed17-track26.yml`.
Workflow creation commit `abb259d56e5ac7039af8529733e368fb3b0bfdca`.
Explicit trigger commit `a09e06afc5c3e93765824cc4cec3d5b31c2ad893`.
Authoritative latest regression run: **`34886396511`**.

At the latest check all four jobs are genuinely queued on the Japan self-hosted runner:
- job `104118010334` Kiryu3
- job `104118010588` Kiryu6
- job `104118010689` Kiryu12 standard
- job `104118010508` Kiryu12 varied
Do not launch another duplicate while this run remains legitimately queued/running.

### v26 design
v26 deliberately keeps v25 proposal reachability, immutable appearance anchors/bank, beam search, NCC thresholds, reverse-motion corridor, fleet order/separation/edge gates and absolute screen-step safety ceiling unchanged. It changes only the later-step motion decomposition:
- compute the robust median screen step of the current six boats at the candidate frame;
- subtract that current shared screen motion before applying the same 24 px/native-frame residual cap;
- compute previous boat-relative motion by subtracting the previous six-boat median step;
- apply the same 20 px/native-frame acceleration cap to current relative motion minus previous relative motion;
- retain the unchanged absolute raw screen-step ceiling of 42 px/native-frame;
- retain immutable slit-direction/reverse gates and fail closed when no safe successor remains.

This is not a free threshold relaxation: the same numerical residual and acceleration caps are used in a coordinate system that removes causal same-frame shared camera motion. No future frame, race result, boat-number special case or race-specific offset is used.

## v26 exact restart point
1. Inspect run `34886396511` first. Do not duplicate it while queued/running.
2. When complete, fetch all four jobs and artifacts `seed17-track26-*`; workflow green alone is insufficient.
3. Inspect `exhibition_tracking_v26.json` for accepted/failure reason and `v26_diagnostic` rejection attribution.
4. Record fallback fractions, identity/anchor NCC, min lane separation, +0.5/+1.0/+1.5 centers, physical on-frame survival, and FastClip+seed+tracker latency for each race.
5. Kiryu3 result remains unread. Confirm boat6 continues physically rightward and never regains the old high-NCC left/off-frame wake path.
6. Confirm Kiryu6 boats5/6 remain distinct/sane and both Kiryu12 technical samples are not regressed.
7. If v26 fails from coding/import/runtime mechanics, fix and rerun immediately.
8. If v26 fails scientifically, do not widen caps merely to pass. Use rejection attribution to decide whether beam state must carry shared-camera velocity explicitly or whether a robust causal affine/shared-motion estimate is required.
9. If correctness passes but runtime is >60 sec, optimize computation while preserving exact decisions before production wiring.
10. Only after one unchanged seed+tracker passes all four physically sane and <=60 sec may `run_exhibition_ses_live_local.py` be updated; then perform at least one Japan self-hosted end-to-end live-style validation.
11. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID, artifact/log evidence and next restart point.

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
