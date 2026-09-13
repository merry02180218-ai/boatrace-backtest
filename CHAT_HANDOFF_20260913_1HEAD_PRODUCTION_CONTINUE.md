# CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE

## Mandatory operating rule
Before every work unit, record current position and intended next action here. After work, record commit/run/result/next action. Latest GitHub wins.

## Frozen production stack
v308 PRE head -> v317 SECOND OUTER_L2_1 -> v318 THIRD DROPSTART_T0.1 -> v320 HYBRID alpha=.70 exactly 3 tickets -> three odds -> composite odds `1/(1/o1+1/o2+1/o3)`.
Development regression: 345 selected / 290 head wins / 139 exact3. Jul/Aug 2026 NON-PRISTINE/reference-only. September outcomes unread. `meet_*` forbidden.

## Production adapter status
v323 implementation was completed and a successful GitHub Actions production run was verified: run **34757079269** (`live-1head-v323-20260913`). Historical regression remained 345/290/139 and frozen hcut 0.8073405637. 2026-09-13 current scoring selected 2 races and calculated current 3-ticket composite odds. No BUY cutoff was frozen; status remained fail-safe.

## WORK UNIT 2026-09-13-4 — Jul/Aug composite-odds BUY reference audit — COMPLETED
User hypothesis: with roughly 40% exact-3-ticket hit probability, a composite-odds BUY condition around 3.0 may be reasonable. User explicitly requested testing this on July/August.

Implementation:
- `run_v324_1head_julaug_composite_odds.py`
- `.github/workflows/v324-1head-julaug-composite-odds.yml`
- commits:
  - `7346141821c540c3dc72563393ee0e44ae5ce6db` — add v324 audit script
  - `c0ef06d56065f928fa5099e35bcfd824c9c0bf53` — add workflow
  - `8307774bda882110cf7f761faab15b21bad687d4` — fix historical odds lookup to match v322 source

Actions:
- first run `34762913278` failed because the initial odds lookup implementation did not match v322's historical odds DataFrame interface.
- corrected run **34762939723**: **completed / success**
- job ID: `103738822011`
- artifact: `v324-1head-julaug-composite-odds`, artifact ID `10318928652`
- frozen v321 reconciliation: **55 selected / 21 exact3 hits / 55 complete odds**, missing odds = 0.

### July
|rule|R|H|hit rate|return units|profit units|ROI|
|---|---:|---:|---:|---:|---:|---:|
|ALL|13|3|23.08%|6.059|-6.941|46.61%|
|>=2.5|4|1|25.00%|2.643|-1.357|66.06%|
|>=2.7|1|0|0.00%|0.000|-1.000|0.00%|
|>=3.0|1|0|0.00%|0.000|-1.000|0.00%|
|>=3.2|0|0|n/a|0.000|0.000|n/a|
|>=3.5|0|0|n/a|0.000|0.000|n/a|

### August
|rule|R|H|hit rate|return units|profit units|ROI|
|---|---:|---:|---:|---:|---:|---:|
|ALL|42|18|42.86%|41.052|-0.948|97.74%|
|>=2.5|18|5|27.78%|14.834|-3.166|82.41%|
|>=2.7|16|4|25.00%|12.243|-3.757|76.52%|
|>=3.0|9|1|11.11%|3.713|-5.287|41.25%|
|>=3.2|7|1|14.29%|3.713|-3.287|53.04%|
|>=3.5|6|1|16.67%|3.713|-2.287|61.88%|

### Jul+Aug combined
|rule|R|H|hit rate|return units|profit units|ROI|
|---|---:|---:|---:|---:|---:|---:|
|ALL|55|21|38.18%|47.111|-7.889|85.66%|
|>=2.5|22|6|27.27%|17.476|-4.524|79.44%|
|>=2.7|17|4|23.53%|12.243|-4.757|72.02%|
|>=3.0|10|1|10.00%|3.713|-6.287|37.13%|
|>=3.2|7|1|14.29%|3.713|-3.287|53.04%|
|>=3.5|6|1|16.67%|3.713|-2.287|61.88%|

