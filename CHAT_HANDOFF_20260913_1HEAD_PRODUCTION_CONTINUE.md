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
- family ATTACK_ENV_SOFT
- env_w=.1
- q=.65
- Feb-Aug PASS 96R / head83=86.46% / exact3 45=46.88%
- 13.7 races/month
- September still unread.

# 4. Research lineage
- v331: attack_core more stable than env_pair; hard env AND harmful.
- v332 Run 34774010225
- v333 Run 34774493891
- v334 Run 34776500418

# 5. v335 volume expansion COMPLETE
Run 34777110285, Job 103777132353, Artifact 10323577430.
Same ATTACK_ENV_SOFT/env_w=.1, only q changed:
- q=.65: 96 PASS = 13.7/month, head 86.46%, exact3 46.88%
- q=.60: 111 = 15.9/month, head 85.59%, exact3 45.05%
- q=.55: 119 = 17.0/month, head 86.55%, exact3 43.70%
- q=.50: 138 = 19.7/month, head 86.96%, exact3 44.93%
- q=.45: 151 = 21.6/month, head 86.75%, exact3 43.05%
Current adopted production remains q=.65 until explicitly replaced.

# 6. v336 PRE-WORK — deeper threshold relaxation
User asks to see data with q loosened further than .45.
Exact work:
1. Keep ATTACK_ENV_SOFT and env_w=.1 fixed.
2. Evaluate q=.40,.35,.30,.25, retaining .65,.50,.45 anchors.
3. Use same causal evaluation as v335: Feb-Jul leave-one-month-out OOF; August trained only on Feb-Jul.
4. Report pooled Feb-Aug PASS count, races/month, head rate, exact3 rate and lifts for each q.
5. Report newly admitted race quality versus q=.65 and between adjacent q steps.
6. Save monthly metrics and note any clear monthly deterioration.
7. Diagnostic only; do not change adopted q=.65 in this work unit.
8. September outcomes remain unread.
Success criteria: q=.65 must reproduce 96/head83/exact3 45 and q=.50 must reproduce 138/head120/exact3 62. Quantify where added volume begins to dilute quality.
Failure fallback: identity mismatch => fix reconstruction only.
Next resume point: implement run_v336_1head_deeper_volume_expansion.py and workflow, run Actions, append results here, then report before v337.