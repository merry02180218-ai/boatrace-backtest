# v170 3号艇 venue OOS stability

- Venue groups are determined from Mar-May only; Jun-Aug is OOS evaluation only.
- Frozen policy: p3 >= 0.30, v166 top 10.
- No venue exclusion/adoption rule is created from Jun-Aug.

## OOS overall
- Jun-Aug: R 270, ③頭率 38.52%, hit 29.26%, coverage 75.96%, ROI 103.2%.

## Pre-period venue class -> OOS result
|pre class|venues|OOS R|③頭率|hit|coverage|ROI|
|---|---:|---:|---:|---:|---:|---:|
|pre_roi100plus|0|0|0.00%|0.00%|0.00%|0.0%|
|pre_roi70_100|0|0|0.00%|0.00%|0.00%|0.0%|
|pre_roi_under70|0|0|0.00%|0.00%|0.00%|0.0%|
|pre_sparse|24|270|38.52%|29.26%|75.96%|103.2%|

## Interpretation guardrail
If pre-period strong/weak venue classes preserve meaningful separation OOS, venue suitability may be structural. If separation collapses or reverses, v169 dispersion is more consistent with sampling noise. Do not optimize a new venue filter on Jun-Aug.
