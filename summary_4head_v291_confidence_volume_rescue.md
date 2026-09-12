# HEAD4 v291 leakage-safe confidence / variable-N rescue

- Confidence is recomputed for all 100 candidates through v287 outcome-independent monthly inference.
- The outcome-conditioned v283 prediction CSV is explicitly NOT used as a confidence source.
- BASE HEAD4_V291_COMP7 is immutable; rescue only acts on BASE PASS races.
- Inputs are frozen v283 p2/conditional-third/order + archived odds only. No v96. Jul/Aug/Sep outcomes excluded.

## S+A

- selection tier: **NO_SAFE_CANDIDATE**

### LOMO

|holdout|train rule|added R|added ROI|combined ROI|
|---|---|---:|---:|---:|
|2026-04|P2R_FIXED N2 f7.0 c2.00|3|0.00%|412.47%|
|2026-05|NO_TRAIN_CANDIDATE|-|-|-|
|2026-06|NO_TRAIN_CANDIDATE|-|-|-|

## S

- selection tier: **NO_SAFE_CANDIDATE**

### LOMO

|holdout|train rule|added R|added ROI|combined ROI|
|---|---|---:|---:|---:|
|2026-04|NO_TRAIN_CANDIDATE|-|-|-|
|2026-05|NO_TRAIN_CANDIDATE|-|-|-|
|2026-06|NO_TRAIN_CANDIDATE|-|-|-|

## Promotion guard

- A candidate is not production until its LOMO rescue is profitable in all held-out months and a new version is frozen.
- S is the only immediately operational head layer; S+A still requires the frozen A_SCORE LIVE-scale mapping.
- Formal OOS starts only after immutable official pre-deadline odds capture + audit persistence are wired.
