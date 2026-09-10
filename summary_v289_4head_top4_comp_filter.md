# v289 fixed Top4 composite-odds filter (v283)

- Base tickets: **v283 Top4 fixed**. No variable N.
- Only filter input: Top4 composite odds.
- Every selected BET race costs 10,000 yen; exact Dutch economics retained.
- Jul/Aug excluded; September outcomes not read.
- Archived odds are retrospective proxy; this is exploratory development evidence, not prospective OOS.

## Verification

- All 100 unfiltered races reproduce v285 Top4 exactly: return **1261210 yen**, ROI **126.12%**.

## Does Top4 composite odds contain signal?

- Oriented AUC for boat-4 head result from composite odds alone: **0.6038**.
- Oriented AUC for exact trifecta hit from composite odds alone: **0.6125**.

## Absolute composite-odds bands

|band|R|4-head wins|head rate|hits|hit rate|avg comp|profit|ROI|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|<4|24|8|33.3%|4|16.7%|3.37|-103150|57.02%|
|4-5|26|10|38.5%|3|11.5%|4.57|-126930|51.18%|
|5-6|10|2|20.0%|1|10.0%|5.60|-42040|57.96%|
|6-8|19|5|26.3%|2|10.5%|6.76|-54700|71.21%|
|8-10|13|9|69.2%|5|38.5%|8.77|+309470|338.05%|
|10-12|6|5|83.3%|2|33.3%|10.80|+165390|375.65%|
|12-15|2|1|50.0%|1|50.0%|14.12|+113170|665.85%|

## Simple floor filter: BET only if Top4 composite odds >= floor

|floor|R|coverage|head rate|hits|hit rate|profit|ROI|min monthly ROI|
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|3.0|94|94.0%|38.3%|16|17.0%|+262310|127.91%|82.81%|
|4.0|76|76.0%|42.1%|14|18.4%|+364360|147.94%|100.56%|
|5.0|50|50.0%|44.0%|11|22.0%|+491290|198.26%|106.18%|
|6.0|40|40.0%|50.0%|10|25.0%|+533330|233.33%|110.97%|
|7.0|28|28.0%|64.3%|9|32.1%|+590750|310.98%|166.46%|
|8.0|21|21.0%|71.4%|8|38.1%|+588030|380.01%|174.80%|
|9.0|12|12.0%|66.7%|5|41.7%|+424540|453.78%|0.00%|
|10.0|8|8.0%|75.0%|3|37.5%|+278560|448.20%|0.00%|
|12.0|2|2.0%|50.0%|1|50.0%|+113170|665.85%|665.85%|
|15.0|0|0.0%|nan%|0|nan%|+0|nan%|nan%|

## LOMO floor robustness

For each held-out month, choose the floor using only the other two months (minimum support constraints), then apply it unchanged to the held-out month.

|holdout|chosen floor|train R|train ROI|hold R|hold hits|hold profit|hold ROI|
|---|---:|---:|---:|---:|---:|---:|---:|
|2026-04|6.0|23|154.73%|17|6|+407460|339.68%|
|2026-05|6.0|29|245.04%|11|3|+112700|202.45%|
|2026-06|7.0|20|368.79%|8|1|+53170|166.46%|

- Combined LOMO holdouts: **36 bets, return 933330 yen, ROI 259.26%**.

## Development read

- Best same-sample floor with R>=20: **>= 8.0**, R=21, ROI=380.01%.
- Best minimum-month floor with R>=20: **>= 8.0**, R=21, aggregate ROI=380.01%, min-month=174.80%.
- Same-sample leaders are not production thresholds. The LOMO result is the more useful robustness check.
- If LOMO is not clearly positive/stable, keep unfiltered Top4 as the stronger current baseline rather than forcing an odds filter.
