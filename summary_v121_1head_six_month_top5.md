# v121 1-head six-month top5/day diagnostic

- Period: **2026-03-01..2026-08-31**.
- v109 p109 is refit month-by-month using only strictly earlier dates.
- v110 role model is also refit month-by-month using only strictly earlier dates; lambda is fixed at **0.50**.
- Race selection uses p109 only. Current/final odds and current-race results are not selection inputs.
- **Important:** Mar-May overlap the original development/tuning period, so treat them as retrospective diagnostics. Jun-Aug are the clean holdout block.

## Monthly model volume
|month|v109 train R|eval R|S candidates|
|---|---:|---:|---:|
|2026-03|17,350|4,528|1,017|
|2026-04|21,878|4,185|997|
|2026-05|26,063|4,550|1,058|
|2026-06|30,613|4,388|1,042|
|2026-07|35,001|4,772|1,155|
|2026-08|39,773|4,776|1,109|

## Daily top-N aggregate: six months
|rule|N/day|selected R|①頭率|7点的中率|7点coverage|7点ROI|8点ROI|10点ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|P75-center|3|549|76.9%|52.3%|68.0%|85.8%|85.9%|85.7%|
|P75-center|5|915|76.5%|50.8%|66.4%|83.6%|85.1%|85.9%|
|P75-center|7|1281|76.4%|50.6%|66.2%|82.3%|83.6%|83.2%|
|P75-center|10|1830|76.8%|50.2%|65.4%|79.9%|80.6%|81.0%|
|P-high|3|549|84.7%|58.7%|69.2%|83.1%|81.1%|78.1%|
|P-high|5|915|85.6%|58.6%|68.5%|84.8%|82.4%|78.5%|
|P-high|7|1281|84.7%|58.0%|68.5%|86.8%|84.2%|81.0%|
|P-high|10|1830|82.6%|56.0%|67.8%|81.5%|80.0%|78.2%|

## Top-5/day by month
|month|rule|R|①頭率|7点的中率|7点ROI|8点ROI|10点ROI|
|---|---|---:|---:|---:|---:|---:|---:|
|2026-03|P75-center|155|74.8%|50.3%|81.5%|75.8%|78.2%|
|2026-03|P-high|155|86.5%|56.8%|75.2%|82.5%|76.0%|
|2026-04|P75-center|150|72.7%|53.3%|79.5%|81.3%|74.7%|
|2026-04|P-high|150|87.3%|63.3%|90.6%|84.9%|72.9%|
|2026-05|P75-center|155|75.5%|45.8%|82.7%|90.9%|89.5%|
|2026-05|P-high|155|86.5%|60.0%|77.0%|70.4%|70.3%|
|2026-06|P75-center|145|81.4%|54.5%|93.3%|94.1%|101.9%|
|2026-06|P-high|145|82.8%|54.5%|78.0%|75.1%|68.1%|
|2026-07|P75-center|155|83.2%|53.5%|90.6%|97.5%|98.7%|
|2026-07|P-high|155|80.6%|54.8%|98.9%|96.0%|94.1%|
|2026-08|P75-center|155|71.6%|47.7%|74.6%|71.3%|73.3%|
|2026-08|P-high|155|89.7%|61.9%|88.8%|85.5%|88.9%|

## Clean holdout focus: Jun-Aug, P75-center top5/day
- selected: **455R**
- ①頭率: **78.7%**
- 7点的中率: **51.9%** / coverage **65.9%** / ROI **86.0%**
- 8点 ROI: **87.5%**
- 10点 ROI: **91.1%**

## S head-hit but fixed7 miss decomposition
- S valid-payout races: **6,378R**
- ①頭的中かつ7点外れ: **1,640R**
- 2nd_out=660, 3rd_out=271, both_out=28, both_roles_present_wrong_pair=681.

## Interpretation guardrail
- P75-center (77.5%付近) was suggested from the later Sep-01..04 diagnostic, so the six-month check is a retrospective robustness test, not a time-forward rule discovery test.
- Do not replace the frozen production/shadow rule from this result alone. Use the Jun-Aug clean block plus Sep prospective results to decide whether a top5/day selector deserves adoption.
