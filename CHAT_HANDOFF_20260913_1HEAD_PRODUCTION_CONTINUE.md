# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## READ THIS FIRST — authoritative current 1-head state
Latest GitHub wins over old chat memory/stale handoff text.
Mandatory pattern: **handoff update -> work -> result append -> next work handoff update**.
Before every work unit/code change/restart record current position, exact work, success criteria, failure fallback. After every work unit record actual work, commit SHA(s), Actions Run ID/status, metrics/results, exact next resume point.

---

# 1. Frozen production stack — DO NOT ALTER
- HEAD v308
- SECOND v317 `OUTER_L2_1`
- THIRD v318 `DROPSTART_T0.1`
- 3-ticket policy v320 `HYBRID alpha=.70`
- exactly 3 trifecta tickets per selected race
- composite odds = `1 / (1/o1 + 1/o2 + 1/o3)`
- frozen regression **345 selected / 290 boat1 wins / 139 exact3**
- v308 q=.980, opponent mass>=.375, head cutoff=0.8073405637
- v308 is true PRE; same-race exhibition is post-PRE only.

Guardrails:
- Jul/Aug 2026 = NON-PRISTINE/reference-only; never tune/promote on them.
- September outcomes = UNREAD.
- no same/later-race result, payout, future/backfill contamination.
- month M trains strictly on `<M`.
- missing current exhibition inputs fail closed for any feature/route that requires them.
- no `meet_*` unless separately audited.
- neutral 0.5 defaults are not proof a raw metric existed.
- do not modify v308/v317/v318/v320/v323.

Mandatory causal cache family:
- `cache_v313_1head_opponent_pre.csv.gz`
- `cache_v313_1head_opponent_p3.csv.gz`
- `cache_v313_1head_opponent_p4.csv.gz`
- `CACHE_V313_1HEAD_OPPONENT_CAUSAL.md`

---

# 2. Frozen research summary through v320
- v309 exact3 132/345; SECOND TOP2 71.72%.
- v310 causal p3/p4 exact3 133/345; SECOND TOP2 72.07%.
- v311 DROP_START exact3 136/345; SECOND TOP2 72.41%.
- v312 outer gate exact3 136/345; SECOND TOP2 73.10%.
- v314 role split unstable, not promoted.
- v315 pairwise SECOND exact3 133/345.
- v316 multiclass SECOND exact3 136/345.
- v317 `OUTER_L2_1` exact3 137/345.
- v318 `DROPSTART_T0.1` exact3 137/345.
- v319 direct ordered-pair weaker, exact3 134/345.
- v320 `HYBRID alpha=.70` exact3 **139/345=40.29%**.

Useful frozen code:
- `run_v308_1head_volume_opponent_joint.py`
- `run_v317_1head_opponent_error_features.py`, `add_engineered(...,'OUTER')`
- `run_v318_1head_opponent_third_rebuild.py`, `pc_predict(...,.1,'DROP_START')`
- `run_v299_1head_trifecta3_policy_search.py`
- frozen ticket identity `analysis_v320_1head_exact3_ticket_policy_best_race.csv`

---

# 3. Completed production/reference work v321-v324
- v321 Jul/Aug NON-PRISTINE reference: Run 34750719803; 55R / head45 / exact3 21 (38.18%).
- v322 composite odds: Run 34753932483; 345R / 139 exact3 / 339 complete odds; ROI 91.27%; no BUY cutoff promoted.
- v323 production adapter: Run 34757079269; frozen 345/290/139 preserved; September outcomes unread.
- v324 corrected Jul/Aug odds audit: Run 34762939723; 55R/21 exact3, ROI85.66%; composite>=3 unsupported.

---

# 4. Exhibition source audit
Historical result-blind sources:
- `data/previews/tkz/YYYY/MM/DD.csv`
- `data/previews/stt/YYYY/MM/DD.csv`
- `data/previews/original_exhibition/YYYY/MM/DD.csv`
- audited transform `backtest_v51_lane_corrected_tickets.py::corrected_direct`
- `corrected_direct` applies lane/frame correction then within-race rank scores; ST bias is learned only from prior dates.
- coverage on historical frozen source family: tkz/stt ~92.8%, original exhibition ~88.5%.

---

# 5. v325-v327 postfilter attempts — COMPLETE / NOT PROMOTED
- v325 Run 34764329333: June PASS 8/25=32.00%, baseline 34.78%, unsupported.
- v326 Run 34766426083: June PASS 8/25=32.00%, unsupported.
- v327 Run 34766775614: June PASS 13/39=33.33%, unsupported.

