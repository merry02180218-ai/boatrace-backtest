# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research version: `v289-addon-wave1`
- decision: **NO_ADOPTION_WAVE1**
- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.
- July/August are NON-PRISTINE. September outcomes were not loaded or used.
- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.

## Wave-1 result
- candidate pool: 178 races
- best tested variant: `return_rank@0.45`
- best add-on: 84R / 15 hits / ROI 54.92% / profit -378,700 yen
- combined: 178R / ROI 117.04%

## Methods tested / dead ends retained
- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family only.
- `return_rank`: prior-reject realized-return ranking trained only on prior months.
- `attack_style_split`: separate stretch-vs-turn regimes, then outcome ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score plus current composite odds, alpha chosen on prior months only.

## Real-operation audit
- all scoring inputs are columns already present before settlement in the canonical v243/v288 audit artifact;
- decisions use only prior-month outcomes for fitting; current test-month result/payout enters settlement only;
- missing features are median-imputed from prior training; production promotion must replace any required-current missingness with fail-closed gates;
- overlap with v288 baseline is zero by construction;
- no production workflow/model was changed.

## Next restart point
- If no wave-1 variant passes, next research must change the information/ticket family rather than loosen v288 thresholds.
- Priority next: opponent/ticket re-ranking on NO_BETs, PRE-B/new-population research with full leak audit, and venue/field archetype residual models.
- Before any promotion, build live shadow scorer with fail-closed source checks and exact 10,000-yen Dutch.

## Generated artifacts
- `research_v289_3head_addon.json`
- `research_v289_3head_addon.md`



## AFTER WORK — Broad50 Wave10 nonlinear interaction result (Run 35315697326, 2026-09-18)
- Final optimized SUCCESS: Run **35315697326** / Job **105506745578** / Artifact **10535610790**; head SHA **eebc3aa7e59c99214d126ace72cc7b01b4612fff**.
- Existing PRE only; nonlinear components/interactions were predeclared; daily walk-forward; February-only diagnostic. March was not opened. September outcomes UNREAD; production v288 unchanged.
- Evaluated **84,240** nonlinear scenario/model candidates using percentile and positive-superiority gating. Components included WALL_BREAK, INNER_COLLAPSE, ATTACK_SYNERGY, COUNTER_SAFETY, geometric/min/harmonic aggregators, and selected pair/triple/four-way products.
- The nonlinear family **did not beat Wave9 at any useful support floor**. Worst-half ceiling vs Wave9:
  - >=20R/half: Wave10 **38.10%** (H1 8/21=38.10%, H2 13/34=38.24%, 21/55=38.18%) vs Wave9 39.13% (**-1.04pt**). Best: window28 / R1-8 / `wall_x_attack` q=.95 + logistic q=.95.
  - >=30R/half: **35.48%** vs 37.50% (**-2.02pt**). Best: window28 / R1-10 / `wall_min` q=.80 + logistic q=.95.
  - >=50R/half: **33.96%** vs 34.41% (**-0.45pt**). Best: window42 / R1-8 / `wall_x_attack` q=.925 + logistic q=.925.
  - >=75R/half: **31.45%** vs 34.41% (**-2.96pt**).
  - >=100R/half: **29.63%** vs 32.35% (**-2.72pt**).
  - >=150R/half: **28.49%** vs 29.74% (**-1.25pt**).
  - >=200R/half: **26.00%** vs 27.61% (**-1.61pt**).
- Weekly instability remained, especially Feb 15-21. Example >=20R best weeks: 22.22%, 50.0%, 27.78%, 50.0%.
- Conclusion: intuitive multiplicative scenario construction from the current signals does not create additional stable predictive information; the same temporal weakness remains. This rejects the hand-crafted interaction path, not all possible interactions.

## BEFORE WORK — Broad50 Wave11 automated interaction discovery on prior months (2026-09-18)
- To avoid hand-picking formulas after seeing February labels, interaction discovery will move one period earlier.
- Fetch **December 2025 + January 2026** PRE/results from BoatraceCSV. Use leakage-safe daily walk-forward with prior-day labels only.
- Generate a curated base set of oriented PRE signals, normalize each against trailing history, and automatically enumerate pairwise multiplicative interactions (plus a limited set of triple interactions selected only from prior-month evidence).
- **Discovery/selection uses January only**: require chronological Jan halves, venue dispersion and support; rank interactions by worst-half head rate, not combined rate. February labels are not used to choose which interaction formulas survive.
- Freeze the top diverse January-stable interactions, their thresholds, window/band definitions and any small interaction ensemble before February evaluation.
- February is then a one-shot transfer test for the frozen interaction family. Report the same support-size ceiling (20/30/50/75/100 per half) and direct comparison to Wave9. Do not iterate Wave11 formulas from February result.
- March remains unopened. September outcomes UNREAD; production v288 unchanged.


