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
- Apr-Jun recalibrated: 341R / 77 hits / ROI 111.111% / +378,890 yen.
- Jul-Aug: ROI 95.364% / -126,090 yen.
- One-month calibration helped Jun-Aug but damaged May badly.

## Wave36S smoother p3 calibration — COMPLETE / RESEARCH_CANDIDATE
- Run 34785370650 success; artifact 10326411657; workflow research-3head-wave36s-smooth-calibration.
- Method: 3-month-cap pooled prior-month OOS Platt calibration. April uses Mar only; May uses Mar+Apr; June uses Mar+Apr+May; July uses Apr+May+Jun; August uses May+Jun+Jul. Threshold remains March-anchored: raw 0.365448 -> calibrated 0.391729. No current-month outcomes used for own calibration.
- Rolling pooled calibration Apr-Jun pristine: 358R / 81 hits / ROI 116.938% / +606,380 yen / head hits 148 / head rate 41.341% / conversion 54.730% / max DD 625,060 yen.
- Raw Wave36 Apr-Jun comparator: 391R / 87 hits / ROI 114.913% / +583,090 yen / head rate 40.921% / conversion 54.375% / max DD 717,360 yen.
- Therefore rolling smoother improves pristine ROI by +2.025 points, profit by +23,290 yen, head rate by +0.420 points, conversion by +0.355 points, and reduces max DD by 92,300 yen, while selecting 33 fewer races.
- Rolling monthly ROI: Apr 175.280% (121R/33 hits), May 99.502% (125R/28), Jun 73.368% (112R/20), Jul NON-PRISTINE 86.716% (130R/32), Aug NON-PRISTINE 107.155% (142R/40).
- Rolling Jul-Aug robustness: 272R / 72 hits / ROI 97.386% / -71,090 yen / head rate 43.75% / conversion 60.504% / max DD 363,720 yen. This is better than raw Jul-Aug ROI 89.074% / -357,270 and Wave36C Jul-Aug ROI 95.364% / -126,090.
- Fixed 50% shrink-to-March variant Apr-Jun: 377R / 85 hits / ROI 116.127% / +607,980 yen / head rate 41.114% / conversion 54.839% / max DD 684,270 yen. It has slightly lower ROI than rolling but slightly higher absolute profit.
- Shrink monthly ROI: Apr 175.280%, May 104.012%, Jun 69.637%, Jul 82.164%, Aug 104.487%.
- Shrink Jul-Aug robustness: 301R / 77 hits / ROI 93.659% / -190,850 yen / max DD 452,990 yen.
- Exact v288 overlap rolling=0, shrink=0.
- Interpretation: smoother calibration clearly avoids Wave36C's May collapse and improves the Apr-Jun pristine aggregate over raw Wave36 on ROI/profit/DD. Rolling pooled calibration is currently the strongest calibration candidate; however improvement is modest and June remains weak, so retain RESEARCH_CANDIDATE rather than final adoption until robustness/audit confirms no accidental selection instability or hidden tuning.

## Exact restart point
1. Treat Wave36S rolling pooled calibration as the leading 3-head add-on research candidate, with raw Wave36 still the fixed benchmark.
2. Next: audit Wave36S month-by-month selected-race deltas versus raw, especially what was removed from May/June and whether gains are concentrated in a few payouts.
3. Reconfirm causality/leak guards and payout concentration before any adoption decision. Jul/Aug remain NON-PRISTINE diagnostics.
