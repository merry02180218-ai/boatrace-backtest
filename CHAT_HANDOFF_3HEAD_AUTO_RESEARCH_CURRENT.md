# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Active continuation branch: research/3head-player-attack-mode, forked from historical verified attack-mode pivot commit dcc012e4e81ef19636a070f221282c1b87ed262c. Do not rewrite current main.
- Fixed v288 baseline 94R /52 hits / ROI172.560638%.
- Pre-deadline features only; JPY10,000 per selected race. Jul/Aug NON-PRISTINE. September forbidden/unread.
- 3号艇 hourly research monitor was explicitly disabled by user on 2026-09-14. Do not recreate it unless user asks.

## Wave36 benchmark
- Run34780059085: Apr-Jun391R/87 hits/ROI114.913%/+583,090.
- Conditional ranking on160 actual boat3-head cases: Top5=87/160.

## Wave36S-C
- Run34786354062: Apr-Jun305R/74 hits/ROI128.218%/+860,660. RESEARCH_CANDIDATE.

## Rank replacement research
- Wave39 direct linear pair:68/160, ROI70.911%, NO_ADOPTION.
- Wave40 blend:68/160, ROI70.911%, NO_ADOPTION.
- Wave36G ordinal blend:88/160 but ROI94.187%, NO_ADOPTION.
- Wave41 ExtraTrees:71/160, ROI74.814%, NO_ADOPTION.
- Wave42 factorized second/third:79/160, ROI90.795%, NO_ADOPTION.

## Wave43 conservative boundary correction — COMPLETE / NO_ADOPTION
- Plan commit6657d886e6ec0b8bce57c4113fd9275530b8fa8a.
- CI Run34793612036 success; Job103822377750; artifact10328797771.
- March and Apr-Jun correction collapsed to no-op; Apr-Jun old/new Top5 both87/160. NO_ADOPTION.

## User hypothesis / research pivot — PLAYER-SPECIFIC ATTACK MODE
- User proposes that MAKURI vs MAKURI-SASHI may be identifiable primarily from the individual racer's historical tendencies rather than generic race-level features.
- This supersedes the generic attack-mode classifier as the immediate experiment.
- Historical actual kimarite is target/diagnostic only. Never feed current-race result/kimarite into live prediction.

## BEFORE-WORK PLAN — 2026-09-14
1. Inspect historical pre-race/source data for stable racer ID and historical results/kimarite availability. Never infer kimarite from finish order.
2. Build leakage-safe player-history features available strictly before each race, prioritizing boat3/3-course history: prior MAKURI count/rate, prior MAKURI-SASHI count/rate, smoothed log-odds/share, sample size, recent-window and longer-window tendencies where source coverage permits. Use only races chronologically before target race.
3. Evaluate whether player-history features improve Feb-trained -> March OOS MAKURI-vs-MAKURI-SASHI discrimination versus the prior generic mode model. Report class counts, coverage, AUC/logloss/accuracy as feasible, and performance by history sample size.
4. Only if March OOS mode discrimination shows meaningful improvement, feed predicted mode probabilities into mode-specific opponent ranking and compare frozen Wave36 Top1/3/5/8/10, MRR, retained/lost/rescued, March early/late.
5. March promotion gate remains conservative: Top5 must improve by >=1, lost existing Wave36 Top5 hits <=2, and improvement cannot exist only in one March half. If gate fails, do not open Apr-Jun.
6. If March passes, freeze design and run Apr-Jun exactly once with exact JPY10,000 Dutch economics. Production v288 remains untouched. Jul/Aug diagnostic only; September outcomes remain unread.

## Exact restart point
- Start with source/schema audit for stable racer ID + historical kimarite and implement player-history attack-mode features on this isolated branch.
