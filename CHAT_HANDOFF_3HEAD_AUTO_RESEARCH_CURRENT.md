# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research branch: `research/3head-v289-addon-expansion`
- v288 production: **unchanged**
- fixed production-compatible baseline: **94R / 52 hits / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%**
- July/August: **NON-PRISTINE**
- September outcomes used for tuning: **NO**
- source for wave1: frozen canonical v243 artifact from Run `34383567078`, artifact `v243-3head-expand-feature-audit` (artifact id `10118044294`), max date 2026-08-31.

## Wave 1 — v289 NO_BET add-on ranking
- Actions Run: `34703771330`
- artifact: `v289-3head-addon-wave1`
- artifact id: `10301626123`
- research/scoring steps and leakage/baseline guards: **success**
- final workflow status was failure only at the report-persist git-push step after the branch advanced concurrently; the uploaded research artifact is valid and the reports are persisted manually here.
- candidate universe: operational PRE S/A + v242-buyable + final v288 `NO_BET` only.
- candidate pool: **178R**.

### Wave-1 result
Decision: **NO_ADOPTION_WAVE1**.

Best tested variant was `return_rank@0.45`:
- add-on: **84R / 15 hits / ROI 54.92% / profit -378,700 yen**
- combined with fixed v288: **178R / ROI 117.04%**
- this materially degrades the v288 baseline, so it is rejected.

Other tested families were also rejected:
- `residual_hit`: prior-reject outcome-effect ranking over safe pre-race/live features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family.
- `return_rank`: prior-reject realized-return ranking, prior months only.
- `attack_style_split`: stretch-vs-turn regimes followed by prior-trained ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score + current composite odds, alpha selected on prior months only.

All tested Wave-1 add-ons were below 100% ROI. Do **not** repeat these variants merely with looser/tighter coverage fractions.

## Real-operation audit for Wave 1
- baseline overlap: **0 by construction**.
- test-month decisions were fitted only on prior-month outcomes.
- current test-month result/payout was used only after decision for settlement/evaluation.
- source ends 2026-08-31; September outcomes were not loaded.
- all score inputs exist in the canonical pre-settlement v243/v288 audit data.
- research imputed missing historical features with prior-training medians; any production/shadow promotion must instead fail closed on required current inputs.
- no production workflow/model was changed.

## Next research — Wave 2
Do **not** relax v288 thresholds. Change the information/ticket family.

Priority order:
1. Rebuild the frozen V221 ordered-ticket ranking for historical v288 NO_BETs and test alternative ticket counts / target composite odds with exact 10,000-yen Dutch settlement.
2. Evaluate each ticket policy with strict prior-month walk-forward selection; keep add-on-only metrics separate from the 94R baseline.
3. If ticket-only family fails, research PRE-B/new-population routes and opponent re-ranking with a full leakage/source audit.
4. Venue/field archetype segmentation only when prior-training sample size is adequate.
5. A challenger may advance only to September outcome-blind shadow; it does not replace v288 from historical model-selection results alone.

## Mandatory metrics for every later wave
- add-on BETs / hits / hit rate / payout / profit / ROI
- monthly ROI, red-month count, minimum monthly ROI
- max drawdown
- overlap with v288
- combined v288 + add-on totals
- pre-race source availability / fail-closed viability
- failed trials and rejection reason
- Run ID / artifact name + ID / latest commit SHA

## Exact restart point
Implement and run **Wave 2 ticket-structure research** from this branch, using the fixed 94R v288 baseline and the frozen v243 source. Preserve Wave-1 failure evidence.