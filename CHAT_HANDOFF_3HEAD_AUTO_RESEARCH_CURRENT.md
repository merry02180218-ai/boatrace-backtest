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
- Run **`34706218140`** completed successfully.
- artifact **`v289-3head-addon-wave5-pair-rerank`**, artifact ID **`10302397653`**.
- generated-results commit **`b35fa0ccb73dacf0c1d7a365bca137d3012a6bf6`**.
- distinct from Wave 2: retrained the ordered 2着/3着 pair ranking itself using only prior-month reject races where boat 3 actually won.
- best method: `ev_target3` / `ev_top10` = **178R / 24 hits / ROI 82.29% / profit -315,260 yen / minimum monthly ROI 0% / 6 red months / max DD 663,710 yen**.
- combined v288 + add-on: **272R / ROI 113.49%**.
- other residual/blend methods were worse (ROI 46.88%–52.32%).
- decision: **NO_ADOPTION_WAVE5**.
- rejection reason: pair re-ranking improves on frozen-order ticket research but add-on-only remains materially negative and unstable month-to-month.

## Wave 6 — separate 2nd-place / 3rd-place role models
- restarted automatically after Wave 5 rejection because no research run remained active.
- script: `research_v289_3head_addon_wave6_role_split.py`.
- workflow: `.github/workflows/research-3head-v289-addon-wave6-role-split.yml`.
- script commit: `e1070444596a576a40d70e259b56bd43a9d1e443`.
- workflow-trigger commit: `c12126a1e0fe68ba6065c181ef087ef896e79df4`.
- structurally distinct from Wave 5: independent opponent-role classifiers for 2着 and 3着, trained only on prior-month reject races where boat 3 won; ticket ordering is role-probability product or role-probability × pre-race odds EV.
- variants: role-product target3 / role-EV target3 / role-product Top10 / role-EV Top10.
- exact 10,000-yen Dutch; all evaluation Feb-Aug walk-forward; September outcomes forbidden; v288 overlap zero; fail-closed requirements retained.
- expected artifact: `v289-3head-addon-wave6-role-split`.

## What NOT to repeat
- simple coverage-fraction tweaks of Wave-1 scores.
- simple TopN/composite-odds changes on frozen V221 order.
- PRE-B families already tested in Wave 3.
- venue/archetype segmentation without adequate sample.
- Wave-5 ordered-pair residual/blend/EV reranking unchanged.

## Real-operation audit
- v288 baseline overlap is zero by construction in evaluated add-on populations.
- every test-month fit uses prior-month outcomes only; current-month result/payout is settlement/evaluation only.
- source max date 2026-08-31; September outcomes excluded from tuning.
- all promoted/shadow routes must use inputs obtainable before deadline and fail closed on missing required current inputs.
- exact 10,000-yen Dutch settlement is retained where tickets are evaluated.
- no production workflow/model was changed.

## Exact restart point
1. Finish Wave 6 CI; if it fails, inspect logs, fix, and rerun.
2. If Wave 6 produces a robust historical passer (>=20R, ROI>=100%, minimum monthly ROI>=60%, <=3 red months), advance only to September outcome-blind shadow, never directly over v288.
3. If Wave 6 is rejected, next distinct family should condition opponent roles on motor/racer role or generate a genuinely new PRE candidate population; do not revisit failed Wave1–5 families unchanged.
