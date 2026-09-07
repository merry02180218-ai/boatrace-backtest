# v169 3号艇 corrected venue stability

- v168 bug fixed: venue is read from explicit `venue` field, matching v166 feature encoding.
- Frozen candidate unchanged: p3 >= 0.30, v166 top 10.
- No Jun-Aug retuning; payout settlement-only.

## Overall cross-check
- R 270, ③頭率 38.52%, hit 29.26%, coverage 75.96%, ROI 103.2%.

## Venue diagnostics
|venue|R|③頭率|hit|coverage|ROI|
|---|---:|---:|---:|---:|---:|
|01|8|25.00%|25.00%|100.00%|31.4%|
|02|33|30.30%|21.21%|70.00%|86.6%|
|03|10|50.00%|40.00%|80.00%|145.7%|
|04|45|40.00%|33.33%|83.33%|101.3%|
|05|8|50.00%|37.50%|75.00%|178.9%|
|06|9|55.56%|55.56%|100.00%|467.8%|
|07|1|0.00%|0.00%|0.00%|0.0%|
|08|6|16.67%|16.67%|100.00%|23.7%|
|09|6|66.67%|0.00%|0.00%|0.0%|
|10|11|45.45%|36.36%|80.00%|53.6%|
|11|11|36.36%|27.27%|75.00%|52.0%|
|12|6|0.00%|0.00%|0.00%|0.0%|
|13|13|53.85%|23.08%|42.86%|27.5%|
|14|23|30.43%|26.09%|85.71%|94.6%|
|15|8|37.50%|37.50%|100.00%|191.5%|
|16|7|28.57%|28.57%|100.00%|85.3%|
|17|3|100.00%|33.33%|33.33%|271.7%|
|18|2|0.00%|0.00%|0.00%|0.0%|
|19|10|50.00%|50.00%|100.00%|215.0%|
|20|2|50.00%|50.00%|100.00%|46.5%|
|21|9|0.00%|0.00%|0.00%|0.0%|
|22|18|44.44%|33.33%|75.00%|102.9%|
|23|14|50.00%|35.71%|71.43%|134.1%|
|24|7|42.86%|42.86%|100.00%|48.3%|

## Stability flags
- Venues represented: **24**.
- Venues with >=5 candidate races: **20**.
- Among >=5R venues, ROI >=100%: **8/20**.
- Among >=5R venues, ROI <70%: **9/20**.

Do not exclude or select venues from these Jun-Aug diagnostics. This is a stability check for the already frozen candidate, not a venue optimization.
