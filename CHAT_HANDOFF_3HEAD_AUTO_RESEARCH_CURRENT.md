# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Scope Feb-Aug 2026 full six-boat population; exclude exact v288 94R.
- Pre-deadline features only. Settlement/closing odds eval/staking only.
- JPY10,000 per selected race, Dutch. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run 34780059085: Apr-Jun 391R /87 hits / ROI114.913% / +583,090.

## Wave36S-C pre-April motor robustness modifier — RESEARCH_CANDIDATE
- Run 34786354062 success; artifact 10326661910.
- Apr-Jun pristine:305R/74 hits/ROI128.218%/+860,660/head42.295%/conversion57.364%/maxDD481,120.
- Monthly: Apr190.737%, May112.675%, Jun72.542%. June head rate41.111%, conversion43.243%.
- Jul-Aug NON-PRISTINE ROI94.628%/-123,550. Not production adopted.

## Wave36S-E confidence-margin narrowing — COMPLETE / NO_ADOPTION
- Run 34787362679 success; Apr-Jun 175R/46 hits/ROI100.446%/+7,800; no adoption.

## Wave36S-D exact v288 opponent selection — FAILED / RECOVERY STARTED
- Run 34787885427 failed by intentional fail-closed parity guard; Job 103806586829; artifact 10327506732; artifact SHA256 6706ce5b35c740393b71d42eca13b8e998b476d06287486c81e0c34c8fec604d.
- Exact stack attempted: production V221 ordered-pair ranker safe_order -> v242 variable TopN target composite odds3.00 -> skip if unconstrained TopN<5 -> cap10 -> exact JPY10,000 Dutch.
- Wave36S-C expected Apr-Jun candidates305R; exact v288-orderer inputs covered296R; 9R missing/invalid, so decision FAIL_CLOSED_PARITY_INCOMPLETE and CI exited1 by design.
- Missing race codes: 202604190602, 202605020105, 202605070503, 202605070505, 202605071301, 202605191810, 202605280107, 202606160302, 202606240705.
- Partial 296R metrics are diagnostic only and must NOT be treated as valid parity result: Apr106R ROI107.446%; May102R ROI64.874%; Jun88R ROI33.461%; Apr-Jun ROI70.780%/-864,900; conversion42.742%; v288 overlap0.
- Recovery rule: investigate only technical/source recovery for those 9R. Do not impute or change model/order criteria. If exact required pre-deadline fields cannot be recovered, keep fail-closed and record blocker; do not substitute an unaudited orderer.

## Exact restart point
1. Inspect Wave36S-D script and the 9 missing/invalid races to identify whether fetch/parsing/source plumbing caused the parity gap.
2. If recoverable without imputation/model changes, fix plumbing and rerun exact parity automatically.
3. If not recoverable, record exact missing fields/source blocker and stop this exact-parity branch while preserving Wave36S-C candidate.