Conclusion / guardrail:
- The Jul/Aug NON-PRISTINE reference **does not support composite odds >=3.0 as a BUY cutoff**. Combined >=3.0 gave only 1/10 exact3 = 10.00% and ROI 37.13%.
- Even >=2.5 underperformed ALL on Jul+Aug (79.44% vs 85.66%).
- The ~40% unconditional exact3 rate cannot be converted directly into a fair-odds threshold without conditioning hit probability on composite odds; observed hit probability fell sharply in the higher-odds subset.
- Do NOT freeze/promote any BUY cutoff from this reused Jul/Aug evidence. Keep production fail-safe until a cutoff has genuinely out-of-sample support.

## WORK UNIT 2026-09-13-5 — Exhibition-time post-PRE filter for exact3 >=50% — written BEFORE execution
User goal: raise the frozen 3-ticket exact3 hit rate from ~40% toward **50% or more** by using data that becomes available after exhibition, rather than changing the frozen PRE model itself.

Do now:
1. Keep the frozen PRE stack unchanged: v308 -> v317 -> v318 -> v320, exactly 3 tickets. The new logic is an additional post-exhibition PASS/SKIP layer only.
2. Inspect existing repository sources for same-race exhibition data already available historically and in live operation: exhibition time, exhibition ST, actual exhibition entry/course, and original exhibition metrics such as straight, one-lap, turn/handling where available.
3. Build candidate same-race exhibition features as **relative/field-adjusted values**, not raw times alone. At minimum inspect boat1 vs field, predicted SECOND/THIRD boats vs field, and ticket-covered opponents vs uncovered opponents.
4. Explicitly separate current-race exhibition data from PRE predictors. These same-race exhibition fields are allowed only in the new post-exhibition filter and must never leak into v308/v317/v318/v320 training/scoring.
5. First objective is classification/calibration: among races already selected by the frozen PRE stack, identify exhibition patterns associated with exact3 hits versus misses. Optimize for useful retained race count while testing whether PASS exact3 can reach >=50%; report coverage, head hit rate, exact3 hit rate, and odds/ROI diagnostics where odds are complete.
6. Use development data for feature research/training. Jul/Aug 2026 remain NON-PRISTINE/reference-only and may only be used as a final reference check after a rule/model is fixed. September outcomes remain unread.
7. Avoid simple threshold overfitting on individual exhibition times. Prefer causal, interpretable relative features and month-forward/OOS validation where possible.
8. Before implementing the filter, identify exact source files/columns and historical coverage. If original exhibition coverage is partial, quantify missingness and make the filter fail-safe rather than silently imputing future/post-race values.

Success criteria for this work unit:
- exact source and timing of exhibition/original-exhibition columns are audited;
- same-race exhibition data is isolated to a post-PRE layer;
- a reproducible dataset for the frozen selected races is created with exact3 label + exhibition features;
- no September outcome is read;
- if a candidate filter is tested, report retained R, exact3 H/rate, head H/rate, and Jul/Aug reference only after freezing the candidate on development data.

