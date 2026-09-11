# v299 1HEAD exact-trifecta 3-ticket policy search

- Development research only; production unchanged.
- Jul/Aug excluded upstream; September outcomes unread.
- Race selection is frozen to v298 HGB q0.95 + baseline alpha=.60 TOP2XTOP2 top5 mass >= .45.
- Every candidate policy is scored on the identical selected denominator; boat-1 losses remain misses.
- Fixed selected races: **204**; head rate: **81.37%**.

## Baseline
|strategy|alpha|R|3pt hits|3pt hit rate|worst month|
|---|---:|---:|---:|---:|---:|
|TOP2XTOP2|0.60|204|102|50.00%|44.44%|

## Best 3-ticket policies on the same races
|strategy|alpha|R|hits|hit rate|delta|worst month|
|---|---:|---:|---:|---:|---:|---:|
|TOP2XTOP2|0.20|204|102|50.00%|+0.00pt|44.44%|
|TOP2XTOP2|0.30|204|102|50.00%|+0.00pt|44.44%|
|TOP2XTOP2|0.40|204|102|50.00%|+0.00pt|44.44%|
|TOP2XTOP2|0.50|204|102|50.00%|+0.00pt|44.44%|
|HYBRID|0.50|204|102|50.00%|+0.00pt|44.44%|
|TOP2XTOP2|0.60|204|102|50.00%|+0.00pt|44.44%|
|HYBRID|0.60|204|102|50.00%|+0.00pt|44.44%|
|TOP2XTOP2|0.70|204|102|50.00%|+0.00pt|44.44%|
|HYBRID|0.70|204|102|50.00%|+0.00pt|44.44%|
|TOP2XTOP2|0.80|204|102|50.00%|+0.00pt|44.44%|
|HYBRID|0.80|204|102|50.00%|+0.00pt|44.44%|
|JOINT|0.40|204|101|49.51%|-0.49pt|44.44%|
|HYBRID|0.40|204|100|49.02%|-0.98pt|44.44%|
|JOINT|0.60|204|98|48.04%|-1.96pt|38.89%|
|JOINT|0.50|204|97|47.55%|-2.45pt|44.44%|

## Monthly best-policy audit
|month|R|hits|hit rate|
|---|---:|---:|---:|
|2026-02|18|8|44.44%|
|2026-03|29|16|55.17%|
|2026-04|37|19|51.35%|
|2026-05|69|33|47.83%|
|2026-06|51|26|50.98%|

## Decision
- No policy beats the frozen v298 3-point baseline; retain baseline and change model features rather than ticket ordering.
