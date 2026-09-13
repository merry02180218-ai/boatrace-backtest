# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R / 52 hits / ROI 172.560638%.
- Scope Feb-Aug 2026 full six-boat population; exclude exact v288 94R.
- Pre-deadline features only. Settlement/closing odds eval/staking only.
- JPY10,000 per selected race, Dutch. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run 34780059085: Apr-Jun 391R /87 hits / ROI114.913% / +583,090.

## Wave36S — RESEARCH_CANDIDATE
- Run 34785370650; artifact 10326411657.
- Apr-Jun: 358R /81 hits / ROI116.938% / +606,380 / head rate41.341% / conversion54.730% / maxDD625,060.
- Monthly ROI: Apr175.280 / May99.502 / Jun73.368 / Jul86.716 / Aug107.155.
- Jul-Aug: 272R /72 hits / ROI97.386% / -71,090. v288 overlap0.

## Wave36S-A audit — COMPLETE
- Fixed audit Run 34785891378 success; Job 103801181659; artifact 10326059528.
- Wave36S is always a stricter subset of raw Wave36: adds 0 races.
- Removed subsets: May 20R ROI124.9% +49,800; Jun 13R ROI43.777% -73,090; Jul 24R ROI30.121% -167,710; Aug 31R ROI61.784% -118,470.
- Apr-Jun payout concentration: removing largest win leaves ROI100.109%; removing top3 leaves86.201%; removing top5 leaves80.221%.
- Apr-Jun first half: 179R /49 hits / ROI164.355% / +1,151,960 / head45.810% / conversion59.756%.
- Apr-Jun second half: 179R /32 hits / ROI69.521% / -545,580 / head36.872% / conversion48.485%.
- Conclusion: aggregate edge is tail-dependent and late-pristine performance collapses. No production adoption yet.

## Wave36S-B descriptive diagnosis — STARTING
- Preserve exact Wave36S selections/model; diagnostic only.
- Compare early vs late Apr-Jun on the 63 static pre-deadline features, raw/calibrated p3, head rate, Top5 conversion, payout/return distribution.
- Rank standardized feature drift; summarize by ST, racer strength, motor, boat and relative-gap families.
- Diagnose whether late decline is mainly head-selection, order-conversion, payout compression, or combination.
- Do not tune any threshold/filter from Apr-Jun outcomes. Any mitigation must later be designed from Feb/March evidence.

## Restart
Implement Wave36S-B diagnosis, run CI, record exact results, then define the safest pre-April-designed next experiment.
