# v163 / v162 prospective shadow freeze

Frozen: 2026-09-07 09:49 JST

## Purpose

Prospectively compare the current production opponent ranking **v110** against the new direct-pair shadow **v162** on future live 1-head races without using race results or payout before ticket freeze.

## Frozen models

- Head decision: **v109** unchanged.
- BUY rule: **S only, p109 >= 0.72**.
- Production opponent ranking: **v110**, lambda 0.50, fixed top 7.
- Shadow opponent ranking: **v162**, direct ordered-pair model, lambda 1.00, fixed top 7.
- v162 source file at freeze: `analyze_v162_1head_pair_direct.py`.
- v162 retrospective summary at freeze: `summary_v162_1head_pair_direct.md`.

## Prospective start rule

Only races whose ticket ranking is frozen **after this freeze timestamp and before the race result is known** count as prospective v163 observations.

Do not backfill 2026-09-01 through the freeze time as prospective. Those dates may be used only as retrospective diagnostics if explicitly labeled as such.

## Live scoring order

For each future race that passes the normal 1-head PRE selection and current direct-data process:

1. Freeze current-race direct inputs.
2. Compute v109 p109.
3. If p109 < 0.72: SKIP, and do not count as a v163 S-ticket observation.
4. If p109 >= 0.72: freeze **both** ticket lists before result:
   - v110 top 7
   - v162 top 7
5. Save the frozen timestamp, race key, p109, v110 top7, v162 top7.
6. Only after both lists are frozen may result/payout be read and settlement fields be added.

## Primary adoption metrics

Priority order:

1. S / 7-ticket conditional coverage given 1-head win.
2. S / 7-ticket trifecta hit rate over all S races.
3. Monthly / rolling stability.
4. Equal-stake ROI as settlement-only information.

Retrospective reference from v162 (Jun-Aug diagnostic only):

- v110 S / 7 coverage: 66.43%
- v162 S / 7 coverage: 69.86% (+3.43pt)
- v110 S / 7 trifecta hit: 50.97%
- v162 S / 7 trifecta hit: 53.60%

## Adoption rule

Do **not** replace v110 immediately.

A production switch requires prospective evidence after this freeze. Minimum recommended checkpoint:

- at least 100 settled S observations, and
- v162 S/7 coverage not worse than v110, and
- no material degradation in trifecta hit rate, and
- direction not driven by a single venue/day cluster.

Until then:

- **v110 = production**
- **v162 = shadow**

## No-leak rule

Never use current-race result, payout, post-race actual course, or final/deadline odds to choose or reorder tickets. Current-race final odds may be attached only after both ticket lists are frozen, for settlement/ROI analysis.
