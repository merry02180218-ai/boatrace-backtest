# v214 3-head cumulative-mass variable points

- signal: direct v166 cumulative pair probability mass only
- frozen July thresholds: **mass4 >= inf -> 4pt; else mass6 >= inf -> 6pt; else mass8 >= inf -> 8pt; else 10pt**
- July tuning constraint: hit >=85% of fixed Top10 and avg points <10
- August untouched uses the frozen July thresholds
- old stress 2025-12..2026-06 reconstructs v165/v166 month-by-month using prior dates only
- settlement: unified pre-deadline odds, 10,000 yen/race, 100-yen Hamilton Dutch
- IMPORTANT: backward old-month results are stress tests, not pristine OOS.

## July/August comparison
|month|strategy|R|hit|avg pts|avg comp|return|ROI|profit|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|2026-07|Top4 fixed|87|14.94%|4.00|7.968|602760|69.3%|-267240|
|2026-07|Top6 fixed|87|21.84%|6.00|5.884|930510|107.0%|+60510|
|2026-07|Top8 fixed|87|22.99%|8.00|4.905|859830|98.8%|-10170|
|2026-07|Top10 fixed|87|26.44%|10.00|4.327|858800|98.7%|-11200|
|2026-07|v214 mass variable|87|26.44%|10.00|4.327|858800|98.7%|-11200|
|2026-08|Top4 fixed|109|18.35%|4.00|8.625|1308620|120.1%|+218620|
|2026-08|Top6 fixed|109|22.94%|6.00|6.358|1339050|122.8%|+249050|
|2026-08|Top8 fixed|109|27.52%|8.00|5.264|1239450|113.7%|+149450|
|2026-08|Top10 fixed|109|30.28%|10.00|4.584|1173880|107.7%|+83880|
|2026-08|v214 mass variable|109|30.28%|10.00|4.584|1173880|107.7%|+83880|

## August point distribution
|points|R|share|
|---:|---:|---:|
|4|0|0.0%|
|6|0|0.0%|
|8|0|0.0%|
|10|109|100.0%|

## Old-month frozen-rule stress
|month|candidates|settled|hit|avg pts|avg comp|return|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2025-12|109|107|22.43%|10.00|5.647|910640|85.1%|-159360|
|2026-01|100|99|25.25%|10.00|4.807|622820|62.9%|-367180|
|2026-02|36|34|29.41%|10.00|5.429|302330|88.9%|-37670|
|2026-03|58|56|35.71%|10.00|4.174|450560|80.5%|-109440|
|2026-04|40|40|32.50%|10.00|4.826|267810|67.0%|-132190|
|2026-05|77|77|31.17%|10.00|3.745|724820|94.1%|-45180|
|2026-06|73|73|30.14%|10.00|3.021|520480|71.3%|-209520|

## Aggregate Dec-Jun
- v214 mass variable: **486R, hit 28.40%, avg points 10.00, avg composite 4.528, ROI 78.2%, profit -1060540 yen**

## Interpretation
- Primary clean comparison for the new threshold rule is August untouched.
- Dec-Jun is backward stability stress only because the point rule was created later on July and v166 lambda has prior tuning history.
- Production remains unchanged unless the rule shows materially better stability than fixed Top6/Top10 and v212.
