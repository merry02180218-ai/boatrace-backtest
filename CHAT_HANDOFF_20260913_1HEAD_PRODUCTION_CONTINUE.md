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
- User explicitly changed the old Jul/Aug restriction on 2026-09-14: **July/August 2026 may now be used for model learning/tuning.**
- September outcomes remain **UNREAD** and are reserved as the final untouched evaluation period.
- no same/later-race result, payout, future/backfill contamination in race-time features.
- current-race exhibition is post-PRE only and must be result-blind at prediction time.
- missing current exhibition inputs fail closed for any feature/route requiring them.
- no `meet_*` unless separately audited.
- neutral 0.5 defaults are not proof raw metric existed.

# 3. Frozen research through v331
- v320 `HYBRID alpha=.70`: **139/345=40.29%** exact3.
- v321 Jul/Aug base: Run 34750719803; **55R/head45/exact3 21**.
- v329 multistage Run **34771215699**: June PASS 17R/8 exact3=47.06%, head16/17=94.12%.
- v330 Run **34772689488**: fixed-v329 Jul+Aug PASS 10/55, exact3 2/10=20%, head5/10=50%; fixed v329 not production-ready.
- v331 Run **34773137181** SUCCESS, Job **103766279485**, Artifact **10322896490**. Identity Feb-Jun 345/head290/exact3 139; Jul-Aug 55/head45/exact321. Key finding: `attack_core` was materially more stable than `env_pair`; hard attack+env AND was main reversal mechanism; `turn_core` weak/unstable.

# 4. Exhibition source audit
Historical result-blind sources:
- `data/previews/tkz/YYYY/MM/DD.csv`
- `data/previews/stt/YYYY/MM/DD.csv`
- `data/previews/original_exhibition/YYYY/MM/DD.csv`
- transform `backtest_v51_lane_corrected_tickets.py::corrected_direct`
- ST lane bias learned only from prior dates.
- readiness uses raw completeness, never neutral 0.5 as proof.

# 5. v332 attack-first redesign — COMPLETE / REPORTED
Implementation `db15c03df9f2d551d6ac1f724433401be5c155c0`; workflow `17db56410c92729df34c3c680f360d98b5781fbb`.
Run **34774010225** SUCCESS, Job **103768650973**, Artifact **10323285065**.
Identity **400 rows / 335 head / 160 exact3** Feb-Aug; September unread.
Chosen Feb-Jul month-OOF config: `ATTACK_ENV_SOFT`, env_w=.1, q=.65.
OOF PASS **86R**, exact3 **41/86=47.67%**, head **76/86=88.37%**, fraction **24.02%**; baseline lifts exact3 +8.01pp, head +4.29pp; exact3 nonnegative 4/6 months.
August one-shot: baseline 42R/exact3 42.86%/head80.95%; PASS **10R/exact34=40.00%/head7=70.00%**, fraction23.81%; therefore not promoted under v332 rule.
Important interpretation from user/assistant after report: **10 August PASS races is a small sample; 70% head and 40% exact3 may plausibly be ordinary month-to-month variance rather than structural failure. Do not discard v332 before quantifying this.**

# 6. v333 — PRE-WORK DECLARATION: v332 MONTHLY VARIANCE / STABILITY AUDIT
Current position: v332 improved catastrophic v329 reversal and has stable ~24% volume, but failed the strict August one-shot criterion on only 10 PASS races. User explicitly requested testing whether this is just monthly sampling variance before redesigning the model.

Exact work now:
1. **Do not alter or retune v332.** Reconstruct the exact frozen v332 chosen rule (`ATTACK_ENV_SOFT`, env_w=.1, q=.65) in its month-OOF form for Feb-Jul and its frozen one-shot form for August.
2. Produce month-by-month Feb-Aug table for baseline and v332 PASS: R, PASS fraction, head wins/rate, exact3 hits/rate, head lift, exact3 lift.
3. Compute Wilson 95% confidence intervals for PASS head rate and PASS exact3 rate each month, plus pooled Feb-Jul OOF intervals.
4. Quantify whether August PASS 7/10 head and 4/10 exact3 are statistically unusual relative to the preceding v332 OOF performance using exact/binomial predictive-tail or Fisher-style small-sample tests. Report effect sizes and p-values; do not treat p>0.05 as proof of equality.
5. Run leave-one-month-out stability summaries: dispersion/range of monthly lifts, count positive/nonnegative months, and compare August to the empirical distribution of prior month deviations.
6. Include a small-sample sensitivity table showing August rates if 1 or 2 race outcomes differed, to make denominator=10 instability explicit.
7. Diagnostic only. **No new selector, no threshold search, no September outcomes.**

Success criteria:
- exact v332 identity and August PASS 10/head7/exact3 4 reproduced;
- all Feb-Jul OOF selections reproduced without using each held-out month's labels in its fit;
- statistical audit can distinguish `clear structural break evidence` from `insufficient evidence; monthly variance plausible`;
- no September outcome read.

Failure fallback:
- if exact v332 OOF selections cannot be reconstructed from the v332 implementation, stop and fix identity/reconstruction only; do not substitute a newly fitted rule;
- if small sample makes tests underpowered, report that explicitly rather than forcing a structural-failure conclusion.

Exact next resume point:
- implement `run_v333_1head_v332_monthly_variance_audit.py` and workflow; run Actions; append Run/Job/Artifact and metrics here; **report v333 once before starting any v334 redesign.**