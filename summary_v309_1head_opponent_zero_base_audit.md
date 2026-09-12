# v309 opponent zero-base audit

- Frozen head model/race set: v308 selected 345 races. No race-selection retuning.
- Current opponent benchmark: v300 augmented SECOND L2=3 / conditional THIRD L2=.1 / TOP2XTOP2 alpha=.60.
- Boat-1 losses remain exact-ticket misses.

## Overall decomposition
- R=**345**; head wins **290/345 = 84.06%**; exact 3-ticket **132/345 = 38.26%**
- On the 290 head-win races, actual SECOND rank: TOP1 **43.79%**, TOP2 **71.72%**, TOP3 **87.93%**
- Given the actual SECOND, actual THIRD rank: TOP1 **41.38%**, TOP2 **72.76%**, TOP3 **91.03%**

## Error classes on head-win races
|class|R|share|
|---|---:|---:|
|EXACT3_HIT|132|45.52%|
|SECOND_OUTSIDE_TOP2|82|28.28%|
|THIRD_OUTSIDE_TOP2_GIVEN_ACTUAL2|51|17.59%|
|COMBINATION_POLICY_OR_ORDER|25|8.62%|

## Monthly diagnostic
|month|R|head|exact3|second TOP2|third TOP2 given actual second|
|---|---:|---:|---:|---:|---:|
|2026-02|63|51|36.51%|72.55%|76.47%|
|2026-03|16|15|43.75%|66.67%|66.67%|
|2026-04|53|48|52.83%|79.17%|85.42%|
|2026-05|121|101|38.02%|74.26%|67.33%|
|2026-06|92|75|30.43%|64.00%|70.67%|

## By actual SECOND
|actual second|R|second TOP1|second TOP2|third TOP2|exact3|
|---:|---:|---:|---:|---:|---:|
|2|114|67.54%|98.25%|78.95%|68.42%|
|3|89|47.19%|84.27%|75.28%|48.31%|
|4|42|16.67%|35.71%|64.29%|16.67%|
|5|32|3.12%|18.75%|59.38%|12.50%|
|6|13|0.00%|0.00%|61.54%|0.00%|
