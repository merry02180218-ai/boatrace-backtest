# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research branch: `research/3head-v289-addon-expansion`
- v288 production is **unchanged**.
- fixed production-compatible baseline: **94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%**.
- July/August are **NON-PRISTINE**.
- September outcomes are **not loaded / not used for tuning**.
- frozen canonical source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.
- latest completed research-results commit before this handoff update: `75c2094a51907d8e40fac4872fa9969695a87c8c`.

## Wave 1 — final-NO_BET signal ranking
- Run `34703862487`, artifact `v289-3head-addon-wave1`, artifact ID `10300816836`.
- candidate pool: **178R**.
- best: `return_rank@0.45` = **84R / 15 hits / ROI 54.92% / profit -378,700 yen**.
- combined: 178R / ROI 117.04%.
- decision: **NO_ADOPTION_WAVE1**.
- dead ends retained: residual_hit, exhibition_upgrade, return_rank, attack_style_split, orthogonal_consensus, ev_calibrated.

## Wave 2 — ticket structure while keeping frozen V221 opponent order
- Run `34703969778` completed successfully.
- artifact: `v289-3head-addon-wave2-ticket-structure`, artifact ID **`10301039743`**.
- generated-results commit: `1b8bd73ededaab51b854bd029ce588993846439e`.
- population: operational PRE S/A + original v242-buyable + final v288 NO_BET only.
- tested fixed Top2..Top10; target composite odds 2.5 / 3 / 3.5 / 4 / 5 / 6 / 8; exact 10,000-yen Dutch.
- best fixed structure: **Top10 = 177R / 45 hits / ROI 57.70% / profit -748,660 yen / minimum monthly ROI 24.50% / 7 red months**.
- prior-month-only selectors `wf_profit`, `wf_stable`, `wf_recent` all chose **0 add-on races**, correctly refusing the weak pool.
- decision: **NO_ADOPTION_WAVE2**.
- interpretation: changing only ticket count/composite-odds target while retaining frozen V221 order does not rescue v288 NO_BETs.

## Wave 3 — independent PRE-B LIVE rescue
- not an S/A threshold relaxation; separate PRE-B population.
- Run `34704413463` success; artifact `v289-3head-addon-wave3-preb`, artifact ID **`10301232830`**.
- generated-results commit `258ec82`.
- raw PRE-B buyable pool: **81R / 23 hits / ROI 84.42%**.
- best numerical ROI: `preb_ev@0.20` = **5R / 2 hits / ROI 117.28% / profit +8,640 yen**, but only 5 races and minimum monthly ROI 0%, so rejected.
- best 20+ race variant: `preb_return_rank@0.50` = **26R / 6 hits / ROI 67.47% / profit -84,590 yen / minimum monthly ROI 36.93%**.
- decision: **NO_ADOPTION_WAVE3**.
- tiny-sample positive ROI is explicitly rejected.

## Wave 4 — venue / field-archetype residual research
- distinct family added after Wave 2 completed; v288 thresholds and tickets unchanged.
- Run **`34706093149`** success.
- run head SHA `4217631f55ecfa2b0555942e9e11b9870d2f1308`.
- artifact `v289-3head-addon-wave4-archetype`, artifact ID **`10301509909`**.
- generated-results commit **`75c2094a51907d8e40fac4872fa9969695a87c8c`**.
- candidate pool: **178R**.
- tested: venue-local, field-archetype-local, venue×archetype, prior-venue-ROI gate; each month prior-month-only with minimum local sample guards.
- only positive numerical variant: `archetype_local@0.25` and `@0.40` = **2R / 1 hit / ROI 156.40% / profit +11,280 yen**.
- this is rejected because sample is only 2 races; it does not satisfy the >=20 race robustness gate.
- venue-local / venue×archetype / venue-ROI-gate routes selected 0 races after minimum-sample guards.
- decision: **NO_ADOPTION_WAVE4**.

## What NOT to repeat
- simple coverage-fraction tweaks of Wave-1 scores.
- simple TopN/composite-odds changes on frozen V221 order.
- PRE-B families already tested in Wave 3.
- venue/archetype segmentation without enough prior sample; the 2R positive result is not promotion evidence.

## Real-operation audit
- v288 baseline overlap is zero by construction in the add-on populations.
- every test-month fit uses prior-month outcomes only; current-month result/payout is settlement/evaluation only.
- source max date is 2026-08-31; September outcomes are excluded from tuning.
- research-time historical missing features may use prior-training imputation; any shadow/production route must fail closed on missing required current inputs.
- no production workflow/model was changed.

## Exact next restart point
1. Start **Wave 5 true opponent re-ranking**. Wave 2 proved ticket-count changes are not enough; next research must change the opponent / trifecta ordering itself using only prior-month evidence and pre-race-available inputs.
2. Keep v288 94R fixed and evaluate only add-on races outside baseline; report add-on-only metrics separately.
3. Candidate Wave-5 families: pair-position residual model, opponent-order model by 2nd/3rd-place racer strength, calibrated ticket-level EV, and independent consensus of opponent order vs current V221.
4. Require exact 10,000-yen Dutch, pre-race odds only, zero overlap, monthly metrics, max DD, and source/fail-closed audit.
5. Any historical passer advances only to **September outcome-blind shadow**; never directly replace v288.
