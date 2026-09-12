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
- candidate pool: **178R**; best `return_rank@0.45` = **84R / 15 hits / ROI 54.92% / profit -378,700 yen**; combined ROI 117.04%.
- decision: **NO_ADOPTION_WAVE1**.
- dead ends retained: residual_hit, exhibition_upgrade, return_rank, attack_style_split, orthogonal_consensus, ev_calibrated.

## Wave 2 — ticket structure on frozen V221 opponent order
- Run `34703969778`, artifact `v289-3head-addon-wave2-ticket-structure`, ID `10301039743`.
- best Top10: **177R / 45 hits / ROI 57.70% / profit -748,660 / min month 24.50% / 7 red**; prior-month selectors chose 0 races.
- decision: **NO_ADOPTION_WAVE2**.

## Wave 3 — independent PRE-B LIVE rescue
- Run `34704413463`, artifact `v289-3head-addon-wave3-preb`, ID `10301232830`.
- raw pool **81R / 23 hits / ROI 84.42%**; tiny 5R positive rejected; best 20+ race variant **26R / 6 hits / ROI 67.47%**.
- decision: **NO_ADOPTION_WAVE3**.

## Wave 4 — venue / field-archetype residual
- Run `34706093149`, artifact `v289-3head-addon-wave4-archetype`, ID `10301509909`.
- only positive **2R / 1 hit / ROI 156.40%**, rejected for sample; guarded local models otherwise selected 0.
- decision: **NO_ADOPTION_WAVE4**.

## Wave 5 — TRUE ordered-pair re-ranking
- Run `34706218140`, artifact `v289-3head-addon-wave5-pair-rerank`, ID `10302397653`, result commit `b35fa0ccb73dacf0c1d7a365bca137d3012a6bf6`.
- best: **178R / 24 hits / ROI 82.29% / profit -315,260 / min month 0% / 6 red / max DD 663,710**; combined **272R / ROI 113.49%**.
- decision: **NO_ADOPTION_WAVE5**.

## Wave 6 — separate 2nd / 3rd role models
- Run `34710538598` success; result commit `7d082f4b5401b8acd979675e608e4d120dd621dd`; artifact `v289-3head-addon-wave6-role-split`.
- best `role_ev_top10`: **178R / 24 hits / ROI 66.16% / profit -602,410 / min month 0% / 7 red / max DD 688,360**; combined **272R / ROI 102.93%**.
- decision: **NO_ADOPTION_WAVE6**.

## Wave 7 — attack-style-conditioned role models
- canonical successful Run **`34712604315`**; artifact `v289-3head-addon-wave7-attack-role`, ID **`10304192454`**; result commit **`2ce77cd52af26b419883401d8790cf1582cfb2b9`**.
- an overlapping earlier Run `34712587015` computed and guarded successfully but failed only during report persistence because the successful concurrent Run had already added the same result files; do not treat that persistence conflict as research failure.
- best `attack_role_ev_target3`: **178R / 25 hits / hit 14.04% / ROI 63.39% / profit -651,720 / min month 0% / 7 red / max DD 723,200 / overlap 0**; combined **272R / ROI 101.12%**.
- `attack_role_ev_top10`: ROI 62.63%; product variants ROI 53.00%–53.93%.
- decision: **NO_ADOPTION_WAVE7**.
- rejection: attack-style conditioning did not improve robustness or add-on profitability.

## Wave 8 — motor/racer-regime-conditioned role models
- auto-restarted after Wave7 rejection with no active next research family.
- script: `research_v289_3head_addon_wave8_motor_racer_role.py`.
- workflow: `.github/workflows/research-3head-v289-addon-wave8-motor-racer-role.yml`.
- script commit: **`4e852982f04df6eb9d5d59aebeb888059bf43165`**.
- workflow creation commit: **`520d45ab980e557c229fac2e5af3bd749d771f90`**.
- explicit trigger commit: **`c66b5d48436f426aa6c44e0e8bfaba8a4fff8125`**.
- Actions Run **`34719074934`** is in progress.
- candidate remains only final v288 NO_BET.
- pre-race regime: sign of mean boat3 inside/outside motor edge × sign of mean boat3 inside/outside past-win edge, giving M+R+, M+R-, M-R+, M-R-; missing any required input => fail closed.
- separate 2着/3着 role models are fitted only from prior-month reject races in the same regime where boat3 won.
- variants: motor/racer role product or odds-EV × target3 or Top10; exact 10,000-yen Dutch.
- required metrics: add-on R/hits/hit rate/ROI/profit, monthly ROI, min month ROI, red months, max DD, overlap, combined totals.
- expected artifact: `v289-3head-addon-wave8-motor-racer-role`.

## What NOT to repeat
- Wave1 coverage/threshold tweaks; frozen-V221 TopN/odds-target changes; Wave3 PRE-B families; undersampled venue segmentation; Wave5 ordered-pair unchanged; Wave6 global role split unchanged; Wave7 attack-style role split unchanged.

## Real-operation audit
- v288 overlap must remain zero.
- every test-month fit uses only prior-month outcomes; current-month result/payout enters settlement only.
- source max date 2026-08-31; September outcomes excluded from tuning.
- all production/shadow inputs must be available pre-deadline; required-current missingness fails closed.
- exact 10,000-yen Dutch retained; production v288 workflow/model unchanged.

## Exact restart point
1. Finish Wave8 Run `34719074934`; inspect/fix/re-run automatically if it fails.
2. If historical gates pass (>=20R, ROI>=100%, min monthly ROI>=60%, <=3 red months), advance only to September outcome-blind shadow.
3. If rejected, move to a genuinely new PRE candidate-generation population with full leak audit; do not retune Wave1–7 families.
