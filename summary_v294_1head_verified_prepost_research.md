# v294 1HEAD verified PRE/POST research — recovered source

- Research only; production unchanged.
- Selection/evaluation ends 2026-06-30. Jul/Aug are excluded; Sep outcomes are unread.
- Historical waku10/current-preview files are no longer retained pre-Jul on BoatraceCSV/main; v294 therefore does not pretend they are available.
- PRE = true scheduled-lane1 race-card + prior-day history universe. POST = separate v108 actual-course1 frozen feature ledger.
- v108 result/target/payout columns are not loaded into the POST feature frame. Current winners are joined after feature construction.
- Monthly expanding walk-forward; Platt calibration and quantile gates are training-OOF only.

## Source / leakage audit
|metric|value|
|---|---:|
|pre_cards|35921|
|pre_frozen|35921|
|bad_code|0|
|post_v108_before_course1_gate|35001|
|post_course1_gate_rate|0.9127739207451215|
|post_frozen|31948|
|post_static_join_coverage|1.0|
|result_coverage|0.9907763485538317|
|history_player_features|71|
|history_prior_exhibition_features|328|

## Feature sets
|variant|family|features|universe|
|---|---|---:|---|
|PRE_LR_RECOVERED|lr|524|PRE|
|PRE_HGB_RECOVERED|hgb|524|PRE|
|POST_LR_RECOVERED|lr|558|POST|
|POST_HGB_RECOVERED|hgb|558|POST|

## Pooled Feb-Jun metrics
|variant|score|R|AUC|Brier|LogLoss|
|---|---|---:|---:|---:|---:|
|PRE_HGB_RECOVERED|p_cal|21860|0.8620|0.1554|0.5041|
|POST_HGB_RECOVERED|p_cal|18949|0.8567|0.1610|0.5282|
|PRE_LR_RECOVERED|p_cal|21860|0.8445|0.1628|0.5189|
|POST_LR_RECOVERED|p_cal|18949|0.8409|0.1659|0.5277|
|PRE_HGB_RECOVERED|p_raw|21860|0.8623|0.1575|0.5171|
|POST_HGB_RECOVERED|p_raw|18949|0.8581|0.1630|0.5479|
|PRE_LR_RECOVERED|p_raw|21860|0.8412|0.1683|0.5613|
|POST_LR_RECOVERED|p_raw|18949|0.8374|0.1732|0.5805|

## >=90% realized zones, R>=100
|variant|score|source|rule|R|heads|rate|Wilson low|Wilson high|worst month|min month R|
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.980|1214|1203|99.09%|98.38%|99.49%|95.15%|165|
|PRE_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.950|484|481|99.38%|98.19%|99.79%|97.26%|1|
|POST_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.950|547|541|98.90%|97.63%|99.50%|94.23%|87|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.980|1229|1210|98.45%|97.60%|99.01%|92.53%|174|
|POST_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.900|1237|1216|98.30%|97.42%|98.89%|76.19%|21|
|PRE_HGB_RECOVERED|p_raw|fixed_probability|>=0.980|1422|1397|98.24%|97.42%|98.81%|80.00%|25|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.960|1700|1667|98.06%|97.29%|98.61%|92.00%|275|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.970|1435|1408|98.12%|97.28%|98.70%|91.56%|225|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.970|1510|1481|98.08%|97.26%|98.66%|91.80%|244|
|POST_HGB_RECOVERED|p_raw|fixed_probability|>=0.980|1379|1353|98.11%|97.25%|98.71%|84.21%|19|
|PRE_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.975|132|132|100.00%|97.17%|100.00%|100.00%|1|
|PRE_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.900|1424|1393|97.82%|96.93%|98.46%|77.08%|48|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.960|1639|1602|97.74%|96.90%|98.36%|90.36%|280|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.950|1957|1910|97.60%|96.82%|98.19%|90.43%|9|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.950|1861|1812|97.37%|96.54%|98.00%|88.75%|1|
|PRE_HGB_RECOVERED|p_raw|fixed_probability|>=0.970|1679|1633|97.26%|96.37%|97.94%|76.79%|56|
|POST_HGB_RECOVERED|p_raw|fixed_probability|>=0.970|1621|1575|97.16%|96.24%|97.87%|76.09%|46|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.940|2282|2211|96.89%|96.09%|97.53%|80.00%|20|
|POST_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.975|220|217|98.64%|96.07%|99.54%|95.71%|16|
|POST_LR_RECOVERED|p_cal|training_OOF_quantile|q0.975|289|284|98.27%|96.01%|99.26%|90.70%|1|
|PRE_HGB_RECOVERED|p_raw|fixed_probability|>=0.960|1980|1915|96.72%|95.84%|97.42%|76.32%|76|
|PRE_LR_RECOVERED|p_cal|training_OOF_quantile|q0.975|339|332|97.94%|95.80%|99.00%|66.67%|3|
|POST_HGB_RECOVERED|p_raw|fixed_probability|>=0.960|1928|1863|96.63%|95.73%|97.35%|77.46%|71|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.940|2154|2080|96.56%|95.71%|97.25%|86.93%|9|
|PRE_HGB_RECOVERED|p_raw|fixed_probability|>=0.950|2374|2282|96.12%|95.27%|96.83%|76.70%|103|
|POST_LR_RECOVERED|p_cal|training_OOF_quantile|q0.950|618|599|96.93%|95.25%|98.02%|76.47%|17|
|PRE_LR_RECOVERED|p_cal|training_OOF_quantile|q0.990|115|114|99.13%|95.24%|99.85%|96.30%|25|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.920|3030|2901|95.74%|94.96%|96.41%|77.19%|57|
|PRE_LR_RECOVERED|p_cal|training_OOF_quantile|q0.950|691|667|96.53%|94.88%|97.66%|69.57%|23|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.920|2756|2634|95.57%|94.74%|96.28%|81.58%|38|
|POST_LR_RECOVERED|p_cal|fixed_probability|>=0.980|2041|1953|95.69%|94.72%|96.49%|69.57%|46|
|PRE_HGB_RECOVERED|p_raw|fixed_probability|>=0.940|2790|2665|95.52%|94.69%|96.23%|76.12%|134|
|POST_LR_RECOVERED|p_cal|training_OOF_quantile|q0.900|1289|1236|95.89%|94.66%|96.84%|73.21%|56|
|POST_HGB_RECOVERED|p_raw|fixed_probability|>=0.950|2262|2162|95.58%|94.65%|96.35%|74.76%|103|
|PRE_LR_RECOVERED|p_cal|training_OOF_quantile|q0.900|1500|1436|95.73%|94.59%|96.64%|75.36%|69|
|PRE_LR_RECOVERED|p_cal|fixed_probability|>=0.980|2159|2062|95.51%|94.55%|96.30%|72.00%|50|
|POST_HGB_RECOVERED|p_raw|fixed_probability|>=0.940|2630|2506|95.29%|94.41%|96.03%|77.27%|132|
|PRE_LR_RECOVERED|p_cal|fixed_probability|>=0.970|2600|2474|95.15%|94.26%|95.91%|76.71%|73|
|POST_LR_RECOVERED|p_cal|fixed_probability|>=0.970|2449|2323|94.86%|93.91%|95.66%|74.63%|67|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.900|3317|3135|94.51%|93.69%|95.24%|77.22%|79|

