# v321 Jul/Aug 2026 NON-PRISTINE validation

- **Reference only; NOT pristine and NOT eligible for promotion.**
- Frozen v308 head gate: development-only q=.98 cutoff **p_head>=0.80734056**, opponent mass >= 0.375.
- Jul/Aug opponent mass is reconstructed with the frozen v308 BASE opponent model, month M trained only on < M.
- Frozen opponent ranking: v317 SECOND + v318 DROP_START THIRD.
- Frozen ticket policy: **HYBRID alpha=0.70**, exactly 3 tickets.
- `meet_*` forbidden; missing p3/p4 never future-backfilled; September outcomes untouched.

## Result
- Jul+Aug: R **55**, head **45/55=81.82%**, exact3 **21/55=38.18%**.

## Monthly
|month|R|head|head rate|exact3|exact3 rate|
|---|---:|---:|---:|---:|---:|
|2026-07|13|11|84.62%|3|23.08%|
|2026-08|42|34|80.95%|18|42.86%|

## Interpretation
- Contamination-aware stress check only; do not tune or promote from Jul/Aug.
