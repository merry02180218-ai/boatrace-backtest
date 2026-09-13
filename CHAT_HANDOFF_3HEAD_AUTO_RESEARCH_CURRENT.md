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
- Monthly recalibrated: Apr 175.280%; May 74.235%; Jun 77.521%; Jul 84.128%; Aug 106.275%.
- Jul-Aug recalibrated robustness: 272R / 71 hits / ROI 95.364% / -126,090 / head rate 43.75% / max DD 393,720.
- Exact v288 overlap 0.
- Interpretation: temporal calibration helped Jun-Aug but one-month calibration was too reactive and damaged May.

## Wave36S smoother p3 calibration — STARTING
- Preserve the exact Wave36 63 static features, shrinkage-LDA head model, conditional-logit Top5 orderer, expanding chronology, JPY10k Dutch, and exact v288 exclusion.
- Test a predeclared smoother head-probability recalibration that uses only already-settled prior-month OOS predictions and never current-month outcomes.
- Primary rule: rolling prior OOS months with a 3-month cap (March for April; Mar+Apr for May; Mar+Apr+May for June; Apr+May+Jun for July; May+Jun+Jul for August), fitting one Platt calibrator to the pooled prior OOS rows.
- Keep the decision threshold anchored from March only by mapping raw p3=0.365448 through the March-only calibrator; do not optimize any threshold on Apr-Aug ROI.
- Also report a conservative shrinkage variant blending rolling calibration parameters toward the March calibrator with a fixed predeclared weight, but selection/adoption must be judged on Apr-Jun pristine only and Jul/Aug remain NON-PRISTINE diagnostics.
- Compare against raw Wave36 and Wave36C: selected races, head rate, Top5 conversion, ROI/profit, monthly ROI, min month, red months, max DD, overlap.

## Exact restart point
1. Implement Wave36S from the actual Wave36/Wave36C code without changing prediction features/orderer.
2. Launch CI and auto-fix technical failures without weakening temporal guards.
3. On completion, write exact Run/artifact/results here before reporting.
