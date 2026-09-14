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

## Wave47 head-condition zoning — COMPLETE / NO_ADOPTION
- March baseline:90R /38 head hits /42.222%; Top5 24 /26.667%.
- March winner: motor family top60% =>54R / head48.148% (+5.926pt), early46.875%, late50.000%.
- Apr-Jun fixed holdout:174R /36 hits / ROI95.511% / -78,100 yen.
- Monthly: Apr49R/12/ROI111.384%; May63R/15/124.390%; Jun62R/9/53.623%.
- Decision NO_ADOPTION. Do not retune Wave47 on Apr-Jun.

## BEFORE-WORK PLAN — Wave48 June failure diagnostic — 2026-09-14
1. User hypothesis: Wave47 could become useful if the June collapse is understood and a live-identifiable failure regime exists.
2. This is DIAGNOSTIC ONLY. Apr-Jun outcomes are already opened/contaminated for Wave47; do not promote or retune a production rule from this audit.
3. Reproduce the frozen Wave47 Apr-Jun selections and decompose each month into: boat3 head rate, conditional frozen-Wave36 Top5 capture given boat3 head, ticket hit rate, average/median winning odds for hits/misses where available, and exact payout contribution.
4. Compare pre-race distributions across Apr/May/Jun for Wave36 p3, frozen Wave47 motor-zone score, boat3-vs-1/2/4 motor gaps, ST gaps, national/local win-rate gaps, and venue/race-number composition. Outcome labels may be used only to describe failure, never to search/choose a new cutoff.
5. Determine whether June loss is primarily (A) head-selection failure, (B) opponent Top5 failure conditional on head, (C) payout/odds economics, or a mixture.
6. Report candidate pre-race drift indicators only if they are visible without outcomes and show a clear June distribution shift. Mark them HYPOTHESIS_FOR_FUTURE_PRISTINE_TEST, not adoption rules.
7. No Jul/Aug validation because NON-PRISTINE. September outcomes remain unread. v288 untouched.

## Exact restart point
- Implement Wave48 diagnostic using the already-open Apr-Jun Wave47 holdout rows, run CI, classify the June failure mechanism, and record future-test hypotheses without retuning Wave47.
