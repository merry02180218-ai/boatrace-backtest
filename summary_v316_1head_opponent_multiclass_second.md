# v316 multiclass SECOND autoresearch

- Fixed v308 cohort: **345 races / 290 boat-1 wins**; IDs unchanged.
- Uses v313 reusable causal cache; no `meet_*`; no future backfill.
- Race-level multinomial SECOND classifier with outer-route sample weighting; THIRD frozen at v300 conditional L2=.1.
- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.

## Development result
- DROP_START base TOP2 72.41%, outer 26.44%, exact3 136/345=39.42%, worst month 60.00%.
- Best **MC_ow1.0_m0.50** TOP2 **72.76%**, outer **27.59%**, exact3 **136/345=39.42%**, worst month **66.67%**.

## Best by actual SECOND
|boat|R|TOP1|TOP2|TOP3|exact3|
|---:|---:|---:|---:|---:|---:|
|2|114|77.19%|97.37%|100.00%|72.81%|
|3|89|35.96%|85.39%|97.75%|47.19%|
|4|42|14.29%|42.86%|88.10%|16.67%|
|5|32|0.00%|18.75%|46.88%|12.50%|
|6|13|0.00%|0.00%|23.08%|0.00%|

## Monthly
|month|R|head|TOP1|TOP2|TOP3|exact3|
|---|---:|---:|---:|---:|---:|---:|
|2026-02|63|51|39.22%|72.55%|88.24%|34.92%|
|2026-03|16|15|20.00%|66.67%|93.33%|43.75%|
|2026-04|53|48|47.92%|79.17%|95.83%|52.83%|
|2026-05|121|101|48.51%|75.25%|88.12%|39.67%|
|2026-06|92|75|41.33%|66.67%|82.67%|33.70%|

## Automatic decision rule
- If multiclass route balancing remains weak/unstable, proceed automatically to error-driven causal PRE/prior feature engineering or conditional THIRD rebuild depending on the latest failure decomposition.
- Any suspicious large gain requires leakage/causal audit before acceptance.
