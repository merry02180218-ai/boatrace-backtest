# v297 clean 1HEAD loss-guard + trifecta <=5 research

- **Development research only. v296 production state is unchanged.**
- Jul/Aug 2026 excluded. September outcomes unread.
- Feb-Jun expanding walk-forward is reused development evidence, not untouched validation.
- Features are v296-clean PRE only; contaminated `meet_st_strength`, `meet_win`, `meet_p2` are excluded.
- Settlement is attached only after feature freeze: realtime results first, payout CSV second, archived v108 only for an already-official settlement row; none are prediction features.
- Head gate: HGB + optional independent LR safety consensus. Every monthly cut comes from training temporal OOF only.
- Trifecta: one multiclass model ranks all 20 exact orders `1-a-b`; hit rate denominator is every final selected race, so a boat1 loss is a trifecta miss.
- Settlement universe: scheduled=35921, official-settlement rows=35483 (98.78%), scheduled-but-unsettled/void=438. Winner completeness within official rows=99.986%. Exact combos: realtime=35279, payout fallback=183, archive fallback=0.
- Exact-order completeness among winner-known settled rows: **99.95%**.

## Fold audit
|month|train|test|head features|guard features|combo features|combo train 1-head|classes|
|---|---:|---:|---:|---:|---:|---:|---:|
|2026-02|13428|4071|154|118|154|7450|20|
|2026-03|17499|4565|154|118|154|9708|20|
|2026-04|22064|4204|154|118|154|12218|20|
|2026-05|26268|4744|154|118|154|14538|20|
|2026-06|31012|4450|154|118|154|17141|20|

## Stable development zones with head >=90%
|rule|conf|R|head rate|head Wilson low|5pt hit|5pt Wilson low|worst head month|worst 5pt month|min month R|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|None|-|-|-|-|-|-|-|-|-|

## Best joint zones (R>=100, all 5 months, min month R>=10)
|rule|conf|R|head rate|5pt hit|worst head|worst 5pt|min month R|
|---|---:|---:|---:|---:|---:|---:|---:|
|HGB_q0.975_AND_LR_q0.950|0.60|136|89.71%|53.68%|83.33%|23.08%|13|
|HGB_q0.975_AND_LR_q0.975|0.60|100|88.00%|53.00%|79.17%|30.00%|10|
|HGB_q0.975|0.60|170|87.06%|52.94%|80.95%|23.08%|13|
|HGB_q0.975_AND_LR_q0.900|0.60|165|86.67%|52.12%|80.95%|23.08%|13|
|HGB_q0.950|0.60|468|85.47%|52.35%|81.19%|47.46%|59|
|HGB_q0.950|0.65|265|85.28%|52.08%|79.63%|44.68%|37|
|HGB_q0.950|0.70|124|83.06%|54.03%|60.00%|40.00%|10|
|HGB_q0.975_AND_LR_q0.975|0.55|144|87.50%|49.31%|80.00%|30.00%|10|
|HGB_q0.975_AND_LR_q0.950|0.55|200|88.00%|48.00%|82.14%|23.08%|13|
|HGB_q0.950|0.55|640|85.00%|50.00%|80.50%|44.03%|62|
|HGB_q0.975|0.55|249|86.35%|48.59%|80.82%|23.08%|13|
|HGB_q0.975_AND_LR_q0.900|0.55|239|85.77%|48.12%|80.56%|23.08%|13|
|HGB_q0.950|0.50|751|83.75%|47.67%|78.57%|40.31%|63|
|HGB_q0.975_AND_LR_q0.975|0.50|168|85.12%|45.83%|79.25%|26.42%|10|
|HGB_q0.975_AND_LR_q0.950|0.50|237|85.65%|45.15%|79.17%|21.43%|14|
|HGB_q0.950|0.45|794|83.38%|46.98%|77.88%|38.94%|65|
|HGB_q0.975|0.50|294|84.35%|45.92%|78.02%|21.43%|14|
|HGB_q0.950|0.00|798|83.33%|46.74%|77.62%|38.57%|65|
|HGB_q0.975_AND_LR_q0.950|0.00|253|85.77%|44.27%|80.26%|21.43%|14|
|HGB_q0.975_AND_LR_q0.950|0.45|253|85.77%|44.27%|80.26%|21.43%|14|

## <=5 point ceiling for best joint development rule
|points|R|hits|hit rate|Wilson low|
|---:|---:|---:|---:|---:|
|1|136|21|15.44%|10.33%|
|2|136|40|29.41%|22.40%|
|3|136|56|41.18%|33.26%|
|4|136|65|47.79%|39.58%|
|5|136|73|53.68%|45.31%|

## Target decision
- **No stable development rule simultaneously reaches 1-head >=90% and 3連単5点以内 >=80%.**
- Do not weaken the denominator or condition trifecta accuracy on boat1 wins; that would overstate live accuracy.
- Any candidate chosen from this report must be frozen before prospective September input-snapshot replay; outcomes remain unread until after the freeze.
