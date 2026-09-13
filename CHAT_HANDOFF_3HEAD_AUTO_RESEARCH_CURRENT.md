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
- Run **`34763079073`**, workflow `research-3head-wave27-leakfree`: success.
- Artifact `3head-wave27-leakfree-exactorder`, ID **`10318874127`**.
- Features: **63 static card-only**; every `節D` ST/着順 field removed.
- Wave26 leak signature reproduced: **15,280 matched rows / 97.997% agreement**.
- April-only tune chose **p3>=0.38, top5**.
- Strict untouched May-Jun holdout: **195R / 26 hits / ROI 57.947% / profit -820,040 yen**.
- Holdout monthly: May **129R / 16 hits / ROI 51.947% / -619,880**; Jun **66R / 10 hits / ROI 69.673% / -200,160**.
- Holdout min-month ROI **51.947%**; red months **2**; max DD **857,540 yen**.
- Jul-Aug NON-PRISTINE shadow: **170R / 46 hits / ROI 124.170% / profit +410,890 yen**.
- Shadow monthly: Jul **75R / 18 hits / ROI 111.251% / +84,380**; Aug **95R / 28 hits / ROI 134.369% / +326,510**.
- Baseline + strict holdout: **289R / ROI 95.226% / profit -137,970 yen**.
- Legacy overlap **0**. Decision **NO_ADOPTION**.
- Interpretation: leak-free family is not adoptable, but Jul/Aug positive shadow justifies structural research. Do not tune directly to Jul/Aug outcomes.

## Wave28 — RUNNING leak-free structure gate
- Script commit `9ecdbf319d0fc54520334c1751551a62af1b2f4c`: `research_v289_3head_wave28_structure_gate.py`.
- Workflow commit `1ac80a231a0010d81321e3335f953e60c0432c02`: `.github/workflows/research-3head-wave28-structure.yml`.
- Current Run **`34764021442`**, workflow `research-3head-wave28-structure`, status at launch `in_progress`.
- Base Wave27 config is frozen: **p3>=0.38 / top5**.
- All `節D` fields remain excluded; 63 static card features only.
- Candidate gates are deliberately limited/interpretable: 3号艇-vs-others strength, ST, motor differentials, 3-vs-1/2 differentials, and race-number bands.
- Gate thresholds come from April feature quantiles; April outcomes choose among the limited gates. May-Jun remain untouched strict holdout. Jul-Aug remain NON-PRISTINE shadow only.
- No direct Jul/Aug optimization. Closing odds staking-only. Legacy overlap 0. September forbidden.

## Exact restart point
1. Inspect Run `34764021442` first.
2. If failed, inspect logs, fix and rerun automatically without weakening leak/date/zero-overlap guards.
3. If success, record chosen structural gate, April tune metrics, strict May-Jun holdout R/hits/ROI/profit/monthly/min month/red months/max DD, Jul-Aug shadow, overlap and combined baseline.
4. If Wave28 does not generalize, continue a genuinely distinct leak-free family; do not rescue by tuning Jul/Aug.
5. Keep v288 production unchanged unless independent leak-free validation supports promotion.
