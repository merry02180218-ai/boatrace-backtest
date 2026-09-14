# CHAT HANDOFF — 3HEAD AUTO RESEARCH CURRENT

## Policy
- Active branch: research/3head-player-attack-mode. Do not rewrite main.
- v288 baseline fixed: 94R / 52 hits / ROI172.560638%.
- Pre-deadline only. Jul/Aug NON-PRISTINE. September unread.
- Hourly 3-head monitor remains disabled unless user asks.

## Benchmarks
- Wave36: Apr-Jun 391R / 87 hits / ROI114.913% / +583,090 yen.
- Wave36S-C: Apr-Jun 305R / 74 hits / ROI128.218% / +860,660 yen. RESEARCH_CANDIDATE.

## Closed research
- Wave39/40/41/42/43 rank replacements: NO_ADOPTION.
- Wave44 attack-mode route: best March AUC0.5895, below 0.60 gate. CLOSED.
- Wave45 confidence/margin: March 90R/24 Top5 hits; best confidence subset had zero lift. NO_ADOPTION.

## BEFORE-WORK PLAN — Wave46 second-place / third-place role factorization — 2026-09-14
1. New structural hypothesis: when boat3 wins, the attributes that make an opponent likely to finish second are not identical to those that make it likely to finish third. Model the two finishing roles separately rather than predicting the ordered pair directly.
2. Use only the frozen pre-race 63 static feature family and Feb training -> March OOS. No current-race result/kimarite/exhibition leakage.
3. Train two opponent-level classifiers on actual historical 3-head training rows: P(opponent=2nd | boat3 wins) and P(opponent=3rd | boat3 wins). Score each legal ordered pair (a,b) with a predeclared combination of second-role and third-role probabilities; compare against frozen Wave36 Top5 on March only.
4. Keep model family deliberately small and regularized. Test only a few predeclared pair-score forms (product, geometric mean equivalent ranking, and conservative blend with frozen Wave36 score if available). Do not search dozens of weights.
5. March promotion gate: at least +1 Top5 hit over Wave36 baseline on the same gated rows, lose no more than 2 old hits, and no early/late collapse. If gate fails, stop and do not open Apr-Jun.
6. If gate passes, open Apr-Jun once and evaluate exact JPY10,000 Dutch economics against Wave36/Wave36S-C. v288 untouched.
7. Jul/Aug remain NON-PRISTINE; September outcomes remain unread.

## Exact restart point
- Implement Wave46 role-factorized second/third opponent model using Wave21 source and frozen Wave36 gate p3>=0.365448, run March OOS CI, then decide whether Apr-Jun may be opened.
