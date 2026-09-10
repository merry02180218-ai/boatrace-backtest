# v280 independent role-split 4-head opponent model

- v96 is NOT used in features, model fitting, candidate restriction, or pair ordering.
- SECOND and THIRD feature family/L2 are selected independently using Feb-Mar only.
- Pair alpha and conditional-third formula are also selected on Feb-Mar only; Apr-Jun is untouched holdout-like evaluation.
- Jul/Aug excluded; September not read; no odds.

## Frozen role choices from Feb-Mar

- SECOND: **PLAYER_START**, L2 **10**, role objective **46.67**
- THIRD: **PLAYER_START**, L2 **0.3**, role objective **45.19**

## Pair-composition choice on Feb-Mar

- chosen second weight alpha: **0.60**
- conditional third normalization: **False**
- tune Top2/Top4/Top6/Top10: **29.6% / 42.6% / 53.7% / 66.7%**

### Pair grid

|cond3|alpha2|R|T1|T2|T4|T6|T10|objective|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|False|0.60|54|16.7%|29.6%|42.6%|53.7%|66.7%|38.98|
|True|0.65|54|16.7%|27.8%|44.4%|53.7%|66.7%|38.61|
|True|0.50|54|16.7%|27.8%|42.6%|53.7%|74.1%|38.43|
|True|0.70|54|16.7%|27.8%|40.7%|55.6%|70.4%|37.96|
|False|0.55|54|16.7%|27.8%|42.6%|51.9%|66.7%|37.78|
|True|0.60|54|16.7%|25.9%|44.4%|53.7%|68.5%|37.78|
|False|0.65|54|16.7%|27.8%|42.6%|51.9%|64.8%|37.69|
|True|0.55|54|16.7%|24.1%|44.4%|55.6%|72.2%|37.31|
|False|0.75|54|14.8%|27.8%|37.0%|57.4%|70.4%|37.13|
|False|0.50|54|16.7%|25.9%|44.4%|50.0%|66.7%|37.13|
|False|0.70|54|14.8%|27.8%|37.0%|55.6%|68.5%|36.76|
|True|0.75|54|16.7%|27.8%|35.2%|57.4%|70.4%|36.57|

## Apr-Jun holdout-like result

|scope|R|2nd T1|T2|3rd T1|T2|Pair T1|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|ALL 4-head wins|87|41.4%|60.9%|26.4%|48.3%|19.5%|33.3%|41.4%|49.4%|75.9%|28.7%|44.8%|55.2%|75.9%|
|Frozen S+A head-wins|40|32.5%|55.0%|27.5%|42.5%|20.0%|27.5%|32.5%|42.5%|75.0%|35.0%|45.0%|57.5%|77.5%|

## S+A monthly

|month|R|T2|T4|T6|T10|v96 T2|T4|T6|T10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-04|11|36.4%|36.4%|36.4%|63.6%|27.3%|36.4%|36.4%|54.5%|
|2026-05|15|26.7%|33.3%|53.3%|93.3%|46.7%|53.3%|66.7%|86.7%|
|2026-06|14|21.4%|28.6%|35.7%|64.3%|28.6%|42.9%|64.3%|85.7%|

## Decision
- Keep the opponent-model rebuild independent of v96 regardless of result.
- If v280 improves small-N coverage and monthly stability, next test exact 10,000-yen Dutch/composite-odds economics.
- If not, next research should target THIRD-role features and race-scenario interactions, because SECOND is already the stronger independent component.