### Wave11 failure/repair note (Run 35316102805)
- Initial Wave11 Run **35316102805** / Job **105507965184** failed before any February transfer result was produced.
- Cause: candidate universe was generated from globally available base signals, while some rolling window/mode caches legitimately lacked an interaction column when one member signal had insufficient finite trailing support. Evaluator raised `KeyError` instead of treating that candidate as unavailable for that cache.
- Repair is implementation-only: fail-closed skip candidates whose exact interaction column is absent in that window/mode cache. Discovery rules, support floors, formulas and February transfer protocol remain unchanged. A fresh run from current main is required; do not rerun the stale failed SHA.


## AFTER WORK — Broad50 Wave11 prior-month automated interaction transfer (Run 35316272342, 2026-09-18)
- Repaired fresh SUCCESS: Run **35316272342** / Job **105508476110** / Artifact **10535127216**; head SHA **690b2d0cc12cf0b4fca818566dfa0ef985fab0a2**. Initial Run 35316102805 failed on a rolling-cache missing interaction column and produced no result; repair only added fail-closed skipping for unavailable columns.
- Discovery used December history + January labels only. February was a one-shot transfer and did not choose interaction formulas. March unopened; September UNREAD; production v288 unchanged.
- Clean source: Dec 4,647R / Jan 4,963R / Feb 3,970R; previous-session date violations 0; canonical-vs-realtime Feb winners 3970/3970 = 100%.
- Automated base set: 19 oriented PRE signals -> **171 pair interactions**. January pair discovery could reach worst-half 50% at >=20/30R per half; top signal vocabulary then generated 56 triple interactions.
- Top prior-month interaction vocabulary: vs1 national2, attack-player-inner, b1 pressure, vs2 national2, attack-start-inner, vs2 ST, vs1 ST, b2 wall-break.
- Frozen from January before February: **258 candidate settings / 33 unique interactions**.
- February transfer support frontier:
  - >=20R/half: **H1 9/22=40.91%, H2 12/30=40.00%, worst-half 40.00%, combined 21/52=40.38%**. This is **+0.87pt** worst-half over Wave9's 39.13%. Winning formula: positive-gated window21 / R1-10 / q=.95, triple `sig_vs1_全国2連対率 × sig_attack_player_inner × sig_b1_pressure`.
  - >=30R/half: worst-half **31.82%** (below Wave9 37.50%).
  - >=50R/half: **28.57%** (below 34.41%).
  - >=75R/half: **25.00%** (below 34.41%).
  - >=100R/half: **24.00%** (below 32.35%).
- Interpretation: automated prior-month interaction discovery finds a real-looking **narrow high-precision pocket around pressure on boat1**, and is the first cross-month interaction test to edge above the Wave9 20R/half ceiling. It does not yet scale in volume; larger-support transfer deteriorates sharply.

## BEFORE WORK — Broad50 Wave12 January-frozen interaction ensemble / union expansion (2026-09-18)
- Goal: test whether the narrow ~40% cross-month interaction pocket can be expanded in volume without selecting ensemble rules from February.
- Reconstruct the exact Wave11 January discovery/freeze procedure. For each unique frozen interaction, choose its representative setting using January worst-half precision/support only.
- Build January-only ensemble candidates over the top representative interactions: top-N sets (3/5/8/12/20/all available), vote thresholds including union (k=1), small-k consensus, and fractional-majority gates.
- Select/freeze ensemble definitions using January only, stratified by useful support. February does **not** select N, k, members, thresholds, windows or formula settings.
- Replay the frozen ensembles once on February and report worst-half precision at >=20/30/50/75/100 races per half. Primary comparison is Wave11 40.0% at >=20R/half and Wave9 volume ceilings.
- March remains unopened; September outcomes UNREAD; production v288 unchanged.


## AFTER WORK — Broad50 Wave12 January-frozen interaction ensemble result (Run 35316568275, 2026-09-18)
- SUCCESS: Run **35316568275** / Job **105509396833** / Artifact **10535217625**; head SHA **da6f4e9189027815dd6217d142046f6347cd161b**.
- January-only ensemble search itself produced strong in-sample stability (e.g. n_top=12,k=3: Jan H1 24/43=55.81%, H2 16/29=55.17%; n_top=20,k=5 at >=30R: 27/53=50.94%, 19/37=51.35%).
- But the frozen January ensembles did not transfer to February:
  - >=20R/half: best Feb H1 9/24=37.50%, H2 13/38=34.21%, worst-half **34.21%**, combined 22/62=35.48%.
  - >=30R/half: worst-half **34.00%**, combined 29/83=34.94%.
  - >=50R/half: worst-half **26.25%**, combined 54/195=27.69%.
  - >=75R/half: worst-half **26.25%**.
  - >=100R/half: worst-half **21.60%**, combined 88/370=23.78%.
