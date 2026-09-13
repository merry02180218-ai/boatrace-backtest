# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- FINAL scope: Wave20 full six-boat population Feb 1-Aug 31 2026; exclude exact v288 operational 94R only.
- Prediction uses pre-deadline card information only. Settlement/closing odds evaluation/staking only.
- JPY10,000 per selected race, Dutch; v288 overlap must be zero.

## Wave36 benchmark
- Run 34780059085; shrinkage-LDA head gate + conditional logistic Top5.
- Apr-Jun 391R / 87 hits / ROI 114.913% / +583,090 yen.
- Apr 175.280%, May 103.005%, Jun 70.290%.

## Wave36X extended learning — COMPLETE
- Run 34784017004 success; expanding Apr-Aug 718R / 166 hits / ROI 103.145% / +225,820 yen.
- Monthly ROI Apr 175.280 / May 103.005 / Jun 70.290 / Jul 77.896 / Aug 99.025.

## Wave36D temporal diagnosis — COMPLETE
- Run 34784246428 success; artifact 10325977322.
- June: head rate 37.60%, Top5 conversion 44.68%, ROI 70.29% — both head and order quality weakened.
- July: head rate 38.31%, conversion 57.63%, ROI 77.90% — head calibration weak plus low payout mix.
- High raw p3 was not reliably safer in Jun/Jul; p3>0.60 head rate was only 16.7% / 14.3%.
- Feature drift was strongest in relative ST and racer-strength fields.

## Wave36C one-month-lag p3 recalibration — STARTED
- Preserve Wave36 63 static features, shrinkage-LDA head model, conditional-logit Top5 orderer, expanding monthly chronology, JPY10k Dutch, and exact v288 exclusion.
- Recalibrate only the head probability p3; do not change the underlying head/order models.
- Use one-month-lag Platt calibration only from already-settled prior-month out-of-sample predictions: March OOS calibrates April, April calibrates May, May calibrates June, June calibrates July, July calibrates August. No current-month outcomes enter its own calibration.
- Anchor the calibrated decision threshold from March only by mapping the original Wave36 raw gate p3=0.365448 through the March Platt calibrator. Freeze that calibrated-probability threshold for all later months.
- Compare recalibrated-gate results against the original raw-gate Wave36 month by month. Report selected races, head hits/rate, Top5 hits/conversion, ROI/profit, max DD, Apr-Jun pristine aggregate, Jul-Aug NON-PRISTINE robustness, and exact v288 overlap.
- Jul/Aug may participate as prior-month learning only for this explicitly requested extended robustness diagnostic; they remain NON-PRISTINE for adoption. September outcomes forbidden.
- No Apr-Aug ROI-derived threshold tuning.

## Exact restart point
1. Implement Wave36C monthly Platt recalibration using actual Wave36 code.
2. Launch CI and auto-fix technical failures without weakening temporal guards.
3. On completion, update this handoff with exact results before reporting.
