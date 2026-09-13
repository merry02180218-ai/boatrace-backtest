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
Key finding: `attack_core` remained materially more stable than `env_pair`; the hard `attack+env` AND gate was the main reversal mechanism, and `turn_core` was weak/unstable.

# 6. v332 attack-first redesign — COMPLETE / REPORTED NEXT
Pre-work handoff commit `7c39d2255c34e52af03653ea5a2a458cbc0f8ae5`.
Implementation `db15c03df9f2d551d6ac1f724433401be5c155c0`; workflow `17db56410c92729df34c3c680f360d98b5781fbb`.
Run **34774010225** SUCCESS, Job **103768650973**, Artifact **10323285065**, artifact SHA256 `0a44eb060033dd7c140e9057824207b726c267d30dfb14f206948e39434fc6d4`.
Identity preserved: **400 rows / 335 head / 160 exact3** across Feb-Aug. September outcomes remained unread.

Method:
- no hard `env_pair` AND gate;
- candidate families were ATTACK_ONLY, ATTACK_ENV_SOFT, ATTACK_COMPONENT_LOGIT;
- candidate selection used month-level OOF across Feb-Jul only;
- one candidate was frozen before the one-shot August check;
- August was not used to switch candidates after seeing its result.

Chosen Feb-Jul OOF config:
- family `ATTACK_ENV_SOFT`
- `env_w=0.1`
- `q=0.65`
- OOF PASS **86R**, exact3 **41/86=47.67%**, head **76/86=88.37%**, PASS fraction **24.02%**.
- Relative to Feb-Jul baseline: exact3 lift **+8.01pp**, head lift **+4.29pp**.
- Exact3 lift non-negative in **4/6 months**.

August one-shot forward check:
- baseline **42R / exact3 18=42.86% / head34=80.95%**.
- v332 PASS **10R / exact3 4=40.00% / head7=70.00%**.
- PASS fraction **23.81%**.
- exact3 fell **-2.86pp** vs August baseline and head fell **-10.95pp**.
- therefore `AUGUST_SUPPORTED=False` and `PROMOTE_TO_SEPTEMBER_CANDIDATE=False`.

Final Feb-Aug descriptive fit parameters were computed only for audit/future comparison, NOT promoted:
- attack_mean `0.6008956109134045`
- attack_sd `0.18729631819954082`
- env_mean `-0.3286239620403322`
- env_sd `0.19113530593568695`
- threshold `0.36493599145988975`

Conclusion:
- Removing hard env gating fixed the catastrophic 0-20% style collapse seen in v329, and raised stable usable volume to ~24%, but **head preservation still failed in August**.
- The remaining problem is no longer primarily the hard env AND rule. A soft attack+env score that looked strong in Feb-Jul still over-selected August races where boat1 lost.
- v332 is **not promoted** and must not be used to read September outcomes.

# 7. Exact next resume point — DO NOT START BEFORE REPORTING v332 TO USER
Next research direction should be predeclared as v333 only after the v332 report is delivered.
Recommended v333 direction:
1. Keep September outcomes unread.
2. Stop using exact3 as the main selector target for the exhibition filter; first build/calibrate a **direct boat1 head-survival probability** from result-blind current exhibition components.
3. Diagnose August head losses among the 10 v332 PASS races versus August non-PASS/head wins, focusing on which current-exhibition dimensions separate escape failures without hard env gating.
4. Use July/Aug labels for learning as permitted, but require month-level cross-validation and explicit head-rate floor.
5. Only after head-survival is stable should exact3/ticket quality be applied as a secondary layer.
6. Do not inspect September outcomes until a final candidate is frozen.