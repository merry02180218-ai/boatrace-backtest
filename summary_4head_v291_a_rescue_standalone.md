# HEAD4 v291 A-layer standalone rescue research

- Existing HEAD4_V291_COMP7 bets are immutable and excluded from rescue evaluation.
- Rescue universe = frozen v273 A-layer races that current COMP7 base passes.
- Rule inputs = frozen v283 prefix order + pre-deadline odds only; Top4 is not fixed.
- Jul/Aug/Sep outcomes are excluded. No v96.

- Current BASE: **28R / ROI 310.98%**.

## Selection: NO_STANDALONE_SAFE_CANDIDATE

No A-rescue rule passed standalone monthly-profitability guardrails.

## LOMO selection-procedure check

|holdout|train-selected rule|hold R|hold ROI|hold profit|
|---|---|---:|---:|---:|
|2026-04|NO_TRAIN_CANDIDATE|-|-|-|
|2026-05|NO_TRAIN_CANDIDATE|-|-|-|
|2026-06|NO_TRAIN_CANDIDATE|-|-|-|

- All LOMO holdout rescue ROIs >=100%: **NO**.

## Production decision gate

- Promotion requires both a standalone-safe fixed rule and all LOMO held-out months >=100%.
- Even then A-layer LIVE score-scale mapping must be frozen outcome-blind before deployment.
- Formal prospective performance begins only after a new policy version + official pre-deadline odds audit are operational.
