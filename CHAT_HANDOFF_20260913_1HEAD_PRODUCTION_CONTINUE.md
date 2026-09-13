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
- User explicitly changed the old Jul/Aug restriction on 2026-09-14: **July/August 2026 may now be used for model learning/tuning.** Old `NON-PRISTINE never tune/promote` rule is superseded for future versions.
- September outcomes remain **UNREAD** and are reserved as the final untouched evaluation period.
- no same/later-race result, payout, future/backfill contamination in race-time features.
- current-race exhibition is post-PRE only and must be result-blind at prediction time.
- missing current exhibition inputs fail closed for any feature/route requiring them.
- no `meet_*` unless separately audited.
- neutral 0.5 defaults are not proof raw metric existed.
- Any use of July/Aug labels must be explicitly documented; no claim that those months are out-of-sample once used for tuning.

# 3. Frozen research through v330
- v320 `HYBRID alpha=.70`: **139/345=40.29%** exact3.
- v321 Jul/Aug base: Run 34750719803; **55R/head45/exact3 21**.
- v322 composite odds Run 34753932483; ROI91.27%; no odds-only cutoff promoted.
- v323 production adapter Run 34757079269; frozen 345/290/139.
- v324 corrected Jul/Aug odds audit Run 34762939723; 55R/21 exact3, ROI85.66%.
- v325-v327 exhibition filters failed June forward support.
- v328 showed broad June deterioration; no single ticket miss class dominated.
- v329 multistage Run **34771215699**: June PASS 17R/8 exact3=47.06%, head16/17=94.12%.
- v330 Run **34772689488**: fixed-v329 Jul+Aug PASS 10/55, exact3 2/10=20%, head5/10=50%; SKIP exact3 19/45=42.22%, head40/45=88.89%. Fixed v329 is not production-ready.

# 4. Exhibition source audit
Historical result-blind sources:
- `data/previews/tkz/YYYY/MM/DD.csv`
- `data/previews/stt/YYYY/MM/DD.csv`
- `data/previews/original_exhibition/YYYY/MM/DD.csv`
- transform `backtest_v51_lane_corrected_tickets.py::corrected_direct`
- ST lane bias learned only from prior dates.
- readiness uses raw completeness, never neutral 0.5 as proof.

# 5. v331 component/route stability — COMPLETE / REPORTED
Implementation `edb154f6242a5ef31050ac611ab170835867e977`; workflow `fb37197f97e29e90527438dd5caef84e5615fd90`.
Run **34773137181** SUCCESS, Job **103766279485**, Artifact **10322896490**, artifact SHA256 `5988b5aac9e8141c05a5acb4aa7438de91cb1df8de9c1d8f05380a837db1af58`.
Identity preserved: Feb-Jun **345/head290/exact3 139**; Jul-Aug **55/head45/exact3 21**.

Key diagnostic findings:
- June baseline exact3 32/92=34.78%, head75/92=81.52%.
- June `attack_core` gate: 24R, exact3 **13/24=54.17%**, head22/24=91.67%.
- June `attack+env`: 14R, exact3 **8/14=57.14%**, head13/14=92.86%.
- June `turn_core`: 31R, exact3 only **7/31=22.58%**.
- Jul+Aug baseline: exact3 21/55=38.18%, head45/55=81.82%.
- Jul+Aug `attack_core` alone: **19R, exact3 8/19=42.11%, head14/19=73.68%** — exact3 direction remains slightly positive.
- Jul+Aug `env` alone: 13R, exact3 4/13=30.77%, head8/13=61.54%.
- Jul+Aug `attack+env`: **6R, exact3 1/6=16.67%, head3/6=50%** — strong reversal.
- August baseline exact3 18/42=42.86%, head34/42=80.95%.
- August `attack_core` alone: **14R, exact3 6/14=42.86%, head10/14=71.43%**.
- August `attack+env`: **3R, exact3 0/3=0%, head1/3=33.33%**.
- Conclusion: v329 deterioration is primarily associated with making `env_pair` a mandatory AND gate. `attack_core` itself is materially more stable. `turn_core` is unstable/weak. Future redesign should be attack-first, environment soft/optional rather than mandatory.

# 6. Work Unit 8A — v332 attack-first redesign — ABOUT TO IMPLEMENT
Current position: v331 isolated the main failure mechanism. User permits July/August labels for learning. September stays untouched.

Predeclared design:
1. Build one development dataset by concatenating v329 Feb-Jun and v330 July-Aug reconstructed causal exhibition rows. Assert **400 rows / head335 / exact3 160**.
2. Keep frozen PRE selection and v317/v318/v320 tickets unchanged. v332 only decides post-PRE PASS/SKIP.
3. Primary route is **attack-first**. No candidate may require `env_pair >= threshold` as a hard mandatory AND condition.
4. Candidate families:
   - `ATTACK_ONLY`: threshold/quantile on `attack_core` only, fail-closed on `attack_ready`.
   - `ATTACK_ENV_SOFT`: standardized/rank-like attack score with a small additive environment term; environment may shift score but cannot hard-veto an otherwise strong attack signal.
   - optional `ATTACK_COMPONENT_LOGIT`: regularized logistic head model using current-race result-blind 1-boat attack components (`one_ex`,`one_st`,`one_straight`,`one_orig_avg`) with environment inputs only as optional secondary coefficients, never a hard gate.
5. Development chronology:
   - model/config discovery on **Feb-Jul** only;
   - **August is a one-shot development forward check** for candidate selection/support;
   - after a v332 config is frozen, refit/freeze its learned parameters on **Feb-Aug** for future September inference.
   - Once August is used to select v332, August is not described as out-of-sample thereafter.
6. Selection objective must balance exact3 improvement and 1-head preservation; reject configurations that gain exact3 only by collapsing head rate.
7. Prefer broader usable coverage than v329; target PASS >=20% of eligible PRE races when supported, but do not force volume at the expense of direction.
8. Output monthly Feb-Aug PASS counts, exact3, head rate, August one-shot result, and final Feb-Aug fitted parameters for September use.
9. **Do not inspect September outcomes.**

Success criteria:
- source identity 400/head335/exact3160;
- August forward PASS exact3 rate >= August baseline 42.86% OR clear head-rate improvement with no material exact3 loss;
- August head rate must not fall more than 5pp below baseline 80.95%;
- PASS volume on August >=8 races and preferably >=20% of 42R;
- no hard env AND gate;
- final parameters can be computed using Feb-Aug without touching September outcomes.

Failure fallback:
- if all attack-first candidates fail August support, do not promote/relabel; record v332 unsupported and next test should use direct head-probability calibration or richer result-blind attack features, not a return to env hard gating.
- any identity/readiness drift => fail closed and record before correction.

Exact next resume point:
- implement `run_v332_1head_attack_first_redesign.py` and workflow; run Actions; record exact v332 result here; report once before starting v333.