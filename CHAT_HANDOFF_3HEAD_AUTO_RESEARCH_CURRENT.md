# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research version: `v289-addon-wave1`
- decision: **NO_ADOPTION_WAVE1**
- v288 production is unchanged; baseline replay assertion is 94R / 52 hits / payout 1,622,070 yen.
- July/August are NON-PRISTINE. September outcomes were not loaded or used.
- Candidate universe is only v288 final NO_BET among operational PRE S/A and v242-buyable races.

## GitHub / CI provenance
- infrastructure merged to main by PR #2; merge SHA: `bf26c1fe1ba5974341a6f204b583c7c9e68358b0`
- research branch: `research/3head-v289-addon-expansion`
- successful Actions run: `34703862487`
- run head SHA: `f47d1df93112340dcdc9042c5ce131bb70bafcb1`
- generated-results commit: `40dedd505e624cd5645fec97969330299e9d0249`
- artifact: `v289-3head-addon-wave1`
- artifact ID: `10300816836`
- guard markers: baseline 94R/52 hits/payout 1,622,070 yen; source max date <= 2026-08-31; September outcomes unused; v288 overlap zero.

## Wave-1 result
- candidate pool: 178 races
- best tested variant: `return_rank@0.45`
- best add-on: 84R / 15 hits / ROI 54.92% / profit -378,700 yen
- combined: 178R / ROI 117.04%
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
- all scoring inputs are columns already present before settlement in the canonical v243/v288 audit artifact;
- decisions use only prior-month outcomes for fitting; current test-month result/payout enters settlement only;
- missing features are median-imputed from prior training; production promotion must replace any required-current missingness with fail-closed gates;
- overlap with v288 baseline is zero by construction;
- no production workflow/model was changed.

## Next restart point
- Move to **wave 2**, changing the information/ticket family rather than loosening v288 thresholds.
- Priority 1: opponent/ticket re-ranking specifically on NO_BETs; current v242 tickets may be the bottleneck.
- Priority 2: PRE-B / new-population expansion with full leakage/source-availability audit, kept separate from the fixed 94R baseline.
- Priority 3: venue/field-archetype residual models with minimum sample guards.
- Before any production promotion, build live shadow scorer with fail-closed source checks, no duplicate bets, and exact 10,000-yen Dutch.

## Generated artifacts
- `research_v289_3head_addon.json`
- `research_v289_3head_addon.md`
- `CHAT_HANDOFF_3HEAD_AUTO_RESEARCH_CURRENT.md`
