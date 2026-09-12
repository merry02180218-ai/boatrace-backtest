# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research version: `v289-addon-wave1`
- decision: **NO_ADOPTION_WAVE1**
- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.
- July/August are NON-PRISTINE. September outcomes were not loaded or used.
- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.

## GitHub / CI provenance
- infrastructure merged by PR #2; merge SHA: `bf26c1fe1ba5974341a6f204b583c7c9e68358b0`
- research branch: `research/3head-v289-addon-expansion`
- successful Actions run: `34703862487`
- run head SHA: `f47d1df93112340dcdc9042c5ce131bb70bafcb1`
- generated-results commit on research branch: `40dedd505e624cd5645fec97969330299e9d0249`
- artifact: `v289-3head-addon-wave1`
- artifact ID: `10300816836`
- guards passed: source max date <= 2026-08-31; September outcomes unused; baseline exactly 94R/52 hits/payout 1,622,070 yen; overlap with v288 zero.

## Wave-1 result
- candidate pool: 178 races
- best tested variant: `return_rank@0.45`
- best add-on: 84R / 15 hits / hit rate 17.86% / ROI 54.92% / profit -378,700 yen
- add-on max drawdown: 397,300 yen
- combined v288 + best add-on: 178R / 67 hits / ROI 117.04% / profit +303,370 yen
- combined max drawdown: 177,340 yen
- best add-on monthly ROI: Feb 72.05%, Mar 83.80%, Apr 98.60%, May 58.62%, Jun 21.07%, Jul 50.42%, Aug 56.74%; minimum 21.07%.
- conclusion: **do not adopt**. The combined ROI remains positive only because the fixed v288 baseline carries the weak add-on; add-on-only performance is unacceptable.

## Methods tested / dead ends retained
- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family only.
- `return_rank`: prior-reject realized-return ranking trained only on prior months.
- `attack_style_split`: separate stretch-vs-turn regimes, then outcome ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score plus current composite odds, alpha chosen on prior months only.
- Wave 1 shows that simply ranking the existing v242-ticket NO_BET pool with these signal families is not enough; do not repeat this family unchanged.

## Real-operation audit
- all scoring inputs are pre-settlement columns from the canonical v243/v288 audit artifact;
- current test-month result/payout is settlement-only and never used to fit that month;
- overlap with v288 baseline is zero by construction;
- no v288 production model or production workflow was changed;
- any future promoted live scorer must replace research median-imputation for required current inputs with explicit fail-closed source checks.

## Next restart point — wave 2
1. Opponent/ticket re-ranking specifically on v288 NO_BETs; the existing v242 ticket family may be the bottleneck.
2. PRE-B / new-population expansion with a fresh full leakage/source-availability audit, kept separate from the fixed 94R baseline.
3. Venue/field-archetype residual models with minimum sample guards.
4. Any candidate that survives research must first run as live shadow: pre-race obtainable inputs only, fail closed, no duplicate betting, variable tickets if justified, exact 10,000-yen Dutch.

## Generated evidence
- Actions run `34703862487`
- Artifact `v289-3head-addon-wave1` (ID `10300816836`)
- research branch files: `research_v289_3head_addon.json`, `research_v289_3head_addon.md`, `CHAT_HANDOFF_3HEAD_AUTO_RESEARCH_CURRENT.md`
