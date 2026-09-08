# v201 3号艇 combo discovery -> locked late validation

- discovery: 2025-12..2026-02 only
- locked test: 2026-03..2026-06 only
- joined features: ex_margin23 / st_margin23 / straight_margin23 / turn_margin23
- search ranking emphasizes 10,000-yen capped ROI to reduce jackpot dependence
- minimum discovery sample: 15 races
- exploratory only; production is unchanged

## Baseline
|segment|R|3-head|hit|ROI|
|---|---:|---:|---:|---:|
|DISCOVERY BASE|245|29.80%|24.49%|69.1%|
|LOCKED TEST BASE|248|39.11%|31.85%|86.2%|

## Top locked rules
|rank|rule|Disc R|Disc ROI|Disc cap10k|Test R|Test head|Test hit|Test ROI|Test cap10k|
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|1|p3>=0.325 & turn>=0.0|0|0.0%|0.0%|0|0.00%|0.00%|0.0%|0.0%|

## Interpretation
- No rule cleared the provisional locked-test screen (R>=20, raw ROI>=100%, capped ROI>=100%).
- Keep v165/v166 production unchanged; do not force a combo filter from this search.
