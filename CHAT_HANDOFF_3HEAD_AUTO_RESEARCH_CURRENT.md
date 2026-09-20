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



## 2026-09-20 — Adopted A+.60 opponent-model stage
- Adopted head gate remains frozen: PRE q>=.925, boat3 motor EWMA-rank edge vs boat2 >= +0.20, boat3 current exhibition rank=1.
- Adopted purchase gate remains frozen: post_motor_inner_rank_edge >= +0.60.
- Nov-Jan development cohort reproduced: 118R / 54 boat3 wins = 45.76%.
- March venue-aware forward audit remains 33 purchases / 16 boat3 wins / 12 ticket hits / ROI 106.61%; March is validation only, not tuning.
- Loss-pattern research complete. motor-edge1 extra filter was rejected; do not alter A or +0.60.
- Opponent reference audit SUCCESS: Run 35467021760 / Job 105961123488 / Artifact 10591343589.
- Among 54 boat3 wins: SECOND counts 1=20,4=18,2=10,5=5,6=1; THIRD counts 6=15,4=12,5=11,2=8,1=8.
- Reference architecture frozen for next research: 1HEAD factorized SECOND+THIRD preferred over direct ordered pair; 4HEAD separate SECOND and scenario/conditional THIRD, then TOP2xTOP2 composition.
- Existing 3HEAD baseline remains V221 direct ordered-pair ranking + v242 variable TopN/Dutch.
- Next: develop role-split SECOND + conditional THIRD on Nov-Jan/earlier causal data, compare against V221 by SECOND Top1/Top2, THIRD Top1/Top2, exact-pair Top1/2/4/6/10 and monthly stability. Do not use March for selection; after freeze, one-shot March compare against current 12/16 opponent/ticket capture. September 2026 outcomes remain UNREAD.
