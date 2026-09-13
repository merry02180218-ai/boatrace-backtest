# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Status
- research branch: `research/3head-v289-addon-expansion`
- v288 production is **unchanged**.
- fixed production-compatible baseline: **94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%**.
- July/August are **NON-PRISTINE**.
- September outcomes are **not loaded / not used for tuning**.
- frozen canonical source: Run `34383567078`, artifact `v243-3head-expand-feature-audit`, artifact ID `10118044294`, max date 2026-08-31.
- target is **v288 final NO_BET only**; v288 overlap must stay 0.

## Rejected research summary
- Wave1 Run `34703862487`: best 84R / 15 hits / ROI 54.92% / -378,700; **NO_ADOPTION_WAVE1**. Dead ends included residual_hit, exhibition_upgrade, return_rank, attack_style_split, orthogonal_consensus, ev_calibrated.
- Wave2 Run `34703969778`, artifact `v289-3head-addon-wave2-ticket-structure` ID `10301039743`: best Top10 177R / 45 hits / ROI 57.70% / -748,660 / min month 24.50%; **NO_ADOPTION_WAVE2**.
- Wave3 Run `34704413463`: best 20+ variant 26R / 6 hits / ROI 67.47%; **NO_ADOPTION_WAVE3**.
- Wave4 Run `34706093149`: only positive 2R / 1 hit / ROI 156.40%, sample-rejected; **NO_ADOPTION_WAVE4**.
- Wave5 Run `34706218140`: ordered-pair reranking best 178R / 24 hits / ROI 82.29% / -315,260 / min month 0%; **NO_ADOPTION_WAVE5**.
- Wave6 Run `34710538598`: separate 2nd/3rd role models best 178R / 24 hits / ROI 66.16% / -602,410; **NO_ADOPTION_WAVE6**.
- Wave7 Run `34712604315`: attack-style role models best 178R / 25 hits / ROI 63.39% / -651,720; **NO_ADOPTION_WAVE7**.
- Wave8 Run `34719090370`: motor/racer-regime role models best 178R / 31 hits / ROI 64.78% / -626,900; **NO_ADOPTION_WAVE8**.
- Wave9 Run `34723795903`: independent PRE head classifier best 37R / 7 hits / ROI 57.26% / -158,130; **NO_ADOPTION_WAVE9**.
- Wave10 Run `34723857336`: KNN analog best 166R / 23 hits / ROI 42.31% / -957,580; **NO_ADOPTION_WAVE10**.
- Wave11 canonical Run `34723924180`: reject-cause MoE best 94R / 15 hits / ROI 48.69% / -482,340; **NO_ADOPTION_WAVE11**.

## Wave 12 — learned joint race + ticket value — FINAL
- script `research_v289_3head_addon_wave12_joint_ticket_value.py`.
- first Run `34724049674` timed out during ticket-matrix reconstruction; workflow timeout fix commit `9021f76f71438a19c5638ebbe752737c05c8df57` changed no research rule.
- replacement Run **`34729958264` completed success**.
- artifact **`v289-3head-addon-wave12-joint-ticket-value`**, artifact ID **`10310055975`**.
- result commit **`bc1f82fe56f0b2164de4b9841222d32df43a1dca`**.
- best `joint_ticket_value_rf@0.40`: **75R / 21 hits / hit 28.00% / ROI 65.73% / profit -257,010 / min month ROI 0.00% / 7 red months / max DD 281,230 / overlap 0**.
- combined v288+add-on: **169R / ROI 125.15%**.
- smaller fractions were also negative: 47R ROI 57.14%; 11R ROI 52.11%.
- decision: **NO_ADOPTION_WAVE12**. Rejection reason: direct settled-value learning improves hit rate but cannot recover positive add-on EV or monthly robustness.

## Wave 13 — hurdle ticket EV + independent agreement — RUNNING
- restart was required because Wave12 had completed but no next candidate-source family had been launched and the stable handoff was stale.
- new script commit **`edcaf8d98532e078de29107bb16b211b92676845`**: `research_v289_3head_addon_wave13_hurdle_ticket_ev.py`.
- workflow commit **`bf8330a0ab3a37f5e9336b25d669d0c70bf19b2a`**: `.github/workflows/research-3head-v289-addon-wave13-hurdle-ticket-ev.yml`.
- Actions Run **`34733351060`** started from workflow commit; current state at handoff update: **in_progress**.
- expected artifact: **`v289-3head-addon-wave13-hurdle-ticket-ev`**.
- mechanism deliberately changes candidate generation after Wave12: model `P(ticket hit)` and conditional hit payout separately, multiply them into hurdle EV, then require an independent direct-value model to choose the same ticket configuration. This is not a simple threshold relaxation.
- candidate ticket families remain regenerated Top2..Top10 / target composite-odds with exact **10,000-yen Dutch**.
- walk-forward Feb-Aug only; every test month fits prior months only; current required feature missing => **FAIL_CLOSED**.
- acceptance gate unchanged: **>=20R, ROI>=100%, min monthly ROI>=60%, <=3 red months**, plus overlap 0 and all guards passing.

## What NOT to repeat
- Wave1 threshold/coverage tweaks; TopN/odds changes alone; PRE-B; undersampled venue splits; ordered-pair unchanged; global role split; attack-role; motor/racer-role; linear head classifier; KNN analogs; reject-cause ranking unchanged; Wave12 direct joint settled-value regression unchanged.

## Real-operation audit
- v288 overlap must remain zero.
- all test-month fitting uses only prior-month outcomes; current-month result/payout is settlement only.
- source max date 2026-08-31; September outcomes excluded from tuning.
- all production/shadow inputs must be available pre-deadline; required-current missingness fails closed.
- exact 10,000-yen Dutch retained; production v288 workflow/model unchanged.

## Exact restart point
1. Inspect Run `34733351060` and its jobs/artifact.
2. If failed/cancelled, inspect logs, patch Wave13, and rerun automatically.
3. If success, record add-on-only R/hit rate/ROI/profit/monthly/min-month/max-DD/overlap and combined v288+add-on in this handoff.
4. If the historical gate passes, advance only to September **outcome-blind** shadow. If rejected, record why and move to a genuinely different candidate-source mechanism rather than retuning Waves1–13.
