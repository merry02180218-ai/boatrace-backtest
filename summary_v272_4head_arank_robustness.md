# v272 4-head A-rank robustness audit

- v268 S-rank remains untouched.
- Jul/Aug 2026 excluded completely.
- Gate is fixed from v271 at PRE>=0.18 / POST>=0.18; only the nearby A-score threshold is stress-tested.
- Leave-one-month-out: choose threshold on two months, evaluate the untouched third month.
- BROAD gate itself came from v271, so this is robustness/model-selection evidence, not pristine OOS.

## Fixed v271 candidate: A-score >= 0.28
- A=47R, A head=44.68%, A hit=17.02%, A ROI=150.16%.
- S+A=100R, head=40.00%, hit=16.00%, ROI=131.26%, monthly floor=104.00%.
- Months: 2026-04:31R ROI104.00% head35.48% hit9.68%;2026-05:34R ROI170.66% head44.12% hit23.53%;2026-06:35R ROI117.13% head40.00% hit14.29%

## Threshold neighborhood
|A cut|A R|A head|A ROI|S+A R|S+A head|S+A ROI|min month ROI|
|---:|---:|---:|---:|---:|---:|---:|---:|
|0.24|58|41.38%|128.07%|111|38.74%|121.59%|92.12%|
|0.25|54|42.59%|137.55%|107|39.25%|126.14%|97.70%|
|0.26|51|41.18%|138.38%|104|38.46%|126.21%|97.70%|
|0.27|48|43.75%|147.03%|101|39.60%|129.96%|104.00%|
|0.28|47|44.68%|150.16%|100|40.00%|131.26%|104.00%|
|0.29|42|47.62%|145.33%|95|41.05%|128.13%|104.00%|
|0.30|38|50.00%|136.13%|91|41.76%|123.53%|115.15%|
|0.31|34|47.06%|125.55%|87|40.23%|118.82%|106.51%|
|0.32|29|48.28%|147.19%|82|40.24%|126.06%|114.12%|
|0.33|28|50.00%|152.45%|81|40.74%|127.62%|118.35%|

## Rotating leave-one-month-out threshold test
|held-out month|cut chosen on other 2 months|train S+A R|train ROI|train floor|holdout A R|holdout A ROI|holdout S+A R|holdout S+A ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-04|0.28|69|143.51%|117.13%|14|67.37%|31|104.00%|
|2026-05|0.27|67|109.31%|104.00%|12|298.90%|34|170.66%|
|2026-06|0.26|67|134.72%|97.70%|23|109.89%|37|110.80%|

## Robustness decision
- All rotating held-out months keep combined ROI >=100%: YES.
- A-score 0.27-0.30 neighborhood combined ROI range: 123.53% to 131.26%.
- Same neighborhood monthly-floor range: 104.00% to 115.15%.
- If frozen later, keep A-rank separate from v268 S-rank and map the OOF score threshold to the final live model outcome-blind before prospective use.
- Do not inspect/tune against September results before the A-rank freeze.
