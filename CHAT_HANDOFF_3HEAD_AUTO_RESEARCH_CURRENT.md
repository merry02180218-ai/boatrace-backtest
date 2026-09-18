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



### Wave19 failure/repair + official rerun (2026-09-18)
- Run **35336822315** / Job **105573463674** failed before producing results. Exact cause: October was incorrectly requested as a PRE-score target even though October is only the historical training month in the Wave17 protocol; its prediction frame could be empty, leading to `AttributeError: DataFrame has no attribute family`.
- Implementation-only repair commit **ebf7dc23095de8a0bab2702f2b1b49bd9d443377**: score only Nov-Dec-Jan-Feb and keep October as PRE history. Research gates/features/thresholds unchanged. Fresh Run **35345961408** started but is superseded by the performance-only rerun below.
- Performance-only commit **ec7ed0bcf300544c3b66fc02a2586bcab6d20a2d**: Wave19 uses only the frozen 42-day Logistic PRE score actually needed by the candidate grid, instead of recomputing unused 21-day and HistGradient models. Also removes unused September-2025 PRE build; October remains the training-history month exactly as in Wave17. No selection rule, labels, or feature definitions changed.
- New official fresh Run **35346043952** from head SHA **ec7ed0bcf300544c3b66fc02a2586bcab6d20a2d**. Use this run for the formal Wave19 result. Run 35345961408 is superseded even if it completes.
