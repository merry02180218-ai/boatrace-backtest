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

# 6. v336 deeper threshold relaxation — COMPLETE / REPORT BEFORE v337
Pre-work commit f7480a1ed80494658a7eb0c29cad9a442e4c6034.
Implementation commit 6a4b041b1ac6bd70d343b16a198a171e419513e0.
Workflow commit 8ebaebf7b6f3df8805f67e4e7524d00962f9de12.
Run **34777511185** SUCCESS, Job **103778214979**, Artifact **10323958215**, artifact SHA256 `0c4b5533963cfeb501504a4f4b0b5cef32a6121f044a27d37ecb3b0a642977ca`.
Identity checks passed: q=.65 = 96/head83/exact345; q=.50 = 138/head120/exact362. September outcomes remained unread.

Deeper q tradeoff:
- q=.65: **96 PASS = 13.7/month**, head **86.46%**, exact3 **46.88%**, lifts +2.71pp / +6.88pp.
- q=.50: **138 = 19.7/month**, head **86.96%**, exact3 **44.93%**, lifts +3.21pp / +4.93pp.
- q=.45: **151 = 21.6/month**, head **86.75%**, exact3 **43.05%**, lifts +3.00pp / +3.05pp.
- q=.40: **164 = 23.4/month**, head **85.98%**, exact3 **43.29%**, lifts +2.23pp / +3.29pp.
- q=.35: **176 = 25.1/month**, head **84.66%**, exact3 **43.18%**, lifts +0.91pp / +3.18pp.
- q=.30: **192 = 27.4/month**, head **85.94%**, exact3 **41.15%**, lifts +2.19pp / +1.15pp.
- q=.25: **207 = 29.6/month**, head **85.99%**, exact3 **39.61%**, lifts +2.24pp / -0.39pp.

Adjacent newly admitted bands:
- .65 -> .50 adds 42R: head 88.10%, exact3 40.48%.
- .50 -> .45 adds 13R: head 84.62%, exact3 23.08%.
- .45 -> .40 adds 13R: head 76.92%, exact3 46.15%.
- .40 -> .35 adds 12R: head 66.67%, exact3 41.67%.
- .35 -> .30 adds 16R: head 100.00%, exact3 18.75%.
- .30 -> .25 adds 15R: head 86.67%, exact3 20.00%.

Interpretation:
- q=.40 gives **23.4 races/month** while retaining head ~86% and exact3 ~43.3%; this is the strongest high-volume candidate in the current one-dimensional relaxation.
- q=.35 reaches ~25/month but head lift shrinks to only +0.91pp and the incremental .40->.35 band has only 66.67% head, so caution increases there.
- q=.30 reaches 27.4/month but exact3 drops to 41.15%; the incremental .35->.30 band is head-strong but ticket-poor (18.75% exact3).
- q=.25 reaches 29.6/month but exact3 falls below baseline (lift -0.39pp), so it is too loose for the current 3-ticket objective.
- Current formally adopted production remains q=.65 until user explicitly approves replacement.

# 7. Exact next resume point
Report v336. If user wants a higher-volume replacement, q=.40 is the strongest current candidate for a monthly-stability/bootstrap audit; q=.50 remains the cleaner quality-volume compromise. Do not read September outcomes until the replacement threshold is explicitly frozen.