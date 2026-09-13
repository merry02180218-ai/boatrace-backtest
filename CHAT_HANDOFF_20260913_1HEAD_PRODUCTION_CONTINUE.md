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

# 5. v335 — PRE-WORK DECLARATION: INCREASE PASS VOLUME WITHOUT CHANGING SIGNAL FAMILY
User says ~14 races/month is too few and asks whether more races can be selected.

Exact work:
1. Keep the v332 signal family and env weight fixed: `ATTACK_ENV_SOFT`, `env_w=0.1`.
2. Change only the quantile threshold to compare `q = 0.65` (adopted reference), `0.60`, `0.55`, `0.50`, and `0.45`.
3. Reproduce the exact same causal evaluation scheme as v332/v333:
   - Feb-Jul: leave-one-month-out OOF fitting; held-out month labels never used to fit its threshold.
   - August: fit on Feb-Jul only and evaluate August once.
4. For every q report pooled Feb-Aug PASS count, races/month, pass fraction, head rate, exact3 rate, head/exact3 lifts versus matched monthly baseline, and each month's PASS count/rates.
5. Report incremental added-race quality relative to q=.65: the races newly admitted by each relaxed q, with head and exact3 rates. This answers whether extra volume is useful or merely dilutive.
6. Do not search env_w, family, or any new feature. This is a one-dimensional capacity/volume audit only.
7. September outcomes remain unread.

Decision guide (diagnostic, user decides adoption):
- Prefer the loosest q that materially increases volume while keeping pooled head rate >=83% and exact3 rate >=42%, with no obvious single-month catastrophic collapse attributable to the added band.
- Do not automatically replace adopted q=.65; report tradeoff first.

Success criteria:
- q=.65 reproduces 96 PASS / 83 head / 45 exact3 exactly;
- relaxed variants give exact monthly volume/quality tradeoffs;
- September unread.

Failure fallback:
- identity mismatch => stop and fix reconstruction only;
- if added bands are clearly poor, keep q=.65 formally adopted and investigate a separate secondary route later instead of lowering the main threshold.

Exact next resume point:
- implement `run_v335_1head_v332_volume_expansion.py` and workflow; run Actions; append results; report once before any v336.