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

## v21 verified appearance bank — REJECTED, diagnostic progress
File `track_exhibition_boats_v21.py`.
Implementation commit `555796903f400528f94173dba42e41a02685431a`.
Workflow `.github/workflows/regress-exhibition-seed17-track21.yml`.
Authoritative run `34856451633`.

All four unchanged matrix jobs reached tracker v21 and failed closed; FastClip and seed v17 succeeded. No outcome was read and no gate was relaxed.

Artifact IDs:
- Kiryu3 `10353063788`
- Kiryu6 `10353487395`
- Kiryu12 standard `10353830465`
- Kiryu12 varied `10353193682`

Fresh artifact audit established that Kiryu3 and Kiryu6 reach dead late frames with hundreds of verified-bank proposals, so the issue is not simply absence of rescue proposals. Kiryu3 outer boat6 and Kiryu6 boats5/6 remain physically concerning before safe fail-close.

## v22 rejection-attribution diagnostic — COMPLETE, diagnostic result
File `track_exhibition_boats_v22.py`.
Implementation commit `94444b58858208bc9341840f3708bf3dcf33637e`.
Workflow `.github/workflows/regress-exhibition-seed17-track22.yml`.
Workflow commit `a413cec2a413aedace8acfb800121612e4944a1c`.
Authoritative run **`34865180548`**.

All four unchanged matrix jobs completed and failed closed at tracker v22. FastClip and seed v17 succeeded. v22 intentionally changed no tracking behaviour and relaxed no threshold.

Artifact IDs:
- Kiryu3 `10356563858`
- Kiryu6 `10357410404`
- Kiryu12 standard `10356433365`
- Kiryu12 varied `10355774470`

Artifact audit:
- Kiryu3: runtime 55.036s; failure `verified appearance-bank beam exhausted`; dead after native frame 18. Final dead step had 219 bank proposals, 0 predecessor expansions. Cumulative `_safe_state`: 4,768 calls / 497 rejects / 4,271 accepts. `_transition`: 4,271 calls / **0 rejects** / 4,271 accepts. Last best centers `[[997,409],[951,492],[964,589],[900,699],[975,819],[520,1016]]`.
- Kiryu6: runtime 54.333s; dead after native frame 20. Final dead step had 284 bank proposals, 0 expansions. `_safe_state`: 18,171 / 748 rejects / 17,423 accepts. `_transition`: 17,423 / **0 rejects** / 17,423 accepts. Last centers `[[930,448],[873,503],[1006,606],[952,742],[897,834],[921,843]]`.
- Kiryu12 standard: runtime 47.266s; dead after native frame 20. Final dead step had 144 bank proposals, 0 expansions. `_safe_state`: 26,692 / only 64 rejects / 26,628 accepts. `_transition`: 26,628 / **0 rejects** / 26,628 accepts. Last centers `[[851,386],[984,447],[983,496],[1054,561],[958,602],[706,771]]`.
- Kiryu12 varied: runtime 83.643s; dead after native frame 36. Final recorded bank proposal count was 0 and 0 expansions. `_safe_state`: 35,473 / 1,153 rejects / 34,320 accepts. `_transition`: 34,320 / **0 rejects** / 34,320 accepts. Last centers `[[878,400],[938,451],[707,811],[691,530],[978,586],[1093,666]]`.

Critical v22 conclusion: the existing v17 transition function is **not** causing these dead ends in any audited race; it rejected zero states. Cumulative safe-state rejection is also too coarse to explain the exact dead frame, especially Kiryu12 standard where only 64 of 26,692 total safe-state calls rejected. The next step must attribute each `_expand_predecessor` call and split `_safe_state` rejection categories without changing behaviour. Threshold relaxation remains unjustified.

## CURRENT candidate: v23 fine-grained rejection attribution diagnostic
File `track_exhibition_boats_v23.py`.
Implementation commit **`4a8df5f9974c92c65493f2cb228004ef9fcb6372`**.
Workflow `.github/workflows/regress-exhibition-seed17-track23.yml`.
Workflow commit **`5b1038e265cda0e71004bcdbf2710f0aa740ad29`**.
Authoritative run **`34872289293`** launched by push on Japan self-hosted runner.

v23 deliberately preserves v21 behaviour exactly. It adds:
- `_safe_state` rejection split: order / <=4px gap / frame edge / <20px duplicate / reverse corridor / unknown;
- transition accept/reject counters;
- one diagnostic record for every `_expand_predecessor` invocation with six candidate-list lengths, Cartesian state count, safe-state counter deltas, transition deltas, and output expansion count.
This should distinguish whether the final dead predecessor has viable candidate lists whose fleet combinations are rejected, or loses feasibility before fleet-state evaluation. `behavior_changed_from_v21=false`; no gate or score was changed.

At this handoff update run `34872289293` was active: Kiryu12 varied had entered tracker v23 and the remaining three matrix jobs were queued. Do not launch a duplicate run while this one is legitimately active.

## v23 exact restart point
1. Inspect run `34872289293` all four jobs and artifacts when complete.
2. Read `exhibition_tracking_v23.json`; focus on the final expansion-call records preceding failure.
3. Record which exact safe-state categories dominate at dead calls and whether candidate-list lengths / Cartesian states are already zero or non-zero before `_safe_state`.
4. If candidate lists disappear before `_safe_state`, instrument proposal/merge source loss (global immutable, predecessor-local immutable, verified bank, reachability/dedup) rather than modifying safety gates.
5. If one fleet-safety category dominates only at the dead calls, inspect the physical centers/proposals and determine whether it is correctly preventing an identity collision. Do not relax it just to pass.
6. Transition rejection should remain zero under unchanged v21 behaviour; if not, audit the exact per-call evidence before any algorithm change.
7. Once the failure locus is established, make the next principled tracker change; likely direction remains stronger multi-frame identity/trajectory likelihood or proposal continuity, not threshold relaxation.
8. Only if one unchanged seed+tracker combination passes all four physically sane with total latency <=60 sec may `run_exhibition_ses_live_local.py` be updated.
9. After a four-sample technical pass, perform at least one Japan self-hosted end-to-end live-style validation before calling live-ready.
10. Update this handoff after every meaningful result/design change with exact commit SHA, Run ID and artifact/log evidence.

## Production wrapper
`run_exhibition_ses_live_local.py` remains old seed v1 + tracker v3. DO NOT update until an unchanged seed+tracker passes the full technical matrix with sane identity/geometry and <=60 sec.

## Live-ready milestone
Before user notification as complete:
- multiple independent September samples including varied entry;
- automatic acquisition + seed + tracker only, no manual/race-specific edits;
- accepted with sane identity/geometry and fail-closed retained;
- ideally <=30 sec, maximum <=60 sec;
- `run_exhibition_ses_live_local.py` updated to the validated pipeline;
- >=1 self-hosted end-to-end live-style success.
Prefer 10+ samples before treating SES as stable/predictive. SES remains an attack/head-support feature candidate, not direct finishing-order rank.
