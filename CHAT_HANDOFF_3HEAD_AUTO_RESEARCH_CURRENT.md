# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Scope Feb-Aug 2026 full six-boat population; exclude exact v288 94R.
- Pre-deadline features only. Settlement/closing odds eval/staking only.
- JPY10,000 per selected race, Dutch. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run 34780059085: Apr-Jun 391R /87 hits / ROI114.913% / +583,090.

## Wave36S — RESEARCH_CANDIDATE
- Run 34785370650; Apr-Jun 358R /81 hits / ROI116.938% / +606,380.

## Wave36S-C pre-April motor robustness modifier — RESEARCH_CANDIDATE
- Run 34786354062 success; artifact 10326661910.
- Frozen rule: racer composite >= Feb q50 AND motor composite <= Feb q50 => subtract 0.08 from calibrated p3. Rule selected from March OOS head rate only.
- Apr-Jun pristine:305R/74 hits/ROI128.218%/+860,660/head42.295%/conversion57.364%/maxDD481,120.
- Monthly: Apr190.737%, May112.675%, Jun72.542%. June head rate recovered to41.111% but conversion only43.243%.
- Jul-Aug NON-PRISTINE ROI94.628%/-123,550. Not production adopted.

## Wave36S-D pre-April order-conversion robustness — STARTING
- Preserve Wave36S-C head-selection rule exactly; do not alter its p3 calibration, motor-mismatch penalty, threshold, or temporal chronology.
- Target only conditional opponent ordering / Top5 conversion robustness because June head selection recovered while order conversion remained weak.
- Design candidate orderer robustness changes using Feb training and March OOS only. Candidate choice must use March conditional-order accuracy/conversion metrics only; never March payout/ROI and never Apr-Aug outcomes.
- Keep prediction inputs strictly pre-deadline. Closing odds remain Dutch staking/evaluation only. Settlement fields evaluation only. September forbidden. Exact v288 overlap must remain zero.
- Freeze the March-selected orderer rule, then evaluate Apr-Jun pristine month-by-month and aggregate; Jul/Aug NON-PRISTINE diagnostic only.
- Compare against frozen Wave36S-C and original Wave36S on R/hits/ROI/profit/head rate/conversion/maxDD. No Apr-Aug threshold/filter tuning.

## Exact restart point
1. Implement Wave36S-D orderer candidates from Feb/March evidence only.
2. Run CI and inspect exact Apr-Jun plus Jul-Aug results.
3. Record run/artifact/results here before reporting; if no robust improvement, keep Wave36S-C as candidate and do not adopt D.
