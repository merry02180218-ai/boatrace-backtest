# v290 Top4 composite-odds floor risk audit

- Base: v283 fixed Top4, 10,000 yen exact inverse-odds Dutch.
- Audited floors only: **6.0 / 7.0 / 8.0**. No threshold search beyond these three.
- Apr-Jun only; Jul/Aug excluded; September outcomes not read.
- Archived odds are retrospective proxy; this remains development evidence.

## Overall risk / return

|floor|R|coverage|4-head rate|hit rate|profit|ROI|max DD|max miss streak|max losing-bet streak|worst 5 bets|worst 10 bets|min month ROI|
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|6.0|40|40.0%|50.0%|25.0%|+533330|233.33%|77280|7|7|-50000|-27280|110.97%|
|7.0|28|28.0%|64.3%|32.1%|+590750|310.98%|60000|6|6|-50000|-27280|166.46%|
|8.0|21|21.0%|71.4%|38.1%|+588030|380.01%|70000|7|7|-50000|+33170|174.80%|

## Monthly

|floor|month|R|4-head rate|hits|profit|ROI|max DD|max miss streak|
|---:|---|---:|---:|---:|---:|---:|---:|---:|
|6.0|2026-04|17|58.8%|6|+407460|339.68%|60000|6|
|6.0|2026-05|11|54.5%|3|+112700|202.45%|70000|7|
|6.0|2026-06|12|33.3%|1|+13170|110.97%|60000|6|
|7.0|2026-04|11|81.8%|6|+467460|524.96%|20000|2|
|7.0|2026-05|9|55.6%|2|+70120|177.91%|60000|6|
|7.0|2026-06|8|50.0%|1|+53170|166.46%|40000|4|
|8.0|2026-04|9|88.9%|6|+487460|641.62%|10000|1|
|8.0|2026-05|5|60.0%|1|+37400|174.80%|40000|4|
|8.0|2026-06|7|57.1%|1|+63170|190.24%|30000|3|

## S / A split

|floor|layer|R|4-head rate|hits|profit|ROI|max DD|max miss streak|
|---:|---|---:|---:|---:|---:|---:|---:|---:|
|6.0|A|26|53.8%|7|+384860|248.02%|50000|5|
|6.0|S|14|42.9%|3|+148470|206.05%|60000|6|
|7.0|A|18|66.7%|6|+402280|323.49%|40000|4|
|7.0|S|10|60.0%|3|+188470|288.47%|50000|5|
|8.0|A|14|71.4%|5|+369560|363.97%|50000|5|
|8.0|S|7|71.4%|3|+218470|412.10%|30000|3|

## Venue split

Small venue cells are descriptive only. R>=3 cells shown first; do not create venue filters from this table.

|floor|venue|R|4-head wins|hits|profit|ROI|
|---:|---|---:|---:|---:|---:|---:|
|6.0|蒲郡|6|5|3|+219210|465.35%|
|6.0|唐津|4|2|1|+56660|241.65%|
|6.0|常滑|4|2|1|+22580|156.45%|
|6.0|江戸川|3|0|0|-30000|0.00%|
|6.0|津|3|1|0|-30000|0.00%|
|6.0|福岡|3|2|2|+192490|741.63%|
|7.0|蒲郡|4|4|3|+239210|698.02%|
|7.0|唐津|3|2|1|+66660|322.20%|
|7.0|常滑|3|1|0|-30000|0.00%|
|7.0|津|3|1|0|-30000|0.00%|
|8.0|蒲郡|4|4|3|+239210|698.02%|

## Risk read

- Descriptive risk-balanced candidate among only 6/7/8: **floor >= 7.0** (R=28, ROI=310.98%, max DD=60000 yen, min-month ROI=166.46%).
- This is not a formal freeze: all three candidates were already motivated by Apr-Jun diagnostics, so prospective validation still requires an immutable pre-deadline odds snapshot.
- Prefer a threshold that preserves enough bets and survives month/layer/venue concentration rather than simply choosing the highest retrospective ROI.
