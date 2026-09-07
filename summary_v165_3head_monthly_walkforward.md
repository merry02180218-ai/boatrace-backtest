# v165 3-head monthly walk-forward

- source: `analysis_v108_1head_feasibility.csv`
- target: `winner==3`
- explicit features: 10
- strict monthly walk-forward: target month trains only on earlier dates

|month|R|actual 3-head|AUC|Brier|p>=20 R|head%|p>=25 R|head%|p>=30 R|head%|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-06 | 4388 | 12.69% | 0.6607 | 0.10621 | 517 | 26.89% | 196 | 34.69% | 73 | 41.10% |
| 2026-07 | 4772 | 13.12% | 0.6187 | 0.11134 | 618 | 23.62% | 236 | 30.51% | 87 | 29.89% |
| 2026-08 | 4776 | 13.53% | 0.6588 | 0.11180 | 650 | 27.54% | 264 | 35.23% | 110 | 43.64% |

## Aggregate

- R: 13936
- actual 3-head: 13.12%
- AUC: 0.6457
- Brier: 0.10988
- p>=0.15: 4101R, head 20.56%
- p>=0.20: 1785R, head 25.99%
- p>=0.25: 696R, head 33.48%
- p>=0.30: 270R, head 38.52%
- p>=0.35: 98R, head 37.76%
- p>=0.40: 30R, head 46.67%
