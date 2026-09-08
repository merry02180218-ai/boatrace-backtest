# v212 3-head joint-confidence variable points

- input: v211 exact v166 monthly prior-only rankings + new 10k Dutch settlements
- variable signal = frozen July-standardized blend of p3head and opponent concentration (-effN)
- selected head/concentration blend weight on p3head: **0.50** (remaining 0.50 on concentration)
- frozen joint-score cuts: **0.2746 / -0.1427 / -0.4034**
- mapping: highest confidence => 4pt, then 6pt, then 8pt, else 10pt
- July constraint: hit >=85% of fixed Top10 and avg points <10
- August untouched: July mean/sd, weight, cuts all frozen

## Comparison
|month|strategy|R|hit|avg points|avg comp|cost|return|ROI|profit|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|2026-07|Top6 fixed|87|21.84%|6.00|5.884|870000|930510|107.0%|+60510|
|2026-07|Top10 fixed|87|26.44%|10.00|4.327|870000|858800|98.7%|-11200|
|2026-07|joint variable|87|22.99%|6.80|5.775|870000|954520|109.7%|+84520|
|2026-08|Top6 fixed|109|22.94%|6.00|6.358|1090000|1339050|122.8%|+249050|
|2026-08|Top10 fixed|109|30.28%|10.00|4.584|1090000|1173880|107.7%|+83880|
|2026-08|joint variable|109|25.69%|6.88|6.306|1090000|1281080|117.5%|+191080|

## August variable distribution
|points|R|share|
|---:|---:|---:|
|4|37|33.9%|
|6|25|22.9%|
|8|9|8.3%|
|10|38|34.9%|

## Interpretation
- SHADOW only. July is tune; August is the only untouched test for this joint rule.
- Compare primarily against fixed Top6 and Top10 under the same 10k Dutch definition.
- If joint variable does not beat fixed Top6 in August, the evidence currently favors simple Top6 over complexity.
