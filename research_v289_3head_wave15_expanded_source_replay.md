# 3号艇 Wave15 — expanded source + prior-Wave replay

- legacy v288 **94R is a floor, not a fixed research count**
- candidate source now includes buyable final-NO_BET races formerly excluded by old PRE S/A
- old Wave1 signal families are re-evaluated only because the population changed
- prior-month-only walk-forward; Jul/Aug NON-PRISTINE; September outcomes unused
- current required features missing => fail closed; overlap with legacy v288 must be 0

Expanded pool: 232R (old NO_BET 178 / old PRE-excluded 54)

## Methods
|method|frac|add R|old PRE-excluded|hits|ROI|profit|min month|red|max DD|combined R|combined ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|return_rank|0.15|23|12|4|55.00%|-103,500|0.00%|3|121,980|117|149.45%|
|residual_hit|0.15|25|12|4|50.60%|-123,500|0.00%|3|141,980|119|146.94%|
|ev_calibrated|0.15|27|13|4|46.85%|-143,500|0.00%|3|161,980|121|144.51%|
|orthogonal_consensus|0.15|23|10|3|42.27%|-132,780|0.00%|3|160,000|117|146.95%|
|residual_hit|0.45|87|26|11|38.85%|-531,990|0.00%|4|543,850|181|108.29%|
|return_rank|0.45|87|26|11|38.85%|-531,990|0.00%|4|543,850|181|108.29%|
|ev_calibrated|0.45|87|25|11|38.85%|-531,990|0.00%|4|543,850|181|108.29%|
|return_rank|0.25|44|14|5|35.55%|-283,600|0.00%|4|302,240|138|128.87%|
|residual_hit|0.25|45|15|5|34.76%|-293,600|0.00%|4|312,240|139|127.95%|
|exhibition_upgrade|0.45|71|16|8|34.73%|-463,450|0.00%|4|463,690|165|113.25%|
|orthogonal_consensus|0.45|81|23|9|34.37%|-531,590|0.00%|4|533,450|175|108.60%|
|ev_calibrated|0.25|46|15|5|34.00%|-303,600|0.00%|4|303,600|140|127.03%|
|exhibition_upgrade|0.15|23|5|2|29.43%|-162,320|0.00%|4|170,800|117|144.42%|
|orthogonal_consensus|0.25|46|14|4|27.50%|-333,500|0.00%|4|333,500|140|124.90%|
|exhibition_upgrade|0.25|41|8|2|16.51%|-342,320|0.00%|4|342,320|135|125.17%|

## Decision
**NO_ADOPTION_WAVE15**
