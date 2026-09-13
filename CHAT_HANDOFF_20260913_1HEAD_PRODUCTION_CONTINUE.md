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

# 6. v334 v332 bootstrap/month-block robustness audit — COMPLETE / REPORTED NEXT
Pre-work handoff commit `7d4900021128c22dd1e08d95cca8cd473bd5c9c7`.
Implementation `e20c352b5998d66d712f5112d55602fa29103408`; workflow `ee54e08fe5f37db1d7cb7ee5a44c0c9e9e47d34e`.
Run **34776500418** SUCCESS, Job **103775463224**, Artifact **10323272716**, artifact SHA256 `439ea86e3f29759db9a182414872a3ff505f37adbc7a9739080b82ea3a5d0df9`.
Identity reproduced: pooled v332 PASS **96R / head83 / exact3 45** = Feb-Jul 86R/head76/exact341 + August10R/head7/exact34. No retuning; September unread.

Deterministic bootstrap setup:
- RNG seed `33420260914`
- 20,000 race-level within-month bootstrap draws
- 20,000 month-block bootstrap draws across Feb-Aug months

Race-level bootstrap:
- PASS head rate median **86.46%**, 95% interval **80.21–92.71%**.
- PASS exact3 rate median **46.88%**, 95% interval **37.50–56.25%**.
- head lift median **+2.75pp**, 95% interval **-5.00 to +10.00pp**.
- exact3 lift median **+6.88pp**, 95% interval **-3.88 to +17.83pp**.
- P(head lift >0) **0.76125**.
- P(exact3 lift >0) **0.89220**.
- P(both lifts >0) **0.70130**.
- P(head lift <= -5pp) **0.02525**.
- P(exact3 lift <= -5pp) **0.01485**.

Month-block bootstrap:
- PASS head rate median **86.54%**, 95% interval **80.00–92.39%**.
- PASS exact3 rate median **46.88%**, 95% interval **36.76–56.57%**.
- head lift median **+2.63pp**, 95% interval **-3.16 to +7.91pp**.
- exact3 lift median **+6.85pp**, 95% interval **-2.40 to +15.45pp**.
- P(head lift >0) **0.81830**.
- P(exact3 lift >0) **0.91255**.
- P(both lifts >0) **0.80225**.
- P(head lift <= -5pp) **0.00450**.
- P(exact3 lift <= -5pp) **0.00020**.

Predeclared diagnostic label: **ROBUST_PROVISIONAL**.
Interpretation:
- v332's advantage survives month-composition resampling more often than not and satisfies the predeclared robustness rule.
- August weakness is therefore more consistent with ordinary small-sample/month variation than with a clearly fragile selector.
- Uncertainty still exists: both 95% lift intervals include 0, so this is not proof of a positive true effect.
- However severe underperformance probabilities are low, especially in month-block resampling.
- v332 should remain the leading provisional candidate; do not redesign it merely because of August 7/10.
- September outcomes remain unread. No retuning.

# 7. Exact next resume point — REPORT v334 BEFORE ANY v335/SEPTEMBER EVALUATION
After reporting v334 to user, recommended next unit is to freeze the v332 rule/parameters on Feb-Aug and build a **September inference-only adapter** that can produce selections without reading September outcomes. Only after the inference output is frozen should September outcomes be opened for the final untouched evaluation. Do not read September outcomes before that freeze.