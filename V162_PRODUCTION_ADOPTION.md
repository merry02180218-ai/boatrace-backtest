# v162 production adoption

Adopted: 2026-09-07 JST

## User decision

v162 is formally adopted as the production opponent-ranking model for the 1-head strategy.

## Production pipeline

1. PRE selection remains unchanged.
2. Current direct/exhibition inputs are applied to v109.
3. BUY only when v109 is S: p109 >= 0.72.
4. For a BUY race, rank all 20 ordered `1-s-t` pairs with v162 direct-pair model (lambda = 1.00).
5. Present the top 7 pairs in rank order. The user decides actual stake/ticket count.
6. Freeze tickets before reading result/payout.

## Replaced component

- Previous production opponent model: v110 role-factorized ranking, lambda 0.50.
- New production opponent model: v162 direct ordered-pair ranking, lambda 1.00.
- v109 head judgment is unchanged.

## Adoption evidence

Jun-Aug monthly walk-forward retrospective comparison, S / top 7:

- June conditional coverage: v110 68.44% -> v162 73.38% (+4.94pt)
- July conditional coverage: v110 65.44% -> v162 68.68% (+3.24pt)
- August conditional coverage: v110 65.61% -> v162 67.84% (+2.22pt)
- Jun-Aug aggregate conditional coverage: 66.43% -> 69.86% (+3.43pt)
- Jun-Aug S/top7 trifecta hit rate: 50.97% -> 53.60% (+2.63pt)

The user explicitly accepted the model for production based on the repeated monthly walk-forward improvement.

## Current canonical 1-head operation

**Legacy PRE -> v109 S-only head decision -> v162 top-7 opponent tickets**

v110 remains available as the previous/baseline model but is no longer the production opponent selector.

## No-leak rule

Never use the current-race result, payout, post-race actual course, final/deadline odds, or any other post-freeze information to select or reorder tickets. Result/payout may be read only after the ticket list is frozen.
