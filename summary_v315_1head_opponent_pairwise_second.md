# v315 pairwise SECOND autoresearch

- Fixed v308 cohort: **345 races / 290 boat-1 wins**; IDs unchanged.
- Uses v313 reusable causal cache; no `meet_*`; no future backfill.
- Pairwise candidate-vs-candidate logistic ranking with outer-winner weighting.
- THIRD frozen at v300 conditional L2=.1 for SECOND attribution.
- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.

## Development result
- DROP_START base TOP2 72.41%, outer 26.44%, exact3 136/345=39.42%, worst month 60.00%.
- Best **PAIR_ow1.0_m1.00** TOP2 **72.76%**, outer **27.59%**, exact3 **133/345=38.55%**, worst month **60.00%**.

## Best by actual SECOND
|boat|R|TOP1|TOP2|TOP3|exact3|
|---:|---:|---:|---:|---:|---:|
|2|114|69.30%|99.12%|99.12%|67.54%|
|3|89|47.19%|83.15%|97.75%|48.31%|
|4|42|16.67%|40.48%|80.95%|19.05%|
|5|32|0.00%|18.75%|46.88%|12.50%|
|6|13|0.00%|7.69%|15.38%|7.69%|

## Monthly
|month|R|head|TOP1|TOP2|TOP3|exact3|
|---|---:|---:|---:|---:|---:|---:|
|2026-02|63|51|41.18%|72.55%|86.27%|33.33%|
|2026-03|16|15|20.00%|60.00%|86.67%|43.75%|
|2026-04|53|48|47.92%|79.17%|91.67%|54.72%|
|2026-05|121|101|48.51%|76.24%|90.10%|38.84%|
|2026-06|92|75|42.67%|66.67%|78.67%|31.52%|

## Automatic decision rule
- If pairwise gain is weak/flat (roughly <= +0.5pp TOP2 with no robust outer improvement), do not micro-tune endlessly; move to a materially different multiclass/listwise formulation with route/class balancing.
- Any suspicious large gain requires leakage/causal audit before acceptance.
