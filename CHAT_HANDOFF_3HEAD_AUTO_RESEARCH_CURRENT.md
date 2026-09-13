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

## Wave 13 — hurdle ticket EV + independent agreement — FINAL
- script commit **`edcaf8d98532e078de29107bb16b211b92676845`**: `research_v289_3head_addon_wave13_hurdle_ticket_ev.py`.
- workflow commit **`bf8330a0ab3a37f5e9336b25d669d0c70bf19b2a`**: `.github/workflows/research-3head-v289-addon-wave13-hurdle-ticket-ev.yml`.
- Actions Run **`34733351060` completed success**.
- artifact **`v289-3head-addon-wave13-hurdle-ticket-ev`**, artifact ID **`10310494882`**.
- result commit **`4318d5cb132fe92cb8c0476e672a905367f0963f`**.
- best `hurdle_ticket_ev_consensus@0.40`: **4R / 1 hit / hit 25.00% / ROI 58.65% / profit -16,540 / min month ROI 0.00% / 2 red months / max DD 20,000 / overlap 0**.
- combined v288+add-on: **98R / ROI 167.91%**.
- other fractions: 2R / 0 hits / ROI 0%; 1R / 0 hits / ROI 0% (two variants).
- decision: **NO_ADOPTION_WAVE13**.
- rejection reason: independent hurdle-EV agreement collapses coverage to 1–4 races and remains negative; fails the minimum 20R gate and ROI gate, so there is no production adoption case.

## Wave 14 — conformal market/field selective gating — RUNNING
- automatic restart condition was met: no new 3-head add-on commit/Run for more than 2 hours after Wave13 finalization.
- new candidate-source family is **not** a prior-score threshold relaxation: choose one exact JPY10,000 Dutch ticket by deterministic pre-deadline market structure (`comp_alt` relative to ticket count), then apply a chronological positive-class conformal selective gate learned only from prior-month NO_BET outcomes.
- script commit **`1857c5528e978ca4ed6e2e21d50ec8ce84839434`**: `research_v289_3head_addon_wave14_conformal_market.py`.
- workflow commit **`8dc48dbcd428370a780bcc7a422ddc9d33f3512d`**: `.github/workflows/research-3head-v289-addon-wave14-conformal-market.yml`.
- Actions Run **`34741605409`** is in progress.
- intended artifact: **`v289-3head-addon-wave14-conformal-market`**.
- policies compared: `market_density` and `market_efficiency`; conformal alpha 0.05/0.10/0.20/0.30.
- immutable guards retained: v288 94R fixed, final NO_BET only, Feb-Aug prior-month-only walk-forward, Jul/Aug NON-PRISTINE, September outcomes forbidden, required-current missing => fail closed, overlap 0, exact 10,000-yen Dutch.

## What NOT to repeat
- Wave1 threshold/coverage tweaks; TopN/odds changes alone; PRE-B; undersampled venue splits; ordered-pair unchanged; global role split; attack-role; motor/racer-role; linear head classifier; KNN analogs; reject-cause ranking unchanged; Wave12 direct joint settled-value regression unchanged; Wave13 hurdle/direct-value agreement unchanged.

## Real-operation audit
- v288 overlap must remain zero.
- all test-month fitting uses only prior-month outcomes; current-month result/payout is settlement only.
- source max date 2026-08-31; September outcomes excluded from tuning.
- all production/shadow inputs must be available pre-deadline; required-current missingness fails closed.
- exact 10,000-yen Dutch retained; production v288 workflow/model unchanged.

## Exact restart point
1. Inspect Actions Run `34741605409` first.
2. If success: persist add-on-only BET count/hits/hit rate/ROI/profit/monthly/min-month/max-DD/overlap and v288+add-on combined metrics, artifact ID, result commit SHA, decision and rejection/adoption reason here.
3. If failed/cancelled: inspect the failed job/log, fix only the technical/scientific defect without weakening immutable guards, rerun automatically, and record replacement Run ID.
4. If Wave14 is NO_ADOPTION, do not retune conformal alpha or market-score cutoffs as a threshold-relaxation exercise; move to another genuinely distinct pre-deadline candidate-source family.
5. Preserve v288 94R baseline, final-NO_BET-only scope, Feb-Aug prior-month-only walk-forward, Jul/Aug NON-PRISTINE, September outcomes unused, overlap 0, fail-closed guards, and exact 10,000-yen Dutch.
