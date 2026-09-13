# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline: 94R / 52 hits / ROI 172.560638%.
- FINAL scope: Wave20 full six-boat population Feb 1-Aug 31 2026; exclude exact v288 operational 94R only.
- Jul/Aug NON-PRISTINE shadow only; September outcomes forbidden.
- Prediction uses pre-deadline card information only. Settlement/closing odds evaluation/staking only.
- JPY10,000 per selected race, Dutch; v288 overlap must be zero.

## Stable source
- Wave20 Run 34749917116 success: 32,111R; Feb 4100 / Mar 4607 / Apr 4244 / May 4832 / Jun 4488 / Jul 4920 / Aug 4920.
- Wave21 Run 34751314113: settlement usable 31,518R.
- Wave22 Run 34752573368: full 120 closing odds 31,605R.
- Wave19b Run 34749707037 failed missing payout column; superseded, never revert to old 678/584 scope.

## Wave36 shrinkage-LDA — RESEARCH CANDIDATE
- Run 34780059085; Apr-Jun 391R / 87 hits / ROI 114.913% / +583,090 yen.
- Apr 175.280%, May 103.005%, Jun 70.290%; Jul-Aug shadow 89.756%; overlap 0.

## Wave36L/R
- Leak audit Run 34781494240 PASS: 63 features, no suspicious names, causal walk-forward, shuffled-label AUC 0.506287.
- Robustness Run 34781673254: April high-payout concentrated; June weakness includes 26 correct-head/order-miss races.

## Wave37 opponent/order research — COMPLETE
- Run 34782216334 success; artifact 10325149135.
- March conditional conversion: logit 63.158%, position 50.000%, ExtraTrees 34.211%. Current conditional logistic retained.
- Apr-Jun 391R / 87 hits / ROI 114.913%; conditional conversion 54.375%.

## Wave38 opponent structural features — COMPLETE
- Run 34782510443 success; Job 103791972125; artifact 10325785027.
- Expanded static opponent feature set: 198 features from each opponent and pairwise gaps.
- March candidates selected without ROI. Baseline static63 C=.15 remained best: 24/38 conditional top5 hits = 63.158%, worst-half 52.632%.
- Expanded variants: C=.03 60.526%, C=.08 57.895%, C=.15 55.263%, C=.30 52.632%; all had worst-half 47.368%.
- Therefore expanded opponent features were not selected and Apr-Jun reproduces Wave36/Wave37: 391R / 87 hits / ROI 114.913% / +583,090 yen; conversion 54.375%; overlap 0.
- Monthly Apr 175.280%, May 103.005%, Jun 70.290%. Jul/Aug remain NON-PRISTINE.
- Conclusion: naive race-level feature expansion worsens March order conversion. Do not adopt.

## Wave39 candidate-pair ranker — STARTED
- Freeze Wave36 3-head gate p3>=0.365448 and head model chronology.
- Replace 20-class race-level order prediction with candidate-pair binary ranking: for every 3-head training race, create 20 candidate 3-a-b rows; positive label is the actual exact order.
- Candidate row uses global static card context plus candidate-specific second/third boat values and pair differences derived only from nationwide/local/ST/motor/boat static metrics.
- Compare predeclared regularization values on Feb->Mar conditional top5 conversion and early/late worst-half conversion; no March ROI selection.
- Freeze selected pair ranker before Apr-Jun. Jul/Aug shadow only; September forbidden; closing odds never prediction features.

## Exact restart point
1. Implement/run Wave39 pair ranker.
2. Auto-fix technical failures without weakening guards.
3. Record exact March selection, Apr-Jun conversion/ROI/monthly/overlap, and Jul-Aug shadow.
4. If pair ranking fails to beat 63.158% March / 54.375% pristine conversion robustly, retain Wave36 orderer and move to calibration/selection-count research without using Apr-Jun outcomes for tuning.
