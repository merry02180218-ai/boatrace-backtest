# v271 4-head A-rank expansion audit

- v268 remains frozen S-rank and is never modified here.
- A-score uses only v270 stable pre-result features and is generated month-walk-forward.
- Evaluation months: Apr-Jun 2026 only; Jul/Aug excluded completely.
- Ticket/settlement: prior-only v96 4-x-y pair order, N=2..20 nearest composite odds 10.5, exact 10,000-yen Dutch/Hamilton.
- Archived odds proxy => retrospective development/model-selection only, NOT prospective/live OOS.

## Frozen S benchmark
- S: 53R, head 35.85%, hit 15.09%, ROI 114.50%, monthly floor 100.70%.

## Best S+A cells around 80-120 races
|gate|PRE|POST|A cut|A R|A head|A hit|A ROI|total R|total head|total hit|total ROI|min month ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|BROAD_18_18|0.18|0.18|0.33|28|50.00%|17.86%|152.45%|81|40.74%|16.05%|127.62%|118.35%|
|BROAD_18_18|0.18|0.18|0.30|38|50.00%|15.79%|136.13%|91|41.76%|15.38%|123.53%|115.15%|
|BROAD_18_18|0.18|0.18|0.32|29|48.28%|17.24%|147.19%|82|40.24%|15.85%|126.06%|114.12%|
|PRE20_POST22|0.20|0.22|0.29|28|42.86%|17.86%|153.76%|81|38.27%|16.05%|128.07%|110.12%|
|BROAD_18_18|0.18|0.18|0.31|34|47.06%|14.71%|125.55%|87|40.23%|14.94%|118.82%|106.51%|
|PRE20_POST22|0.20|0.22|0.28|31|41.94%|19.35%|169.65%|84|38.10%|16.67%|134.85%|106.19%|
|BAL_20_20|0.20|0.20|0.29|31|41.94%|16.13%|138.88%|84|38.10%|15.48%|123.50%|106.19%|
|BAL_20_20|0.20|0.20|0.30|28|42.86%|14.29%|120.51%|81|38.27%|14.81%|116.58%|106.19%|
|PRE20_POST22|0.20|0.22|0.25|37|40.54%|18.92%|152.15%|90|37.78%|16.67%|129.98%|104.49%|
|BROAD_18_18|0.18|0.18|0.28|47|44.68%|17.02%|150.16%|100|40.00%|16.00%|131.26%|104.00%|
|BROAD_18_18|0.18|0.18|0.27|48|43.75%|16.67%|147.03%|101|39.60%|15.84%|129.96%|104.00%|
|BROAD_18_18|0.18|0.18|0.29|42|47.62%|16.67%|145.33%|95|41.05%|15.79%|128.13%|104.00%|
|PRE20_POST22|0.20|0.22|0.27|32|40.62%|18.75%|164.34%|85|37.65%|16.47%|133.27%|102.52%|
|PRE20_POST22|0.20|0.22|0.24|41|39.02%|17.07%|137.30%|94|37.23%|15.96%|124.45%|101.32%|
|PRE20_POST22|0.20|0.22|0.23|44|38.64%|15.91%|127.94%|97|37.11%|15.46%|120.60%|101.32%|
|PRE20_POST22|0.20|0.22|0.26|34|38.24%|17.65%|154.68%|87|36.78%|16.09%|130.20%|99.11%|
|BAL_20_20|0.20|0.20|0.28|35|40.00%|17.14%|150.26%|88|37.50%|15.91%|128.72%|99.11%|
|BAL_20_20|0.20|0.20|0.25|41|39.02%|17.07%|137.30%|94|37.23%|15.96%|124.45%|98.34%|
|PRE20_POST22|0.20|0.22|0.21|47|38.30%|14.89%|119.78%|100|37.00%|15.00%|116.98%|98.34%|
|PRE20_POST22|0.20|0.22|0.22|47|38.30%|14.89%|119.78%|100|37.00%|15.00%|116.98%|98.34%|

## Descriptive checkpoints
- Closest to 100R with combined ROI>=100% and monthly floor>=90%: BROAD_18_18, A cut 0.28, A=47R, total=100R, A ROI=150.16%, combined ROI=131.26%, floor=104.00%.
- Maximum race count while combined ROI>=100% and floor>=90%: total=111R (BROAD_18_18, A cut 0.24), combined ROI=121.59%, floor=92.12%.

## Guardrail
- Do NOT alter HEAD4_V268_FROZEN_20260910.md from this retrospective search.
- Any A-rank rule chosen from v271 must be frozen as a separate version before September outcomes are inspected/used.
- Formal prospective evaluation starts only after that separate A-rule freeze.
