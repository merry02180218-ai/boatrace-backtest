# v284 independent conditional THIRD regime split

- No v96 signal in model/features/restriction/fallback/order. v96 benchmark only after freeze.
- SECOND fixed PLAYER_START/L2=10. Conditional THIRD split by candidate SECOND side: INNER 1/2/3 vs OUTER 5/6.
- Regime family/L2 and pair policy selected on Feb-Mar only; Apr-Jun untouched.
- Sparse-regime fallback is independent GLOBAL COND_BASE/L2=.3, never v96.
- Jul/Aug excluded; September not read; no odds.

## Frozen regime choices

- INNER SECOND -> THIRD: **COND_COMPACT**, L2 **0.3**
- OUTER SECOND -> THIRD: **COND_COMPACT**, L2 **0.3**

### Regime grid

|regime|family|L2|R|T1|T2|objective|
|---|---|---:|---:|---:|---:|---:|
|INNER|COND_COMPACT|0.3|35|40.0%|71.4%|52.57|
|INNER|COND_BASE|0.3|35|42.9%|65.7%|52.00|
|INNER|COND_BASE|1|35|42.9%|65.7%|52.00|
|INNER|COND_DIFF|0.3|35|42.9%|65.7%|52.00|
|INNER|COND_DIFF|1|35|42.9%|65.7%|52.00|
|INNER|COND_COMPACT|1|35|40.0%|68.6%|51.43|
|INNER|COND_DIFF|3|35|37.1%|65.7%|48.57|
|INNER|COND_BASE|3|35|37.1%|62.9%|47.43|
|INNER|COND_DIFF|10|35|37.1%|62.9%|47.43|
|INNER|COND_COMPACT|3|35|34.3%|65.7%|46.86|
|INNER|COND_BASE|10|35|34.3%|62.9%|45.71|
|INNER|COND_COMPACT|10|35|31.4%|62.9%|44.00|
|OUTER|COND_COMPACT|0.3|19|36.8%|63.2%|47.37|
|OUTER|COND_BASE|1|19|31.6%|63.2%|44.21|
|OUTER|COND_COMPACT|1|19|31.6%|63.2%|44.21|
|OUTER|COND_DIFF|1|19|31.6%|63.2%|44.21|
|OUTER|COND_BASE|3|19|26.3%|68.4%|43.16|
|OUTER|COND_COMPACT|3|19|26.3%|68.4%|43.16|
|OUTER|COND_COMPACT|10|19|26.3%|68.4%|43.16|
|OUTER|COND_BASE|0.3|19|31.6%|57.9%|42.11|
|OUTER|COND_DIFF|0.3|19|31.6%|57.9%|42.11|
|OUTER|COND_DIFF|10|19|21.1%|73.7%|42.11|
|OUTER|COND_DIFF|3|19|26.3%|63.2%|41.05|
|OUTER|COND_BASE|10|19|21.1%|63.2%|37.89|

## Frozen pair-order policy (Feb-Mar)

- mode: **TOP2XTOP2**
- alpha2: **0.60**
- tune T2/T4/T6/T10: **29.6% / 42.6% / 53.7% / 72.2%**

## Apr-Jun holdout-like result

|scope|R|2nd T1|T2|cond3 T1|T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|ALL 4-head wins|87|41.4%|60.9%|36.8%|63.2%|20.7%|32.2%|44.8%|58.6%|73.6%|28.7%|44.8%|55.2%|75.9%|
|Frozen S+A head-wins|40|32.5%|55.0%|37.5%|62.5%|17.5%|22.5%|35.0%|55.0%|75.0%|35.0%|45.0%|57.5%|77.5%|

## Apr-Jun conditional THIRD by actual SECOND regime

|regime|R|T1|T2|
|---|---:|---:|---:|
|INNER|61|37.7%|60.7%|
|OUTER|26|34.6%|69.2%|

## S+A monthly

|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-04|11|9.1%|27.3%|54.5%|72.7%|27.3%|36.4%|36.4%|54.5%|
|2026-05|15|33.3%|46.7%|53.3%|80.0%|46.7%|53.3%|66.7%|86.7%|
|2026-06|14|21.4%|28.6%|57.1%|71.4%|28.6%|42.9%|64.3%|85.7%|

## Decision
- Promote v284 only if S+A small-N coverage improves and monthly deterioration is reduced.
- Otherwise retain v282/v283 as the independent baseline and next add more data or a pre-Apr-frozen attack-strength regime rather than tuning on Apr-Jun outcomes.
