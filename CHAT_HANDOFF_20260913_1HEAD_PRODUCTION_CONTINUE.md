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
- ST lane bias is learned only from prior dates.
- route readiness uses raw completeness, never neutral 0.5 as proof of observation.

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
Implementation commit `c21b058773138c7a9148e4b3a05b68474a741621`; workflow commit `b69b2ac9b078604ee6eb056e8afd44900efd70d3`; retrigger commit `71a46a174563d97b98630042bbb74eeec5dc2976`.
Actions Run **34771215699** SUCCESS, Job **103761044413**, Artifact **10322321569**, artifact SHA256 `6d61c88386ff54ab443c03b36b0f034da7fbac0298185bb722d0ee0d383cb2f9`.
Frozen identity remained 345/290/139; tickets unchanged; September outcomes unread.
Frozen config: attack_q=.55, turn_q=.55, env_q=.60, bcore_q=.90, benv_q=.40.
Fixed thresholds from discovery: attack `0.6453333333333333`; turn `0.5980000000000001`; env `-0.29666666666666663`; bcore `0.8973333333333333`; benv `-0.37666666666666665`.
Feb-Apr PASS 25R / 12 exact3 = 48.00%, head22/25=88.00%.
May PASS 24R / 10 exact3 = 41.67%, head21/24=87.50%.
June baseline 92R / 32 exact3 = 34.78%, head75/92=81.52%.
June PASS **17R / 8 exact3 = 47.06%, head16/17=94.12%**; SKIP 75R / 24 exact3=32.00%.
June S grade 14R / 8 exact3=57.14%, head13/14=92.86%; A grade 3R / 0 exact3; B 0R.
`FORWARD_SUPPORTED=True`, `PROMOTE=True` under v329's predeclared criterion.
User caveat: 17/92 June PASS may be too selective; longer-period robustness/volume test required before practical production use.

---

# 9. Work Unit 6D-A — v330 period-extension source audit — COMPLETE
Audit findings recorded before v330 code:
1. `analyze_v294_1head_verified_prepost_research.py` has `START=2025-11-01`, but formal walk-forward `TEST_MONTHS` are only **2026-02..2026-06**. Nov-Jan are warm-up/training lineage, not an existing comparable frozen evaluation cohort.
2. `run_v308_1head_volume_opponent_joint.py` inherits those same TEST_MONTHS.
3. `run_v326_1head_ticketaware_exhibition.py` and v329 hard-code the frozen v320 345-row Feb-Jun identity, so an earlier Jan-or-before extension would require rebuilding/redefining the full PRE/opponent evaluation design rather than simply applying the same frozen rule.
4. A directly comparable later frozen-stack cohort already exists from v321: `analysis_v321_1head_julaug_nonpristine_validation_race.csv`, exactly **55 rows / head45 / exact3 21**, split Jul13 and Aug42. It was reconstructed month-by-month using the frozen v308 head gate, v317 SECOND, v318 THIRD and v320 HYBRID tickets with month M trained only on <M.
5. Jul/Aug are NON-PRISTINE because their outcomes were exposed previously, so they can only be a **fixed-rule stress/volume reference**; they cannot tune thresholds or promote a model. September remains unread.

Revised v330 design now frozen before implementation:
- load the v321 55-row Jul/Aug frozen-stack cohort and assert 55/head45/exact3=21 before exhibition filtering;
- recreate same-race exhibition features with the v326 audited raw-readiness + `corrected_direct` path and prior-day-only ST bias, preloading from 2025-10-01;
- use v329 formulas and the exact already-frozen numeric thresholds above; **no quantiles/grid/refit/threshold change**;
- grade S -> A -> B with exactly the v329 precedence and fail-closed route readiness;
- report July, August, Jul+Aug baseline/readiness/PASS/SKIP/S-A-B, PASS fraction, head rate, exact3 rate, unique selected days and practical PASS volume;
- also report descriptive Feb-Jun vs Jul/Aug and Feb-Aug totals, while keeping the NON-PRISTINE caveat explicit.

Success criteria:
- base reconciliation exactly 55/head45/exact3=21;
- no September result access;
- frozen v329 thresholds unchanged;
- Jul/Aug exhibition feature generation completes causally with missing-source routes failing closed;
- enough output to judge whether v329's ~19% Feb-Jun PASS share and June 17/92 selectivity are stable or an artifact.

Failure fallback:
- if Jul/Aug source coverage is missing, report readiness and fail closed; never neutral-fill a missing required source;
- if base identity differs, stop before scoring and record exact mismatch;
- if code fails, record Run/Job/error here before correction.

Exact next resume point:
- implement `run_v330_1head_extended_v329_reference.py` and `.github/workflows/v330-1head-extended-v329-reference.yml`; run Actions; append actual results before any v331 widening experiment.