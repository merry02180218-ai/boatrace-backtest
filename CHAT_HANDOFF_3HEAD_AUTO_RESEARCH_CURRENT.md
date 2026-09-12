# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research branch: `research/3head-v289-addon-expansion`
- v288 production is **unchanged**.
- fixed production-compatible baseline: **94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%**.
- July/August are **NON-PRISTINE**.
- September outcomes are **not loaded / not used for tuning**.
- frozen canonical source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.

## Wave 1 — final-NO_BET signal ranking
- infrastructure merged to main by PR #2; merge SHA `bf26c1fe1ba5974341a6f204b583c7c9e68358b0`.
- successful canonical Wave-1 Run `34703862487`, artifact `v289-3head-addon-wave1`, artifact ID `10300816836`.
- equivalent earlier in-session Run `34703771330`, artifact ID `10301626123`, had valid research/guards/artifact but failed only at concurrent report-persist push.
- candidate pool: **178R**, operational PRE S/A + v242-buyable + final v288 `NO_BET` only.
- best tested variant: `return_rank@0.45`.
- best add-on: **84R / 15 hits / ROI 54.92% / profit -378,700 yen**.
- combined: **178R / ROI 117.04%**.
- decision: **NO_ADOPTION_WAVE1**.

### Wave-1 dead ends retained
- `residual_hit`: prior-reject outcome effect ranking over pre-race safe features.
- `exhibition_upgrade`: current exhibition/ST/original-exhibition family.
- `return_rank`: prior-reject realized-return ranking, prior months only.
- `attack_style_split`: stretch-vs-turn regimes followed by prior-trained ranking.
- `orthogonal_consensus`: residual + exhibition + return independent-score consensus.
- `ev_calibrated`: residual hit score + current composite odds, alpha selected on prior months only.
- Do not repeat these merely by loosening/tightening coverage fractions.

## Wave 2 — ticket-structure / opponent-order research
- script: `research_v289_3head_addon_wave2.py`.
- workflow: `.github/workflows/research-3head-v289-addon-wave2.yml`.
- current Run: **`34703969778`**, head SHA `8f3fa8cfd8033838fa8be5ece7b25a01ed7b45f1`.
- state at this handoff update: **in progress**, inside ticket-structure research step.
- tests frozen V221 opponent order with exact 10,000-yen Dutch using:
  - fixed Top2..Top10;
  - target composite odds 2.5 / 3 / 3.5 / 4 / 5 / 6 / 8;
  - prior-month-only selectors `wf_profit`, `wf_stable`, `wf_recent`.
- v288 thresholds are untouched.
- planned artifact: `v289-3head-addon-wave2-ticket-structure`.
- if the run fails, inspect/fix/re-run. If it succeeds, record best fixed + walk-forward policy, add-on-only and combined metrics, monthly minimum ROI, red months and max DD here.

## Wave 3 — independent PRE-B LIVE rescue
- This is **not** an S/A threshold relaxation. It is a separate candidate population: operational PRE grade B + existing v242-buyable ticket structure, then prior-PRE-B-trained LIVE rescue scoring.
- workflow Run: **`34704413463`** — success.
- run head SHA: `f16915524e4c2e94ae6e1b810387310d3858a00f`.
- generated-results commit: `258ec82` (full SHA can be refreshed from branch log if needed).
- artifact: `v289-3head-addon-wave3-preb`.
- artifact ID: **`10301232830`**.
- guards passed: baseline 94/52/1,622,070; source <= 2026-08-31; September unused; not-threshold-relaxation=true; overlap zero.
- raw PRE-B buyable pool: **81R / 23 hits / ROI 84.42%**.
- best numerical ROI was `preb_ev@0.20`: **5R / 2 hits / ROI 117.28% / profit +8,640 yen**, but minimum monthly ROI **0%**, only 5 races, so it fails robustness/sample gates.
- among 20+ race variants, best was `preb_return_rank@0.50`: **26R / 6 hits / ROI 67.47% / profit -84,590 yen**, minimum monthly ROI 36.93%.
- `preb_return_rank@0.35`: 20R / 4 hits / ROI 58.06%.
- `preb_ev@0.50`: 20R / 3 hits / ROI 44.09%.
- `preb_ticket_quality@0.50`: 22R / 3 hits / ROI 40.84%.
- decision: **NO_ADOPTION_WAVE3**.

### Wave-3 dead ends retained
- PRE-B hit rank.
- PRE-B exhibition-only rank.
- PRE-B return rank.
- PRE-B ticket-quality rank.
- PRE-B independent-score consensus.
- PRE-B EV rank using composite odds with alpha selected only on prior PRE-B months.
- Tiny-sample positive ROI is explicitly rejected; do not promote `preb_ev@0.20`.

## Real-operation audit
- Wave 1/3 score inputs are columns present before settlement in the canonical v243/v288 artifact.
- all test-month fitting uses only prior-month outcomes; current test-month result/payout is settlement/evaluation only.
- missing historical features may be prior-training median-imputed for research; any shadow/production promotion must fail closed on required current inputs.
- no add-on overlaps the fixed v288 baseline in the evaluated population.
- no v288 production workflow/model was changed.

## Mandatory metrics for later waves
- add-on BETs / hits / hit rate / payout / profit / ROI.
- monthly ROI, red-month count, minimum monthly ROI.
- max drawdown.
- overlap with v288.
- combined v288 + add-on totals.
- pre-race source availability / fail-closed viability.
- failed trials and rejection reason.
- Run ID / artifact name + ID / latest commit SHA.

## Exact restart point
1. Finish **Wave 2 Run 34703969778** and persist the ticket-structure result.
2. If Wave 2 is also rejected, next distinct family is venue/field-archetype residual research with minimum prior-sample guards and/or true opponent re-ranking; do not revisit Wave-1 coverage tweaks or the failed PRE-B families unchanged.
3. Any historical passer advances only to **September outcome-blind shadow**, never directly over v288 production.
