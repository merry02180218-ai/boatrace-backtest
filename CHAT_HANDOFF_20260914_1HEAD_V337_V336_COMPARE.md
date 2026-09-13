# CHAT_HANDOFF_20260914_1HEAD_V337_V336_COMPARE

This continuation handoff supplements `CHAT_HANDOFF_20260913_1HEAD_PRODUCTION_CONTINUE.md` because the previous in-place append attempt was blocked by the tool safety layer. Latest GitHub still wins.

## PRE-WORK — written before comparison
Current frozen production is unchanged: v332 ATTACK_ENV_SOFT env_w=.1 q=.65 with v308 head cutoff 0.8073405637. September outcomes remain UNREAD.

Completed v337 repair/run:
- repair commit `fc5f4ad7523dc30abf879db7b98ac9c2d759e292`
- Run `34782769446` SUCCESS
- final audit Job `103794355983` SUCCESS
- Artifact `10325922020`
- anchor reproduced exactly 96 PASS / 83 head / 45 exact3
- Waku10 dependency in v308/v337 PRE path: NONE

Exact work now:
1. Compare v336 exhibition-q relaxation versus v337 PRE-head-cutoff relaxation over Feb-Aug only.
2. Focus on v337 cutoff .78 and compare against nearest v336 volumes.
3. Compare PASS/month, head rate, exact3 rate, incremental/newly admitted quality, and month-by-month stability.
4. Quantify overlap/unique PASS sets if row-level artifacts permit.
5. Flag non-monotonic or month-concentrated behavior; do not adopt production in this work unit.
6. Keep September outcomes UNREAD.
7. After completion, append actual comparison results, conclusion, and exact next resume point to this file.

## WORK RESULT — v337 PRE relaxation is the stronger expansion route so far
Sources:
- v336 Run `34777511185`, Job `103778214979`, Artifact `10323958215`
- v337 Run `34782769446`, Job `103794355983`, Artifact `10325922020`
- September outcomes remained unread.

### Aggregate comparison
Frozen anchor: 96 PASS / 13.7 per month / head 86.46% / exact3 46.88%.

v336 exhibition-q relaxation:
- q=.50: 138 PASS / 19.7 per month / head 86.96% / exact3 44.93%
- q=.40: 164 / 23.4 / head 85.98% / exact3 43.29%
- q=.35: 176 / 25.1 / head 84.66% / exact3 43.18%
- q=.30: 192 / 27.4 / head 85.94% / exact3 41.15%
- q=.25: 207 / 29.6 / head 85.99% / exact3 39.61%

v337 PRE-head-cutoff relaxation with exhibition q fixed at .65:
- cutoff .79: 187 PASS / 26.7 per month / head 85.56% / exact3 42.25%
- cutoff .78: 276 / 39.4 / head 87.32% / exact3 43.12%
- cutoff .77: 363 / 51.9 / head 84.30% / exact3 41.87%

Nearest-volume apples-to-apples:
- v337 .79 = 187 PASS, head 85.56%, exact3 42.25%
- v336 q=.30 = 192 PASS, head 85.94%, exact3 41.15%
These are essentially tied on head rate; v337 .79 has +1.10pp exact3, v336 q=.30 has +0.38pp head.

But v337 .78 is materially stronger: 276 PASS, head 87.32%, exact3 43.12%. It produces far more volume than any tested v336 setting while exceeding all v336 q<=.40 settings on head rate and retaining exact3 around the q=.35-.40 level.

### Incremental/newly admitted quality vs frozen anchor
v336 cumulative added races versus q=.65 anchor:
- q=.50: +42R, head 88.10%, exact3 40.48%
- q=.40: +68R, head 85.29%, exact3 38.24%
- q=.30: +96R, head 85.42%, exact3 35.42%
- q=.25: +111R, head 85.59%, exact3 33.33%

v337 .78 added races versus anchor:
- +180R, head 87.78%, exact3 41.11%
This is currently the best observed combination of expansion size and added-race quality.

### Month-by-month stability
v337 .78 monthly head rates:
- Feb 86.96%
- Mar 90.63%
- Apr 85.42%
- May 84.38%
- Jun 88.68%
- Jul 90.48%
- Aug 88.57%
Unweighted monthly head-rate std dev ≈2.22pp; range 84.38%-90.63%.
Monthly exact3 std dev ≈6.41pp; range 32.81%-50.00%.

For comparison, v336 q=.30 monthly head-rate std dev ≈7.53pp and q=.25 ≈6.89pp. Their exact3 monthly std devs are ≈11.30pp and ≈9.59pp respectively.
So v337 .78 is not being carried by one or two months; head performance is notably more stable across Feb-Aug than the aggressive v336 exhibition relaxation settings.

### Important caution
The v337 grid is non-monotonic: .79 -> .78 improves aggregate head rate, then .77 falls to 84.30%. Therefore .78 should be treated as a candidate sweet spot, not evidence that lowering the cutoff always helps.

### Overlap limitation
The v336 artifact contains summary/monthly/band outputs but no row-level PASS race identity file, so exact v336-v337 overlap/unique-race decomposition cannot be recovered from the artifact alone without a dedicated reconstruction run. Do not infer overlap percentages from aggregate counts.

## Conclusion
Research preference: v337 cutoff .78 is the leading volume-expansion candidate. It expands from 96 to 276 PASS while preserving/improving head quality and maintaining better exact3 than aggressive v336 q relaxation. Do NOT adopt to production yet.

Exact next resume point:
1. Build a dedicated v338 validation that freezes candidate settings before execution: anchor, v337 .79, v337 .78, and a small neighborhood around .78 such as .785/.7825/.7775 if causally reconstructable.
2. Evaluate month stability, incremental bands, venue/date concentration, and bootstrap/binomial uncertainty using Feb-Aug only.
3. Reconstruct row-level v336 comparator identities only if needed for direct overlap analysis.
4. Keep September outcomes unread until a single challenger is frozen for final untouched evaluation.
5. Do not change production v332/current cutoff before that validation.