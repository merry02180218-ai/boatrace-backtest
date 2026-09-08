# v204 3-head audited Dutch10k discovery -> locked test

- ROI definition: exactly 10,000 yen/race, equal-gross Dutch, 100-yen rounding
- source settlement: corrected official closing odds from v202/v203 audit
- discovery: 2025-12..2026-02 only
- locked test: 2026-03..2026-06 only
- test is never used for rule ranking
- exploratory/SHADOW only; production unchanged

## Baseline
|segment|R|hit|avg composite odds|ROI|
|---|---:|---:|---:|---:|
|DISCOVERY BASE|240|24.58%|5.270|76.5%|
|LOCKED TEST BASE|246|32.11%|3.804|79.8%|

## Top discovery rules, frozen on locked test
|rank|rule|Disc R|Disc hit|Disc comp|Disc ROI|Test R|Test hit|Test comp|Test ROI|
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|1|p3>=0.300 & turn>=-0.2 & straight>=0.0|16|50.00%|4.295|141.4%|19|36.84%|3.666|71.0%|
|2|p3>=0.325 & turn>=0.0|15|46.67%|5.463|141.7%|13|30.77%|5.170|72.2%|
|3|p3>=0.300 & turn>=0.0|21|47.62%|6.184|137.4%|23|39.13%|4.068|86.3%|
|4|p3>=0.300 & turn>=-0.2 & straight>=-0.2|18|44.44%|4.096|125.7%|25|36.00%|3.479|74.4%|
|5|p3>=0.300 & turn>=-0.2 & ST>=-0.2|17|35.29%|6.574|117.1%|23|47.83%|5.049|133.3%|
|6|p3>=0.300 & turn>=-0.2|42|33.33%|5.017|98.1%|51|37.25%|4.034|96.4%|
|7|p3>=0.325 & turn>=-0.2|29|31.03%|4.662|93.4%|26|38.46%|4.328|113.0%|
|8|p3>=0.300 & straight>=-0.2|103|24.27%|5.668|82.5%|126|30.16%|3.531|76.8%|
|9|p3>=0.300|240|24.58%|5.270|76.5%|246|32.11%|3.804|79.8%|
|10|p3>=0.350 & turn>=-0.2|17|35.29%|3.666|78.0%|15|40.00%|3.819|135.2%|
|11|p3>=0.350|84|27.38%|3.838|72.6%|77|38.96%|3.290|106.6%|
|12|p3>=0.300 & turn>=-0.4|97|23.71%|4.753|66.4%|109|37.61%|3.885|97.3%|
|13|p3>=0.325 & turn>=-0.4|63|25.40%|4.473|68.4%|61|39.34%|3.570|112.5%|
|14|p3>=0.325|156|23.08%|5.320|63.8%|137|37.23%|3.518|94.7%|
|15|p3>=0.325 & turn>=-0.4 & ST>=-0.2|19|21.05%|6.172|69.6%|21|42.86%|4.970|133.7%|

## Interpretation
- 5 rule(s) cleared provisional locked-test screen: Test R>=20 and audited Dutch ROI>=100%.
- Treat only as SHADOW candidates because this feature family has prior historical inspection; do not production-adopt from v204 alone.
