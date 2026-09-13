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
- Apr: 121R; head 54/121=44.628%; top5 ticket 33/121=27.273%; ROI 175.280%. Remove largest return => 125.490%; remove top3 => 99.181%. April profit is materially high-payout concentrated.
- May: 145R; head 59=40.690%; top5 33=22.759%; ROI 103.005%. Early ROI 148.194%, late 58.434%.
- Jun: 125R; head 47=37.600%; top5 21=16.800%; 26 races had correct 3-head but exact-order top5 miss; ROI 70.290%. Early 56.765%, late 83.602%.
- Jul NON-PRISTINE: head 38.312%, top5 22.078%, ROI 77.896%.
- Aug NON-PRISTINE: head 43.103%, top5 25.862%, ROI 100.253%.
- Conclusion: no monotonic leakage signature. Wave36 head gate retains signal, but opponent/exact-order conversion is a major weakness, especially June. Keep head gate fixed and research opponent/order selection separately.

## Wave37 opponent/order research — STARTED
- Freeze Wave36 3-head gate and its pre-April selection logic; do not optimize head threshold on Apr-Jun or Jul/Aug.
- Research only conditional 2nd/3rd ordering among combos beginning with 3.
- Train opponent/order model using pre-test historical rows only. March is the only validation/tuning month; Apr-Jun untouched pristine evaluation; Jul/Aug shadow only.
- Compare current conditional logistic top5 against structurally different orderers using the same 63 static features: regularized multinomial conditional model and pairwise/position decomposition if implementable.
- Selection objective in March must emphasize exact-order/top5 conversion conditional on actual 3-head, not realized ROI. Closing odds cannot select/tune the orderer.
- Freeze selected orderer before Apr-Jun. Report head hits, ticket hits, conditional conversion ticket_hits/head_hits, ROI/profit/monthly/min month/max DD/overlap and baseline+combined.
- Required feature missing => fail closed; September forbidden.

## Exact restart point
1. Implement Wave37 conditional opponent/order comparison with fixed Wave36 head gate.
2. Launch CI and auto-fix technical failures without weakening guards.
3. Record exact results here after completion.
4. If no improvement in pristine conversion/robustness, move to opponent-specific structural features without using Apr-Jun/Jul-Aug outcomes for tuning.
