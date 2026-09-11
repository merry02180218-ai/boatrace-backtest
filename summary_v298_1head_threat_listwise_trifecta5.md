# v298 clean 1HEAD threat + v283-style listwise trifecta <=5

- Development research only; production unchanged.
- Jul/Aug 2026 excluded; September outcomes unread.
- PRE/history features are frozen before exact settlement; meeting self-slot leakage features stay forbidden.
- Every final-selected settled race is in the exact denominator. Boat-1 losses are misses.
- SECOND = listwise PLAYER-style candidate ranker L2=10; THIRD = conditional four-way L2=0.3.
- Pair policy = TOP2XTOP2 prefix + alpha2=0.60 joint blend (frozen from v283 semantics).
- candidate symmetric suffixes=12; explicit head-threat features=86; exact settlement coverage=99.95%.

## Fold audit
|month|train|test|head f|guard f|second f|third f|second train races|third train races|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-02|13428|4071|240|216|78|193|13428|7450|
|2026-03|17499|4565|240|216|78|193|17499|9708|
|2026-04|22064|4204|240|216|78|193|22064|12218|
|2026-05|26268|4744|240|216|78|193|26268|14538|
|2026-06|31012|4450|240|216|78|193|31012|17141|

## Best stable development zones
|rule|conf|R|head|5pt exact|worst head|worst 5pt|min month R|
|---|---:|---:|---:|---:|---:|---:|---:|
|HGB_q0.950|0.45|204|81.37%|58.82%|78.38%|50.00%|18|
|HGB_q0.975_AND_LR_q0.900|0.00|321|84.11%|47.04%|73.33%|20.00%|14|
|HGB_q0.975|0.00|341|83.58%|47.21%|75.00%|25.00%|14|
|HGB_q0.950|0.00|841|81.69%|48.63%|79.40%|43.78%|66|
|HGB_q0.975_AND_LR_q0.975|0.00|165|85.45%|44.24%|72.73%|18.18%|11|
|HGB_q0.975_AND_LR_q0.950|0.00|252|84.52%|44.84%|78.57%|21.43%|11|

## <=5-point ceiling for best joint rule
|points|R|hits|hit rate|Wilson low|
|---:|---:|---:|---:|---:|
|1|204|45|22.06%|16.91%|
|2|204|82|40.20%|33.71%|
|3|204|102|50.00%|43.20%|
|4|204|108|52.94%|46.10%|
|5|204|120|58.82%|51.97%|

## Target decision
- **No stable development rule simultaneously reaches head >=90% and exact <=5 points >=80%. Do not promote v298.**
