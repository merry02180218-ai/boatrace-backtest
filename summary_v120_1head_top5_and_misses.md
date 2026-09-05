# v120 1-head: fixed7 miss diagnostics + ~5 races/day exploration

- Source is frozen v118 Sep-01..04 replay. No result is used to rank/select races.
- This is exploratory only; production v109/v110 rules are unchanged.

## S head-hit but fixed7 miss diagnostics
- S races: **151**; head hits: **124**; head-hit/fixed7-miss: **41**.
- Actual 2nd boat appears somewhere in fixed7 second-position set: **29/41 (70.7%)**.
- Actual 3rd boat appears somewhere in fixed7 third-position set: **30/41 (73.2%)**.
- Miss decomposition: 3rd_out=11, both_roles_present=18, 2nd_out=12.

## Daily top-N selection (pre-result fixed ranking rules)

Rule P75-center = among S, rank closest to p109=77.5% (motivated only as a fixed diagnostic rule, not production).
Rule P-high = among S, rank highest p109.

|rule|N/day|R|①頭率|7点的中率|投資|払戻|ROI|
|---|---:|---:|---:|---:|---:|---:|---:|
|P75-center|3|12|91.7%|91.7%|¥8,400|¥10,820|128.8%|
|P75-center|5|20|95.0%|80.0%|¥14,000|¥16,620|118.7%|
|P75-center|7|28|89.3%|78.6%|¥19,600|¥22,110|112.8%|
|P75-center|10|40|90.0%|67.5%|¥28,000|¥28,140|100.5%|
|P-high|3|12|91.7%|41.7%|¥8,400|¥5,270|62.7%|
|P-high|5|20|90.0%|60.0%|¥14,000|¥13,210|94.4%|
|P-high|7|28|92.9%|60.7%|¥19,600|¥16,750|85.5%|
|P-high|10|40|90.0%|57.5%|¥28,000|¥24,730|88.3%|

## Top-5/day details
|date|rule|selected R|①頭率|7点的中率|ROI|
|---|---|---|---:|---:|---:|
|2026-09-01|P75-center|芦屋4R(77.9%), 下関12R(78.0%), 芦屋1R(78.1%), 蒲郡9R(76.7%), 下関4R(78.4%)|80.0%|60.0%|82.3%|
|2026-09-01|P-high|徳山3R(87.7%), 蒲郡10R(86.7%), 児島1R(86.4%), 蒲郡4R(86.3%), 下関10R(83.5%)|100.0%|80.0%|111.1%|
|2026-09-02|P75-center|下関4R(77.5%), 浜名湖10R(77.6%), 福岡10R(77.1%), 福岡12R(78.3%), 多摩川11R(78.4%)|100.0%|80.0%|138.3%|
|2026-09-02|P-high|大村9R(94.3%), 児島2R(87.7%), 大村12R(84.0%), 住之江10R(83.8%), 尼崎10R(82.5%)|60.0%|40.0%|62.9%|
|2026-09-03|P75-center|浜名湖12R(77.5%), 児島12R(76.9%), 大村7R(76.8%), 下関4R(76.6%), 大村9R(78.7%)|100.0%|80.0%|157.7%|
|2026-09-03|P-high|児島7R(89.8%), 尼崎10R(89.0%), 戸田7R(85.0%), 徳山9R(84.3%), 下関12R(83.7%)|100.0%|80.0%|128.0%|
|2026-09-04|P75-center|住之江10R(77.6%), 徳山5R(77.7%), 浜名湖11R(77.9%), 津12R(76.5%), 住之江9R(78.5%)|100.0%|100.0%|96.6%|
|2026-09-04|P-high|大村10R(92.7%), 三国12R(88.6%), 尼崎7R(88.6%), 宮島12R(85.5%), 徳山1R(85.3%)|100.0%|40.0%|75.4%|
