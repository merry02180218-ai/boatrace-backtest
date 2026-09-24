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



## 2026-09-24 A+ high-precision decision
- Exact accepted CORE remains 107R.
- A+ selected working boundary: PRE >= 0.970, PLAYERHistory >= 0.50, motor >= 0.60.
- Dec 2025-Aug 2026, exact-CORE excluded: 97R / 47 heads = 48.4536%, avg 10.8R/month.
- Monthly: Dec 6/4 66.67%; Jan 13/8 61.54%; Feb 11/2 18.18%; Mar 19/9 47.37%; Apr 10/4 40.00%; May 10/6 60.00%; Jun 8/5 62.50%; Jul 12/6 50.00%; Aug 8/3 37.50%.
- Higher precision shadow candidate only (NOT adopted): motor >= .85, PRE >= .925, PH >= .65 => 21R/13 heads = 61.90%.
- User accepted current A+ working boundary; stop further A+ tuning for now.
- Next: recompute layered CORE -> A+ -> FULL_3V2 with exact race-code dedup, target combined volume around 40 races/month.
- September outcomes remain UNREAD. Production unchanged.


## 2026-09-24 overlap handling update
- User decision: model overlaps are NOT discard-only. Treat any race selected by 2+ of CORE / A+ / FULL_3V2 as 注目レース.
- Monthly total volume counts a duplicated race once, but report overlap count and overlap combination separately.
- Keep each model flag so overlap identity is visible in LIVE/research outputs.
