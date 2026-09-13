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