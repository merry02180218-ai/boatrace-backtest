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
User correctly flagged that n=10 may make this ordinary month-to-month variance; v333 audits that before any redesign.

# 5. v333 v332 monthly variance/stability audit — COMPLETE / REPORTED NEXT
Pre-work handoff commit `edcf0192942cc6c1a8967d34e842c6730e1632ce`.
Implementation `54c3a63a3b54c4f9eae8b2223c083431a35247c4`; workflow `a15835414285111bbb22b5f2333217a6a9580ca8`.
Run **34774493891** SUCCESS, Job **103769983424**, Artifact **10322953353**, artifact SHA256 `7349220630cd0e9e3350c81949b79da259637787cb6cfd28e55ac2d862e12092`.
Exact v332 reproduction succeeded:
- Feb-Jul OOF **86R / head76=88.37% / exact3 41=47.67%**.
- pooled Wilson95: head **79.90–93.56%**, exact3 **37.45–58.10%**.
- August PASS **10R / head7=70.00% / exact3 4=40.00%**.
- August Wilson95: head **39.68–89.22%**, exact3 **16.82–68.73%**.
- August vs preceding pooled OOF two-sided binomial p-values: **head p=0.1009**, **exact3 p=0.7566**.
- August lifts vs its own baseline: head **-10.95pp**, exact3 **-2.86pp**.
- Prior Feb-Jul nonnegative monthly lifts: head **4/6**, exact3 **4/6**.
- Empirical add-one absolute-lift extremeness: head **0.143**, exact3 **0.857**.
- With n=10, one result moves a rate by exactly **10 percentage points**, two results by 20pp.

Conclusion:
- **INSUFFICIENT_EVIDENCE_MONTHLY_VARIANCE_PLAUSIBLE**.
- The August 7/10 head result is weaker than preceding pooled performance, but not statistically unusual enough on this sample to call a structural break.
- The August 4/10 exact3 result is very consistent with ordinary sampling variation.
- Therefore **do not discard v332 on August alone**. Treat v332 as a strong provisional candidate whose strict August fail flag was likely too harsh for n=10.
- This is not proof v332 is correct; sample is underpowered and p>0.05 is not equivalence.
- September outcomes remain unread. No retuning was performed.

# 6. Exact next resume point — REPORT v333 BEFORE v334
After reporting v333 to user, next work should preserve v332 as a provisional candidate rather than redesign immediately.
Recommended next unit:
1. Decide whether to freeze v332 on Feb-Aug and prepare a September inference-only adapter without reading September outcomes; or
2. run one more **result-blind robustness audit** on v332 using bootstrap/month-block resampling and head/exact3 uncertainty, still without retuning and without September outcomes.
Do not start v334 before user sees this v333 result.