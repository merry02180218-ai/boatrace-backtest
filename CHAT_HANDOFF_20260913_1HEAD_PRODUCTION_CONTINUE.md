# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state
Latest GitHub wins over old chat memory/stale handoff text.
Mandatory pattern: handoff update -> work -> result append -> next work handoff update.

# 1. Frozen production stack — DO NOT ALTER
- HEAD v308
- SECOND v317 OUTER_L2_1
- THIRD v318 DROPSTART_T0.1
- 3-ticket policy v320 HYBRID alpha=.70
- frozen regression 345 selected / 290 boat1 wins / 139 exact3
- v308 q=.980, opponent mass>=.375, head cutoff=0.8073405637
- v308 is true PRE; same-race exhibition is post-PRE only.
- do not modify v308/v317/v318/v320/v323.

# 2. Causality / evaluation rules
- July/August 2026 may be used for model learning/tuning.
- September outcomes remain UNREAD and reserved as final untouched evaluation.
- current-race exhibition is post-PRE only and result-blind at prediction time.
- missing current exhibition inputs fail closed.
- no meet_* unless separately audited.

# 3. v332 FORMALLY ADOPTED
- family ATTACK_ENV_SOFT; env_w=.1; q=.65
- Feb-Aug PASS 96R / head83=86.46% / exact3 45=46.88%; 13.7 races/month.
- September still unread.

# 4. Volume research through v336
v335/v336 changed only exhibition-stage q while keeping v308 PRE identity fixed. v336 Run 34777511185 SUCCESS, Job 103778214979, Artifact 10323958215.
- q=.65 96 PASS=13.7/month, head86.46%, exact346.88%
- q=.50 138=19.7/month, head86.96%, exact344.93%
- q=.40 164=23.4/month, head85.98%, exact343.29%
- q=.35 176=25.1/month, head84.66%, exact343.18%
- q=.30 192=27.4/month, head85.94%, exact341.15%
- q=.25 207=29.6/month, head85.99%, exact339.61%
Current adopted production remains q=.65.

# 5. v337 PRE-WORK — HEAD CUTOFF ONLY RELAXATION
User asks what happens if only the PRE head-probability model is loosened. This is deliberately different from v335/v336.

Exact work:
1. Keep adopted exhibition-stage v332 exactly fixed: ATTACK_ENV_SOFT, env_w=.1, q=.65.
2. Keep SECOND v317, THIRD v318 and v320 tickets fixed.
3. Change only v308 PRE head cutoff from 0.8073405637 downward over a predeclared grid: 0.80, 0.79, 0.78, 0.77, 0.75 (plus current 0.8073405637 anchor).
4. Reconstruct the broader PRE candidate universe causally from the v308 pipeline rather than filtering the already-selected 345 rows. This is mandatory because lower head cutoff can add races not present in the frozen 345 identity.
5. For each cutoff, run the same downstream v317/v318/v320 + fixed v332 q=.65 exhibition PASS logic on the newly admitted races, using result-blind current exhibition data and the same readiness rules.
6. Evaluate Feb-Aug with July/Aug allowed for development, but no September outcomes. Report PRE count, final PASS count/month, head rate and exact3 rate; separately report quality of races newly admitted versus the current cutoff.
7. Do not change the formally adopted production cutoff in this work unit.

Success criteria:
- current cutoff must reproduce the known v332 Feb-Aug identity: 96 PASS/head83/exact345 after final q=.65;
- only the head cutoff changes across variants;
- quantify whether relaxing PRE head probability adds more usable final PASS races than relaxing exhibition q, without unacceptable head/exact3 dilution.

Failure fallback:
- if the broader PRE universe cannot be reconstructed with identical current-cutoff regression, stop and fix reconstruction/identity only; do not report incomparable numbers.

# 6. 2026-09-14 PRE-WORK UPDATE — CANONICAL WAKU10 IMPACT AUDIT FIRST
User explicitly requested that the newly updated Waku10 lineage be audited for its impact on the 1-head model before continuing v337. This section is written BEFORE starting that work.

