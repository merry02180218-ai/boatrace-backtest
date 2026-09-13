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

## Wave36S-E confidence-margin narrowing — COMPLETE / NO_ADOPTION
- Run 34787362679 success; job 103805147776; artifact 10327236674; artifact SHA256 100da520acc1ec98e3b3af08db72b669aea4fa5d3d01d14f326684ad9ed0ee7a.
- Checkout SHA 6d99d440ac5184e341541c40199548bcaa8fc733.
- Selection used March OOS head rate only; no March payout/ROI and no Apr-Aug tuning.
- March Wave36S-C pool 79R. Tested confidence-margin keep levels 100/80/65/50/40/33%.
- March-selected setting: keep65%, margin_cut 0.0853103576642292, 51R, head rate43.137%.
- Apr-Jun pristine narrowed result:175R/46 ticket hits/79 head hits/head45.143%/conversion58.228%/ROI100.446%/+7,800/maxDD319,330.
- Monthly: Apr63R/19 hits/ROI117.984%/+113,300; May63R/15 hits/ROI85.176%/-93,390; Jun49R/12 hits/ROI97.529%/-12,110.
- Jul-Aug NON-PRISTINE diagnostic:130R/35 hits/ROI94.733%/-68,470; Jul55.000%, Aug133.262%.
- Exact v288 overlap 0; September forbidden true.
- Decision: NO_ADOPTION. Narrowing improved head rate, conversion, maxDD and June from72.542% to97.529%, but destroyed aggregate pristine economics versus Wave36S-C ROI128.218%/+860,660. Keep Wave36S-C unchanged as research candidate.

## Wave36S-D v288-style opponent selection — STARTING
- User explicitly requested that opponent selection use v288 as the reference.
- Preserve Wave36S-C head-selection rule exactly; do not alter p3 calibration, motor-mismatch modifier, threshold, or v288 exclusion.
- Reference opponent stack is the production v288 path: frozen V221 ordered-pair ranker (`safe_order`) -> v242 variable TopN targeting composite odds 3.00 -> skip if unconstrained TopN<5 -> cap TopN at10 -> exact JPY10,000 Dutch.
- First test whether the Wave36 all-race source contains the fields required to run the exact v288 V221 orderer without imputation. If exact parity is possible, use the v288 orderer unchanged. If not, fail closed and record the missing-field blocker rather than inventing features.
- Any optional adaptation beyond exact v288 parity must be selected/frozen from Feb training + March OOS order accuracy/conversion only. Never choose from March payout/ROI; never tune from Apr-Aug outcomes.
- Evaluate Apr-Jun pristine month-by-month and aggregate on R/hits/head hits/head rate/conversion/ROI/profit/maxDD. Jul/Aug NON-PRISTINE diagnostic only. September forbidden. Exact v288 overlap must remain zero.
- Compare against frozen Wave36S-C and the v288 baseline context. Do not modify production v288.

## Exact restart point
1. Implement exact v288 V221/v242 opponent-selection parity on Wave36S-C candidates if source fields permit.
2. Run CI and inspect exact Apr-Jun plus Jul-Aug diagnostic results.
3. Record run/artifact/results here before reporting; if exact parity is blocked, record the blocker and do not substitute an unaudited orderer.
