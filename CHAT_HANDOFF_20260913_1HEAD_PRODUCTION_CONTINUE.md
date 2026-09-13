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

Exact next resume point:
- audit v308/v323 row-generation entry points, implement v337 head-cutoff-only sweep, run Actions, append actual commits/Run/Job/Artifact/results here, then report once before any v338.