---

# 6. v328 ticket-selection error audit — COMPLETE / REPORTED
Run 34767480326 SUCCESS. ALL R345/head290/exact3 139. June R92/head75/exact3 32. Broad June deterioration confirmed; richer direct-before-start judgement selected as next target.

---

# 7. v329 3-head/4-head architecture audit — COMPLETE
Transferred architecture only: frozen PRE -> multiple current-exhibition dimensions -> core POST + opponent/environment stage -> S/A/B routes -> route-specific raw readiness/fail-closed. Head-specific 3/4 thresholds were not copied.

---

# 8. v329 multistage exhibition judgement — COMPLETE / REPORTED
Implementation `run_v329_1head_multistage_exhibition.py`; workflow `.github/workflows/v329-1head-multistage-exhibition.yml`.
Retrigger commit `71a46a174563d97b98630042bbb74eeec5dc2976`.
Actions Run **34771215699** SUCCESS, Job **103761044413**, Artifact **10322321569**, artifact SHA256 `6d61c88386ff54ab443c03b36b0f034da7fbac0298185bb722d0ee0d383cb2f9`.
Frozen identity remained 345/290/139; tickets unchanged; Jul/Aug unopened for tuning/performance; September outcomes unread.
Frozen config: attack_q=.55, turn_q=.55, env_q=.60, bcore_q=.90, benv_q=.40.
Feb-Apr PASS 25R / 12 exact3 = 48.00%, head22/25=88.00%.
May PASS 24R / 10 exact3 = 41.67%, head21/24=87.50%.
June baseline 92R / 32 exact3 = 34.78%, head75/92=81.52%.
June PASS **17R / 8 exact3 = 47.06%, head16/17=94.12%**; SKIP 75R / 24 exact3=32.00%.
June S grade 14R / 8 exact3=57.14%, head13/14=92.86%; A grade 3R / 0 exact3; B 0R.
`FORWARD_SUPPORTED=True`, `PROMOTE=True` under v329's predeclared criteria.
Important caveat raised by user: 17/92 June PASS is likely too selective; robustness/volume must be tested over a longer backtest period before treating v329 as practical production promotion.

---

# 9. Work Unit 6D — v330 extended-period v329 robustness/volume audit — ABOUT TO START
Current position:
- v329 passed its one-shot June forward test but selects only 17/92 June frozen PRE races.
- User explicitly requested a longer backtest period to determine whether the apparent lift is robust and whether the race count is too restrictive.
- Frozen production v308/v317/v318/v320/v323 remains unchanged while this audit runs.

Exact work about to be done:
1. Audit repository historical availability before choosing dates. Extend backward as far as the existing causal PRE/opponent/exhibition pipeline can be reproduced without future/backfill leakage. Do NOT simply append Jul/Aug because those are NON-PRISTINE and were exposed during research.
2. Prefer a genuinely earlier untouched historical window (before Feb 2026) if required source/cache lineage supports it. Month M must train only on <M and current-race exhibition remains post-PRE.
3. Apply the already-frozen v329 scoring formulas and thresholds/config without retuning on the extended evaluation months.
4. Report per-month and aggregate: PRE-selected R, exhibition-ready R, v329 PASS R and PASS rate, exact3 hit rate, head rate, S/A/B counts/rates, SKIP metrics, and confidence intervals/dispersion sufficient to judge whether 47.06% was small-sample noise.
5. Also report practical volume: PASS races per racing day / per month where possible. Do not relax v329 thresholds in this work unit; first measure robustness honestly.
6. Jul/Aug may remain only previously-known NON-PRISTINE reference and must not be used to select/retune thresholds. September outcomes remain unread.

Success criteria:
- at least several additional months or a materially larger independent race sample is evaluated with the frozen v329 rule;
- no future/backfill contamination and frozen ticket identity logic is preserved for comparable cohorts;
- volume and accuracy tradeoff is quantified, not just hit rate;
- result determines whether next work should be (a) keep v329, (b) cautiously widen routes in a separately predeclared v331, or (c) reject v329 as unstable.

Failure fallback:
- if earlier months cannot be reconstructed causally from existing repo data, document the exact earliest valid boundary and why; do not fabricate or silently use contaminated data.
- if extended cohort differs from the 345 frozen cohort construction, explicitly reconcile the difference before comparing rates.

Exact next resume point:
- inspect historical data/cache/model date coverage and implement a frozen-rule extended-period evaluator as v330; run Actions and report the v330 result before any threshold-widening experiment.