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
