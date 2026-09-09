# v258 4-head scenario-aware direct ordered-pair

- 3-head v221 design transferred structurally to boat-4: direct 20-pair logistic ranking, not separate role-score addition.
- Pair training is strict monthly prior-only and uses only prior boat-4 wins.
- Prior1/prior2 corrected exhibition/original-exhibition and player/frame traits are frozen before current-day results.
- Primary evaluation is Feb-Jun only. Jul/Aug are excluded from improvement evidence.
- Historical odds are settlement-only; exact 10,000-yen Hamilton Dutch.
- This is research/model-selection evidence, not production adoption.

## GATE_123R: PRE>=0.28 / POST>=0.25
- races: **97**, boat4 wins: **38**

|TopN|old coverage|v258 coverage|old hit|v258 hit|old ROI|v258 ROI|
|---:|---:|---:|---:|---:|---:|---:|
|2|31.58%|23.68%|12.50%|9.38%|102.74%|104.91%|
|3|34.21%|23.68%|13.54%|9.38%|90.28%|85.09%|
|5|47.37%|31.58%|18.75%|12.50%|86.08%|73.02%|
|10|78.95%|55.26%|31.25%|21.88%|86.68%|64.29%|

### Variable TopN target composite 10.0
|ranker|R|avg N|hit|avg comp|ROI|
|---|---:|---:|---:|---:|---:|
|old|96|2.38|13.54%|7.764|101.34%|
|v258|96|2.57|9.38%|8.245|81.59%|

### Monthly variable10
|month|ranker|R|hit|ROI|
|---|---|---:|---:|---:|
|2026-02|old|14|14.29%|99.95%|
|2026-02|v258|14|14.29%|125.35%|
|2026-03|old|16|18.75%|172.88%|
|2026-03|v258|16|12.50%|116.25%|
|2026-04|old|24|8.33%|73.99%|
|2026-04|v258|24|8.33%|80.74%|
|2026-05|old|25|16.00%|88.62%|
|2026-05|v258|25|8.00%|48.71%|
|2026-06|old|17|11.76%|92.48%|
|2026-06|v258|17|5.88%|62.51%|

## GATE_156R: PRE>=0.25 / POST>=0.25
- races: **127**, boat4 wins: **47**

|TopN|old coverage|v258 coverage|old hit|v258 hit|old ROI|v258 ROI|
|---:|---:|---:|---:|---:|---:|---:|
|2|29.79%|21.28%|11.11%|7.94%|93.40%|92.47%|
|3|36.17%|23.40%|13.49%|8.73%|92.51%|82.05%|
|5|46.81%|34.04%|17.46%|12.70%|81.40%|74.86%|
|10|80.85%|59.57%|30.16%|22.22%|84.68%|67.93%|

### Variable TopN target composite 10.0
|ranker|R|avg N|hit|avg comp|ROI|
|---|---:|---:|---:|---:|---:|
|old|126|2.52|12.70%|7.932|100.44%|
|v258|126|2.69|7.94%|8.300|69.11%|

### Monthly variable10
|month|ranker|R|hit|ROI|
|---|---|---:|---:|---:|
|2026-02|old|19|10.53%|73.65%|
|2026-02|v258|19|15.79%|138.39%|
|2026-03|old|21|14.29%|131.71%|
|2026-03|v258|21|9.52%|88.57%|
|2026-04|old|27|11.11%|100.70%|
|2026-04|v258|27|7.41%|71.77%|
|2026-05|old|35|17.14%|119.98%|
|2026-05|v258|35|5.71%|34.79%|
|2026-06|old|24|8.33%|65.51%|
|2026-06|v258|24|4.17%|44.28%|

