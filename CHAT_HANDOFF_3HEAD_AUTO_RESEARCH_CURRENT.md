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

## Wave36S-F two-layer opponent allocation — STARTING
- User requested a Wave36-specific opponent-selection study after examining both the strong 10–20x hit band and the 50x+ hits.
- Preserve Wave36 head-selection logic and exact v288 exclusion; do not alter production v288.
- Design target: two-layer ticket allocation with mainline Top1–3 and retained longshot Top4–5 rather than trimming all lower-ranked opponents.
- Critical observation to test: 10–20x winners are concentrated in higher-ranked opponent combinations, while 50x+ winners disproportionately survive in ranks 3–5; therefore Top4–5 must be evaluated as a small-stake longshot layer rather than discarded.
- Selection/tuning discipline: derive and freeze any ranking/allocation thresholds from Feb training + March OOS only. Do not use Apr–Jun payout/ROI for tuning. Jul/Aug remain NON-PRISTINE diagnostics only. September forbidden/unread.
- Evaluate Apr/May/Jun separately and aggregate with actual JPY10,000 per bet, exact stake accounting, ticket hits, head hits, conversion, ROI, profit, max drawdown, hit-odds distribution, and 50x+ capture/return contribution.
- Explicitly report whether the two-layer design preserves the 50x+ winners that drive tail profit while improving the 10–20x core.
- If no robust OOS improvement, NO_ADOPTION.

## Exact restart point
1. Build Wave36S-F research script from the frozen Wave36 dataset/artifact and only pre-April design information.
2. Freeze mainline/longshot allocation from Feb + March only; no Apr-Jun tuning.
3. Run Apr-Jun pristine evaluation, then Jul/Aug NON-PRISTINE diagnostics if available without violating source parity.
4. Record exact CI/run/artifact IDs, monthly/aggregate metrics, 10–20x and 50x+ contributions, v288 overlap0, September guard, and adoption/no-adoption.
