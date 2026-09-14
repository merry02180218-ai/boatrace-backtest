# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Branch research/3head-v289-addon-expansion; newest GitHub state wins.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Full research universe is Wave20 every available six-boat race Feb 1-Aug 31 2026, no v243/PRE/bet/route candidate prefilter.
- Wave20 Run34749917116 success: 32,111R; Feb4100 Mar4607 Apr4244 May4832 Jun4488 Jul4920 Aug4920; missing program date 2026-06-17.
- Wave19b Run34749707037 failed for missing payout column and remains superseded; do not revert to 584R scope.
- Pre-deadline features only; JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden.

## Wave36 benchmark
- Run34780059085: Apr-Jun391R/87 hits/ROI114.913%/+583,090; conditional Top5 87/160 actual boat3-head cases.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE, not production adoption.

## Rank replacement research
- Wave39 direct linear pair 68/160 ROI70.911 NO_ADOPTION; Wave40 blend 68/160 NO_ADOPTION; Wave36G ordinal blend88/160 but ROI94.187 NO_ADOPTION; Wave41 ExtraTrees71/160 NO_ADOPTION; Wave42 factorized79/160 NO_ADOPTION.
- Wave43 prior successful Run34793612036: correction no-op, old/new Top587/160, NO_ADOPTION.
- Duplicate Wave43 Run34794147756 failed only on March assignment length mismatch. Plumbing fix commit a5cab5d65c7d0331c8940a2b53cf50f44974ed9e auto-triggered rerun Run34794554978; scientific result remains subordinate to prior successful Wave43 unless rerun contradicts it.

## Wave44 ATTACK MODE FIRST — STARTING
- Raw BoatraceCSV `results/realtime` schema was inspected and contains reliable post-race column `決まり手`; examples include `まくり` and `まくり差し`. Wave21 source currently discards this field, so Wave44 will rejoin it by race code strictly as historical target/diagnostic. It is NEVER a prediction input.
- Preserve Wave20 full population, exact v288 exclusion, Wave36 63 pre-deadline static features, head p3 gate and JPY10,000 Dutch evaluation.
- February: quantify actual boat3-win opponent topology separately for MAKURI vs MAKURI-SASHI and train a binary attack-mode predictor on the 63 pre-deadline features using only actual boat3 wins with either label.
- Train two mode-specific opponent-pair classifiers on February boat3 wins, one for MAKURI and one for MAKURI-SASHI. March predictions use a probability mixture from the Feb-only mode predictor; no actual March `決まり手` enters ticket construction.
- March OOS is the only architecture gate. Predeclared support rule: mixture Top5 on March selected actual boat3-head cases must improve frozen Wave36 by at least 1 net hit, lose no more than 2 existing hits, and must not collapse either chronological half. No March payout/ROI is used to select architecture.
- Only if March passes, freeze architecture and run expanding prior-month training for Apr-Jun one-shot pristine evaluation. Jul/Aug are NON-PRISTINE diagnostics and train only from history available before each target month; September unread.
- Report mode counts/topology, mode-predictor accuracy/AUC, March old/new Top5 retention/rescue, then if opened: R/hits/ROI/profit/monthly/min month/red months/maxDD/v288 overlap/baseline+addon combined.

## Exact restart point
1. Let fixed Wave43 rerun finish and record it.
2. In parallel implement/run Wave44 attack-mode diagnostic using `決まり手` only as historical label.
3. If March support gate fails, NO_ADOPTION without opening Apr-Jun; if it passes, run one-shot Apr-Jun and record exact results before any adoption decision.
