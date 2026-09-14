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
Current seed remains `auto_seed_exhibition_motion_v17.py`, commit `3f628a0099a5b93b38da7a9be8acdbf89fdcef2b`.
Evidence still indicates the principal blocker is tracker identity/path preservation rather than seed placement.

## Retained tracker progression
- v8 joint per-frame assignment: Kiryu12 std/var passed, Kiryu3/6 failed.
- v9 immutable appearance memory: rejected.
- v10 fleet-affine y reference: rejected.
- v11-v18 progressively added result-blind motion/path constraints and multi-hypothesis temporal search; all failed safely without justifying threshold relaxation.
- v19 predecessor-conditioned beam, run `34835647158`: all four failed closed after healthy beams eventually reached a frame with zero feasible expansion. Diagnosis: immutable slit appearance becomes proposal-brittle after appearance phase shift.
- v20 causal rescue proposal, authoritative run `34843565746`: all four failed closed; adaptive appearance as proposal-only did not solve late beam exhaustion.
- v21 verified appearance bank, run `34856451633`: all four failed closed. Hundreds of verified-bank proposals could still exist near dead frames, so simple proposal absence was not the full explanation.
- v22 rejection-attribution diagnostic, run `34865180548`: transition gate rejected zero states in all four; cumulative safe-state rejection was too coarse to locate the exact failure. This justified finer attribution without changing behavior.

## v23 fine-grained rejection attribution — COMPLETE
File `track_exhibition_boats_v23.py`.
Implementation commit `4a8df5f9974c92c65493f2cb228004ef9fcb6372`.
Workflow `.github/workflows/regress-exhibition-seed17-track23.yml`.
Workflow commit `5b1038e265cda0e71004bcdbf2710f0aa740ad29`.
Authoritative run **`34872289293`**.

All four unchanged technical jobs reached tracker v23 and failed closed. FastClip and seed v17 succeeded. v23 changed no tracking behavior, no gate and no score.

Artifact IDs:
- Kiryu3 `10358763705`
- Kiryu6 `10360125362`
- Kiryu12 standard `10359768240`
- Kiryu12 varied `10358768292`

### v23 audited evidence
Kiryu3:
- runtime 55.813s; dead after native frame 18.
- last centers `[[997,409],[951,492],[964,589],[900,699],[975,819],[520,1016]]`.
- cumulative safe-state: 4,768 calls, 497 rejects = 475 reverse-corridor + 22 order; transition rejects 0.
- at the final recorded predecessor expansions candidate lists were non-empty, Cartesian fleet states were non-zero, but every state was rejected by the immutable reverse-motion corridor (with occasional order rejection). Example tail calls had candidate lengths such as `[3,1,1,1,3,1]`, 9 Cartesian states, 9/9 reverse-corridor rejects, 0 output expansions.
- conclusion: Kiryu3 reaches fleet safety and is correctly fail-closed by motion-direction identity protection. Do not relax the reverse corridor merely to make it pass.

Kiryu6:
- runtime 52.280s; dead after native frame 20.
- last centers `[[930,448],[873,503],[1006,606],[952,742],[897,834],[921,843]]`.
- cumulative safe-state: 18,171 calls, 748 rejects = 736 order + 12 <=4px gap; transition rejects 0.
- final diagnostic frame: predecessor_count=0, rescue_attempts=24, bank_proposals=284.
- the final v23 `_expand_predecessor` records immediately before death still had non-zero outputs; therefore the dead frame never reached `_expand_predecessor`. At least one per-boat merged proposal list becomes empty first.
- conclusion: failure locus is pre-safe proposal merge/reachability, not transition and not a reason to relax fleet order.

Kiryu12 standard:
- runtime 46.618s; dead after native frame 20.
- last centers `[[851,386],[984,447],[983,496],[1054,561],[958,602],[706,771]]`.
- cumulative safe-state: 26,692 calls, only 64 rejects, all order; transition rejects 0.
- final diagnostic frame: predecessor_count=0, rescue_attempts=24, bank_proposals=144.
- as with Kiryu6, preceding expansion calls were healthy/non-zero, so the dead frame loses viability before `_expand_predecessor` is invoked.
- conclusion: proposal merge/reachability loss is the direct locus.

