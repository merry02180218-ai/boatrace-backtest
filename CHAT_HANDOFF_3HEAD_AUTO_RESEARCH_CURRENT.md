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



## 2026-09-20 — A+.60 opponent role-split continuation
- Frozen head/purchase gate remains A+.60; opponent research must not reduce race count.
- March remains one-shot forward validation and has NOT been used. September 2026 outcomes remain UNREAD.
- Failed Run 35518739823 / Job 106099021692 proved canonical v221 feature frame starts 2025-11-01: train_audit for 2025-11 was 0. This was a cold-start/data-window issue, not settlement/parser failure.
- Fix commit: 9886da565975726db14dac57cc7551f2a9e15956. Role-split development now starts Dec causally; Nov is explicitly cold-start excluded, not backfilled/fabricated.
- SUCCESS Run 35519413390 / Job 106100786656 / Artifact 10607738427.
- date_audit: n=35001, min=2025-11-01, max=2026-06-30, pre-Nov=0, Nov=3782.
- settlement_audit: attached=34985, parsed 3-head=4344.
- training: Dec 3782R / 455 3-head; Jan 8390R / 1015 3-head.
- Dec+Jan A+.60 head-win eval: 41R.
- Role split overall: SECOND Top1 41.46%, Top2 63.41%; conditional THIRD Top1 34.15%, Top2 58.54%; factor pair Top1/2/4/6/10 = 17.07/26.83/41.46/53.66/75.61%.
- V221 direct pair Top1/2/4/6/10 = 21.95/31.71/48.78/60.98/80.49%; simple factorized role split loses at every pair cutoff overall.
- Decision: DO NOT open March yet. Next: decompose the 41R into SECOND miss / SECOND hit but THIRD miss / factorization-order degradation, then improve SECOND using only Dec-Jan walk-forward-safe information. Keep V221 as reference and preserve race count.
