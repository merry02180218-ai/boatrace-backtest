# v200 3号艇 turn>=-0.2 robustness diagnostics

- source: v198 strict walk-forward frozen predictions
- window: 2025-12 .. 2026-06 only (Jul/Aug excluded)
- candidate: turn_margin23 >= -0.2 (predeclared in v199)
- production remains unchanged; this is NOT an adoption test

## Overall
|rule|R|3-head|hit|Top10 cov|cost|return|ROI|
|---|---:|---:|---:|---:|---:|---:|---:|
|BASE|493|34.48%|28.19%|81.76%|491000|381840|77.8%|
|turn>=-0.2|93|45.16%|35.48%|78.57%|91000|99950|109.8%|

## Payout-cap sensitivity
|cap per hit|R|cost|capped return|ROI|
|---:|---:|---:|---:|---:|
|3000|93|91000|61200|67.3%|
|5000|93|91000|72810|80.0%|
|10000|93|91000|88660|97.4%|

## Leave-one-winning-hit-out sensitivity
|case|ROI|removed date|race|removed return|
|---|---:|---|---|---:|
|worst remaining ROI|89.6%|2026-05-01|202605010205|19280|
|best remaining ROI|110.5%|2026-01-05|202601051301|460|

### Five largest winning returns
|date|race|return|ROI after removal|
|---|---|---:|---:|
|2026-05-01|202605010205|19280|89.6%|
|2025-12-09|202512091108|11450|98.3%|
|2026-05-13|202605131104|10560|99.3%|
|2025-12-27|202512270307|5820|104.6%|
|2026-06-01|202606011407|5030|105.5%|

## Monthly ROI distribution
|month|R|ROI|
|---|---:|---:|
|2025-12|15|151.8%|
|2026-01|21|52.6%|
|2026-02|6|77.3%|
|2026-03|9|105.2%|
|2026-04|7|43.1%|
|2026-05|10|336.4%|
|2026-06|25|65.6%|

- monthly median ROI: 77.3%
- months ROI >=100%: 3/7
- months ROI >=80%: 3/7

## Sequence risk
- longest losing streak: 5 settled races
- max drawdown (100 yen x Top10 accounting): 16890 yen
- max drawdown span: 2025-12-27/202512270307 -> 2026-04-21/202604211301
- ending cumulative profit: 8950 yen
