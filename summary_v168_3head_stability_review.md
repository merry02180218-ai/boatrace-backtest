# v168 3号艇 stability review

- Frozen candidate: p3 >= 0.30, v166 top 10 tickets.
- v165 p3head and v166 direct-pair ranking are unchanged.
- Jun-Aug is diagnostic only; no retuning from these outcomes.
- payout is settlement-only.

## Overall
|R|③頭率|hit|coverage|ROI|top1 return share|top3 return share|
|---:|---:|---:|---:|---:|---:|---:|
|270|38.52%|29.26%|75.96%|103.2%|11.2%|21.3%|

## Monthly
|month|R|hit|coverage|ROI|
|---|---:|---:|---:|---:|
|2026-06|73|30.14%|73.33%|91.2%|
|2026-07|87|26.44%|88.46%|116.3%|
|2026-08|110|30.91%|70.83%|100.9%|

## p3 bands
|band|R|③頭率|hit|coverage|ROI|
|---|---:|---:|---:|---:|---:|
|0.30-0.35|172|38.95%|30.81%|79.10%|116.1%|
|0.35-0.40|68|33.82%|25.00%|73.91%|89.9%|
|0.40-0.50|26|46.15%|34.62%|75.00%|68.7%|
|0.50-2.00|4|50.00%|0.00%|0.00%|0.0%|

## Venue diagnostics (>=5 candidate races)
|venue|R|hit|ROI|
|---|---:|---:|---:|
|20|270|29.26%|103.2%|

## Stability flags
- Minimum monthly ROI: **91.2%**.
- Venues with >=5 races and ROI <70%: **0/1**.
- Top-3 winning payouts share of total return: **21.3%**.

This review is diagnostic. Production adoption should be decided only after checking these stability flags and the predeclared v167 candidate; do not search a new threshold on Jun-Aug here.