Kiryu12 varied `1,2,4,5,6,3`:
- runtime 81.548s; dead after native frame 36.
- last centers `[[878,400],[938,451],[707,811],[691,530],[978,586],[1093,666]]`.
- cumulative safe-state: 35,473 calls, 1,153 rejects = 982 <=4px gap + 171 order; transition rejects 0.
- final diagnostic frame: predecessor_count=0, rescue_attempts=24, bank_proposals=0.
- no zero candidate lengths were seen in the preceding `_expand_predecessor` calls; dead-frame viability disappears before fleet-state evaluation.
- conclusion: this sample additionally needs attribution of why verified-bank/local/global proposals fail to survive predecessor merge/reachability at the dead frame.

### v23 conclusion
There are at least two distinct failure loci:
1. Kiryu3: candidates survive proposal generation/merge but are physically unsafe under the immutable slit-motion corridor.
2. Kiryu6 and both Kiryu12 technical samples: viability disappears earlier, before fleet `_safe_state`; v23 did not instrument `_merge`, so source loss/reachability/dedup must be measured next.
Threshold relaxation is not justified.

## CURRENT candidate: v24 proposal-merge source attribution diagnostic
File `track_exhibition_boats_v24.py`.
Implementation commit **`f3c75fce1f10b3278a08f5f2d5569813e81efd3d`**.
Workflow `.github/workflows/regress-exhibition-seed17-track24.yml`.
Workflow creation/trigger commit **`d17e7fd200d2861832017a76ceca79ce0fcc32cb`**.
Authoritative run **`34876804919`** launched by push on the Japan self-hosted runner; queued at this handoff update.

v24 deliberately preserves v21/v23 tracking behavior exactly. It wraps the existing proposal `_merge` as a side-channel diagnostic and records for every merge call:
- input counts by source: global immutable / predecessor-local immutable / verified appearance bank;
- unchanged predecessor reachability radius and minimum candidate distance by source;
- counts rejected by the unchanged reachability radius;
- counts rejected by the unchanged 8px merge dedup;
- accepted source counts and capacity-skipped count;
- authoritative output count plus diagnostic replay output count.
It also retains the v23 safe-state and transition attribution. `behavior_changed_from_v21=false`; no threshold, score, beam width, proposal source, gate or race-specific rule is changed.

## v24 exact restart point
1. Inspect run `34876804919`; do not launch a duplicate while legitimately queued/running.
2. Download all four `seed17-track24-*` artifacts and inspect `exhibition_tracking_v24.json`, not workflow status alone.
3. For each dead frame, inspect the final merge-call suffix and determine which boat/source loses predecessor reachability:
   - global immutable source present but all outside radius;
   - local immutable source absent;
   - verified bank source absent;
   - bank/global/local candidates exist but all outside radius;
   - 8px merge dedup removes the last distinct reachable option;
   - or another mismatch (diagnostic replay count must equal authoritative output count).
4. Kiryu3 should reproduce v23 reverse-corridor fail-close. If it changes behavior, v24 diagnostic is invalid and must be fixed rather than interpreted.
5. If Kiryu6/Kiryu12 loss is primarily predecessor reachability with physically plausible nearby bank candidates just outside the per-step radius, do NOT blindly widen the radius. Compare multi-frame motion/path evidence and implement a causal trajectory-prediction proposal centered on robust recent velocity while preserving hard physical fail-close.
6. If local/bank proposal generation itself goes empty, instrument the exact NCC/support rejection or add a principled causal appearance-continuity proposal; do not lower NCC merely to pass.
7. If merge dedup is the dominant source of last-option loss, inspect whether the dedup is merging genuinely distinct identities before changing it.
8. After failure locus is proven, implement the next behavioral tracker version and rerun the unchanged four-sample matrix.
9. Only if one unchanged seed+tracker passes all four physically sane with total latency <=60 sec may `run_exhibition_ses_live_local.py` be updated.
10. After a four-sample technical pass, perform at least one Japan self-hosted end-to-end live-style validation before calling live-ready.
11. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID and artifact/log evidence.

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
