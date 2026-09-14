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
- Wave43 conservative boundary correction: March no-op; Apr-Jun old/new Top5 both87/160. NO_ADOPTION.

## Wave44b player-specific attack mode — COMPLETE / WEAK
- CI Run34809931603 success; Job103869078993; artifact10334735981; artifact SHA256 510da759ef69fbf34cdcbe233778a726873ebdb3a3902e98754a6631f4a20641.
- Historical joined rows22074. Feb train381; March OOS445 (MAKURI241 / MAKURI-SASHI204).
- March ML AUC0.5672 / logloss0.6841 / accuracy53.933%.
- Individual 1-year prior AUC0.5765 / logloss0.6920.
- Decision MODE_SIGNAL_WEAK. Individual tendency has some signal but is insufficient alone. Apr-Jun was NOT opened for this experiment.

## BEFORE-WORK PLAN — Wave44c contextual player attack mode — 2026-09-14
User approved combining individual tendency with current-race matchup/context.
1. Keep Wave44b leakage-safe player priors as the base signal.
2. Add only pre-deadline race-context features from the Wave21 source, prioritizing: boat3 vs boats1/2 ST ability/gaps, national/local performance gaps, motor performance gaps, and available motor/exhibition-style proxies that are genuinely pre-deadline. Do not use current-race result/kimarite or September outcomes.
3. Train on February and evaluate March OOS exactly once. Compare against Wave44b AUC0.5672 and individual-prior AUC0.5765; report AUC/logloss/accuracy and early/late March stability.
4. Contextual mode gate: require materially stronger March signal (target AUC >=0.60, preferably >=0.62) and no collapse in either March half before using mode probability for opponent ranking.
5. If mode gate passes, integrate probability softly into Wave36 opponent ranking rather than hard MAKURI/MAKURI-SASHI routing. Compare frozen Wave36 Top1/3/5/8/10, retained/lost/rescued, MRR, early/late March.
6. Ranking promotion gate: March Top5 >= Wave36 24/38 +1, lost existing hits <=2, and lift not isolated to one half. Only then freeze design and open Apr-Jun exactly once with exact JPY10,000 Dutch economics.
7. v288 remains untouched. Jul/Aug NON-PRISTINE diagnostic only. September remains unread.

## Exact restart point
- Implement Wave44c contextual player attack-mode classifier on the isolated research branch, beginning with a Wave21 column audit for safe ST/performance/motor matchup features.
