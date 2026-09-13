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
- Interpretation: single structural gate does not generalize to untouched May-Jun; August strength is not sufficient because Jul/Aug are NON-PRISTINE.

## Wave29 — RUNNING pre-April leak-free validation
- Script commit `607d877689f86b0a20b83d1805633615b8ca4e6d`: `research_v289_3head_wave29_preapril_validation.py`.
- Workflow commit `0dcea2043e69f95b2b29c0cf62b70a3d9a659537`: `.github/workflows/research-3head-wave29-preapril.yml`.
- Current Run **`34764558658`**, workflow `research-3head-wave29-preapril`, status at launch **queued**.
- All `節D`/result-like fields remain excluded; only 63 static pre-deadline-safe card features.
- March is the only tuning month, and March predictions are trained on February only. Threshold/top-K are selected only from March.
- **Apr-Jun are now a fully untouched model-selection holdout**. Jul-Aug remain NON-PRISTINE shadow only.
- Closing odds are staking-only; legacy overlap 0; September forbidden.

## Exact restart point
1. Inspect Run `34764558658` first.
2. If failed, inspect logs, fix and rerun automatically without weakening leak/date/zero-overlap guards.
3. If success, record March chosen p3/top-K, Apr-Jun holdout R/hits/ROI/profit/monthly/min month/red months/max DD, Jul-Aug shadow, overlap and combined baseline.
4. If Wave29 generalizes, treat it as substantially stronger evidence than Wave27/28 because Apr-Jun were never used for selection.
5. If Wave29 fails, continue another genuinely distinct leak-free family; never optimize directly on Jul/Aug outcomes.