## Best zones with R>=100
|variant|score|source|rule|R|heads|rate|Wilson low|worst month|min month R|
|---|---|---|---|---:|---:|---:|---:|---:|---:|
|PRE_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.975|132|132|100.00%|97.17%|100.00%|1|
|PRE_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.950|484|481|99.38%|98.19%|97.26%|1|
|PRE_LR_RECOVERED|p_cal|training_OOF_quantile|q0.990|115|114|99.13%|95.24%|96.30%|25|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.980|1214|1203|99.09%|98.38%|95.15%|165|
|POST_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.950|547|541|98.90%|97.63%|94.23%|87|
|POST_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.975|220|217|98.64%|96.07%|95.71%|16|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.980|1229|1210|98.45%|97.60%|92.53%|174|
|POST_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.900|1237|1216|98.30%|97.42%|76.19%|21|
|POST_LR_RECOVERED|p_cal|training_OOF_quantile|q0.975|289|284|98.27%|96.01%|90.70%|1|
|PRE_HGB_RECOVERED|p_raw|fixed_probability|>=0.980|1422|1397|98.24%|97.42%|80.00%|25|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.970|1435|1408|98.12%|97.28%|91.56%|225|
|POST_HGB_RECOVERED|p_raw|fixed_probability|>=0.980|1379|1353|98.11%|97.25%|84.21%|19|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.970|1510|1481|98.08%|97.26%|91.80%|244|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.960|1700|1667|98.06%|97.29%|92.00%|275|
|PRE_LR_RECOVERED|p_cal|training_OOF_quantile|q0.975|339|332|97.94%|95.80%|66.67%|3|
|PRE_HGB_RECOVERED|p_cal|training_OOF_quantile|q0.900|1424|1393|97.82%|96.93%|77.08%|48|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.960|1639|1602|97.74%|96.90%|90.36%|280|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.950|1957|1910|97.60%|96.82%|90.43%|9|
|POST_HGB_RECOVERED|p_cal|fixed_probability|>=0.950|1861|1812|97.37%|96.54%|88.75%|1|
|PRE_HGB_RECOVERED|p_raw|fixed_probability|>=0.970|1679|1633|97.26%|96.37%|76.79%|56|
|POST_HGB_RECOVERED|p_raw|fixed_probability|>=0.970|1621|1575|97.16%|96.24%|76.09%|46|
|POST_LR_RECOVERED|p_cal|training_OOF_quantile|q0.950|618|599|96.93%|95.25%|76.47%|17|
|PRE_HGB_RECOVERED|p_cal|fixed_probability|>=0.940|2282|2211|96.89%|96.09%|80.00%|20|
|PRE_HGB_RECOVERED|p_raw|fixed_probability|>=0.960|1980|1915|96.72%|95.84%|76.32%|76|
|POST_HGB_RECOVERED|p_raw|fixed_probability|>=0.960|1928|1863|96.63%|95.73%|77.46%|71|

## Decision
- A pooled 90% row alone is not production evidence. Require monthly stability, Wilson interval, adequate volume, then untouched prospective validation.
- If 90% is still not robust, next step is an independently trained boat1-loss-risk gate and PRE/POST consensus; no rescue rule may lower precision.
