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

## Wave36S-F two-layer opponent allocation — COMPLETE / NO_ADOPTION
- Run 34789147056 success; Job 103810013414; artifact 10327388998; artifact SHA256 07439a302357495b3052c107e469630256a59bfac201338848da1a6a37b98931.
- Frozen Wave36 gate unchanged: p3>=0.365448, Top5, exact v288 exclusion, v288 overlap0, September forbidden true.
- Two-layer allocation fixed ex ante: Top1–3 JPY8,000; Top4–5 JPY2,000. Apr-Jun 391R/87 hits/ROI106.616%/+258,700 vs original ROI114.913%/+583,090; NO_ADOPTION.
- Rank4–5 produced 26 winning tickets / JPY1,104,180 payout; five were 50x+ / JPY629,820.

## Wave36 head-hit / Top5-miss rank recovery — STARTING
- User now wants the 73 Apr-Jun races where Wave36 selected the race and actual winner was boat3, but actual 3-X-Y was outside current Top5.
- Goal: rebuild the frozen Wave36 conditional opponent scores for all 20 ordered 3-X-Y combinations and determine the actual combination rank (6..20) for each of those 73 misses.
- Report cumulative recovery at Top6, Top7, Top8, Top10, Top15, Top20; incremental extra ticket counts; actual winning trifecta odds distribution; especially 50x+ misses recovered at each depth.
- This is descriptive diagnosis only. Apr-Jun outcomes MUST NOT be used to choose a new live TopN rule. Any later rule must be selected/frozen using Feb training + March OOS only before Apr-Jun evaluation.
- Preserve exact Wave36 rolling training semantics, v288 exclusion, closing odds only for evaluation, Jul/Aug NON-PRISTINE, September forbidden/unread.

## Exact restart point
1. Rebuild Wave36 full 20-combination conditional ranking with the frozen Wave36 model/training schedule.
2. Isolate Apr-Jun actual boat3-head rows outside Top5 and audit their true rank 6..20.
3. Produce cumulative TopN recovery and high-odds recovery tables without tuning a rule on Apr-Jun.
4. Update this handoff with exact results and provenance after completion.