Observed repository change to audit:
- canonical historical Waku10 materialization work was added on 2026-09-14;
- backtest.py now prefers repository-local `data/programs/waku10/` files when present, instead of always relying on the external BoatraceCSV source;
- therefore historical PRE features/candidate identity may change where the previous Waku10 source was missing, restored, or different;
- exhibition tracker v10 is a separate SES/video-tracking experiment and is NOT to be adopted into the 1-head production stack merely because its version name is v10.

Exact work to execute now, in this order:
1. Audit the canonical Waku10 materialization commits/files and identify the exact historical dates/races whose Waku10 inputs changed or became newly available.
2. Audit v308/v323 row-generation and feature-loading paths to determine whether and where the 1-head PRE pipeline consumes Waku10 and whether the new local-preferred source reaches the current v308 reconstruction.
3. Reconstruct the current-cutoff (`0.8073405637`) Feb-Aug PRE universe with canonical Waku10 while preserving all other frozen logic.
4. Compare old/frozen versus canonical-Waku10 inputs and report: changed Waku10 rows/races, changed 1-head PRE scores, cutoff-crossing races, PRE additions/removals, and any downstream PASS identity changes.
5. Re-run the fixed v332 downstream stack (v317/v318/v320 + ATTACK_ENV_SOFT env_w=.1 q=.65) on the canonical-Waku10 reconstruction.
6. Regression gate: explicitly test whether the canonical-Waku10 anchor still reproduces 96 PASS / 83 head / 45 exact3. If it does not, do NOT silently proceed as though identities are comparable; isolate and document the changed races and causal source difference first.
7. Keep September outcomes UNREAD throughout this audit. September source availability/coverage may be inspected only without reading race outcomes if technically necessary.
8. Only after the Waku10 impact is quantified and the anchor status is understood, execute the predeclared v337 head-cutoff sweep on the correct canonical-Waku10 universe.
9. Compare v337 volume/quality against the earlier v335/v336 exhibition-q relaxation.
10. Do not alter the formally adopted production model during this audit/research unit.

Completion requirement:
- after the work finishes, append actual commit SHA(s), Actions Run/Job/Artifact IDs, Waku10 changed-row/race counts, anchor reproduction result, per-cutoff v337 results, interpretation, and the exact next resume point to THIS handoff file before reporting completion to the user.
- if blocked/failing, append the actual failure/blocker and exact restart point here rather than leaving the handoff at the pre-work plan.

# 7. 2026-09-14 WORK RESULT — WAKU10 IMPACT AUDIT COMPLETE; v337 CI IN PROGRESS

## Waku10 audit result
- Canonical historical Waku10 materializer covers 2025-12-01 through 2026-08-31 and its first full run restored/validated 100% monthly coverage; 2026-07-18 was 180/180 and 2026-07-19 was 192/192. The first run's only final failure was a non-fast-forward push conflict after successful restoration/validation.
- `backtest.py` now prefers repository-local `data/programs/waku10/` where present, but the frozen 1-head v308 HEAD/PRE path does NOT consume Waku10.
- v308 starts from v294 TRUE PRE. v294 reconstructs current-race PRE from race cards plus strictly prior-day player/history state; v221 prior history uses race cards, exhibition history and results strictly after the scoring point; v303/v307 add only causal features derived from that existing PRE/history frame.
- Therefore canonical Waku10 has no causal input edge into v308 p_head or v337 HEAD-cutoff selection.
- Impact on the frozen/current 1-head HEAD/PRE path due solely to Waku10: changed input rows=0; changed p_head rows=0; head-cutoff crossings=0; PRE additions/removals=0; downstream v332 identity changes attributable solely to Waku10=0.
- September outcomes remain unread.

## v337 implementation started
- implementation commit: `a6c0a39088a40c9a2c7236f71ec6bc3539bf2dd2` (`run_v337_1head_head_cutoff_volume.py`).
- workflow commit: `886483907e1f036c2ab15aa4ce2121fd79ec8991` (`.github/workflows/v337-1head-head-cutoff-volume.yml`).
- v337 reconstructs a broader PRE candidate universe down to p_head=.75 rather than filtering only the frozen selected 345 rows; Jul/Aug uses the full causal v321 head universe and frozen SECOND/THIRD artifacts; Feb-Jun uses the full v308 prediction universe plus frozen v317/v318/v320 ticket machinery.
- fixed exhibition policy remains ATTACK_ENV_SOFT env_w=.1 q=.65.
- hard regression gate remains 96 PASS / 83 head / 45 exact3 at cutoff 0.8073405637; if that fails, variant comparison is invalid and reconstruction only must be fixed.

