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

# 7. v329 multistage exhibition judgement — COMPLETE / REPORTED
Architecture transferred from 3-head/4-head: frozen PRE -> multiple current-exhibition dimensions -> POST core + opponent/environment stage -> S/A/B routes -> fail-closed readiness.
Implementation commit `c21b058773138c7a9148e4b3a05b68474a741621`; workflow `b69b2ac9b078604ee6eb056e8afd44900efd70d3`; retrigger `71a46a174563d97b98630042bbb74eeec5dc2976`.
Run **34771215699** SUCCESS, Job **103761044413**, Artifact **10322321569**, SHA256 `6d61c88386ff54ab443c03b36b0f034da7fbac0298185bb722d0ee0d383cb2f9`.
Frozen config: attack_q=.55, turn_q=.55, env_q=.60, bcore_q=.90, benv_q=.40.
Frozen thresholds: attack `0.6453333333333333`; turn `0.5980000000000001`; env `-0.29666666666666663`; bcore `0.8973333333333333`; benv `-0.37666666666666665`.
Feb-Apr PASS 25R/12 exact3=48.00%, head22/25=88.00%.
May PASS 24R/10=41.67%, head21/24=87.50%.
June baseline 92R/32=34.78%, head75/92=81.52%.
June PASS **17R/8=47.06%, head16/17=94.12%**; SKIP 75R/24=32.00%.
June S 14R/8=57.14%, head13/14=92.86%; A 3R/0; B 0R.
`FORWARD_SUPPORTED=True`, `PROMOTE=True` under v329 criterion, but user flagged severe selectivity.

---

# 8. v330 period-extension source audit — COMPLETE
- Formal frozen v308/v320 walk-forward evaluation exists only for Feb-Jun; pre-Feb is warm-up/training lineage and not a directly comparable frozen test cohort.
- v321 provides a directly comparable frozen-stack Jul/Aug cohort: exactly 55R/head45/exact3 21, reconstructed month-by-month with v308/v317/v318/v320 and train `<M`.
- Because Jul/Aug outcomes were previously exposed, v330 treats them as NON-PRISTINE fixed-rule robustness/volume reference only. No tuning/promotion. September remains unread.

---

# 9. v330 extended v329 robustness/volume audit — COMPLETE / ABOUT TO REPORT
Pre-work handoff commit: `c8a9b5d961e66ce0902789857a55d4cec6b72736`.
Implementation: `run_v330_1head_extended_v329_reference.py`, commit `7c63e199f2e8fc02e87f38b2d0150dcd42176759`.
Workflow: `.github/workflows/v330-1head-extended-v329-reference.yml`, commit `e9df21bc1d714a0c2bea24de5aa7e285eaa510c5`.
Actions Run **34772689488** SUCCESS, Job **103765047806**, Artifact **10322487241**, artifact SHA256 `d7506a5984ff6f5e096766f66f97240c918c4c9df72d8a9c2abbf6270b2fcfac`.

Validation/reconciliation:
- Jul/Aug base exactly **55R / head45 / exact3 21**.
- Feb-Jun fixed-v329 PASS exactly **66R / head59 / exact3 30**.
- v329 formulas/config/thresholds unchanged; no retuning.
- September outcomes UNREAD.

July NON-PRISTINE reference:
- baseline 13R / exact3 3 = 23.08%, head11 = 84.62%.
- readiness attack/turn/env = 12/12/12.
- PASS **4/13 = 30.77% of base**, exact3 **1/4 = 25.00%**, head **3/4 = 75.00%**.
- SKIP 9R, exact3 2/9=22.22%, head8/9=88.89%.
- grades S/A/B = 3/1/0.
- selected days10, PASS days4, PASS/selected-day=.400.

August NON-PRISTINE reference:
- baseline 42R / exact3 18 = 42.86%, head34 = 80.95%.
- readiness attack/turn/env = 32/38/32.
- PASS **6/42 = 14.29% of base**, exact3 **1/6 = 16.67%**, head **2/6 = 33.33%**.
- SKIP 36R, exact3 **17/36 = 47.22%**, head **32/36 = 88.89%**.
- grades S/A/B = 3/2/1.
- selected days22, PASS days5, PASS/selected-day=.273.

Jul+Aug NON-PRISTINE reference:
- baseline 55R / exact3 21 = 38.18%, head45 = 81.82%.
- readiness attack/turn/env = 44/50/44.
- PASS **10/55 = 18.18% of base**, exact3 **2/10 = 20.00%** (Wilson95 5.67-50.98%), head **5/10 = 50.00%**.
- SKIP **45R / exact3 19 = 42.22%, head40 = 88.89%**.
- grades S/A/B = 6/3/1.
- selected days32, PASS days9, PASS/selected-day=.312.

Volume comparison:
- Feb-Jun PASS **66/345 = 19.13%**, exact3 30/66=45.45%, head59/66=89.39%.
- Jul-Aug NON-PRISTINE PASS **10/55 = 18.18%**, exact3 2/10=20.00%, head5/10=50.00%.
- Feb-Aug descriptive-only PASS **76/400 = 19.00%**, exact3 32/76=42.11%, head64/76=84.21%; this combined line is NOT promotion evidence because Jul/Aug are NON-PRISTINE.

v330 conclusion:
- **Selectivity is structurally stable at ~18-19%**, so the user's concern that the model filters out roughly 4 of every 5 PRE-selected races is confirmed.
- More importantly, the fixed v329 rule is **not robust in the Jul/Aug stress reference**: PASS head rate collapses to 50% and exact3 to 20%, while SKIP is much stronger (head 88.89%, exact3 42.22%). August is especially adverse (PASS head 33.33%, exact3 16.67%).
- Because Jul/Aug are NON-PRISTINE, this cannot statistically invalidate/promote by itself, but it is strong evidence against treating v329 as practical production-ready despite its June promotion flag.
- Do **not** relax v329 thresholds blindly; the failure is directional, not merely too-low volume.

Exact next resume point — DO NOT START BEFORE USER RECEIVES v330 REPORT:
- After reporting v330, predeclare v331 as a diagnostic redesign, not a threshold-widening exercise. First compare which v329 components/routes flipped sign in Jul/Aug (attack_core, turn_core, env_pair, S/A/B) and whether the opponent/environment sign/definition is unstable. Preserve frozen production v308/v317/v318/v320/v323 until a new direct-before-start rule has independent support.