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
|1|p3>=0.300 & turn>=-0.2 & straight>=0.0|0|0.00%|0.000|0.0%|0|0.00%|0.000|0.0%|

## Interpretation
- No rule cleared Test R>=20 and audited Dutch ROI>=100%. Keep v165/v166 production unchanged.
