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

## Wave36C one-month-lag p3 recalibration — COMPLETE / NO_ADOPTION
- Run 34784940922 success; artifact 10325838776.
- Method: one-month-lag Platt calibration of raw Wave36 p3. March OOS calibrated April; then Apr->May, May->Jun, Jun->Jul, Jul->Aug. No current-month outcomes entered its own calibration.
- March mapped original raw gate p3=0.365448 to fixed calibrated cut 0.391729.
- Apr-Jun pristine recalibrated: 341R / 77 hits / ROI 111.111% / +378,890 yen / 144 head hits / head rate 42.229% / conversion 53.472% / max DD 634,560 yen.
- Original raw Wave36 Apr-Jun comparator: 391R / 87 hits / ROI 114.913% / +583,090 yen / head rate 40.921% / conversion 54.375% / max DD 717,360 yen.
- Monthly recalibrated:
  - Apr: 121R / 33 hits / ROI 175.280% / +910,890; identical to raw.
  - May: 114R / 24 hits / ROI 74.235% / -293,720; worse than raw 103.005%.
  - Jun: 106R / 20 hits / ROI 77.521% / -238,280; improved from raw 70.290%, with head rate 41.51% vs 37.60%.
  - Jul NON-PRISTINE: 134R / 32 hits / ROI 84.128% / -212,690; improved from raw 77.896%.
  - Aug NON-PRISTINE: 138R / 39 hits / ROI 106.275% / +86,600; improved from raw 99.025%.
- Jul-Aug recalibrated robustness: 272R / 71 hits / ROI 95.364% / -126,090 / head rate 43.75% / max DD 393,720.
- Raw Jul-Aug comparator: 327R / 79 hits / ROI 89.074% / -357,270 / head rate 40.37% / max DD 572,990.
- Exact v288 overlap 0.
- Interpretation: monthly recalibration improved June, July and August robustness and reduced drawdown, but materially damaged May. Therefore it does not beat the pristine Apr-Jun benchmark and is NO_ADOPTION as a universal replacement. It is evidence that temporal p3 calibration is useful, but a one-month-only calibrator is too reactive/noisy.

## Exact restart point
1. Keep original Wave36 raw gate + Top5 as the pristine benchmark.
2. Promising direction: smoother calibration using multiple prior months / shrinkage toward the March calibrator, predeclared without Apr-Jun ROI tuning.
3. Jul/Aug improvements from Wave36C are diagnostic only and cannot rescue pristine adoption.
