# v215 strict walk-forward overfit audit

- v165: monthly prior-only fit, fixed BUY threshold p3head>=0.30
- v166: monthly prior-only pair fit
- adaptive opponent strategy: each target month selects lambda in {0,.25,.50,.75,1.0} and points in {4,6,8,10,12,15} using only earlier audit months under the new 10k Dutch ROI
- Dec-2025 is seed/diagnostic only; adaptive OOS aggregate starts Jan-2026
- current-month results/odds never enter model or strategy choice before settlement

## Stage decomposition: fixed lambda=1.00 / Top10
|month|candidates|settled|3-head rate|Top10 coverage given 3-head|trifecta hit|avg comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2025-12|109|107|27.10%|82.76%|22.43%|5.647|85.1%|-159360|
|2026-01|100|99|32.32%|78.12%|25.25%|4.807|62.9%|-367180|
|2026-02|36|34|32.35%|90.91%|29.41%|5.429|88.9%|-37670|
|2026-03|58|56|37.50%|95.24%|35.71%|4.174|80.5%|-109440|
|2026-04|40|40|42.50%|76.47%|32.50%|4.826|67.0%|-132190|
|2026-05|77|77|37.66%|82.76%|31.17%|3.745|94.1%|-45180|
|2026-06|73|73|41.10%|73.33%|30.14%|3.021|71.3%|-209520|
|2026-07|87|87|29.89%|88.46%|26.44%|4.327|98.7%|-11200|
|2026-08|110|109|43.12%|70.21%|30.28%|4.584|107.7%|+83880|

## Strict walk-forward selected opponent strategy
|target month|lambda|points|settled|3-head rate|coverage|hit|avg comp|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2025-12|1.00|10|107|27.10%|82.76%|22.43%|5.647|85.1%|-159360|
|2026-01|1.00|4|99|32.32%|40.62%|13.13%|8.497|54.2%|-453060|
|2026-02|0.75|4|34|32.35%|63.64%|20.59%|9.807|123.4%|+79450|
|2026-03|0.00|4|56|37.50%|52.38%|19.64%|7.839|74.2%|-144430|
|2026-04|0.50|4|40|42.50%|58.82%|25.00%|9.561|109.4%|+37510|
|2026-05|0.50|4|77|37.66%|51.72%|19.48%|7.007|86.8%|-102020|
|2026-06|0.00|4|73|41.10%|40.00%|16.44%|6.030|82.0%|-131170|
|2026-07|0.00|4|87|29.89%|42.31%|12.64%|8.759|101.1%|+9470|
|2026-08|0.00|4|109|43.12%|38.30%|16.51%|9.786|133.1%|+360420|

## Adaptive OOS aggregate Jan-Aug
- races: **575**
- cost: **5750000 yen**
- return: **5406170 yen**
- ROI: **94.0%**
- profit: **-343830 yen**

## Regime comparison for unchanged lambda=1 / Top10
- Dec-Jun: R=486, 3-head=34.77%, coverage=81.66%, hit=28.40%, ROI=78.2%
- Jul-Aug: R=196, 3-head=37.24%, coverage=76.71%, hit=28.57%, ROI=103.7%

## Interpretation guardrails
- If 3-head rate itself rises sharply late, v165/regime shift is a major source of the ROI jump.
- If 3-head rate is stable but pair coverage/ROI rises sharply, v166/opponent or odds regime is the larger source.
- If adaptive prior-only lambda/points still fail to reach 100% OOS, Jul/Aug rule-search gains should be treated as likely overfit or regime-specific rather than production proof.
- No production change is made by this audit.
