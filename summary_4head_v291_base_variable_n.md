# HEAD4 v291 base-race variable-N expansion v2

- Entry identities remain immutable `HEAD4_V291_COMP7`; no races are added or removed.
- Bank remains exactly ¥10,000 per race; only the number of ranked tickets can expand beyond Top4.
- Rule: largest N with composite odds >= floor, capped by maxN.
- v2 fixes LOMO expected-R to the frozen base count in each two-month training split.
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

|holdout|train rule|train R|R|variable ROI|base ROI|variable hit|base hit|
|---|---|---:|---:|---:|---:|---:|---:|
|2026-04|floor=4.0, maxN=16|17|12|239.63%|481.22%|58.33%|50.00%|
|2026-05|floor=5.0, maxN=6|20|9|140.37%|177.91%|22.22%|22.22%|
|2026-06|floor=4.0, maxN=12|21|8|122.51%|166.46%|25.00%|12.50%|

- All LOMO holdout variable-N routes profitable: **YES**.
- Promotion requires a standalone candidate and all three LOMO holdouts >=100% ROI.
- This research does not modify production v291; any promotion requires a new policy/version.
