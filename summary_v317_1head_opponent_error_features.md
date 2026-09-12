# v317 error-driven causal SECOND feature engineering

- Fixed v308 cohort: **345 races / 290 boat-1 wins**; IDs unchanged.
- v313 cache only; no `meet_*`; no future backfill; month M trains only before M.
- Derived interactions use only already-audited PRE/prior features and candidate boat/route identity.
- START family remains dropped; THIRD frozen at v300 conditional L2=.1.
- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.

## Development result
- DROP_START base TOP2 72.76%, outer 26.44%, exact3 136/345=39.42%, worst month 60.00%.
- Best **OUTER_L2_1** TOP2 **72.76%**, outer **28.74%**, exact3 **137/345=39.71%**, worst month **66.67%**.

## Best by actual SECOND
|boat|R|TOP1|TOP2|TOP3|exact3|
|---:|---:|---:|---:|---:|---:|
|2|114|72.81%|97.37%|99.12%|71.93%|
|3|89|43.82%|84.27%|97.75%|48.31%|
|4|42|16.67%|45.24%|85.71%|19.05%|
|5|32|0.00%|18.75%|56.25%|12.50%|
|6|13|0.00%|0.00%|15.38%|0.00%|

## Monthly
|month|R|head|TOP1|TOP2|TOP3|exact3|
|---|---:|---:|---:|---:|---:|---:|
|2026-02|63|51|39.22%|70.59%|86.27%|34.92%|
|2026-03|16|15|20.00%|66.67%|100.00%|43.75%|
|2026-04|53|48|45.83%|79.17%|95.83%|54.72%|
|2026-05|121|101|51.49%|75.25%|89.11%|38.84%|
|2026-06|92|75|42.67%|68.00%|81.33%|34.78%|

## Automatic decision rule
- If v317 remains weak/unstable, SECOND model classes are considered saturated enough to rebuild conditional THIRD next.
- If v317 materially improves SECOND without collapsing inner boats/month stability, preserve the feature set and then rebuild THIRD.
- Any suspicious large gain requires leakage/causal audit before acceptance.
