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

# 3. Key research through v331
- v320 `HYBRID alpha=.70`: **139/345=40.29%** exact3.
- v321 Jul/Aug base: **55R/head45/exact3 21**.
- v329 June PASS 17R/8 exact3=47.06%, head16/17=94.12%, but fixed-v329 Jul+Aug collapsed.
- v331 Run **34773137181**: `attack_core` materially more stable than `env_pair`; hard attack+env AND was main reversal mechanism; `turn_core` weak/unstable.

# 4. v332 attack-first redesign — COMPLETE / REPORTED
Implementation `db15c03df9f2d551d6ac1f724433401be5c155c0`; workflow `17db56410c92729df34c3c680f360d98b5781fbb`.
Run **34774010225** SUCCESS, Job **103768650973**, Artifact **10323285065**.
Identity **400 rows / 335 head / 160 exact3** Feb-Aug; September unread.
Chosen config: `ATTACK_ENV_SOFT`, env_w=.1, q=.65.
Feb-Jul OOF PASS **86R**, exact3 **41/86=47.67%**, head **76/86=88.37%**, PASS fraction **24.02%**, exact3 lift +8.01pp, head lift +4.29pp.
August one-shot PASS **10R / exact3 4=40.00% / head7=70.00%**, fraction23.81%; strict v332 criterion said unsupported because head fell >5pp below August baseline.
User correctly flagged that n=10 may make this ordinary month-to-month variance; v333 audited that before redesign.

# 5. v333 v332 monthly variance/stability audit — COMPLETE / REPORTED
Pre-work handoff commit `edcf0192942cc6c1a8967d34e842c6730e1632ce`.
Implementation `54c3a63a3b54c4f9eae8b2223c083431a35247c4`; workflow `a15835414285111bbb22b5f2333217a6a9580ca8`.
Run **34774493891** SUCCESS, Job **103769983424**, Artifact **10322953353**, artifact SHA256 `7349220630cd0e9e3350c81949b79da259637787cb6cfd28e55ac2d862e12092`.
Exact v332 reproduction succeeded:
- Feb-Jul OOF **86R / head76=88.37% / exact3 41=47.67%**.
- pooled Wilson95: head **79.90–93.56%**, exact3 **37.45–58.10%**.
- August PASS **10R / head7=70.00% / exact3 4=40.00%**.
- August Wilson95: head **39.68–89.22%**, exact3 **16.82–68.73%**.
- August vs preceding pooled OOF two-sided binomial p-values: **head p=0.1009**, **exact3 p=0.7566**.
- conclusion: **INSUFFICIENT_EVIDENCE_MONTHLY_VARIANCE_PLAUSIBLE**.
- therefore do not discard v332 on August alone; treat as strong provisional candidate.

# 6. v334 — PRE-WORK DECLARATION: v332 BOOTSTRAP / MONTH-BLOCK ROBUSTNESS AUDIT
Current position: v333 says August weakness is not strong evidence of structural failure. Before freezing v332 for September inference, quantify how robust the observed Feb-Aug advantage is to race-level and month-level resampling without retuning.

Exact work:
1. **Do not alter v332 config.** Freeze `ATTACK_ENV_SOFT`, env_w=.1, q=.65.
2. Reconstruct exact v332 selections used in v333: Feb-Jul month-OOF + August trained on Feb-Jul. Assert pooled selection identity **96 PASS = 86 OOF + 10 August**, with Feb-Jul head76/exact341 and August head7/exact34.
3. Build paired month-level table containing baseline and PASS head/exact3 rates and lifts for Feb-Aug.
4. Perform deterministic Monte Carlo bootstrap with fixed RNG seed:
   - race-level bootstrap within each month, preserving month and PASS membership, estimating pooled head/exact3 rates and lifts;
   - month-block bootstrap resampling the 7 months with replacement, aggregating original month totals, estimating robustness to month composition.
5. Report 2.5/50/97.5 percentiles for PASS head rate, PASS exact3 rate, head lift, exact3 lift under both bootstrap schemes.
6. Report probabilities that pooled head lift >0, exact3 lift >0, both >0, and probabilities of material underperformance (head lift <= -5pp, exact3 lift <= -5pp).
7. Include leave-one-month-out pooled summaries for Feb-Aug: remove each month in turn and report pooled PASS/base metrics and lifts. This is diagnostic only and must not choose a new config.
8. **No September outcomes, no threshold search, no retraining based on bootstrap results.**

Interpretation rule:
- `ROBUST_PROVISIONAL` if month-block P(head lift>0) >= .70, P(exact3 lift>0) >= .70, and neither material-underperformance probability exceeds .25.
- `MIXED_UNCERTAIN` if these are not met but no material-underperformance probability exceeds .50.
- `FRAGILE` if either material-underperformance probability > .50.
This is a diagnostic label only, not automatic production promotion.

Success criteria:
- exact v332/v333 identities reproduced;
- bootstrap outputs deterministic and saved;
- result answers whether v332 advantage survives plausible race/month resampling;
- September remains unread.

Failure fallback:
- any identity mismatch => stop and fix reconstruction only;
- if month count makes month-block intervals extremely wide, report underpowered rather than overinterpreting.

Exact next resume point:
- implement `run_v334_1head_v332_bootstrap_robustness.py` and workflow; run Actions; append exact Run/Job/Artifact and metrics here; report v334 once before any v335 or September evaluation.