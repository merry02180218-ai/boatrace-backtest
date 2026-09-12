# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research branch: `research/3head-v289-addon-expansion`
- v288 production is **unchanged**.
- fixed production-compatible baseline: **94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%**.
- July/August are **NON-PRISTINE**.
- September outcomes are **not loaded / not used for tuning**.
- frozen canonical source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.

## Waves 1–4 rejected
- Wave1 Run `34703862487`: best 84R / 15 hits / ROI 54.92% / -378,700; **NO_ADOPTION_WAVE1**. Dead ends: residual_hit, exhibition_upgrade, return_rank, attack_style_split, orthogonal_consensus, ev_calibrated.
- Wave2 Run `34703969778`, artifact `v289-3head-addon-wave2-ticket-structure` ID `10301039743`: best Top10 177R / 45 hits / ROI 57.70% / -748,660 / min month 24.50%; **NO_ADOPTION_WAVE2**.
- Wave3 Run `34704413463`, artifact `v289-3head-addon-wave3-preb` ID `10301232830`: best 20+ variant 26R / 6 hits / ROI 67.47%; **NO_ADOPTION_WAVE3**.
- Wave4 Run `34706093149`, artifact `v289-3head-addon-wave4-archetype` ID `10301509909`: only positive 2R / 1 hit / ROI 156.40%, sample-rejected; **NO_ADOPTION_WAVE4**.

## Wave 5 — ordered-pair reranking
- Run `34706218140`, artifact `v289-3head-addon-wave5-pair-rerank` ID `10302397653`, result commit `b35fa0ccb73dacf0c1d7a365bca137d3012a6bf6`.
- best **178R / 24 hits / ROI 82.29% / -315,260 / min month 0% / 6 red / max DD 663,710**; combined 272R / ROI 113.49%. **NO_ADOPTION_WAVE5**.

## Wave 6 — separate 2nd/3rd role models
- Run `34710538598`, result commit `7d082f4b5401b8acd979675e608e4d120dd621dd`, artifact `v289-3head-addon-wave6-role-split`.
- best **178R / 24 hits / ROI 66.16% / -602,410 / min month 0% / 7 red / max DD 688,360**; combined ROI 102.93%. **NO_ADOPTION_WAVE6**.

## Wave 7 — attack-style role models
- Run `34712604315`, artifact `v289-3head-addon-wave7-attack-role` ID `10304192454`, result commit `2ce77cd52af26b419883401d8790cf1582cfb2b9`.
- best **178R / 25 hits / ROI 63.39% / -651,720 / min month 0% / 7 red / max DD 723,200 / overlap 0**; combined ROI 101.12%. **NO_ADOPTION_WAVE7**.

## Wave 8 — motor/racer-regime role models
- Run `34719090370`, artifact `v289-3head-addon-wave8-motor-racer-role` ID `10306048471`, result commit `59127fcb8d1c8a1b54648663a85511b1178e98e1`.
- best `motor_racer_role_ev_target3`: **178R / 31 hits / 17.42% / ROI 64.78% / -626,900 / min month 0% / 6 red / max DD 669,740 / overlap 0**; combined ROI 102.03%. **NO_ADOPTION_WAVE8**.

## Wave 9 — independent PRE head classifier
- canonical Run `34723795903`, artifact `v289-3head-addon-wave9-independent-pre-head` ID `10307052076`, result commit `c0b9db9c4bdd1ca8160ae6a0ee989adf292a132a`.
- best `head_ev@0.15`: **37R / 7 hits / 18.92% / ROI 57.26% / -158,130 / min month 0% / 5 red / max DD 167,870 / overlap 0**; combined 131R / ROI 140.00%. **NO_ADOPTION_WAVE9**.
- duplicate Run `34723808595` failed after canonical result persistence; ignore as a research failure.

## Wave 10 — nonparametric KNN analogs
- Run `34723857336` success; artifact `v289-3head-addon-wave10-knn-analogs`, ID `10306962427`; result commit `5438503f15f4a77b4d2f1fa5b6b0da20b0ef625f`.
- best `knn_head_k25@0.40` / consensus equivalent: **166R / 23 hits / 13.86% / ROI 42.31% / -957,580 / min month 30.87% / 7 red / max DD 976,180 / overlap 0**; combined 260R / ROI 89.40%.
- decision **NO_ADOPTION_WAVE10**; similarity did not isolate profitable add-ons.

## Wave 11 — v288 reject-cause mixture-of-experts
- canonical successful Run **`34723924180`**; result commit **`a871e088a263ed3cf42e013eaff294cd1aae65bc`**.
- artifact from duplicate/computation-equivalent Run: `v289-3head-addon-wave11-reject-cause-moe`, ID **`10307560448`**. Run `34723936660` completed research+guards but failed only at persistence because canonical Run had already added the same result files.
- best `cause_hit@0.50`: **94R / 15 hits / ROI 48.69% / profit -482,340 / min month 21.07% / 7 red / max DD 500,940 / overlap 0**; combined **188R / ROI 110.62%**.
- smaller fractions were worse: `cause_hit@0.35` 60R / 9 hits / ROI 45.93%; `cause_consensus@0.20` 29R / 3 hits / ROI 30.62%.
- decision: **NO_ADOPTION_WAVE11**.
- rejection: nearest failed v288 route explains rejection structure but still does not recover positive betting value.

## Wave 12 — learned joint race + ticket value
- auto-restarted after Wave11 rejection.
- script `research_v289_3head_addon_wave12_joint_ticket_value.py`, commit **`e0a997502ce73777ab0223e7a80ed2c02553f4ab`**.
- workflow `.github/workflows/research-3head-v289-addon-wave12-joint-ticket-value.yml`, commit **`beb049bd185dcab752ec5f49e9717b0d24ea9c56`**.
- Actions Run **`34724049674`** currently running.
- distinct mechanism: train prior-month expected settled value jointly over race features + ticket descriptors, then choose at most one configuration per race from regenerated Top2..Top10 / target composite-odds families.
- exact 10,000-yen Dutch is inherited from Wave2 ticket regeneration; final v288 NO_BET only; overlap must remain zero; current required feature missing => fail closed; September outcomes unused.
- expected artifact: `v289-3head-addon-wave12-joint-ticket-value`.

## What NOT to repeat
- Wave1 threshold/coverage tweaks; frozen V221 TopN/odds changes alone; Wave3 PRE-B; undersampled venue splits; Wave5 ordered-pair unchanged; Wave6 global role split; Wave7 attack role; Wave8 motor/racer role; Wave9 linear head classifier; Wave10 KNN analogs; Wave11 reject-cause ranking unchanged.

## Real-operation audit
- v288 overlap must remain zero.
- every test-month fit uses only prior-month outcomes; current-month result/payout enters settlement only.
- source max date 2026-08-31; September outcomes excluded from tuning.
- all production/shadow inputs must be available pre-deadline; required-current missingness fails closed.
- exact 10,000-yen Dutch retained; production v288 workflow/model unchanged.

## Exact restart point
1. Finish Wave12 Run `34724049674`; inspect/fix/re-run automatically if it fails.
2. If historical gates pass (>=20R, ROI>=100%, min monthly ROI>=60%, <=3 red months), advance only to September outcome-blind shadow.
3. If rejected, next family must change the source/candidate mechanism again rather than repeat Waves1–12 unchanged.
