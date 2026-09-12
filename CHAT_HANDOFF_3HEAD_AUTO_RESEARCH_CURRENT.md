# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research branch: `research/3head-v289-addon-expansion`
- v288 production is **unchanged**.
- fixed production-compatible baseline: **94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%**.
- July/August are **NON-PRISTINE**.
- September outcomes are **not loaded / not used for tuning**.
- frozen canonical source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.

## Wave 1 — final-NO_BET signal ranking
- Run `34703862487`, artifact `v289-3head-addon-wave1`, ID `10300816836`.
- best: **84R / 15 hits / ROI 54.92% / profit -378,700**. Decision **NO_ADOPTION_WAVE1**.
- dead ends: residual_hit, exhibition_upgrade, return_rank, attack_style_split, orthogonal_consensus, ev_calibrated.

## Wave 2 — frozen V221 ticket structure
- Run `34703969778`, artifact `v289-3head-addon-wave2-ticket-structure`, ID `10301039743`.
- best Top10: **177R / 45 hits / ROI 57.70% / profit -748,660 / min month 24.50% / 7 red**. Decision **NO_ADOPTION_WAVE2**.

## Wave 3 — independent PRE-B rescue
- Run `34704413463`, artifact `v289-3head-addon-wave3-preb`, ID `10301232830`.
- raw pool **81R / 23 hits / ROI 84.42%**; best 20+ race variant **26R / 6 hits / ROI 67.47%**. Decision **NO_ADOPTION_WAVE3**.

## Wave 4 — venue / field archetype
- Run `34706093149`, artifact `v289-3head-addon-wave4-archetype`, ID `10301509909`.
- only positive **2R / 1 hit / ROI 156.40%**, rejected for sample. Decision **NO_ADOPTION_WAVE4**.

## Wave 5 — true ordered-pair reranking
- Run `34706218140`, artifact `v289-3head-addon-wave5-pair-rerank`, ID `10302397653`, result commit `b35fa0ccb73dacf0c1d7a365bca137d3012a6bf6`.
- best **178R / 24 hits / ROI 82.29% / profit -315,260 / min month 0% / 6 red / max DD 663,710**; combined **272R / ROI 113.49%**. Decision **NO_ADOPTION_WAVE5**.

## Wave 6 — separate 2nd/3rd role models
- Run `34710538598`, result commit `7d082f4b5401b8acd979675e608e4d120dd621dd`, artifact `v289-3head-addon-wave6-role-split`.
- best **178R / 24 hits / ROI 66.16% / profit -602,410 / min month 0% / 7 red / max DD 688,360**; combined **272R / ROI 102.93%**. Decision **NO_ADOPTION_WAVE6**.

## Wave 7 — attack-style-conditioned role models
- canonical Run `34712604315`, artifact `v289-3head-addon-wave7-attack-role`, ID `10304192454`, result commit `2ce77cd52af26b419883401d8790cf1582cfb2b9`.
- best **178R / 25 hits / ROI 63.39% / profit -651,720 / min month 0% / 7 red / max DD 723,200 / overlap 0**; combined **272R / ROI 101.12%**. Decision **NO_ADOPTION_WAVE7**.

## Wave 8 — motor/racer-regime-conditioned role models
- canonical successful Run **`34719090370`**; artifact `v289-3head-addon-wave8-motor-racer-role`, ID **`10306048471`**; result commit **`59127fcb8d1c8a1b54648663a85511b1178e98e1`**.
- best `motor_racer_role_ev_target3`: **178R / 31 hits / hit 17.42% / ROI 64.78% / profit -626,900 / min month 0% / 6 red / max DD 669,740 / overlap 0**; combined **272R / ROI 102.03%**.
- `ev_top10`: 178R / 32 hits / ROI 63.66%; product variants ROI 59.78%–61.13%.
- decision: **NO_ADOPTION_WAVE8**.
- rejection: regime conditioning raised hit count but not return quality or monthly robustness.

## Wave 9 — independent PRE head classifier
- Run **`34723795903`** success; artifact `v289-3head-addon-wave9-independent-pre-head`, ID **`10307052076`**; result commit **`c0b9db9c4bdd1ca8160ae6a0ee989adf292a132a`**.
- fresh boat3-win classifier trained on all prior-month buyable races; existing p3 excluded; selected-current-feature missingness fails closed.
- best `head_ev@0.15`: **37R / 7 hits / hit 18.92% / ROI 57.26% / profit -158,130 / min month 0% / 5 red / max DD 167,870 / overlap 0**; combined **131R / ROI 140.00%**.
- wider fractions worsened to ROI 40.37%–50.00%.
- decision: **NO_ADOPTION_WAVE9**.
- rejection: independent head probability did not translate into profitable exact-Dutch tickets.
- duplicate Run `34723808595` failed only after the canonical result had already persisted; do not treat it as research failure.

## Wave 10 — nonparametric KNN analogs
- auto-restarted after Wave9 rejection.
- script: `research_v289_3head_addon_wave10_knn_analogs.py`; script commit **`bc8616e0dead1eac9ebea0e675cef86b4c14a0b9`**.
- workflow: `.github/workflows/research-3head-v289-addon-wave10-knn-analogs.yml`; workflow commit **`c8ce0e996cd7bfef46024cf7e3aa3cd897871164`**.
- Actions Run **`34723857336`** in progress.
- distinct family: prior-month nearest-neighbour analog scoring for boat3-head probability, realized ticket value, and independent consensus; K=25/50/75; fractions 0.15/0.25/0.40.
- candidate remains final v288 NO_BET only; existing p3 excluded; current selected-feature missingness fails closed; exact 10,000-yen Dutch settlement retained.
- expected artifact: `v289-3head-addon-wave10-knn-analogs`.

## What NOT to repeat
- Wave1 threshold/coverage tweaks; frozen-V221 TopN/odds changes; Wave3 PRE-B; undersampled venue splits; Wave5 ordered-pair unchanged; Wave6 global role split; Wave7 attack-style role split; Wave8 motor/racer role split; Wave9 linear independent-head classifier unchanged.

## Real-operation audit
- v288 overlap must remain zero.
- every test-month fit uses only prior-month outcomes; current-month result/payout enters settlement only.
- source max date 2026-08-31; September outcomes excluded from tuning.
- all production/shadow inputs must be available pre-deadline; required-current missingness fails closed.
- exact 10,000-yen Dutch retained; production v288 workflow/model unchanged.

## Exact restart point
1. Finish Wave10 Run `34723857336`; inspect/fix/re-run automatically if it fails.
2. If historical gates pass (>=20R, ROI>=100%, min monthly ROI>=60%, <=3 red months), advance only to September outcome-blind shadow.
3. If rejected, next family must change the betting-value mechanism rather than another head-probability ranker (for example learned ticket-value / opponent-order joint optimization with strict prior-month fitting), while keeping v288 94R fixed.
