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

## Wave36S-C narrowing experiment — PLANNED / STARTING
- User requested narrowing Wave36 rather than expanding race count.
- Freeze Wave36S-C model, p3 calibration, motor-mismatch modifier and v288 exclusion; do not change production v288.
- Search for stricter pre-deadline gates that reduce the 305 Apr-Jun races toward roughly 200 / 150 / 100 race bands.
- Candidate gates may use only information available before the target evaluation period. Select/freeze rules using Feb training + March OOS only; never tune from Apr-Jun ROI/payout and never tune from Jul/Aug outcomes.
- Prioritize robustness, not peak aggregate ROI: report Apr, May, Jun separately plus aggregate R/hits/head rate/conversion/ROI/profit/maxDD. Explicitly check whether June ROI can recover while retaining useful volume.
- Jul/Aug remain NON-PRISTINE diagnostic only. September outcomes/data forbidden. Exact v288 overlap must remain zero.
- Closing odds may be used only for exact JPY10,000 Dutch staking/evaluation, never candidate selection.
- Compare every narrowed survivor against frozen Wave36S-C (305R/74 hits/ROI128.218%) and v288 baseline context.
- If no narrowing rule improves robustness without obvious overfitting, keep Wave36S-C unchanged and record NO_ADOPTION.

## Wave36S-D order-conversion robustness — DEFERRED UNTIL NARROWING CHECK
- Preserve Wave36S-C head-selection rule exactly if/when resumed.
- Target conditional opponent ordering / Top5 conversion robustness using Feb training and March OOS only.

## Exact restart point
1. Implement Wave36S-C narrowing candidates with Feb/March-only selection.
2. Run CI and inspect exact Apr-Jun plus Jul-Aug diagnostic results.
3. Record run/artifact/results here before reporting.
4. Only after narrowing decision, resume Wave36S-D if still warranted.