- This is materially below Wave11's narrow single-interaction pocket (40.0% at >=20R/half) and below Wave9 at useful volumes. Conclusion: January-only voting/union over frozen interactions amplifies month-specific overfit rather than producing robust volume.
- March unopened; September UNREAD; production v288 unchanged.

## BEFORE WORK — Broad50 Wave13 multi-month persistent interaction freeze (2026-09-18)
- Goal: remove the remaining prior-month overfit by requiring interaction settings to survive **both December and January** before any February evaluation.
- Use November 2025 only as history for December walk-forward; December outcomes are first validation month. January is second validation month. February is a one-shot transfer month and does not select formulas/settings.
- Enumerate the same 19 oriented PRE base signals and pair interactions. For each exact candidate setting (window/mode/band/interaction/q), compute December H1/H2 and January H1/H2. Rank by the minimum rate across all four half-month blocks, with support/venue floors enforced in both months.
- Build triple vocabulary only from signals appearing repeatedly among pair candidates that are jointly stable in December+January. Triple settings must also pass the same two-month persistence test before freeze.
- Freeze candidate settings separately for minimum support 15/20/30/50/75/100 per half-month, deduplicate exact definitions, and then evaluate the frozen set once on February.
- Primary output is February worst-half support frontier vs Wave11 (40.0% at >=20R/half) and Wave9. No March. September UNREAD; production v288 unchanged.


## AFTER WORK — Broad50 Wave13 multi-month persistent interaction transfer (Run 35317690758, 2026-09-18)
- SUCCESS: Run **35317690758** / Job **105512857146** / Artifact **10535234565**; head SHA **4b2c2660e27fc7231e9ba761863deadb6e85d4bb**.
- Source/audit clean: Nov 3,825R / Dec 4,647R / Jan 4,963R / Feb 3,970R; February canonical-vs-realtime winner agreement remained 100%; previous-session date violations remained 0. March unopened; September UNREAD; production v288 unchanged.
- Used the same 19 oriented PRE signals -> 171 pair interactions; triple vocabulary was derived only from interactions jointly stable in December+January. Candidate settings were frozen using the minimum rate across Dec H1 / Dec H2 / Jan H1 / Jan H2, with venue/support floors, before February was scored.
- Interesting pre-Feb persistence existed: at >=15R/half-month, pair vs1 national2 × vs2 national2 reached persistent worst 50.0%; at >=20R, best persistent worst was 40.74%; at >=30R 37.93%; >=50R 37.74%; >=75R 36.05%; >=100R 34.62%.
- Frozen set: **222 settings / 28 unique interactions**.
- One-shot February transfer:
  - >=20R/half: best H1 **7/22=31.82%**, H2 **11/29=37.93%**; worst-half **31.82%**, combined 18/51=35.29%. Formula: positive window42 / R1-8 / q=.925, b1_pressure × vs1 national2 × b2_wall_break.
  - >=30R/half: H1 10/30=33.33%, H2 13/41=31.71%; worst-half **31.71%**, combined 23/71=32.39%.
  - >=50R/half: H1 16/53=30.19%, H2 20/64=31.25%; worst-half **30.19%**, combined 36/117=30.77%.
  - >=75R/half: worst-half **25.0%**, combined 55/183=30.05%.
  - >=100R/half: worst-half **24.0%**, combined 62/213=29.11%.
- Comparison: Wave13 is worse than Wave11 at >=20R (-8.18pt) and worse than Wave9 at every support tier. It only marginally exceeds Wave11 at >=50R (+1.62pt), while still well below Wave9.
- Conclusion: requiring December+January persistence does not rescue fixed multiplicative interactions. There are strong-looking interaction pockets in individual prior months, but they do not transfer reliably into February. This materially strengthens the conclusion that the current PRE feature family is regime-sensitive/nonstationary rather than missing only a simple interaction formula.
- Recommended next direction: stop searching more static pair/triple products from the same signals. If continuing with current PRE only, move to regime detection / conditional model selection (learn which interaction family is active from contemporaneous PRE distribution without target labels), or switch objective from raw head-rate to odds-aware EV where 30-40% pockets may still be valuable.
