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
- Run 34785370650; artifact 10326411657.
- Apr-Jun 358R /81 hits / ROI116.938% / +606,380 / head41.341% / conversion54.730% / maxDD625,060.
- Monthly ROI Apr175.280 / May99.502 / Jun73.368 / Jul86.716 / Aug107.155.

## Wave36S-A/B audit + diagnosis — COMPLETE
- Wave36S aggregate edge is concentrated early; Apr-Jun halves early ROI164.355% vs late69.521%.
- Wave36S-B Run 34786166134: late degradation combines head-selection and order-conversion failure. Racer-strength gaps became more favorable while motor signal weakened; p3 did not warn adequately.

## Wave36S-C pre-April motor robustness modifier — COMPLETE / RESEARCH_CANDIDATE
- Run 34786354062 success; Job 103802431273; artifact 10326661910; artifact SHA256 cd4c3a54cc33c6f2447b2324bc8d5238e9df5a7946f0a11e8347e9da43ae5dc7.
- Rules: exact Wave36S 63 static features and Top5 architecture; Feb-only standardization for composites; March OOS chooses modifier by head rate only, never payout/ROI. September forbidden; exact v288 overlap0.
- Chosen pre-April rule: racer composite >= Feb q50 (-0.009837) AND motor composite <= Feb q50 (-0.024125) => subtract 0.08 from calibrated p3. March retained79R with head rate43.038%.
- Apr-Jun pristine: 305R /74 ticket hits / stake3,050,000 / payout3,910,660 / profit +860,660 / ROI128.218% / head129 / head rate42.295% / conversion57.364% / maxDD481,120.
- Wave36S comparator Apr-Jun: 358R /81 hits / ROI116.938% / +606,380 / head41.341% / conversion54.730% / maxDD625,060. Raw Wave36 benchmark:391R /87 hits / ROI114.913% / +583,090.
- Monthly Wave36S-C: Apr107R/31 hits/ROI190.737%/+970,890/head43.925%/conversion65.957%; May108R/27/ROI112.675%/+136,890/head41.667%/conversion60.0%; Jun90R/16/ROI72.542%/-247,120/head41.111%/conversion43.243%.
- Pristine robustness: aggregate ROI +11.280 points vs Wave36S; profit +254,280 yen; maxDD improves by143,940 yen; head rate +0.954 points; conversion +2.635 points. May becomes clearly profitable, but June remains weak and is the only red pristine month; minimum month72.542%.
- Jul-Aug NON-PRISTINE:230R/60 hits/ROI94.628%/-123,550/head44.783%/conversion58.252%/maxDD454,990. This is worse than Wave36S Jul-Aug ROI97.386%/-71,090, so shadow robustness is mixed rather than universally improved.
- Decision: keep as RESEARCH_CANDIDATE, not production adoption. The pre-April motor mismatch penalty materially improves pristine aggregate and drawdown without leakage, but June still fails and Jul/Aug shadow does not improve.

## Exact restart point
1. Preserve Wave36S-C frozen rule as a candidate; do not tune it on Apr-Aug.
2. Next experiment should target order-conversion robustness, because June Wave36S-C head rate recovers to41.11% but conversion remains only43.24%.
3. Design any orderer robustness change from Feb/March only, then freeze and evaluate Apr-Jun pristine; Jul/Aug remain NON-PRISTINE diagnostics.
