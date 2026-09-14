# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Full research universe is Wave20 every available six-boat race Feb 1-Aug 31 2026, no v243/PRE/bet/route candidate prefilter.
- Wave20 Run34749917116 success: 32,111R; Feb4100 Mar4607 Apr4244 May4832 Jun4488 Jul4920 Aug4920; missing program date 2026-06-17.
- Wave19b Run34749707037 failed for missing payout column and remains superseded; do not revert to 584R scope.
- Pre-deadline features only; required feature missing => fail closed. Settlement and closing odds evaluation/staking only. JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run34780059085: Apr-Jun391R/87 hits/ROI114.913%/+583,090; maxDD717,360; exact v288 overlap0.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE, not production adoption.

## Rank replacement research
- Wave39 direct linear pair 68/160 ROI70.911 NO_ADOPTION; Wave40 blend 68/160 NO_ADOPTION; Wave36G ordinal blend88/160 but ROI94.187 NO_ADOPTION; Wave41 ExtraTrees71/160 NO_ADOPTION; Wave42 factorized79/160 NO_ADOPTION.
- Wave43 fixed rerun Run34794554978 success. March chosen correction retained all 24 old hits and rescued0; Apr-Jun old87 vs new85 Top5 hits. Money new391R/85 hits/ROI97.473%/-98,820 vs old114.913%/+583,090. Monthly new Apr118.127 May103.390 Jun70.615; NO_ADOPTION. This confirms conservative rerank does not improve production economics.

## Wave44 ATTACK MODE — COMPLETE / NO_ADOPTION
- Run34794666290 success; artifact10329167528.
- Historical `決まり手` shows strong topology difference: Feb MAKURI 189 rows vs MAKURI_SASHI187; MAKURI_SASHI second place is boat1 in118/187, while MAKURI is diffuse.
- However Feb-trained pre-deadline attack-mode predictor is effectively chance on March: AUC0.5078 / accuracy0.5057.
- March selected90R: frozen Wave36 old Top5 24/38 head cases vs attack-mixture20/38; retained18, lost6, rescued2, net -4. Early14->13, late10->7. March gate failed; Apr-Jun was not opened. Decision NO_ADOPTION_MARCH_GATE.
- `決まり手` remains target/diagnostic only and never prediction input.

## Wave45 adaptive TopK uncertainty width — STARTING
- Preserve Wave36 63-feature head p3 model, opponent score order, cut0.365448 and exact v288 exclusion. Do not rerank combinations.
- Hypothesis: repeated rerank failures imply ordering contains useful signal but Top5 is too narrow in uncertain races. Use conditional-model uncertainty only to choose ticket width Top5 vs Top8; always JPY10,000 total Dutch per selected race.
- Uncertainty statistic: cumulative probability mass of frozen opponent model Top5. Low Top5 mass => use Top8; otherwise Top5.
- Feb trains March model. March OOS only selects one mass threshold from predeclared March score-distribution quantiles using ticket-hit coverage, never payout/ROI. Gate requires >=1 net rescued March hit, no chronological-half deterioration, and average tickets <=6.5.
- If March gate passes, freeze the absolute mass threshold and evaluate Apr-Jun pristine once using standard expanding prior-month Wave36 training. Jul/Aug NON-PRISTINE uses Wave36 frozen-through-Jun convention. September unread.
- Report R/hits/ROI/profit/monthly/min month/red months/maxDD/overlap/combined baseline+addon and average ticket count. If gate fails, NO_ADOPTION without Apr-Jun money opening.

## Exact restart point
1. Implement/run Wave45 adaptive TopK.
2. If March gate fails, record and immediately launch a distinct full-population walk-forward idea; do not tune Wave45 on Apr-Aug.
3. If it passes, inspect one-shot Apr-Jun plus Jul/Aug shadow and record exact results before adoption/shadow decision.
