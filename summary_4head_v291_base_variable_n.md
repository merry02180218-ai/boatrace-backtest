# HEAD4 v291 base-race variable-N expansion

- Entry identities remain immutable `HEAD4_V291_COMP7`; no races are added or removed.
- Bank remains exactly ¥10,000 per race; only the number of ranked tickets can expand beyond Top4.
- Rule: largest N with composite odds >= floor, capped by maxN.
- Apr-Jun only; Jul/Aug NON-PRISTINE; September outcomes excluded; no v96.

- Baseline: **29R / ROI 300.26% / hit 31.03% / N=4**.

## Selection: STRONG_STABLE

- Rule: **floor=5.0, maxN=6**
- Full Apr-Jun: **29R / ROI 213.48% / hit 34.48% / avg N 5.72**
- Monthly ROI floor: **140.37%**.

|month|R|ROI|profit|hit|avg N|
|---|---:|---:|---:|---:|---:|
|2026-04|12|298.52%|+238220円|50.00%|5.75|
|2026-05|9|140.37%|+36330円|22.22%|5.67|
|2026-06|8|168.18%|+54540円|25.00%|5.75|

## LOMO

|holdout|train rule|R|variable ROI|base ROI|variable hit|base hit|
|---|---|---:|---:|---:|---:|---:|
|2026-04|NO_TRAIN_CANDIDATE|-|-|-|-|-|
|2026-05|NO_TRAIN_CANDIDATE|-|-|-|-|-|
|2026-06|NO_TRAIN_CANDIDATE|-|-|-|-|-|

- All LOMO holdout variable-N routes profitable: **NO**.
- Promotion requires a standalone candidate and all three LOMO holdouts >=100% ROI.
- This research does not modify production v291; any promotion requires a new policy/version.
