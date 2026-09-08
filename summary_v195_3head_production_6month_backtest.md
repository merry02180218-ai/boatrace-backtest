# v195 3号艇 production exact-operation 6-month backtest

- months: 2026-03 .. 2026-08
- operation: v165 p3head >= 0.30 -> v166 lambda=1.00 -> Top10
- each target month trains only on earlier dates
- equal stake: 100 yen x 10 tickets; payout settlement only after frozen ranking
- no result/payout/odds in prediction or ticket ranking

|month|candidates|3-head|hit|3-head Top10 coverage|cost|return|ROI|
|---|---:|---:|---:|---:|---:|---:|---:|
|2026-03|58|36.21%|34.48%|95.24%|58000|42220|72.8%|
|2026-04|40|42.50%|32.50%|76.47%|40000|27730|69.3%|
|2026-05|77|37.66%|31.17%|82.76%|77000|77370|100.5%|
|2026-06|73|41.10%|30.14%|73.33%|73000|66550|91.2%|
|2026-07|87|29.89%|26.44%|88.46%|87000|101200|116.3%|
|2026-08|110|43.64%|30.91%|70.83%|109000|109960|100.9%|

## Aggregate
- candidates: 445R
- 3-head rate: 38.43%
- trifecta hit rate: 30.56%
- conditional Top10 coverage: 79.53%
- cost: 444000 yen
- return: 425030 yen
- ROI: 95.7%
