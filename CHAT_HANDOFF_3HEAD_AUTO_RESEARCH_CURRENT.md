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
- User requested Wave36-specific opponent allocation after analyzing both 10–20x core hits and 50x+ hits.
- Implementation commit 249efa1295a48accf26cfb6677a5a7a9723365f1; workflow commit 1e5d9339b3ca2e07a9162fb7e1708af14d884651.
- Run 34789147056 success; Job 103810013414; artifact 10327388998; artifact SHA256 07439a302357495b3052c107e469630256a59bfac201338848da1a6a37b98931.
- Frozen Wave36 gate unchanged: p3>=0.365448, Top5, exact v288 exclusion, v288 overlap0, September forbidden true.
- Two-layer allocation fixed ex ante before Apr-Jun inspection: Top1–3 share JPY8,000 via inverse-odds Dutch; Top4–5 share JPY2,000 via inverse-odds Dutch. Total stake exactly JPY10,000/race. No Apr-Jun payout/ROI tuning.
- Apr-Jun pristine two-layer: 391R /87 hits / stake3,910,000 / payout4,168,700 / profit +258,700 / ROI106.616%.
- Same races original Wave36 equal-Dutch baseline: ROI114.913% / profit +583,090. Therefore two-layer weighting reduced profit by 324,390 and is NO_ADOPTION.
- Monthly two-layer: Apr121R/33 hits/ROI158.731%/+710,650; May145R/33 hits/ROI94.486%/-79,950; Jun125R/21 hits/ROI70.240%/-372,000.
- Odds-band two-layer Apr-Jun: <10x 54R/22 hits/ROI114.652%/+79,120; 10–20x 94R/33 hits/ROI119.346%/+181,850; 20–50x 120R/22 hits/ROI98.463%/-18,450; 50x+ 123R/10 hits/ROI101.315%/+16,180.
- Rank4–5 produced 26 winning tickets and JPY1,104,180 payout. Of these, five were 50x+ and paid JPY629,820 under the two-layer allocation.
- Rank4–5 50x+ captured races: 202604091008 3-2-5 90.0x rank4 return108,000; 202604290808 3-1-6 334.7x rank5 return334,700; 202605012309 3-5-1 81.5x rank5 return16,300; 202605100512 3-1-5 86.3x rank5 return129,450; 202605131406 3-2-5 59.1x rank4 return41,370.
- Jul-Aug NON-PRISTINE two-layer diagnostic: 328R /79 hits / ROI89.572% / -342,050; not used for adoption.
- Interpretation: preserving Top4–5 is correct because tail wins are real, but a hard 80/20 stake split underfunds those tail winners and worsens pristine economics. Do not adopt this weighting. Next research should identify pre-race conditions for when rank4–5 deserves full/elevated funding rather than always shrinking it.

## Exact restart point
1. Keep production v288 untouched and keep Wave36 baseline/Wave36S-C as current references.
2. If continuing Wave36 opponent research, do not globally downweight Top4–5. Instead study pre-deadline predictors that distinguish profitable tail races from ordinary rank4–5 noise, using Feb training + March OOS only and no Apr-Jun payout tuning.
3. Preserve exact JPY10,000 stake accounting, v288 overlap0, Jul/Aug NON-PRISTINE, September forbidden/unread.
4. Wave36S-D parity recovery remains a separate technical branch; its old partial ROI numbers remain diagnostic-invalid until NO-BET stake semantics and 9 missing races are resolved.
