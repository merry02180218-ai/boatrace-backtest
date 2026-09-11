# v292 1HEAD 90% baseline research

- Research-only; not production.
- Frozen v108 features only; POST-capable, not PRE.
- Selection/evaluation ends 2026-06-30. Jul/Aug excluded; Sep outcomes unread.
- Monthly expanding walk-forward. Calibration and quantile cuts are training-OOF only.

## Existing feature gap
|family|concept|status|note|
|---|---|---|---|
|BASE_1|boat1 absolute player/motor/form|present|v109 absolute block exists|
|RELATIVE_ATTACK|1v2/1v3 composite score|present|margin2/margin3/margin23/margin_all|
|RELATIVE_ATTACK|1v2/1v3 ST|present|st_margin2/st_margin3/st_margin23|
|RELATIVE_ATTACK|1vAll ST|missing|no explicit all-opponent ST margin|
|RELATIVE_ATTACK|1v2/1v3 direct motor|missing|motor only embedded in composite score|
|RELATIVE_ATTACK|player/course history deltas|missing|no all-win/frame-win/recent-p2 relative ledger|
|WALL_THREAT|boat2/3 composite threat|present|threat2/threat3/threat23_max|
|WALL_THREAT|wall2 collapse / simultaneous attack|partial|structural wall gate absent|
|PRIOR_FORM|meeting ST|present|one_meet_st_strength|
|PRIOR_FORM|prior exhibition/straight/turn/lap|missing|prior-history ledger absent|
|ENV_ENTRY|actual course1 entry|partial|entry is gate only|
|ENV_ENTRY|wind/direction interaction|missing|venue one-hot only|
|POST_EXHIBITION|current display/original display|present|one_ex/st/lap/turn/straight/orig_avg|
|POST_EXHIBITION|1v23 ex/turn/straight|present|existing margin23 features|
|POST_EXHIBITION|1v23 lap + 1vAll display margins|missing|not in v109|
|CONSENSUS|separate PRE/POST/ENV models|missing|v109 monolithic POST-capable model|
|NEGATIVE_RISK|independent boat1-loss guard|missing|no separate nonlinear loss gate|

## Pooled model metrics
|model|score|R|AUC|Brier|LogLoss|
|---|---|---:|---:|---:|---:|
|LR_V109_FULL_POST|p_cal|21692|0.7127|0.2132|0.6154|
|LR_ABS_THREAT_POST|p_cal|21692|0.7125|0.2132|0.6155|
|HGB_V109_FULL_POST|p_cal|21692|0.7096|0.2142|0.6177|
|LR_ABS_POST|p_cal|21692|0.6973|0.2179|0.6261|
|LR_V109_FULL_POST|p_raw|21692|0.7127|0.2131|0.6153|
|LR_ABS_THREAT_POST|p_raw|21692|0.7125|0.2132|0.6154|
|HGB_V109_FULL_POST|p_raw|21692|0.7101|0.2141|0.6175|
|LR_ABS_POST|p_raw|21692|0.6973|0.2179|0.6258|

## >=90% realized zones, R>=100
- None in Feb-Jun walk-forward. Do not rescue with Jul/Aug.

## Best high-confidence zones (R>=100)
|source|model|rule|R|rate|Wilson low|worst month|
|---|---|---|---:|---:|---:|---:|
|fixed_probability|HGB_V109_FULL_POST|>=0.880|125|88.00%|81.14%|83.33%|
|fixed_probability|HGB_V109_FULL_POST|>=0.880|134|87.31%|80.62%|81.40%|
|fixed_probability|LR_ABS_POST|>=0.880|116|87.07%|79.76%|82.14%|
|fixed_probability|LR_ABS_THREAT_POST|>=0.860|595|86.39%|83.40%|81.90%|
|fixed_probability|LR_ABS_THREAT_POST|>=0.900|131|86.26%|79.32%|77.42%|
|fixed_probability|LR_ABS_THREAT_POST|>=0.860|457|86.21%|82.75%|81.55%|
|fixed_probability|LR_ABS_POST|>=0.860|212|85.85%|80.52%|82.69%|
|training_OOF_quantile|LR_ABS_THREAT_POST|training_OOF_q0.995|134|85.82%|78.91%|78.79%|
|training_OOF_quantile|LR_ABS_POST|training_OOF_q0.990|246|85.77%|80.86%|81.82%|
|fixed_probability|LR_V109_FULL_POST|>=0.860|594|85.69%|82.64%|81.55%|
|fixed_probability|HGB_V109_FULL_POST|>=0.840|545|85.69%|82.50%|80.77%|
|fixed_probability|LR_V109_FULL_POST|>=0.860|467|85.44%|81.95%|81.03%|
|training_OOF_quantile|LR_ABS_THREAT_POST|training_OOF_q0.975|635|85.35%|82.39%|78.40%|
|training_OOF_quantile|LR_V109_FULL_POST|training_OOF_q0.975|639|85.29%|82.33%|79.51%|
|training_OOF_quantile|LR_ABS_POST|training_OOF_q0.995|115|85.22%|77.60%|75.00%|

## Calibrated reliability >=75% mean score
|model|bin|R|mean p|realized|Wilson low|
|---|---|---:|---:|---:|---:|
|HGB_V109_FULL_POST|[0.75, 0.8)|1803|77.33%|75.87%|73.84%|
|HGB_V109_FULL_POST|[0.8, 0.85)|957|82.10%|84.33%|81.89%|
|HGB_V109_FULL_POST|[0.85, 0.9)|356|87.03%|84.27%|80.12%|
|HGB_V109_FULL_POST|[0.9, 0.95)|32|90.96%|87.50%|71.93%|
|LR_ABS_POST|[0.75, 0.8)|1924|77.40%|74.01%|72.01%|
|LR_ABS_POST|[0.8, 0.85)|1181|82.20%|79.17%|76.76%|
|LR_ABS_POST|[0.85, 0.9)|413|86.85%|83.29%|79.39%|
|LR_ABS_POST|[0.9, 0.95)|27|91.19%|92.59%|76.63%|
|LR_ABS_THREAT_POST|[0.75, 0.8)|1820|77.38%|75.22%|73.18%|
|LR_ABS_THREAT_POST|[0.8, 0.85)|1331|82.28%|79.19%|76.93%|
|LR_ABS_THREAT_POST|[0.85, 0.9)|652|87.04%|85.43%|82.51%|
|LR_ABS_THREAT_POST|[0.9, 0.95)|129|91.47%|86.05%|79.02%|
|LR_ABS_THREAT_POST|[0.95, 1.0)|2|95.60%|100.00%|34.24%|
|LR_V109_FULL_POST|[0.75, 0.8)|1820|77.42%|74.95%|72.90%|
|LR_V109_FULL_POST|[0.8, 0.85)|1338|82.29%|79.75%|77.51%|
|LR_V109_FULL_POST|[0.85, 0.9)|652|87.09%|85.74%|82.84%|
|LR_V109_FULL_POST|[0.9, 0.95)|118|91.51%|84.75%|77.17%|
|LR_V109_FULL_POST|[0.95, 1.0)|2|95.96%|100.00%|34.24%|

## Next
- Build v293 direct raw-source dataset with PRE/POST separation.
- Add direct 1v2/1v3 motor and player/course deltas, prior exhibition, 1vAll ST/display margins, wall-collapse risk, ENV_ENTRY, and PRE/POST consensus.
- Reuse the same Feb-Jun expanding walk-forward and training-only calibration. Freeze before prospective validation.
