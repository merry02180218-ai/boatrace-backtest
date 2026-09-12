# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research branch: `research/3head-v289-addon-expansion`
- v288 production is **unchanged**.
- fixed production-compatible baseline: **94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%**.
- July/August are **NON-PRISTINE**.
- September outcomes are **not loaded / not used for tuning**.
- frozen canonical source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.

## Wave 1 — final-NO_BET signal ranking
- Run `34703862487`, artifact `v289-3head-addon-wave1`, artifact ID `10300816836`.
- candidate pool: **178R**.
- best: `return_rank@0.45` = **84R / 15 hits / ROI 54.92% / profit -378,700 yen**.
- combined: 178R / ROI 117.04%.
- decision: **NO_ADOPTION_WAVE1**.
- dead ends retained: residual_hit, exhibition_upgrade, return_rank, attack_style_split, orthogonal_consensus, ev_calibrated.

## Wave 2 — ticket structure while keeping frozen V221 opponent order
- Run `34703969778` success; artifact `v289-3head-addon-wave2-ticket-structure`, ID `10301039743`.
- best fixed Top10: **177R / 45 hits / ROI 57.70% / profit -748,660 yen / minimum monthly ROI 24.50% / 7 red months**.
- prior-month-only selectors all chose 0 add-on races.
- decision: **NO_ADOPTION_WAVE2**.

## Wave 3 — independent PRE-B LIVE rescue
- Run `34704413463` success; artifact `v289-3head-addon-wave3-preb`, ID `10301232830`.
- raw PRE-B buyable pool: **81R / 23 hits / ROI 84.42%**.
- tiny positive `preb_ev@0.20` = **5R / 2 hits / ROI 117.28%**, rejected for sample and 0% minimum month.
- best 20+ race variant: **26R / 6 hits / ROI 67.47%**.
- decision: **NO_ADOPTION_WAVE3**.

## Wave 4 — venue / field-archetype residual research
- Run `34706093149` success; artifact `v289-3head-addon-wave4-archetype`, ID `10301509909`.
- only positive result: **2R / 1 hit / ROI 156.40%**, rejected for sample size.
- venue-local / venue×archetype / venue-ROI gate selected 0 with sample guards.
- decision: **NO_ADOPTION_WAVE4**.

## Wave 5 — TRUE ordered-pair re-ranking
- Run `34706218140` success; artifact `v289-3head-addon-wave5-pair-rerank`, ID `10302397653`.
- generated-results commit `b35fa0ccb73dacf0c1d7a365bca137d3012a6bf6`.
- best `ev_target3` / `ev_top10`: **178R / 24 hits / ROI 82.29% / profit -315,260 yen / minimum monthly ROI 0% / 6 red months / max DD 663,710 yen**.
- combined v288 + add-on: **272R / ROI 113.49%**.
- decision: **NO_ADOPTION_WAVE5**.

## Wave 6 — separate 2nd-place / 3rd-place role models
- Run **`34710538598`** completed successfully.
- generated-results commit **`7d082f4b5401b8acd979675e608e4d120dd621dd`**.
- artifact expected/recorded by workflow: `v289-3head-addon-wave6-role-split`.
- separate 2着/3着 role models trained only on prior-month reject races where boat 3 won.
- best method `role_ev_top10`: **178R / 24 hits / ROI 66.16% / profit -602,410 yen / minimum monthly ROI 0% / 7 red months / max DD 688,360 yen**.
- combined v288 + add-on: **272R / ROI 102.93%**.
- `role_ev_target3`: 178R / 23 hits / ROI 65.34%.
- product variants were worse: ROI 48.47%–52.94%.
- decision: **NO_ADOPTION_WAVE6**.
- rejection reason: independent role decomposition worsened Wave5 and failed every robustness gate.

## Wave 7 — attack-style-conditioned role models
- auto-restarted because Wave6 finished with no active next research run.
- script: `research_v289_3head_addon_wave7_attack_role.py`.
- workflow: `.github/workflows/research-3head-v289-addon-wave7-attack-role.yml`.
- script commit: `e527d88d24fa93158bfd0ea1eba8b59416e30861`.
- workflow creation commit: `475c6913e5a8f5972822aa24061def3593d39da2`.
- explicit trigger commit: `9a10c3b52d7a293dfca9b05925f32c83899a80d7`.
- Actions Run **`34712587015`** currently in progress.
- candidate remains only final v288 NO_BET.
- pre-race regime is derived from `f__c_attack3_stretch` vs `f__c_attack3_turn`; missing regime => fail closed.
- separate 2着/3着 role models are trained within the same prior-month regime only; no current-month outcome enters fitting.
- variants: attack-role product / odds-EV × target3 / Top10; exact 10,000-yen Dutch.
- required output: add-on R/hits/hit rate/ROI/profit, monthly ROI, minimum month ROI, red months, max DD, v288 overlap, combined totals.
- expected artifact: `v289-3head-addon-wave7-attack-role`.

## What NOT to repeat
- simple Wave1 coverage/threshold tweaks.
- TopN/composite-odds changes on frozen V221 order.
- PRE-B families already tested in Wave3.
- venue/archetype segmentation without adequate sample.
- Wave5 ordered-pair reranking unchanged.
- Wave6 global 2nd/3rd role split unchanged.

## Real-operation audit
- v288 baseline overlap must remain zero.
- every test-month fit uses only prior-month outcomes; current-month result/payout is settlement/evaluation only.
- source max date 2026-08-31; September outcomes excluded from tuning.
- all inputs used for any shadow/production route must be obtainable before deadline; required-current missingness must fail closed.
- exact 10,000-yen Dutch settlement retained.
- no production workflow/model changed.

## Exact restart point
1. Finish Wave7 Run `34712587015`; inspect/fix/re-run automatically if it fails.
2. If Wave7 passes historical gates (>=20R, ROI>=100%, minimum monthly ROI>=60%, <=3 red months), advance only to September outcome-blind shadow.
3. If rejected, next family must be genuinely distinct again: motor/racer-role conditioned ordering or a new PRE candidate-generation population; do not revisit Wave1–6 unchanged.
