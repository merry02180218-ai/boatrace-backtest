# v197 3号艇 turn-margin forward validation

- base: v165 p3head>=0.30 -> v166 lambda=1.00 -> Top10
- candidate: turn_margin23 threshold
- NOTE: v196 already exposed Mar-Aug behavior, so this is pseudo-forward, not pristine prospective evidence.

## Fixed: tune Mar-May, test Jun-Aug
- chosen cut: **-0.800**

|segment|R|3-head|hit|Top10 cov|cost|return|ROI|
|---|---:|---:|---:|---:|---:|---:|---:|
|Mar-May BASE|175|38.29%|32.57%|85.07%|175000|147320|84.2%|
|Mar-May FILTER|156|38.46%|32.69%|85.00%|156000|134330|86.1%|
|Jun-Aug BASE|270|38.52%|29.26%|75.96%|269000|277710|103.2%|
|Jun-Aug FILTER|246|38.62%|30.08%|77.89%|245000|269670|110.1%|

## Rolling walk-forward
|test month|cut|BASE R|BASE ROI|FILTER R|FILTER head|FILTER hit|FILTER ROI|
|---|---:|---:|---:|---:|---:|---:|---:|
|2026-04|-1.000|40|69.3%|40|42.50%|32.50%|69.3%|
|2026-05|-1.000|77|100.5%|77|37.66%|31.17%|100.5%|
|2026-06|-0.800|73|91.2%|69|39.13%|27.54%|90.3%|
|2026-07|-0.600|87|116.3%|53|35.85%|32.08%|155.9%|
|2026-08|-0.600|110|100.9%|68|47.06%|36.76%|132.0%|

## Rolling aggregate Apr-Aug
|segment|R|3-head|hit|Top10 cov|cost|return|ROI|
|---|---:|---:|---:|---:|---:|---:|---:|
|BASE|387|38.76%|29.97%|77.33%|386000|382810|99.2%|
|FILTER|307|40.39%|31.92%|79.03%|306000|338450|110.6%|

## Decision
- Production is unchanged.
- If fixed and rolling checks both improve materially, use the gate only as Sep SHADOW and require prospective confirmation before adoption.
