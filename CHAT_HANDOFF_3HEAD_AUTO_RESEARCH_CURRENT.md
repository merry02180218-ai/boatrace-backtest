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
- Wave45 confidence/margin: zero lift. NO_ADOPTION.
- Wave46 second/third role factorization: March 16/90 role, 21/90 blend vs Wave36 24/90. NO_ADOPTION.

## BEFORE-WORK PLAN — Wave47 head-condition zoning — 2026-09-14
1. Stop modifying opponent ranking. Freeze Wave36 opponent Top5 and focus on whether a race should be selected at all.
2. Structural hypothesis: Wave36's 3-head signal should be stronger in specific matchup zones defined by boat3 relative to boats1/2/4: b3-vs-b2 average-ST gap and wall weakness, b3-vs-b1 escape resistance, b3-vs-b4 outside attack pressure, and motor-performance gaps.
3. Use only pre-race card/static columns. Feb is training/reference; March is the only OOS evaluation. Apr-Jun outcomes stay unopened until a March zoning gate passes.
4. Predeclare a small interpretable feature set and regularized head classifier / score adjustment; no broad feature fishing. Compare frozen Wave36 p3>=0.365448 against sparse zone variants on March.
5. Primary March gate is selection quality, not opponent-rank replacement: retain a meaningful sample (target >=45 races), improve 3-head strike rate by at least +5 percentage points relative to the same Wave36 March candidate universe, and avoid early/late collapse. Also report Top5 ticket hit rate on selected races using frozen Wave36 ranking.
6. If no variant passes, close Wave47 without Apr-Jun. If one passes, freeze the rule and open Apr-Jun once for exact JPY10,000 Dutch economics versus Wave36 and Wave36S-C.
7. v288 untouched; Jul/Aug NON-PRISTINE; September outcomes unread.

## Exact restart point
- Implement Wave47 sparse head-condition zoning from Wave21 source, Feb->March OOS only, preserving frozen Wave36 opponent ranking and cutoff reference.
