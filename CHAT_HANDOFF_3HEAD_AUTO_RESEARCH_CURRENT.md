# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- FINAL scope: Wave20 full six-boat population Feb 1-Aug 31 2026; exclude exact v288 operational 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction: exactly 63 static pre-deadline features. Settlement/closing odds evaluation/staking only.
- JPY10,000 per selected race, Dutch; v288 overlap must be zero.

## Stable source
- Wave20 Run 34749917116: 32,111R.
- Wave21 Run 34751314113: settlement usable 31,518R.
- Wave22 Run 34752573368: full 120 closing odds 31,605R.

## Wave36 shrinkage-LDA — RESEARCH CANDIDATE
- Run 34780059085; Apr-Jun 391R / 87 ticket hits / ROI 114.913% / +583,090 yen.
- Apr 175.280%, May 103.005%, Jun 70.290%; Jul-Aug shadow 89.756%; overlap 0.

## Wave36L leak audit — PASS
- Run 34781494240; artifact 10325173171.
- 63 features, suspicious feature names 0; walk-forward causality PASS; shuffled-label AUC 0.506287.
- No clear future-information leakage.

## Wave36R robustness decomposition — COMPLETE
- Run 34781673254 success; artifact 10325487808.
- Apr: 121R; head 54/121=44.628%; top5 ticket 33/121=27.273%; ROI 175.280%. Remove largest return => 125.490%; remove top3 => 99.181%.
- May: 145R; head 59=40.690%; top5 33=22.759%; ROI 103.005%. Early ROI 148.194%, late 58.434%.
- Jun: 125R; head 47=37.600%; top5 21=16.800%; 26 races had correct 3-head but exact-order top5 miss; ROI 70.290%.
- Conclusion: Wave36 head gate retains signal; opponent/exact-order conversion is a major weakness.

## Wave37 opponent/order research — COMPLETE
- Run 34782216334 success; Job 103791173136; artifact 10325149135.
- March comparison used conversion conditional on actual 3-head only; no ROI selection.
- March results:
  - logit: 38 head cases / 24 top5 hits / conversion 63.158%; early 73.684%; late 52.632%; worst-half 52.632%.
  - ExtraTrees: 34.211% conversion; worst-half 31.579%.
  - position decomposition: 50.000% conversion; worst-half 47.368%.
- March therefore selected current conditional logistic. The alternative orderers did not beat it.
- Apr-Jun with selected logit reproduces Wave36 exactly: 391R / 87 hits / ROI 114.913% / +583,090 yen; conditional conversion 87/160=54.375%; overlap 0.
- Monthly conversion: Apr 33/54=61.111%; May 33/59=55.932%; Jun 21/47=44.681%.
- Jul NON-PRISTINE: 34/59=57.627%, ROI 77.896%. Aug NON-PRISTINE: 45/75=60.000%, ROI 100.253%.
- Interpretation: simple model-class swap does not fix June. Current conditional logistic remains best among tested orderers; next work should add opponent-specific structural features rather than replacing classifier family.

## Wave38 opponent structural features — NEXT
- Keep Wave36 head gate and March-only selection discipline fixed.
- Add pre-deadline opponent-specific structure for boats 1/2/4/5/6 and pair relationships relevant to 2nd/3rd ordering, without using result/odds/current-meet post-race fields.
- Candidate features should come only from existing static card information: each opponent's nationwide/local/motor/boat rates and ST, plus relative gaps versus boat3 and pairwise opponent gaps.
- Tune/orderer choice on Feb->Mar only using conditional top5 conversion, not ROI. Freeze before Apr-Jun.
- Report pristine Apr-Jun conditional conversion and ROI versus Wave37 baseline; Jul/Aug shadow only; September forbidden.

## Exact restart point
1. Implement Wave38 opponent-specific structural feature orderer.
2. Launch CI and auto-fix technical failures without weakening guards.
3. Record exact results here after completion.