## Current Actions state at this handoff update
- Run `34779669216` — `v337 1-head head-cutoff-only volume audit` — IN PROGRESS.
- current Job `103784237186` (`prepare`) is running `Prepare full Jul-Aug causal head universe`.
- no v337 result/Artifact exists yet at this exact update because the prerequisite causal PRE reconstruction job is still executing.
- this is not treated as v337 completion; production remains unchanged.

Exact next resume point:
1. Inspect Run `34779669216` / Job `103784237186` to completion.
2. If prepare succeeds, inspect second/base-third/third and final audit jobs, then artifact.
3. If final anchor is not exactly 96/83/45, stop cutoff interpretation and fix reconstruction identity only.
4. If anchor passes, record cutoff 0.8073405637/0.80/0.79/0.78/0.77/0.75 PRE/PASS/month/head/exact3 plus newly admitted quality and compare against v336 exhibition-q expansion.
5. Append actual final Run/Job/Artifact/results or blocker to THIS file before reporting v337 complete.
6. Do not start v338 before reporting v337 once.

# 8. 2026-09-14 PRE-WORK UPDATE — v337 ANCHOR DRIFT / WAKU10 RE-AUDIT
User suspects the 96 -> 88 PASS anchor drift may have been caused by the Waku10 rewrite. Treat that as an open hypothesis, despite the earlier static dependency audit.

Known failure to investigate:
- Run `34779669216` final audit Job `103785686708` failed the hard regression gate.
- observed anchor: 88 PASS / 76 head / 43 exact3.
- expected anchor: 96 PASS / 83 head / 45 exact3.
- Artifact `10324652726` was produced despite the failed audit.

Exact work now:
1. Inspect the failed v337 artifact and identify the exact 8 PASS races missing versus the known v332 96-race anchor.
2. Trace each missing race backward through candidate PRE, SECOND/THIRD/ticket readiness, and current exhibition feature/readiness stages.
3. Compare relevant source inputs before and after the canonical Waku10 rewrite/materialization commits, including any indirect effects through shared `backtest.py` fetch behavior or historical helper functions.
4. Do not assume the earlier `Waku10 dependency = NONE` conclusion is sufficient; test the actual missing identities against old/new source behavior.
5. If Waku10 caused the drift, quantify the exact changed races/fields and restore a reconstruction method that reproduces the frozen anchor without changing production logic.
6. If Waku10 did not cause it, identify the true reconstruction mismatch and fix only the v337 reconstruction/audit harness.
7. Keep September outcomes UNREAD and do not interpret relaxed cutoffs until the anchor is exactly 96/83/45 again.
8. After diagnosis/fix, append exact missing races, root cause, commits, rerun IDs and final anchor status to THIS handoff before reporting completion.

# 9. 2026-09-14 PRE-WORK RESUME — CANONICAL ANCHOR DIAGNOSTIC
User instructed to continue. Before any further analysis, resume from the actual latest GitHub state.

Exact work now:
1. Inspect canonical-anchor diagnostic Run `34781252937` / Job `103788554432` to completion.
2. Retrieve its artifact/log output and record the canonical current-state v332 anchor count/head/exact3 and full PASS race identity.
3. Compare that identity directly against the failed v337 anchor (88/76/43) to isolate the exact missing races.
4. For each missing race, identify the first stage where v337 diverges: PRE candidate, SECOND/THIRD/ticket readiness, exhibition feature readiness, ATTACK_ENV_SOFT score, or q=.65 threshold.
5. Re-test the Waku10 hypothesis against actual missing-race inputs and commit chronology; do not infer causation from timing alone.
6. If the canonical v332 anchor remains 96/83/45, fix only the v337 reconstruction harness until it reproduces that exact anchor before interpreting any relaxed-cutoff result.
7. If canonical v332 itself changed, stop and isolate the source-data/model-input change before any v337 comparison.
8. Keep September outcomes UNREAD and do not alter frozen production files.
9. Append the actual diagnostic result, exact missing race identities/root cause, any fix commit, rerun IDs/artifact IDs, and exact next resume point to THIS file before reporting completion.