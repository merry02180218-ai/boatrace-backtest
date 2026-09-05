# v126b clean pair-score validation

- Frozen v110 pair orders regenerated chronologically for Mar-Aug.
- Tune only on Mar-May; Jun-Aug evaluated once after alpha freeze.
- v109 p109>=72 gate unchanged; no Sep outcomes used; no odds used in pair ranking.

## Mar-May development
|alpha|R|7hit|coverage|ROI|
|---:|---:|---:|---:|---:|
|0.00|0|0.0%|0.0%|0.0%|
|0.15|0|0.0%|0.0%|0.0%|
|0.30|0|0.0%|0.0%|0.0%|
|0.45|0|0.0%|0.0%|0.0%|
|0.60|0|0.0%|0.0%|0.0%|
|0.75|0|0.0%|0.0%|0.0%|
|1.00|0|0.0%|0.0%|0.0%|

Frozen alpha = **0.00**

## Jun-Aug untouched holdout
|rule|R|7hit|coverage|ROI|
|---|---:|---:|---:|---:|
|v110 baseline|3306|51.0%|66.4%|80.1%|
|v126b|3306|51.0%|66.4%|80.1%|

- **V126B PAIR SCORE = FAIL**
- PASS requires holdout coverage improvement with no hit-rate or ROI deterioration.
