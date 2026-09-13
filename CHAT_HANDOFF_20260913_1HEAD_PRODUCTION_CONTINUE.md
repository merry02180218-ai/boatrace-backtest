# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state
Latest GitHub wins over old chat memory/stale handoff text.
Mandatory pattern: **handoff update -> work -> result append -> next work handoff update**.
Before every work unit/code change/restart record current position, exact work, success criteria, failure fallback. After every work unit record actual work, commit SHA(s), Actions Run ID/status, metrics/results, exact next resume point.

# 1. Frozen production stack — DO NOT ALTER
- HEAD v308
- SECOND v317 `OUTER_L2_1`
- THIRD v318 `DROPSTART_T0.1`
- 3-ticket policy v320 `HYBRID alpha=.70`
- exactly 3 trifecta tickets per selected race
- frozen regression **345 selected / 290 boat1 wins / 139 exact3**
- v308 q=.980, opponent mass>=.375, head cutoff=0.8073405637
- v308 is true PRE; same-race exhibition is post-PRE only.
- composite odds = `1/(1/o1+1/o2+1/o3)`.
- do not modify v308/v317/v318/v320/v323.

# 2. Causality / evaluation rules
- July/August 2026 may be used for model learning/tuning.
- September outcomes remain **UNREAD** and reserved as the final untouched evaluation period.
- no same/later-race result, payout, future/backfill contamination in race-time features.
- current-race exhibition is post-PRE only and result-blind at prediction time.
- missing current exhibition inputs fail closed.
- no `meet_*` unless separately audited.
- neutral 0.5 defaults are not proof raw metric existed.

# 3. v332 — FORMALLY ADOPTED BY USER ON 2026-09-14
User explicitly instructed: **"とりあえず正式採用で"**.
Production direct-before-start selector is therefore v332 unless a later explicitly approved volume-expanded variant replaces it:
- family `ATTACK_ENV_SOFT`
- `env_w=0.1`
- `q=0.65`
- Feb-Jul OOF PASS **86R / head76=88.37% / exact3 41=47.67%**
- August one-shot PASS **10R / head7=70.00% / exact3 4=40.00%**
- pooled Feb-Aug observed PASS **96R / head83=86.46% / exact3 45=46.88%**
- average PASS volume **96/7 = 13.7 races/month**.
- v333: August weakness plausibly ordinary monthly variance.
- v334: predeclared diagnostic label **ROBUST_PROVISIONAL**; month-block P(head lift>0)=0.8183, P(exact3 lift>0)=0.91255, P(both>0)=0.80225; severe <=-5pp downside probabilities 0.0045/0.0002.
Formal adoption does NOT authorize reading September outcomes yet.

# 4. Key research lineage
- v320 `HYBRID alpha=.70`: 139/345=40.29% exact3.
- v331: `attack_core` stable, hard env AND harmful, turn_core unstable.
- v332 Run **34774010225**, Job **103768650973**, Artifact **10323285065**.
- v333 Run **34774493891**, Job **103769983424**, Artifact **10322953353**.
- v334 Run **34776500418**, Job **103775463224**, Artifact **10323272716**.

# 5. v335 volume expansion audit — COMPLETE / REPORT BEFORE ANY v336
Pre-work handoff commit `1578816cf916920903ed4293f708bfb92acb43fd`.
Implementation `80ea9433d9aee5ea1d8522cc928d1a76b9c1f0d8`; workflow `6a008d20f5da7eb882403d20a7422bd412a4f8b6`.
Run **34777110285** SUCCESS, Job **103777132353**, Artifact **10323577430**, artifact SHA256 `bdd819c79f878679e124b9ef6bc571a8069540b9e8c85e66e0ea007a6e65bd3c`.
September outcomes remained unread.

Exact causal volume tradeoff (same ATTACK_ENV_SOFT, env_w=.1; only q changed):
- `q=.65` adopted reference: **96 PASS = 13.7/month**, head **83/96=86.46%**, exact3 **45/96=46.88%**, lifts head +2.71pp / exact3 +6.88pp.
- `q=.60`: **111 PASS = 15.9/month**, head **95/111=85.59%**, exact3 **50/111=45.05%**, lifts +1.84pp / +5.05pp.
- `q=.55`: **119 PASS = 17.0/month**, head **103/119=86.55%**, exact3 **52/119=43.70%**, lifts +2.80pp / +3.70pp.
- `q=.50`: **138 PASS = 19.7/month**, head **120/138=86.96%**, exact3 **62/138=44.93%**, lifts +3.21pp / +4.93pp.
- `q=.45`: **151 PASS = 21.6/month**, head **131/151=86.75%**, exact3 **65/151=43.05%**, lifts +3.00pp / +3.05pp.

Newly admitted races versus q=.65:
- q=.60 adds 15R: head **80.00%**, exact3 **33.33%**.
- q=.55 adds 23R: head **86.96%**, exact3 **30.43%**.
- q=.50 adds 42R: head **88.10%**, exact3 **40.48%**.
- q=.45 adds 55R: head **87.27%**, exact3 **36.36%**.

Interpretation:
- The surprising best volume/quality balance is **q=.50**, not .60/.55. It raises volume from 13.7 to **19.7 races/month (+43.8%)** while pooled head improves slightly from 86.46% to **86.96%** and exact3 declines modestly from 46.88% to **44.93%**.
- The 42 newly admitted q=.50-vs-.65 races are not weak on head survival: **88.10% head**, with **40.48% exact3**. This suggests q=.50 is a credible volume-expanded production candidate rather than simple dilution.
- q=.45 reaches 21.6/month but added-band exact3 falls to 36.36%, so q=.50 is the cleaner stopping point from this one-dimensional audit.
- Current formally adopted production selector remains **q=.65** until user explicitly approves replacement. Do not silently switch to q=.50.

# 6. Exact next resume point
Report v335 to user. If user approves more volume, the natural replacement candidate is **v332 family with q=.50**. Before replacing production, recommended one last check is q=.50 monthly stability / bootstrap using the exact v334 framework; September remains unread until the final chosen selector is frozen.