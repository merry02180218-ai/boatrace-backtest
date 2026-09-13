# v318 conditional THIRD rebuild

- Fixed v308 cohort: **345 races / 290 boat-1 wins**.
- v313 cache only; no `meet_*`; no future backfill; month M trains only before M.
- SECOND fixed to v317 OUTER_L2_1 so this experiment attributes changes to THIRD only.
- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.

## Result
- Baseline THIRD TOP2 **72.76%**, exact3 **137/345=39.71%**.
- Best **DROPSTART_T0.1** THIRD TOP2 **72.76%**, TOP1 **40.34%**, TOP3 **92.07%**, exact3 **137/345=39.71%**, worst-month THIRD TOP2 **68.32%**.

## Monthly best
|month|R|THIRD TOP1|TOP2|TOP3|
|---|---:|---:|---:|---:|
|2026-02|51|39.22%|74.51%|92.16%|
|2026-03|15|40.00%|73.33%|86.67%|
|2026-04|48|50.00%|83.33%|95.83%|
|2026-05|101|36.63%|68.32%|89.11%|
|2026-06|75|40.00%|70.67%|94.67%|

## Automatic next decision
- If THIRD gain is weak/unstable, move to direct 20 ordered `(second,third)` pair modeling.
- If THIRD materially improves, preserve it and then compare factorized vs direct ordered-pair before ticket optimization.
- Any suspicious large gain triggers leakage/causal audit.
