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


## AFTER WORK — fun-site wide-schema baseline (Run 35296265896)
- SUCCESS: Run 35296265896 / Job 105449323190 / Artifact 10527334659.
- Head SHA f2730aeb81922a0f6c31d38c7e652f5e84ba4432; wide-schema parser commit 5b6b19de7e5c2d541ec5b6a50cbebdbfee911ae6.
- Sources 59/59 days each; fun-site 8,707 races; joined Feb 3,970 / Mar 4,482; 180 PRE features; current-meet session fields excluded; September outcomes UNREAD.
- March frozen one-shot: 50%-target 29R/6=20.69%; 45%-target 107R/36=33.64%; 40%-target 169R/59=34.91% (early 84/30=35.71%, late 85/29=34.12%).
- Conclusion: simple balanced logistic + one score threshold does NOT achieve 50%; do not promote.

## BEFORE WORK — broader 50% head-rate search (2026-09-18)
- User explicitly requests broader hypothesis search; do not stop at the 169R/59 baseline.
- Keep production v288 unchanged and September outcomes UNREAD.
- Search materially different PRE-only model families and interactions: nonlinear tree/boosting models, calibrated logistic variants, explicit boat3-vs-each-opponent matchup features, rank/margin features, recent national/local form interactions, venue/grade/race-number regimes where available, and ensemble/consensus gates.
- February remains the only model/threshold selection period; use chronological splits / stability constraints inside February. March labels are one-shot diagnostics per frozen candidate family, not iterative tuning feedback.
- Report Pareto frontier emphasizing >=50% March head rate with meaningful N; also >=45/40 bands, early/late stability, venue dispersion, and incremental/overlap versus prior 169R baseline/Wave54 where reproducible.
- Explicitly guard against tiny-N 50% artifacts and feature leakage.
