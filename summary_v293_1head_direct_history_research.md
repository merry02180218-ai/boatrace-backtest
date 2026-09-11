# v293 1HEAD direct/history PRE-POST research

- Research only; production unchanged.
- Model-selection/evaluation window ends 2026-06-30. Jul/Aug excluded; Sep outcomes unread.
- Monthly expanding walk-forward. Platt calibration/quantile gates are training-OOF only.
- PRE variants exclude every current-race exhibition/original-exhibition feature. POST variants may use them after entry confirmation.

## Feature sets
|variant|family|available features|
|---|---|---:|
|PRE_LR_DIRECT|lr|0|
|PRE_HGB_HISTORY|hgb|406|
|POST_LR_DIRECT|lr|0|
|POST_HGB_HISTORY|hgb|406|

## Pooled Feb-Jun metrics
|variant|score|R|AUC|Brier|LogLoss|
|---|---|---:|---:|---:|---:|
|POST_HGB_HISTORY|p_cal|21692|0.6911|0.2196|0.6297|
|PRE_HGB_HISTORY|p_cal|21692|0.6911|0.2196|0.6297|
|POST_HGB_HISTORY|p_raw|21692|0.6914|0.2197|0.6299|
|PRE_HGB_HISTORY|p_raw|21692|0.6914|0.2197|0.6299|

## >=90% realized zones, R>=100
- None.

## Best zones with R>=100
|variant|score|source|rule|R|rate|Wilson low|worst month|min month R|
|---|---|---|---|---:|---:|---:|---:|---:|
|POST_HGB_HISTORY|p_cal|fixed_probability|>=0.800|275|81.82%|76.83%|77.42%|1|
|PRE_HGB_HISTORY|p_cal|fixed_probability|>=0.800|275|81.82%|76.83%|77.42%|1|
|POST_HGB_HISTORY|p_raw|fixed_probability|>=0.800|464|81.25%|77.45%|78.16%|37|
|PRE_HGB_HISTORY|p_raw|fixed_probability|>=0.800|464|81.25%|77.45%|78.16%|37|
|POST_HGB_HISTORY|p_cal|training_OOF_quantile|q0.975|251|80.88%|75.56%|78.02%|1|
|PRE_HGB_HISTORY|p_cal|training_OOF_quantile|q0.975|251|80.88%|75.56%|78.02%|1|
|POST_HGB_HISTORY|p_raw|fixed_probability|>=0.820|150|80.00%|72.89%|76.47%|4|
|PRE_HGB_HISTORY|p_raw|fixed_probability|>=0.820|150|80.00%|72.89%|76.47%|4|
|POST_HGB_HISTORY|p_cal|training_OOF_quantile|q0.950|726|79.06%|75.95%|75.13%|21|
|PRE_HGB_HISTORY|p_cal|training_OOF_quantile|q0.950|726|79.06%|75.95%|75.13%|21|
|POST_HGB_HISTORY|p_cal|fixed_probability|>=0.750|1641|77.82%|75.74%|76.00%|102|
|PRE_HGB_HISTORY|p_cal|fixed_probability|>=0.750|1641|77.82%|75.74%|76.00%|102|
|POST_HGB_HISTORY|p_raw|fixed_probability|>=0.750|2445|77.34%|75.64%|74.44%|316|
|PRE_HGB_HISTORY|p_raw|fixed_probability|>=0.750|2445|77.34%|75.64%|74.44%|316|
|POST_HGB_HISTORY|p_cal|training_OOF_quantile|q0.900|1829|77.15%|75.17%|75.50%|110|
|PRE_HGB_HISTORY|p_cal|training_OOF_quantile|q0.900|1829|77.15%|75.17%|75.50%|110|

## Interpretation rule
- A realized >=90% row is a research finding, not yet production adoption. Require sample size, monthly floor, and prospective outcome-blind validation.
- If PRE improves materially, prioritize it for operational robustness. If only POST reaches the zone, keep PRE/POST separate rather than leaking exhibition into PRE.
