# HEAD4 v291 volume-rescue auto research

- BASE immutable: v283 prefix N=4 / composite >= 7.0 / 10,000 JPY Dutch.
- Rescue only touches BASE PASS races and uses pair order + odds only.
- Apr-Jun archived odds are development evidence; Jul/Aug/Sep outcomes are not used.

## S+A

- BASE: 28R / ROI **310.98%** / monthly floor **166.46%**.
- tier: **SAFE_VOLUME_120_180**
- rescue: **FIXED param=4 floor=5.5**
- combined: **45R (+17) / ROI 220.29% / monthly floor 127.42%**
- rescue-only ROI: **70.91%**

|month|combined R|added R|combined ROI|base ROI|added ROI|
|---|---:|---:|---:|---:|---:|
|2026-04|18|7|320.81%|524.96%|0.00%|
|2026-05|12|3|185.58%|177.91%|208.60%|
|2026-06|15|7|127.42%|166.46%|82.80%|

### LOMO search-procedure check

|holdout|train-chosen rule|added R|combined R|combined ROI|
|---|---|---:|---:|---:|
|2026-04|FIXED 4 / 5.5|7|18|320.81%|
|2026-05|ADAPT 3 / 8.5|6|15|106.75%|
|2026-06|FIXED 3 / 6.5|9|17|119.06%|

## S

- BASE: 10R / ROI **288.47%** / monthly floor **0.00%**.
- tier: **NO_SAFE_CANDIDATE**

### LOMO search-procedure check

|holdout|train-chosen rule|added R|combined R|combined ROI|
|---|---|---:|---:|---:|
|2026-04|FIXED 2 / 5.0|11|16|180.29%|
|2026-05|ADAPT 3 / 8.5|3|6|0.00%|
|2026-06|NO_CANDIDATE|-|-|-|

## Production guard

- S scope can be wired after selector + immutable pre-deadline odds audit are implemented.
- S+A stays development-only until A_SCORE LIVE-scale mapping is formally frozen.
- Any promoted rescue gets a new policy version; HEAD4_V291_COMP7 history is not rewritten.
