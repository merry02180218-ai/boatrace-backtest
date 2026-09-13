# v320 exact-3-ticket policy optimization

- Fixed v308 cohort: **345 races / 290 boat-1 wins**; boat-1 losses remain misses.
- Ranking reference frozen to factorized v317 SECOND + v318 DROPSTART_T0.1 THIRD because v319 direct pair was weaker.
- Exactly 3 tickets on every race; no race filtering or denominator shrinkage.
- v313 cache only; no `meet_*`; no future backfill; month M trains only before M.
- Feb-Jun development only; Jul/Aug NON-PRISTINE; September outcomes unread.

## Baseline
- TOP2XTOP2 alpha=.60: **137/345=39.71%**, worst month **33.33%**.

## Best
- **HYBRID alpha=0.70**: **139/345=40.29%**, delta **+0.58pt**, worst month **34.78%**.

## Monthly best
|month|R|hits|hit rate|
|---|---:|---:|---:|
|2026-02|63|22|34.92%|
|2026-03|16|8|50.00%|
|2026-04|53|28|52.83%|
|2026-05|121|49|40.50%|
|2026-06|92|32|34.78%|

## Automatic next decision
- If a policy materially improves exact3 with acceptable monthly stability, freeze it as the development winner; reused Feb-Jun evidence is not prospective validation.
- If no material stable gain, retain the factorized TOP2XTOP2 alpha=.60 baseline and stop micro-tuning ticket order.
- Any suspiciously large gain requires immediate leakage/causal audit.
