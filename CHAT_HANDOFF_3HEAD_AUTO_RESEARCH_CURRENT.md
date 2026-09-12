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
- Run `34703969778` completed successfully.
- artifact `v289-3head-addon-wave2-ticket-structure`, artifact ID **`10301039743`**.
- generated-results commit `1b8bd73ededaab51b854bd029ce588993846439e`.
- tested fixed Top2..Top10; target composite odds 2.5 / 3 / 3.5 / 4 / 5 / 6 / 8; exact 10,000-yen Dutch.
- best fixed: **Top10 = 177R / 45 hits / ROI 57.70% / profit -748,660 yen / minimum monthly ROI 24.50% / 7 red months**.
- prior-month-only selectors `wf_profit`, `wf_stable`, `wf_recent` all chose **0 add-on races**.
- decision: **NO_ADOPTION_WAVE2**.
- interpretation: changing ticket count/composite-odds target while retaining frozen V221 order does not rescue v288 NO_BETs.

## Wave 3 — independent PRE-B LIVE rescue
- not an S/A threshold relaxation; separate PRE-B population.
- Run `34704413463` success; artifact `v289-3head-addon-wave3-preb`, artifact ID **`10301232830`**.
- raw PRE-B buyable pool: **81R / 23 hits / ROI 84.42%**.
- best numerical ROI: `preb_ev@0.20` = **5R / 2 hits / ROI 117.28% / profit +8,640 yen**, but only 5 races and minimum monthly ROI 0%, rejected.
- best 20+ race variant: `preb_return_rank@0.50` = **26R / 6 hits / ROI 67.47% / profit -84,590 yen / minimum monthly ROI 36.93%**.
- decision: **NO_ADOPTION_WAVE3**.

## Wave 4 — venue / field-archetype residual research
- Run **`34706093149`** success.
- artifact `v289-3head-addon-wave4-archetype`, artifact ID **`10301509909`**.
- generated-results commit `75c2094a51907d8e40fac4872fa9969695a87c8c`.
- candidate pool: **178R**.
- tested venue-local, field-archetype-local, venue×archetype, prior-venue-ROI gate with prior-month-only local fitting and minimum-sample guards.
- `archetype_local@0.25` / `@0.40`: **2R / 1 hit / ROI 156.40% / profit +11,280 yen**, but only 2 races so explicitly rejected.
- venue-local / venue×archetype / venue-ROI-gate selected 0 races once sample guards were enforced.
- decision: **NO_ADOPTION_WAVE4**.

## Wave 5 — TRUE opponent / 2着3着 order re-ranking
- **currently running** as of this handoff update.
- workflow: `.github/workflows/research-3head-v289-addon-wave5-pair-rerank.yml`.
- script: `research_v289_3head_addon_wave5_pair_rerank.py`.
- Actions Run **`34706218140`**.
- run head SHA `75b2f178b4255edae94704498bec229a95c4b76b`.
- current step: `Run Wave 5 true opponent reranking research` in progress; frozen canonical artifact download already succeeded.
- this is genuinely distinct from Wave 2: Wave 2 retained V221 ordering; Wave 5 retrains the ordered-pair ranking itself using only prior-month reject races where boat 3 actually won.
- variants fixed before seeing test-month outcome: residual-pair target3, V221+residual blend target3, ticket-level EV target3, and corresponding Top10 versions.
- exact 10,000-yen Dutch; pre-race odds only; September outcomes forbidden.
- planned artifact: `v289-3head-addon-wave5-pair-rerank`.
- when complete, record add-on-only R/hits/ROI/profit/monthly minimum/red months/max DD + combined metrics + artifact ID here.

## What NOT to repeat
- simple coverage-fraction tweaks of Wave-1 scores.
- simple TopN/composite-odds changes on frozen V221 order.
- PRE-B families already tested in Wave 3.
- venue/archetype segmentation without adequate sample; 2R positive result is not promotion evidence.

## Real-operation audit
- v288 baseline overlap is zero by construction in evaluated add-on populations.
- every test-month fit uses prior-month outcomes only; current-month result/payout is settlement/evaluation only.
- source max date 2026-08-31; September outcomes excluded from tuning.
- historical research-time missing features may use prior-training handling; any shadow/production route must fail closed on missing required current inputs.
- no production workflow/model was changed.

## Exact restart point
1. Finish **Wave 5 Run 34706218140**; inspect/fix/re-run if it fails.
2. If Wave 5 produces a historical passer, only advance it to September outcome-blind shadow.
3. If Wave 5 is rejected, next family must be structurally different again (e.g. separate 2nd-place and 3rd-place models, motor/racer-role conditional ordering, or new PRE candidate-generation population), not another V221/TopN tweak.
