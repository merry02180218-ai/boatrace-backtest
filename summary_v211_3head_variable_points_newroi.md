# v211 3-head variable points under new 10k Dutch ROI

- candidate population: frozen v195 production pass (v165 p3head>=0.30), July/August only
- v166 pair model: exact monthly prior-only refit, lambda=1.00
- fixed comparisons: Top4/6/8/10/12/15, each with total 10,000 yen Dutch
- variable rule feature: v166 pair-probability concentration only (effective number of pairs, effN)
- July chooses 3 effN cutoffs from a small quantile grid; rule is monotone 4 -> 6 -> 8 -> 10 points
- tune constraint: variable hit rate must be >=90% of July Top10 hit rate
- August uses the July-frozen rule untouched

## Fixed point-count comparison
|month|points|R|hit|avg comp|cost|return|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-07|4|87|14.94%|7.968|870000|602760|69.3%|-267240|
|2026-07|6|87|21.84%|5.884|870000|930510|107.0%|+60510|
|2026-07|8|87|22.99%|4.905|870000|859830|98.8%|-10170|
|2026-07|10|87|26.44%|4.327|870000|858800|98.7%|-11200|
|2026-07|12|87|26.44%|3.961|870000|784130|90.1%|-85870|
|2026-07|15|87|29.89%|3.604|870000|783930|90.1%|-86070|
|2026-08|4|109|18.35%|8.625|1090000|1308620|120.1%|+218620|
|2026-08|6|109|22.94%|6.358|1090000|1339050|122.8%|+249050|
|2026-08|8|109|27.52%|5.264|1090000|1239450|113.7%|+149450|
|2026-08|10|109|30.28%|4.584|1090000|1173880|107.7%|+83880|
|2026-08|12|109|34.86%|4.151|1090000|1159570|106.4%|+69570|
|2026-08|15|109|38.53%|3.711|1090000|1094940|100.5%|+4940|

## July-tuned variable rule
- frozen effN cutoffs: **-inf / -inf / -inf**
- mapping: effN<=c1 => 4pt; <=c2 => 6pt; <=c3 => 8pt; else 10pt

|month|R|hit|avg points|avg comp|cost|return|ROI|profit|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-07|87|26.44%|10.00|4.327|870000|858800|98.7%|-11200|
|2026-08|109|30.28%|10.00|4.584|1090000|1173880|107.7%|+83880|

## August point distribution
|points|R|share|
|---:|---:|---:|
|4|0|0.0%|
|6|0|0.0%|
|8|0|0.0%|
|10|109|100.0%|

## Interpretation
- This is SHADOW research only. July is explicitly tune; August is the only untouched comparison for the variable rule.
- If variable points beat fixed Top10 on August while using fewer average tickets, that supports a dedicated variable-points production candidate.
- Do not adopt from this one August test alone; next step would be older-month locked/pseudo-forward stability.
