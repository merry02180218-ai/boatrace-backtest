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



## 2026-09-21 — Waku10 restored-source v288 audit (WORK START)
- User reports historical Waku10 restoration is complete. Fresh main confirms shared Boatcast Waku10 Mar-Jun commit 6410b14d, July shared store edcb7be3, and nested-loader fix 44231256.
- Existing v288 operational parity remains frozen reference: 94R total, Feb8/Mar12/Apr12/May16/Jun14/Jul13/Aug19. Do not alter thresholds/routes while measuring Waku10 source effect.
- February fair overlap audit Run 35563969125 was SUCCESS: v288 8R/6 heads=75%, A+.60 32R/12 heads=37.5%, BOTH=0; Sep-2026 unused; no threshold tuning.
- Next: build a source-only Waku10 audit for v288. Compare frozen v288 reference vs restored historical Waku10 with all v288 thresholds unchanged. Measure changed Waku34 values, candidate additions/removals, route changes, race count/head rate; only after membership freeze inspect outcomes. September 2026 outcomes remain UNREAD.

- Waku10 audit Run 35579065473 / Job 106267460878 FAILED before main audit. Preflight passed. Root cause: workflow downloaded wrong artifact Run 35467021760 / research-3head-a-opponent-reference-audit, which contains only reference JSON and not analysis_v243_3head_expand_feature_audit.csv. Main audit was skipped; no outcomes read.
- Verified canonical source path from successful v288 parity workflow: Run 34383567078 artifact v243-3head-expand-feature-audit / analysis_v243_3head_expand_feature_audit.csv. Workflow fixed to use this exact source and added required-column contract check. Fix commit 5af7a5b4440923c15ad50b4c9f36da8510963da7. Do not rerun old failed attempt unchanged.

- Restored Waku10 membership audit SUCCESS: Run 35580738921 / Job 106272777317 / Artifact 10630525833. Outcome-free; thresholds unchanged; September outcomes unread. Old v288 operational membership 94R -> restored 96R, with NO removals. Added only 2 races: 202607222309 and 202608080206. Monthly old->restored: Feb 8->8, Mar 12->12, Apr 12->12, May 16->16, Jun 14->14, Jul 13->14, Aug 19->20. Restored routes: Feb S7/A1/B0; Mar S8/A2/B2; Apr S8/A3/B1; May S9/A3/B4; Jun S4/A6/B4; Jul S7/A3/B4; Aug S16/A2/B2. Coverage restored all source rows except 1 June row (72/73); old Waku values differ widely from reconstructed exact values, so next step must audit formula/semantics before settlement, not immediately treat all reconstructed values as canonical. Membership is frozen before any outcome read.
