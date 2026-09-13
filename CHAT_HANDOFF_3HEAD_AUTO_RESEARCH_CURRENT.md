# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch: `research/3head-v289-addon-expansion`; newest GitHub state wins.
- Legacy v288 stays unchanged: 94R / 52 hits / stake 940,000 yen / payout 1,622,070 yen / profit +682,070 yen / ROI 172.560638%.
- Research source is all available six-boat races from 2026-02-01 through 2026-08-31 from BoatraceCSV race_cards; do not revert to v243 678R/584R as the research universe.
- Jul/Aug NON-PRISTINE. September outcomes forbidden.
- Prediction features must be pre-deadline. Results/payouts are evaluation-only. Historical closing trifecta odds are staking/post-hoc ROI only and never prediction features.
- Missing required current inputs fail closed. Add-on overlap with v288 must be zero. Stake JPY10,000/race.

## Stable source milestones
- Wave20 Run `34749917116`: success; full six-boat universe **32,111R**. Monthly Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920.
- Wave21 Run `34751314113`: success; 32,111 rows; usable exact settlement **31,518/32,111 = 98.153%**; both-source agreement **99.9553%**; actual 3-head wins 4,040.
- Wave22 Run `34752573368`: success; full 120 closing trifecta odds **31,605/32,111 = 98.424%**. Closing odds remain staking-only.

## Prior research summary
- Wave23 Run `34754875342`: Apr-Jun 651R / ROI 135.062%; Jul-Aug shadow ROI 77.598%; NO_ADOPTION.
- Wave24 Run `34757826506`: Apr-Jun 120R / ROI 95.236%; Jul-Aug shadow ROI 55.145%; NO_ADOPTION.
- Wave25 Run `34757888935`: Apr-Jun 5,427R / ROI 70.701%; Jul-Aug shadow ROI 73.452%; NO_ADOPTION.

## Wave26 — INVALIDATED BY LEAK AUDIT
- Run `34759822824`: reported Apr-Jun **1,125R / ROI 226.722%** but used 77 features including current-meet `節D...ST/着順` aggregates.
- Leak audit: boat-3 `節D` slot matched current race on **15,280 rows** and `節D...着順==1` agreed with actual 3-head outcome at **97.997%**.
- Therefore Wave26 result is contaminated and cannot support adoption. Closing odds were not the leak; section-history fields were.

## Wave27 — FINAL leak-free exact-order
- Run **`34763079073`**, artifact ID **`10318874127`**.
- Features: **63 static card-only**; every `節D` field removed.
- April-only tune chose **p3>=0.38, top5**.
- Strict May-Jun holdout: **195R / 26 hits / ROI 57.947% / profit -820,040 yen**.
- Monthly: May **51.947%**, Jun **69.673%**; red months 2; max DD 857,540 yen.
- Jul-Aug NON-PRISTINE shadow: **170R / 46 hits / ROI 124.170% / profit +410,890 yen**.
- Shadow monthly: Jul **111.251%**, Aug **134.369%**.
- Baseline + holdout: **289R / ROI 95.226% / profit -137,970 yen**.
- Legacy overlap 0. Decision **NO_ADOPTION**.

## Wave28 — FINAL leak-free structure gate
- Run **`34764021442`**, workflow `research-3head-wave28-structure`: success.
- Artifact `3head-wave28-structure-gate`, ID **`10318999751`**.
- Candidate count **64**; base config remained Wave27 p3>=0.38/top5.
- Chosen April-only structural gate: **b3_minus_b1_全国勝率 >= 2.415** (April 75th percentile).
- April tune: **37R / ROI 354.568% / profit +941,900 yen**.
- Strict May-Jun holdout: **75R / 11 hits / ROI 73.745% / profit -196,910 yen**.
- Monthly holdout: May **44R / 5 hits / ROI 55.852% / -194,250**; Jun **31R / 6 hits / ROI 99.142% / -2,660**.
- Jul-Aug NON-PRISTINE shadow: **77R / 20 hits / ROI 128.013% / profit +215,700 yen**.
- Shadow: Jul **71.557%**, Aug **175.060%**.
- Baseline + holdout: **169R / ROI 128.708% / profit +485,160 yen**.
- Legacy overlap 0. Decision **NO_ADOPTION**.

## Wave29 — FINAL pre-April leak-free validation
- Run **`34764558658`**, workflow `research-3head-wave29-preapril`: **success**.
- Artifact `3head-wave29-preapril-validation`, ID **`10320410273`**.
- Features: **63 static pre-deadline-safe card features**; no `節D` / current-meet result/ST fields.
- March-only tune using February training chose **p3>=0.38, top7**; March **185R / ROI 118.999%**.
- Strict untouched Apr-Jun holdout: **342R / 63 hits / ROI 93.845% / profit -210,510 yen**.
- Holdout monthly: Apr **147R / 30 hits / ROI 123.769% / +349,400**; May **129R / 22 hits / ROI 78.718% / -274,540**; Jun **66R / 11 hits / ROI 56.762% / -285,370**.
- Holdout min month **56.762%** / red months **2** / max DD **628,780 yen**.
- Jul-Aug NON-PRISTINE shadow: **170R / 53 hits / ROI 111.906% / profit +202,410 yen**.
- Shadow monthly: Jul **75R / 21 hits / ROI 101.352% / +10,140**; Aug **95R / 32 hits / ROI 120.239% / +192,270**.
- Baseline + holdout: **436R / ROI 110.816% / profit +471,560 yen**.
- Legacy overlap **0**. Decision **NO_ADOPTION**.
- Interpretation: stronger validation design than Wave27/28, but May-Jun degradation shows the one-stage multinomial family still fails pristine generalization.

## Wave30 — RUNNING distinct two-stage family
- Script commit **`8e0f9d10b4822650523163175a6ec6de33fab8d4`** introduced `research_v289_3head_wave30_twostage_preapril.py`.
- Workflow commit **`49c2ccccfe9fde1be6945d9eb2b132af882684f5`** introduced `.github/workflows/research-3head-wave30-twostage.yml`.
- Current Run **`34765791471`**, workflow `research-3head-wave30-twostage`, status at last inspection **in_progress**.
- Family is deliberately distinct from Wave29: stage 1 binary `P(3-head)` gate, stage 2 exact-order model conditional on historical 3-head races.
- Same 63 static card-only features; no `節D` / result-like current-meet fields.
- March only selects threshold/top-K using predictions trained on February. Apr-Jun remains untouched model-selection holdout.
- Jul-Aug NON-PRISTINE shadow only. September forbidden. Closing odds staking-only. Legacy overlap 0.

## Exact restart point
1. Inspect Run `34765791471` first.
2. If failed/stopped, inspect logs, fix and rerun automatically without weakening date/leak/zero-overlap guards.
3. If success, record March chosen p3/top-K, Apr-Jun R/hits/ROI/profit/monthly/min month/red months/max DD, Jul-Aug shadow, overlap and combined baseline.
4. Adoption/shadow status must be based on pristine Apr-Jun only; Jul/Aug cannot rescue a weak pristine result.
5. If Wave30 fails to generalize, continue another genuinely distinct full-population leak-free family automatically; do not optimize on Jul/Aug outcomes.
