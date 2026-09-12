# v310 opponent SECOND with causal 3/4-head risk

- Frozen race set: v308 345 races; head model is unchanged.
- p3: monthly walk-forward v243-family head probability using only earlier data for each month.
- p4: v250 PRE monthly walk-forward probability; current-race exhibition is not used.
- Sparse cross-pipeline p3/p4 coverage is represented as zero sentinel + explicit availability flags; no future backfill.
- THIRD remains v300 conditional THIRD L2=.1.

## Config comparison
|config|L2|second TOP1|TOP2|TOP3|exact3|dTOP2 pp|dExact3 pp|
|---|---:|---:|---:|---:|---:|---:|---:|
|HEADRISK_L2_1|1|44.14%|72.07%|86.55%|38.55%|+0.34|+0.29|
|HEADRISK_L2_3|3|44.48%|72.07%|86.90%|38.55%|+0.34|+0.29|
|HEADRISK_L2_30|30|44.48%|72.07%|87.24%|38.26%|+0.34|+0.00|
|BASE|3|43.79%|71.72%|87.93%|38.26%|+0.00|+0.00|
|HEADRISK_L2_10|10|44.48%|71.72%|86.90%|38.26%|+0.00|+0.00|

## Best: HEADRISK_L2_3
- SECOND TOP2: **72.07%** (baseline 71.72%)
- exact 3-ticket: **133/345 = 38.55%** (baseline 38.26%)

## Best by actual SECOND
|boat|R|TOP1|TOP2|TOP3|exact3|
|---:|---:|---:|---:|---:|---:|
|2|114|71.93%|98.25%|100.00%|70.18%|
|3|89|44.94%|84.27%|96.63%|47.19%|
|4|42|16.67%|38.10%|83.33%|16.67%|
|5|32|0.00%|18.75%|50.00%|12.50%|
|6|13|0.00%|0.00%|7.69%|0.00%|

## Monthly
|month|R|head wins|SECOND TOP2|exact3|
|---|---:|---:|---:|---:|
|2026-02|63|51|72.55%|36.51%|
|2026-03|16|15|60.00%|43.75%|
|2026-04|53|48|79.17%|52.83%|
|2026-05|121|101|75.25%|38.02%|
|2026-06|92|75|65.33%|31.52%|
