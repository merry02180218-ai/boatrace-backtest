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


## 2026-09-20 A-head + purchase gate — USER ADOPT / NEXT RESEARCH
- User decision: adopt this head model as the working 3HEAD head-selection model.
- Frozen A head gate remains unchanged: PRE percentile >= .925, boat3 prior-day motor EWMA-rank edge vs boat2 >= +.20, boat3 current exhibition-time rank = 1st.
- Separate purchase gate adopted for working use: post_motor_inner_rank_edge >= +.60. Threshold was selected on Nov-Jan development only; March was one-shot evaluation, not retuning.
- Full March venue-aware audit Run 35456035513 / aggregate Job 105932827239 / Artifact 10588428193: 52/52 evaluable, 0 errors, 33 BET, 19 NO_BET, 12 ticket hits, stake 330,000, payout 351,800, profit +21,800, ROI 106.61%; BET head3 16/33=48.48%; captured 16/21 March head3 winners=76.19%.
- Edogawa JCD03 has no original exhibition. 3HEAD replay now follows HEAD4 venue-aware original-exhibition contract; do not treat Edogawa missing original exhibition as an error.
- September 2026 settlement outcomes remain UNREAD / unused.
- Next order explicitly requested by user: (1) research losing patterns inside the adopted head/purchase model WITHOUT changing the frozen head gate or .60 purchase threshold; (2) after loss-pattern research, design/research the opponent model / ticket ranking.
- Keep opponent work separate from head-model research so head selection is not retuned to ticket outcomes.
