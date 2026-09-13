# v319 direct ordered-pair model

- Fixed v308 cohort: **345 races / 290 boat-1 wins**.
- v313 cache only; no `meet_*`; no future backfill; month M trains only before M.
- Directly ranks all 20 ordered `(second,third)` pairs; top 3 pairs are the exact-3-ticket candidate set.
- Factorized v317 SECOND + v318 THIRD reference exact3: **137/345=39.71%**.

## Result
- Best **ALL_P0.3**: pair TOP1 **21.38%**, TOP2 **34.14%**, TOP3 **46.21%**, TOP5 **60.69%**; exact3 **134/345=38.84%**; worst-month TOP3 **36.00%**.

## Monthly best
|month|R|PAIR TOP1|TOP2|TOP3|TOP5|
|---|---:|---:|---:|---:|---:|
|2026-02|51|27.45%|37.25%|45.10%|54.90%|
|2026-03|15|13.33%|26.67%|46.67%|60.00%|
|2026-04|48|20.83%|39.58%|58.33%|68.75%|
|2026-05|101|21.78%|33.66%|48.51%|61.39%|
|2026-06|75|18.67%|30.67%|36.00%|58.67%|

## Automatic next decision
- Compare direct ordered-pair against factorized 137/345 reference with monthly stability.
- If ordered-pair is not materially better, retain the stronger ranking reference and move to exact-3-ticket policy optimization rather than further micro-tuning.
- Suspicious large gain requires leakage/causal audit before acceptance.