### Work Unit 5A — source audit COMPLETE / v325 implementation specification — written BEFORE coding
Confirmed reusable result-blind exhibition sources and code:
- historical feature ledger: `analysis_v108_1head_feasibility.csv` generated by `analyze_v108_1head_feasibility.py`.
- historical source paths frozen before settlement: `data/previews/tkz/YYYY/MM/DD.csv` (official exhibition time), `data/previews/stt/YYYY/MM/DD.csv` (start exhibition + exhibition course), `data/previews/original_exhibition/YYYY/MM/DD.csv` (original exhibition).
- historical coverage in v108: tkz 92.8%, stt 92.8%, original 88.5%; 45,404 frozen races, 357 changed-entry races excluded, feature errors 0.
- live builder already exists: `build_4head_v283_current_exhibition_live.py`, using official BOAT RACE beforeinfo display time + BOATCAST start display + BOATCAST original exhibition; it emits rank-normalized `cur_ex`, `cur_st`, `cur_orig_lap`, `cur_orig_turn`, `cur_orig_straight`, `cur_orig_avg` and is result-blind.
- v108 historical ledger contains corresponding rank/relative fields including `one_ex`, `one_st`, `one_lap`, `one_turn`, `one_straight`, `one_orig_avg`, `one_direct`, `one_score`, opponent threats, and margins such as `ex_margin23`, `turn_margin23`, `straight_margin23`.
- old v123 proved the architecture can work without adding races after exhibition: its frozen `ex_margin23 >= -0.235` gate improved Jun-Aug 7-ticket hit rate 56.2% -> 58.2% on the old model. This is only architectural evidence, not a threshold to reuse.

Implement next as **new v325**, without mutating v308/v317/v318/v320/v323:
1. Add `run_v325_1head_exhibition_postfilter.py`.
   - Read frozen v320 development cohort `analysis_v320_1head_exact3_ticket_policy_best_race.csv` (Feb-Jun: 345R/139 exact3).
   - Join by `race_code` to `analysis_v108_1head_feasibility.csv` to attach already-frozen same-race exhibition features; never call result/payout APIs during feature construction.
   - Parse v320's 3 tickets and derive ticket-aware opponent sets. Build interpretable relative features from v108 boat1/field features first; if per-opponent historical primitives needed for ticket-aware features are not present in v108 ledger, defer those rather than reconstructing them with unsafe data.
   - Quantify join coverage and missingness, including `has_tkz`, `has_stt`, `has_orig`, and fail closed on missing current same-race exhibition inputs when scoring a postfilter.
2. Candidate filter research design:
   - Research only within Feb-Jun development evidence, using chronological separation rather than random CV.
   - Primary conservative experiment: Feb-Apr discovery, May validation/freeze, Jun one-shot internal forward check. Do not touch Jul/Aug until a candidate specification is frozen.
   - Compare baseline against simple one-dimensional lower-tail skip gates and a small regularized logistic PASS score built only from predeclared exhibition-relative features. Avoid broad combinatorial mining.
   - Target exact3 >=50% with useful retained coverage. Report retained R, exact3 H/rate, head H/rate, monthly stability, and skipped-race exact3 rate.
   - Candidate cannot be promoted merely for reaching 50% in discovery; it must remain >=50% or show credible lift in the forward Jun check before Jul/Aug reference is run.
3. Only after candidate is frozen from Feb-Jun, evaluate it once on Jul/Aug NON-PRISTINE v321 55R/21 exact3 by joining the same exhibition ledger. Mark result reference-only; do not retune threshold/model on Jul/Aug.
4. Add `.github/workflows/v325-1head-exhibition-postfilter.yml`, run GitHub Actions, upload dataset/summary/candidate tables, verify actual Run ID/status/artifact.
5. If v108 ledger lacks enough per-race fields to reproduce the same live feature semantics, stop before model search, report the exact missing fields, and create a separate safe dataset builder from the existing historical `tkz/stt/original_exhibition` snapshots. Do not substitute post-race/backfilled values.

v325 success criteria:
- frozen v320 identity reconciles exactly 345R/139 exact3 before filtering;
- exhibition join coverage/missingness is explicit;
- no September results or payout data read;
- v308/v317/v318/v320 outputs are unchanged;
- chronological validation is reported;
- Jul/Aug reference is run only after the candidate rule is frozen;
- target is >=50% exact3, but no claim/promotion unless forward evidence supports it.

If interrupted: resume Work Unit 5A by creating `run_v325_1head_exhibition_postfilter.py`; the source audit above is complete and should not be repeated unless latest GitHub changed.
